"""
chatbot/admin.py - Admin registration for chatbot models
"""
from django.contrib import admin
from .models import ChatbotFlow, ChatbotNode, ChatbotConnection, ChatbotSession

@admin.register(ChatbotFlow)
class ChatbotFlowAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'trigger_type', 'priority']

@admin.register(ChatbotNode)
class ChatbotNodeAdmin(admin.ModelAdmin):
    list_display = ['flow', 'node_type', 'title']

@admin.register(ChatbotConnection)
class ChatbotConnectionAdmin(admin.ModelAdmin):
    list_display = ['from_node', 'to_node', 'label']

@admin.register(ChatbotSession)
class ChatbotSessionAdmin(admin.ModelAdmin):
    list_display = ['customer', 'flow', 'is_active']
