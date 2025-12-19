"""
whatsapp/models.py - Customer and Message models
"""
from django.db import models


class Customer(models.Model):
    """WhatsApp customer/contact"""
    name = models.CharField(max_length=100, default='Unknown')
    phone_number = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.name} ({self.phone_number})"


class Message(models.Model):
    """WhatsApp message"""
    DIRECTION_CHOICES = [
        ('sent', 'Sent'),
        ('received', 'Received'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField(blank=True)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    media = models.FileField(upload_to='messages/', blank=True, null=True)
    whatsapp_message_id = models.CharField(max_length=100, blank=True)
    error_detail = models.TextField(blank=True, help_text="Error message if send failed")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.direction}: {self.content[:50]}"


class WhatsAppConfig(models.Model):
    """WhatsApp API configuration"""
    phone_number_id = models.CharField(max_length=50)
    access_token = models.TextField(blank=True)
    app_secret = models.CharField(max_length=100, blank=True, help_text="App Secret for webhook signature validation")
    webhook_verify_token = models.CharField(max_length=50, default='sitari_verify_123')
    
    def __str__(self):
        return f"WhatsApp Config ({self.phone_number_id})"

