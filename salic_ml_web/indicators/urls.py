from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('db_test', views.dbConnectionTest, name='db_test')
]