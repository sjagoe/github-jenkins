from django.conf.urls.defaults import patterns, url, include

from github_jenkins.app.views import home, logout, error, projects, pull_requests, rebuild_pr
from github_jenkins.app.notifications import jenkins, github


urlpatterns = patterns(
    '',
    url(r'^$', home, name='home'),
    url(r'^projects/$', projects, name='projects'),
    url(r'^pull_requests/(?P<owner>.*?)/(?P<project>.*?)/$', pull_requests, name='pull_requests'),
    url(r'^build/(?P<owner>.*?)/(?P<project>.*?)/(?P<pr>\d+)/$', rebuild_pr, name='rebuild'),
    url(r'^error/$', error, name='error'),
    url(r'^logout/$', logout, name='logout'),
    url(r'^notification/jenkins/$', jenkins, name='notify_jenkins'),
    url(r'^notification/github/$', github, name='notify_github'),
    url(r'', include('social_auth.urls')),
)
