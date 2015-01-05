import re
from django.contrib import admin
from django import forms
from main_app.models import RemoteDevice, Serie, TimelineChart, SeriePlot
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

admin.site.register(Serie)


class MyRemoteDeviceAdminForm(forms.ModelForm):
	remotedevice_dev = forms.CharField(required=False, widget=forms.Select(choices=[]), label='Interface')

	class Meta:
		model = RemoteDevice

	def __init__(self, *args, **kwargs):
		super(MyRemoteDeviceAdminForm, self).__init__(*args, **kwargs)
		if hasattr(self, 'instance') and self.instance.remotedevice_mode == 'USB':
			self.fields['remotedevice_dev'].widget.choices = [(self.instance.remotedevice_dev, self.instance.remotedevice_dev+' (current)')]

	def clean(self):
		# do something that validates your data
		if self.cleaned_data['remotedevice_mode'] == 'BT':
			if re.match('^([0-9A-Fa-f]{2}[:]){5}([0-9A-Fa-f]{2})$', self.cleaned_data['remotedevice_serial']) is None:
				if len(self.cleaned_data['remotedevice_serial']) == 0:
					raise ValidationError(_('MAC address is missing'))
				else:
					raise ValidationError(_('Invalid MAC address: ')+self.cleaned_data['remotedevice_serial'])
			if re.match('^/dev/rfcomm\d+$', self.instance.remotedevice_dev) is None:
				rfcomm_dev_list = RemoteDevice.objects.filter(remotedevice_mode='BT').values_list('remotedevice_dev', flat=True)
				for rfcomm_num in range(100):
					rfcomm_dev = u'/dev/rfcomm%d' % rfcomm_num
					if rfcomm_dev not in rfcomm_dev_list:
						self.cleaned_data['remotedevice_dev'] = rfcomm_dev
						break
				if re.match('^/dev/rfcomm\d+$', self.cleaned_data['remotedevice_dev']) is None:
					raise ValidationError('No more rfcomm interfaces')
			else:
				self.cleaned_data['remotedevice_dev'] = self.instance.remotedevice_dev
		
		if self.cleaned_data['remotedevice_mode'] == 'USB' and re.match('^/dev/(ftdi|arduino)', self.cleaned_data['remotedevice_dev']) is None:
			raise ValidationError('Le lien vers l\'interface USB doit etre de la forme /dev/ftdi... ou /dev/arduino...')
		return self.cleaned_data


class RemoteDeviceAdmin(admin.ModelAdmin):
	list_display = ('remotedevice_name', 'remotedevice_dev', 'remotedevice_serial', 'remotedevice_mode', )
	radio_fields = {'remotedevice_mode': admin.HORIZONTAL}

	fields = ('remotedevice_name', 'remotedevice_mode', ('remotedevice_dev', 'remotedevice_serial'),)

	form = MyRemoteDeviceAdminForm

	class Media:
		js = ['/static/js/mode_change.js']

admin.site.register(RemoteDevice, RemoteDeviceAdmin)

class SeriePlotInline(admin.TabularInline):
	model = SeriePlot
	extra = 0


class TimelineChartAdmin(admin.ModelAdmin):
	inlines = (SeriePlotInline,)

admin.site.register(TimelineChart, TimelineChartAdmin)
