import re
import serial
import datetime
import pytz
import time
from django.db.models import Count
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from colorfield.fields import ColorField

from main_app import bluetooth
from main_app.device_handler import DeviceHandler, BluetoothHostError, RemoteDeviceCurrentlyInUseError


class RemoteDevice(models.Model):
	MODES = (
		('BT', 'Bluetooth'),
		('USB', 'USB'),)

	remotedevice_name = models.CharField(max_length=30, unique=True, verbose_name=_('Device name'))
	remotedevice_mode = models.CharField(max_length=3, choices=MODES, default=MODES[0][0], verbose_name='Mode')
	remotedevice_serial = models.CharField(max_length=30, blank=True, default = '', verbose_name=_('MAC address'))
	remotedevice_dev = models.CharField(max_length=20, unique=True, verbose_name=_('Device interface'))

	remotedevice_last_connection_attempt = models.DateTimeField(null=True, blank=True, default=None)
	remotedevice_last_connection_status = models.CharField(max_length=10, blank=True, default = '')
	remotedevice_last_status_request = models.DateTimeField(null=True, blank=True, default=None)
	remotedevice_last_status = models.CharField(max_length=4, blank=True, default = '', verbose_name=_('Status'))
	remotedevice_last_time_offset = models.IntegerField(null=True, blank=True, default=None)

	def __unicode__(self):
		return self.remotedevice_name

	def enable(self, enable=True):
		if enable:
			self.remotedevice_last_connection_attempt = timezone.now()
			self.remotedevice_last_connection_status = ''

		if self.remotedevice_mode == 'BT':
			if not bluetooth.enable(enable):
				if enable:
					self.remotedevice_last_connection_status = 'BT_EN_ERR'
					self.save()
					raise BluetoothHostError(self.get_last_connection_status_msg())
			if enable:
				rfcomm_mac, rfcomm_status = bluetooth.get_rfcomm_status(self)
				if rfcomm_status not in ['clean', 'closed', None]:
					raise RemoteDeviceCurrentlyInUseError(_('Device is currently in use')+repr(rfcomm_status))


	def get_last_connection_status_msg(self):
		CONNECTION_STATUS_CODES = {
			'': _('Connection status unknown'),
			'OK': _('Connection has been successfully established'),
			'BT_EN_ERR': _('Cannot enable bluetooth'),
			'TIMEOUT': _('Bluetooth connection timeout'),
			'OPEN_ERR': _('Unable to connect to the device')
		}

		if self.remotedevice_last_connection_status in CONNECTION_STATUS_CODES:
			return CONNECTION_STATUS_CODES[self.remotedevice_last_connection_status]
		else:
			return self.remotedevice_last_connection_status

	def get_last_status_msg(self): # TO DO
		return self.remotedevice_last_status

	def get_last_rtc_info_msg(self):
		if self.remotedevice_last_time_offset == None:
			return _('RTC has not been read')
		if self.remotedevice_last_time_offset == 2147483647:
			return _('RTC offset cannot be determined because the system clock was not set')
		elif self.remotedevice_last_time_offset == -2147483648:
			return _('Error when reading RTC on the remote device')
		else:
			return _('RTC offset has been determined successfully')

	def is_last_rtc_offset_valid(self):
		return self.remotedevice_last_time_offset not in [None, 2147483647, -2147483648]



class ClockDriftLog(models.Model):
	clockdriftlog_remotedevice = models.ForeignKey(RemoteDevice)
	clockdriftlog_syst_time = models.DateTimeField()
	clockdriftlog_rtc_offset_before_sync = models.IntegerField()
	clockdriftlog_rtc_offset_after_sync = models.IntegerField(null=True)


