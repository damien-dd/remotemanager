from django.db.models import Count
from django.db import models
from django.core.exceptions import ValidationError
import re
import serial
import datetime
import pytz
import time

from main_app import bluetooth
from main_app.device_handler import DeviceHandler


def validate_mac(mac):
	if re.match('^([0-9A-Fa-f]{2}[:]){5}([0-9A-Fa-f]{2})$', mac) is None:
		raise ValidationError(u'%s n\'est pas une adresse MAC valide' % mac)

def validate_color(color):
	if re.match('^[0-9A-Fa-f]{6}$', color) is None:
		raise ValidationError(u'%s n\'est pas une couleur valide' % color)

def validate_bt_channel(channel):
	if channel < 1 or channel > 7:
		raise ValidationError(u'%d n\'est pas un canal Bluetooth valide' % channel)


class RemoteDevice(models.Model):
	remotedevice_name = models.CharField(max_length=30, unique=True, verbose_name='Nom du peripherique')
	remotedevice_dev = models.CharField(max_length=20, unique=True, verbose_name='Lien vers l\'interface', help_text='Format: <em>/dev/xxx</em>')

	def __unicode__(self):
		return self.remotedevice_name

	def enable(self, enable=True):
		try:
			bt_device = self.bluetoothremotedevice
			if not bluetooth.enable(enable):
				raise Exception('Cannot enable bluetooth')
			rfcomm_mac, rfcomm_status = bluetooth.get_rfcomm_status(bt_device)
			if enable:
				if rfcomm_status not in ['closed', None]:
					raise Exception('Device is currently in use')
				if bt_device.bluetoothremotedevice_mac != rfcomm_mac and not bluetooth.bind_device(bt_device):
					try:
						bluetooth.enable(False)
					except Exception:
						pass
					raise Exception('Cannot bind bluetooth device')
		except BluetoothRemoteDevice.DoesNotExist:
			pass



class USBRemoteDevice(RemoteDevice):
	def __unicode__(self):
		return self.remotedevice_name

class BluetoothRemoteDevice(RemoteDevice):
	bluetoothremotedevice_mac = models.CharField(max_length=17, unique=True, verbose_name='Adresse MAC', help_text='Format: <em>1A:2B:3C:4D:5E:6F</em>', validators=[validate_mac])
	bluetoothremotedevice_channel = models.IntegerField(default=1, verbose_name='Canal Bluetooth', validators=[validate_bt_channel])

	def __unicode__(self):
		return self.remotedevice_name


class Serie(models.Model):
	SUM = 'SUM'
	AVERAGE = 'AVG'
	SERIE_TYPES = (
		(SUM, 'Somme'),
		(AVERAGE, 'Moyenne'),
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
			device_handler = DeviceHandler(self.serie_remotedevice)

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
				raise Exception('Invalid response from the remote device: %s' % repr(resp))
		except serial.SerialException, err:
			raise Exception('Communication error with the remote device')

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
	timelinechart_title = models.CharField(max_length=30, verbose_name='Titre')
	timelinechart_yaxis_text = models.CharField(max_length=30, verbose_name='Axe Y, texte')
	timelinechart_series = models.ManyToManyField(Serie, through='SeriePlot', verbose_name='Series')

	def __unicode__(self):
		return self.timelinechart_title

class SeriePlot(models.Model):
	serieplot_serie = models.ForeignKey(Serie, verbose_name='Serie')
	serieplot_timelinechart = models.ForeignKey(TimelineChart)
	serieplot_color = models.CharField(max_length=6, verbose_name='Couleur', help_text='Format: <em>RRGGBB</em>, example: <em>2f7ed8</em>', validators=[validate_color])
	serieplot_rank = models.IntegerField(default=1)

	
	
	
