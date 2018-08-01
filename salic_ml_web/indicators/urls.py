from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('db_test', views.db_connection_test, name='db_test'),
]
