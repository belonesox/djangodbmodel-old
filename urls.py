from django.conf.urls import url
from django.contrib import admin
from djangodbmodel.views import plate

urlpatterns = [
    url(r'^$', plate, name='plate'),
]
