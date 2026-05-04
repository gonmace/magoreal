from django.urls import path

from . import views

app_name = 'landing'

urlpatterns = [
    path('', views.index, name='index'),
    path('contacto/', views.contacto_submit, name='contacto_submit'),
    path('pliegos/demo/', views.pliego_demo_submit, name='pliego_demo_submit'),
    path('health/live/', views.health_live, name='health_live'),
    path('health/ready/', views.health_ready, name='health_ready'),
    path('dev/letter-preview/', views.letter_preview, name='letter_preview'),
]
