import datetime
import pytz
from django.utils.timezone import get_current_timezone
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import AuthenticationForm
from django.forms.widgets import PasswordInput, TextInput

from main_app.models import RemoteDevice



class CustomAuthenticationForm(AuthenticationForm):
	username = forms.CharField(widget=TextInput(attrs={'class': 'form-control','placeholder': _('Username')}))
	password = forms.CharField(widget=PasswordInput(attrs={'class': 'form-control','placeholder':_('Password')}))

class ProgramLoaderForm(forms.Form):
	device = forms.ModelChoiceField(queryset = RemoteDevice.objects.all())
	file = forms.FileField()


class DataHistoryForm(forms.Form):
	HOURLY = 'hour'
	DAILY = 'day'
	MONTHLY = 'month'
	YEARLY = 'year'
	TIMESTEPS = (
		(HOURLY, _('Hourly')),
		(DAILY, _('Daily')),
		(MONTHLY, _('Monthly')),
		(YEARLY, _('Yearly')),
	)
	TIMEZONE_CHOICES = (
                ('UTC','UTC'),
                ('GMT+1','GMT+1'), ('GMT+2','GMT+2'), ('GMT+3','GMT+3'), ('GMT+4','GMT+4'),
                ('GMT+5','GMT+6'), ('GMT+7','GMT+7'), ('GMT+8','GMT+8'), ('GMT+9','GMT+9'),
                ('GMT+10','GMT+10'), ('GMT+11','GMT+11'), ('GMT+12','GMT+12'),
                ('GMT-1','GMT-1'), ('GMT-2','GMT-2'), ('GMT-3','GMT-3'), ('GMT-4','GMT-4'),
                ('GMT-5','GMT-5'), ('GMT-6','GMT-6'), ('GMT-7','GMT-7'), ('GMT-8','GMT-8'),
                ('GMT-9','GMT-9'), ('GMT-10','GMT-10'), ('GMT-11','GMT-11'), ('GMT-12','GMT-12'),
                ('GMT-13','GMT-13'), ('GMT-14','GMT-14'),
        )

	timestep = forms.ChoiceField(choices=TIMESTEPS, label=_('Timestep'))
	timezone = forms.ChoiceField(choices=TIMEZONE_CHOICES, label=_('Timezone'))
	limit_to = forms.IntegerField(min_value=0, max_value=10000, initial=500, label=_('Limit number of points to'))

	def __init__(self, *args, **kwargs):
		super(DataHistoryForm, self).__init__(*args, **kwargs)
		self.initial['timestep'] = 'day'
		tz_offset = datetime.datetime.now(get_current_timezone()).utcoffset()
		if tz_offset:
			tz_offset_hours = tz_offset.days*24+tz_offset.seconds/3600
			if tz_offset_hours in range(1,13)+range(-14,0):
				self.initial['timezone'] = 'GMT%+d' % tz_offset_hours
			else:
				self.initial['timezone'] = 'UTC'

