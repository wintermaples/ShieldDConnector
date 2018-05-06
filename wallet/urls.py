from django.conf.urls import url, include
from .views import *

urlpatterns = [
    url(r'^create/', create, name='create'),
    url(r'^address/', address, name='address'),
    url(r'^balance/', balance, name='balance'),
    url(r'^tip/', tip, name='tip'),
    url(r'^send/', send, name='send'),
    url(r'^list/', list, name='list'),
    url(r'^list_txs/', list_txs, name='list_txs'),
    url(r'^delete/', delete, name='delete'),
    url(r'^rain/', rain, name='rain'),
    url(r'^add_manager/', add_manager, name='add_manager'),
    url(r'^remove_manager/', remove_manager, name='remove_manager'),
    url(r'^grant_permission/', grant_permission, name='grant_permission'),
    url(r'^deprive_permission/', deprive_permission, name='deprive_permission'),
    url(r'^get_managers/', get_managers, name='get_managers')
]
