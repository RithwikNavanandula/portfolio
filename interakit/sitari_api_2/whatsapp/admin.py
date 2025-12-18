"""
whatsapp/admin.py - Admin registration for whatsapp models
"""
from django.contrib import admin
from .models import Customer, Message, WhatsAppConfig

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'created_at']
    search_fields = ['name', 'phone_number']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['customer', 'direction', 'status', 'timestamp']
    list_filter = ['direction', 'status']

@admin.register(WhatsAppConfig)
class WhatsAppConfigAdmin(admin.ModelAdmin):
    list_display = ['phone_number_id']
