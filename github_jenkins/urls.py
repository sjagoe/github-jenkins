from django.conf.urls.defaults import patterns, url, include
from django.contrib import admin

from github_jenkins.app.urls import urlpatterns as app_urlpatterns

admin.autodiscover()


urlpatterns = patterns(
    '',
    url(r'^github-jenkins/', include(app_urlpatterns)),
    url(r'^github-jenkins-admin/', include(admin.site.urls)),
    # url(r'^github-jenkins-admin/doc/', include('django.contrib.admindocs.urls')),
)
