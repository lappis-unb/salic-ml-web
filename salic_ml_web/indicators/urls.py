from django.urls import path
from indicators import views, api_views
from rest_framework import routers
from django.conf.urls import url, include
from django.contrib import admin
from django.views.decorators.csrf import csrf_exempt
from rest_framework_swagger.views import get_swagger_view
from django.views.generic import RedirectView

#indicators_router = routers.DefaultRouter()
#indicators_router.register(r'custom_users', views.CustomUserViewSet)
#indicators_router.register(r'entities', views.EntityViewSet)
#indicators_router.register(r'metrics', views.MetricViewSet)
#indicators_router.register(r'indicators', views.IndicatorViewSet)
#indicators_router.register(r'metric_feedbacks', views.MetricFeedbackViewSet)
#indicators_router.register(r'project_feedbacks', views.ProjectFeedbackViewSet)

urlpatterns = [
    path('projetos/<pronac>', csrf_exempt(api_views.ProjectInfoView.as_view()), name='project_info_view'),
    url(r'^projetos', csrf_exempt(api_views.SearchProjectView.as_view()), name='search_project_view'),
    url(r'^docs', get_swagger_view(title='SalicML API'), name='swagger_index'),
    url(r'^', RedirectView.as_view(pattern_name='swagger_index', permanent=False)),
    # path('admin/', admin.site.urls),
]
