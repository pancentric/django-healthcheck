from django.conf.urls import patterns, url
from .views import healthcheckview


urlpatterns = patterns('healthcheck.views',
                       url(r'^$', healthcheckview,
                           name="healthcheck"),
                       )