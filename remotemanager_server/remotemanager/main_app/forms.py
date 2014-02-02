from main_app.models import RemoteDevice
from django import forms
import datetime

class ProgramLoaderForm(forms.Form):
	device = forms.ModelChoiceField(queryset = RemoteDevice.objects.all())
	file = forms.FileField()


class DataHistoryForm(forms.Form):
	HOURLY = 'hour'
	DAILY = 'day'
	MONTHLY = 'month'
	YEARLY = 'year'
	TIMESTEPS = (
		(HOURLY, 'Horaire'),
		(DAILY, 'Journalier'),
		(MONTHLY, 'Mensuel'),
		(YEARLY, 'Annuel'),
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

	timestep = forms.ChoiceField(choices=TIMESTEPS, label='Pas')
	timezone = forms.ChoiceField(choices=TIMEZONE_CHOICES, label='Fuseau horaire')
	from_date = forms.DateField(initial=datetime.date.today)
	to_date = forms.DateField(initial=datetime.date.today)
