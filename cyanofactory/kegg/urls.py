"""
Copyright (c) 2013 Gabriel Kind <gkind@hs-mittweida.de>
Hochschule Mittweida, University of Applied Sciences

Released under the MIT license
"""
from django.conf.urls import url
from . import views

app_name = "kegg"

urlpatterns = [
    url(r'^$', views.index, name="index"),
    url(r'^ajax/$', views.index_ajax, name="index_ajax"),
    url(r'^(?P<map_id>map[0-9]{5})/$', views.map_view, name="map_view")
]
