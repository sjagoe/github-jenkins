from django.conf.urls.defaults import patterns, url, include

from github_jenkins.app.views import home, logout, error, projects, \
    pull_requests, rebuild_pr, pull_requests_body, pull_request_row, \
    new_pull_request_rows
from github_jenkins.app.notifications import jenkins, github


urlpatterns = patterns(
    '',
    url(r'^$', home, name='home'),
    url(r'^projects/$', projects, name='projects'),
    url(r'^pull_requests/(?P<owner>[^/]+?)/(?P<project>[^/]+?)/$', pull_requests,
        name='pull_requests'),
    url(r'^pull_requests/(?P<owner>[^/]+?)/(?P<project>[^/]+?)/update/$',
        pull_requests_body, name='update_pull_requests'),
    url(r'^pull_requests/(?P<owner>[^/]+?)/(?P<project>[^/]+?)/update/(?P<pr_number>\d+)/$',
        pull_request_row, name='update_pull_request'),
    url(r'^pull_requests/(?P<owner>[^/]+?)/(?P<project>[^/]+?)/new/(?P<old_max_pr_number>\d+)/$',
        new_pull_request_rows, name='new_pull_requests'),
    url(r'^build/(?P<owner>[^/]+?)/(?P<project>[^/]+?)/(?P<pr>\d+)/$', rebuild_pr,
        name='rebuild'),
    url(r'^error/$', error, name='error'),
    url(r'^logout/$', logout, name='logout'),
    url(r'^notification/jenkins/$', jenkins, name='notify_jenkins'),
    url(r'^notification/github/$', github, name='notify_github'),
    url(r'', include('social_auth.urls')),
)
