from django.conf.urls import patterns, url, include

from main_app import views

urlpatterns = patterns('',
	url(r'^i18n/', include('django.conf.urls.i18n')),
	url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
	url(r'^logout/$', views.logout_view, name='logout'),
	url(r'^$', views.index, name='index'),
	url(r'^loader/$', views.program_loader, name='loader'),
	
	url(r'^charts/timeline/$', views.timeline_charts, name='timelines'),
	url(r'^chart/timeline/(?P<timelinechart_id>\d+)/$', views.timeline_chart, name='history'),
	url(r'^rtcmd/$', views.rtcmd, name='rtcmd'),
	url(r'^rtcmd/get/vbat/$', views.get_vbat, name='measvbat'),
	url(r'^rtcmd/get/temp/$', views.get_temp, name='meastemp'),
	url(r'^serie/(?P<serie_id>\d+)/(?P<timestep>(hour|day|month|year|(minute\d{6}(\d{2}|xx))))/(?P<timezone>(UTC|(GMT[-+]\d{1,2})))/from/(?P<from_date>\d{8})/to/(?P<to_date>\d{8})/$', views.get_serie, name='serie'),
	url(r'^serie/(?P<serie_id>\d+)/update/$', views.update_serie, name='serie_update'),
	url(r'^test/$', views.test, name='test'),

	url(r'^dev_choices/', views.dev_choices),
)
