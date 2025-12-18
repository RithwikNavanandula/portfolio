"""
agents/models.py - Agent and notification models
"""
from django.db import models
from django.contrib.auth.models import User


class Agent(models.Model):
    """Support agent"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_profile')
    display_name = models.CharField(max_length=100)
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return self.display_name


class ChatAssignment(models.Model):
    """Assignment of customer chat to agent"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('resolved', 'Resolved'),
    ]
    
    customer = models.ForeignKey('whatsapp.Customer', on_delete=models.CASCADE, related_name='assignments')
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name='assignments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        agent_name = self.agent.display_name if self.agent else 'Unassigned'
        return f"{self.customer.name} → {agent_name}"


class AdminNotification(models.Model):
    """Notification for admin"""
    customer = models.ForeignKey('whatsapp.Customer', on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer.name}: {self.message[:30]}"
