from django.urls import path

from . import views

app_name = 'portfolio'

urlpatterns = [
    # Sprint 2: detalle de proyecto
    path('<slug:slug>/', views.detalle, name='detalle'),
]
