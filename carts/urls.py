from django.urls import path
from . import views

app_name = 'carts'

urlpatterns = [
    path('', views.cart, name='cart'),  
    path('add/<int:product_id>/', views.add_cart, name='add_cart'),  # Plus button
    path('decrease/<int:cart_item_id>/', views.decrease_cart, name='decrease_cart'),
    path('delete/<int:cart_item_id>/', views.delete_cart_item, name='delete_cart_item'),

    path('checkout/', views.checkout, name='checkout'),





]
