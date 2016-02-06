from django.conf.urls import url
from django.contrib import admin
from djangodbmodel.views import dbmodel

urlpatterns = [
    url(r'^$', dbmodel, name='dbmodel'),
]
