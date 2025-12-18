"""
agents/admin.py - Admin registration for agents models
"""
from django.contrib import admin
from .models import Agent, ChatAssignment, AdminNotification

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'user', 'is_available']

@admin.register(ChatAssignment)
class ChatAssignmentAdmin(admin.ModelAdmin):
    list_display = ['customer', 'agent', 'status', 'assigned_at']

@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ['customer', 'message', 'is_read', 'created_at']
