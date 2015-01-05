import datetime
from django import forms
from django.utils.translation import ugettext_lazy as _

from main_app.models import RemoteDevice

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
	limit_to = forms.IntegerField(min_value=0, initial=500, label=_('Limit number of points to'))

	def __init__(self, *args, **kwargs):
		super(DataHistoryForm, self).__init__(*args, **kwargs)
		self.initial['timestep'] = 'day'
