from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('show', views.show_metrics, name='metrics'),
    path('db_test', views.dbConnectionTest, name='db_test')
]