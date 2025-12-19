"""
dashboard/urls.py - Dashboard URL routes
"""
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.inbox_view, name='inbox'),
    path('chat/<int:customer_id>/', views.chat_view, name='chat'),
    path('chat/<int:customer_id>/messages/', views.chat_messages_api, name='chat-messages'),
    path('chat/<int:customer_id>/assign/', views.assign_chat, name='assign-chat'),
    path('search/', views.search_messages, name='search'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('terms/', views.terms_view, name='terms'),
    path('api/quick-replies/', views.quick_replies_api, name='quick-replies'),
]