class Serie(models.Model):
	SUM = 'SUM'
	AVERAGE = 'AVG'
	SERIE_TYPES = (
		(SUM, _('Sum')),
		(AVERAGE, _('Average')),
	)

	serie_name = models.CharField(max_length=30)
	serie_remotedevice = models.ForeignKey(RemoteDevice)
	serie_tag = models.CharField(max_length=2)
	serie_type = models.CharField(max_length=3, choices=SERIE_TYPES)
	serie_unit = models.CharField(max_length=10)
	serie_last_timestamp = models.DateTimeField(null=True, blank=True)
	serie_last_update = models.CharField(max_length=12, default='000000,000')
	serie_values_multiplier = models.FloatField(default=1)
	serie_values_offset = models.FloatField(default=0)
	serie_values_decimals = models.IntegerField(default=0)

	class Meta:
		unique_together = ('serie_remotedevice', 'serie_tag',)
	
	def __unicode__(self):
		return '%s (%s:%s)' % (self.serie_name, self.serie_remotedevice.remotedevice_name, self.serie_tag)

	def update(self, nb_file_max, device_handler=None, keep_device_open=False):
		output = {}
		
		if device_handler is None:
			device_handler = DeviceHandler(self.serie_remotedevice, request_status=True)

		file_list_header, file_list_index = self.serie_last_update.split(',')
		cmd = 'GET_DATA_FILES_LIST:%s%s,%03d,%03d' % (str(self.serie_tag), str(file_list_header), int(file_list_index), nb_file_max)
		output['cmd']=cmd
		device_handler.send_command(cmd)
		resp_header = device_handler.read_response(8+4+4+2, timeout=2)
		output['resp_header']=resp_header
		if re.match('^%s\d{6},\d{3},\d{3}\r\n$'%str(self.serie_tag), resp_header):
			list_header, index, nb_files = resp_header.split(',')
			nb_files=int(nb_files)
			index=int(index)
			resp_body_length=nb_files*10
			resp_body=device_handler.read_response(resp_body_length, timeout=1)
			output['resp_body'] = resp_body

			if re.match('^(%s\d{6}\r\n){%d}$'%(str(self.serie_tag), nb_files), resp_body):
				output['file_list']={}
				for file_name in resp_body.split('\r\n')[:-1]:
					output['file_list'][file_name] = self.update_single_day(file_name[2:], device_handler)
				if not keep_device_open:
					device_handler.close()
				self.serie_last_update = '%s,%03d' % (list_header[2:], index+nb_files-1)
				output['last_update'] = self.serie_last_update
				self.serie_last_timestamp = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
				self.save()
			else:
				device_handler.close()
				raise Exception('resp_body: %s' % repr(resp_body))
		else:
			device_handler.close()
			raise Exception('resp_header: %s' % repr(resp_header))

		return output

	def update_single_day(self, date, device_handler):

		output = {}

		try:
			year=2000+int(date[:2])
			month=int(date[2:4])
			day=int(date[4:6])

			cmd = 'GET_DATA_%s:%s' % (str(self.serie_type), str(self.serie_tag))
	
			cmd += '%02d%02d%02d' % (year%100, month, day)
			output['cmd']=cmd
			device_handler.send_command(cmd)
			resp = device_handler.read_response({'SUM': 360, 'AVG': 312}[str(self.serie_type)], timeout=2)

			existing_datafields_list = {}
		
			datafields_to_update = []
			new_datafields_list = []

			if re.match('^(\d{2}h\d{2}[CI]:[0-9A-F]{%d}\r\n)+$' % {'SUM': 6, 'AVG': 4}[str(self.serie_type)], resp):
				datafield_updated = 0

				# Retrieve existing DataFields from the database
				datafields_list = DataField.objects.filter(datafield_serie=self, datafield_timestamp__contains='%04d-%02d-%02d' % (year, month, day)).values_list('id','datafield_timestamp',  'datafield_nb_points')
				for id, timestamp, nbPoints in datafields_list:
					existing_datafields_list[timestamp.hour] = nbPoints

				for datafield in resp.split('\r\n')[:-1]:
					hour = int(datafield[:2])
					nbPoints = int(datafield[3:5])
					value = int(datafield[-({'SUM': 6, 'AVG': 4}[str(self.serie_type)]):], 16)

					if not hour in existing_datafields_list:
						new_datafields_list.append(DataField(datafield_serie=self, datafield_nb_points=nbPoints, datafield_timestamp=datetime.datetime(year, month, day, hour, 0, 0, 0, tzinfo=pytz.utc), datafield_value=value))
					elif hour in existing_datafields_list and nbPoints > existing_datafields_list[hour]:
						existing_datafield = DataField.objects.get(datafield_serie=self, datafield_timestamp__contains='%04d-%02d-%02d %02d' % (year, month, day, hour))
						existing_datafield.datafield_nb_points = nbPoints
						existing_datafield.datafield_value = value
						existing_datafield.save()
						datafield_updated+=1
			
				DataField.objects.bulk_create(new_datafields_list)

				output['datafields_added']=len(new_datafields_list)
				output['datafields_updated']= datafield_updated
			else:
				raise Exception(_('Invalid response from the remote device: ')+ repr(resp))
		except serial.SerialException, err:
			raise Exception(_('Communication error with the remote device'))

		return output

	def get_raw_data(self, date, hour=None, device_handler=None, keep_device_open=False):
		output = {}
		
		if device_handler is None:
			device_handler = DeviceHandler(self.serie_remotedevice)

		epoch = time.mktime(time.strptime('%02d.%02d.%04d' % (date.day, date.month, date.year), '%d.%m.%Y'))
		try:
			hour = '%02d' % (int(hour)%24)
		except ValueError:
			hour = 'xx'

		cmd = 'GET_DATA_RAW:%s%02d%02d%02d,%s' % (str(self.serie_tag), date.year % 100, date.month, date.day, hour)
		output['cmd']=cmd
		device_handler.send_command(cmd)

		if hour == 'xx':
			resp = device_handler.read_response((5+60*(1+3))*24, timeout=2)
		else:
			resp = device_handler.read_response(5+60*(1+3), timeout=2)

		if re.match('^(\r\n\d{2}h:([0-9A-F]{2,3}|\?{2,3})(,([0-9A-F]{2,3}|\?{2,3})){0,59})+$', resp):
			output['data'] = {}
			for line in resp.split('\r\n')[1:]:
				pts=[]
				for pt in line[4:].split(','):
					if pt.startswith('?'):
						pts.append('?')
					else:
						pts.append((int(pt,16)-self.serie_values_offset)*self.serie_values_multiplier)
				output['data'][int(line[:2])] = pts
			if not keep_device_open:
				device_handler.close()
			
			
		else:
			device_handler.close()
			raise Exception('resp: %s' % repr(resp))

		return output


class DataField(models.Model):
	datafield_serie = models.ForeignKey(Serie)
	datafield_nb_points = models.IntegerField()
	datafield_timestamp = models.DateTimeField()
	datafield_value = models.IntegerField()

	class Meta:
		unique_together = ('datafield_serie', 'datafield_timestamp',)

class TimelineChart(models.Model):
	timelinechart_title = models.CharField(max_length=30, verbose_name=_('Title'))
	timelinechart_yaxis_text = models.CharField(max_length=30, verbose_name=_('Y axis text'))
	timelinechart_series = models.ManyToManyField(Serie, through='SeriePlot', verbose_name='Series')

	def __unicode__(self):
		return self.timelinechart_title

class SeriePlot(models.Model):
	serieplot_serie = models.ForeignKey(Serie, verbose_name='Serie')
	serieplot_timelinechart = models.ForeignKey(TimelineChart)
	serieplot_color = ColorField(verbose_name=_('Color'))
	serieplot_rank = models.IntegerField(default=1)



