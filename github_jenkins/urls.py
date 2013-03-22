from django.conf.urls.defaults import patterns, url, include
from django.contrib import admin

from app.views import home, done, logout, error, projects, pull_requests

admin.autodiscover()


main_patterns = patterns('',
    url(r'^$', home, name='home'),
    url(r'^projects/$', projects, name='projects'),
                         url(r'^pull_requests/(?P<owner>.*?)/(?P<project>.*?)/$', pull_requests, name='pull_requests'),
    url(r'^done/$', done, name='done'),
    url(r'^error/$', error, name='error'),
    url(r'^logout/$', logout, name='logout'),
    url(r'', include('social_auth.urls')),
)

urlpatterns = patterns('',
    url(r'^github-jenkins/', include(main_patterns)),
    url(r'^github-jenkins-admin/', include(admin.site.urls)),
    url(r'^github-jenkins-admin/doc/', include('django.contrib.admindocs.urls')),
)
