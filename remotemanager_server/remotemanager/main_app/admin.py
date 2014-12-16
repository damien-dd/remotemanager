from django.contrib import admin
from django import forms
from main_app.models import RemoteDevice, Serie, TimelineChart, SeriePlot
from django.core.exceptions import ValidationError
import re

admin.site.register(Serie)


class MyRemoteDeviceAdminForm(forms.ModelForm):
	class Meta:
		model = RemoteDevice

	def clean(self):
		#cleaned_data=super(MyRemoteDeviceAdminForm, self).clean()
		# do something that validates your data
		if self.cleaned_data['remotedevice_mode'] == 'BT' and re.match('^/dev/rfcomm\d$', self.cleaned_data['remotedevice_dev']) is None:
			raise ValidationError('Le lien vers l\'interface bluetooth doit etre de la forme /dev/rfcommX')
		if self.cleaned_data['remotedevice_mode'] == 'USB' and re.match('^/dev/(ttyUSB|ttyACM)\d+$', self.cleaned_data['remotedevice_dev']) is None:
			raise ValidationError('Le lien vers l\'interface USB doit etre de la forme /dev/ttyUSBX ou /dev/ttyACMX')
		return self.cleaned_data


class RemoteDeviceAdmin(admin.ModelAdmin):
	list_display = ('remotedevice_name', 'remotedevice_serial', 'remotedevice_dev', 'remotedevice_mode', )
	radio_fields = {'remotedevice_mode': admin.HORIZONTAL}
	form = MyRemoteDeviceAdminForm

admin.site.register(RemoteDevice, RemoteDeviceAdmin)

class SeriePlotInline(admin.TabularInline):
	model = SeriePlot
	extra = 1


class TimelineChartAdmin(admin.ModelAdmin):
	inlines = (SeriePlotInline,)

admin.site.register(TimelineChart, TimelineChartAdmin)
