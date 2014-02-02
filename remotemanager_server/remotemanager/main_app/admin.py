from django.contrib import admin
from django import forms
from main_app.models import BluetoothRemoteDevice, USBRemoteDevice, RemoteDevice, Serie, TimelineChart, SeriePlot
from django.core.exceptions import ValidationError
import re

admin.site.register(Serie)
#admin.site.register(RemoteDevice)

class MyUSBRemoteDeviceAdminForm(forms.ModelForm):
	class Meta:
		model = USBRemoteDevice

	def clean_dev(self):
		# do something that validates your data
		if re.match('^/dev/(ttyUSB|ttyACM)\d', self.cleaned_data["remotedevice_dev"]) is None:
			raise ValidationError('Le lien vers l\'interface doit etre de la forme /dev/xxx')
		return self.cleaned_data["remotedevice_dev"]

class USBRemoteDeviceAdmin(admin.ModelAdmin):
	form = MyUSBRemoteDeviceAdminForm

admin.site.register(USBRemoteDevice, USBRemoteDeviceAdmin)



class MyBluetoothRemoteDeviceAdminForm(forms.ModelForm):
	class Meta:
		model = BluetoothRemoteDevice

	def clean_dev(self):
		# do something that validates your data
		if re.match('^/dev/rfcomm\d$', self.cleaned_data["remotedevice_dev"]) is None:
			raise ValidationError('Le lien vers l\'interface doit etre de la forme /dev/rfcommN avec N un nombre')
		return self.cleaned_data["remotedevice_dev"]

class BluetoothRemoteDeviceAdmin(admin.ModelAdmin):
	form = MyBluetoothRemoteDeviceAdminForm

admin.site.register(BluetoothRemoteDevice, BluetoothRemoteDeviceAdmin)

class SeriePlotInline(admin.TabularInline):
	model = SeriePlot
	extra = 1


class TimelineChartAdmin(admin.ModelAdmin):
	inlines = (SeriePlotInline,)

admin.site.register(TimelineChart, TimelineChartAdmin)
