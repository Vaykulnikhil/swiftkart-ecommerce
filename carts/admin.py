from django.contrib import admin
from .models import Cart, CartItem

class CartAdmin(admin.ModelAdmin):
    list_display = ('cart_id', 'date_added')

class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'cart', 'quantity', 'get_variations', 'is_active')
    
    def get_variations(self, obj):
        return ", ".join([v.variation_value for v in obj.variations.all()])
    get_variations.short_description = 'Variations'

admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
