from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payments/', views.payments, name='payments'),
    path('create_order/', views.create_order, name='create_order'),
    path('order_complete/', views.order_complete, name='order_complete'),





]
