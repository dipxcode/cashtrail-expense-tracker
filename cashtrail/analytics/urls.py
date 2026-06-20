from django.urls import path
from . import views

urlpatterns = [
    path('', views.analytics_dashboard, name='analytics'),
    path('ai-insights/', views.ai_insights, name='ai_insights'),
    path('reports/', views.reports, name='reports'),
    path('export/csv/', views.export_csv, name='export_csv'),
]
