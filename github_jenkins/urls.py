from django.conf.urls.defaults import patterns, url, include
from django.contrib import admin

from app.views import home, done, logout, error, projects, pull_requests, rebuild_pr
from app.notifications import jenkins, github

admin.autodiscover()


main_patterns = patterns(
    '',
    url(r'^$', home, name='home'),
    url(r'^projects/$', projects, name='projects'),
    url(r'^pull_requests/(?P<owner>.*?)/(?P<project>.*?)/$', pull_requests, name='pull_requests'),
    url(r'^build/(?P<owner>.*?)/(?P<project>.*?)/(?P<pr>\d+)/$', rebuild_pr, name='rebuild'),
    url(r'^done/$', done, name='done'),
    url(r'^error/$', error, name='error'),
    url(r'^logout/$', logout, name='logout'),
    url(r'^notification/jenkins/$', jenkins, name='notify_jenkins'),
    url(r'^notification/github/$', github, name='notify_github'),
    url(r'', include('social_auth.urls')),
)

urlpatterns = patterns(
    '',
    url(r'^github-jenkins/', include(main_patterns)),
    url(r'^github-jenkins-admin/', include(admin.site.urls)),
    url(r'^github-jenkins-admin/doc/', include('django.contrib.admindocs.urls')),
)
