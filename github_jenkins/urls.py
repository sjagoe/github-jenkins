from django.conf.urls.defaults import patterns, url, include
from django.contrib import admin

from app.views import home, done, logout, error, form, form2

admin.autodiscover()


urlpatterns = patterns('',
    url(r'^github-jenkins/$', home, name='home'),
    url(r'^github-jenkins/done/$', done, name='done'),
    url(r'^github-jenkins/error/$', error, name='error'),
    url(r'^github-jenkins/logout/$', logout, name='logout'),
    url(r'^github-jenkins/form/$', form, name='form'),
    url(r'^github-jenkins/form2/$', form2, name='form2'),
    # url(r'^github-jenkins/admin/', include(admin.site.urls)),
    # url(r'^github-jenkins/admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^github-jenkins/', include('social_auth.urls')),
)
