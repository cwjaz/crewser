from django.conf.urls import patterns, include, url
from django.contrib import admin
from crewdb.views import member_data, company_data, event_data, crew_data

urlpatterns = patterns('',
  # Examples:
  # url(r'^$', 'crewser.views.home', name='home'),
  # url(r'^blog/', include('blog.urls')),
  
  # different ajax-requests toget data into forms
  url(r'^crewdb/member_data/$', member_data, name='member_data'),
  url(r'^crewdb/company_data/$', company_data, name='company_data'),
  url(r'^crewdb/event_data/$', event_data, name='event_data'),
  url(r'^crewdb/crew_data/$', crew_data, name='crew_data'),
  # main admin url
  url(r'', include(admin.site.urls)),
)
