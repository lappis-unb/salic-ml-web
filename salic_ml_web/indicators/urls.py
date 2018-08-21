from django.urls import path
from . import views
from rest_framework import routers
from django.conf.urls import url, include

indicators_router = routers.DefaultRouter()
indicators_router.register(r'custom_users', views.CustomUserViewSet)
indicators_router.register(r'entities', views.EntityViewSet)
indicators_router.register(r'metrics', views.MetricViewSet)
indicators_router.register(r'indicators', views.IndicatorViewSet)
indicators_router.register(r'metric_feedbacks', views.MetricFeedbackViewSet)
indicators_router.register(r'project_feedbacks', views.ProjectFeedbackViewSet)

urlpatterns = [
    path('', views.index, name='index'),
    url(r'v2/', include(indicators_router.urls)),
    path('db_test', views.db_connection_test, name='db_test'),
    path('db_query', views.projects_to_analyse, name='make_query'),
    path('user_info', views.fetch_user_data, name='user_info'),
    path('metrics_feedback', views.post_metrics_feedback, name='metrics_feedback_info'),
    path('<str:pronac>', views.show_metrics, name='show_metrics'),
]
