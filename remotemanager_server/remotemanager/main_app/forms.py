from main_app.models import RemoteDevice
from django import forms


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

	timestep = forms.ChoiceField(choices=TIMESTEPS)


