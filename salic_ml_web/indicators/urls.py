from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('db_test', views.db_connection_test, name='db_test'),
    path('db_query', views.projects_to_analyse, name='make_query'),
    path('user_info', views.fetch_user_data, name='user_info'),
    path('metrics_feedback', views.post_metrics_feedback, name='metrics_feedback_info'),
    path('<str:pronac>', views.show_metrics, name='show_metrics'),
]
