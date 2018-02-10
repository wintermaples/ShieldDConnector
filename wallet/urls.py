from django.conf.urls import url, include
from .views import *

urlpatterns = [
    url(r'^create/', create, name='create'),
    url(r'^address/', address, name='address'),
    url(r'^balance/', balance, name='balance'),
    url(r'^tip/', tip, name='tip'),
    url(r'^send/', send, name='send'),
    url(r'^list/', list, name='list'),
    url(r'^delete/', delete, name='delete'),
    url(r'^rain/', rain, name='rain'),
]
