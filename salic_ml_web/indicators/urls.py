from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('show', views.show_metrics, name='show_metrics'),
    path('db_test', views.db_connection_test, name='db_test'),
    path('db_query', views.projects_to_analyse, name='make_query')
]