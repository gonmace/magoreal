from django.urls import path

from . import views

app_name = 'html_translator'

urlpatterns = [
    path('callback/', views.callback, name='callback'),
    path('request/', views.request_translation, name='request'),
]
