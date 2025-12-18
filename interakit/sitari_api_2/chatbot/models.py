"""
chatbot/models.py - Chatbot flow models
"""
from django.db import models


class ChatbotFlow(models.Model):
    """Chatbot conversation flow"""
    TRIGGER_TYPES = [
        ('keyword', 'Keyword Match'),
        ('first_message', 'First Message'),
        ('all', 'All Messages'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES, default='keyword')
    trigger_keywords = models.JSONField(default=list, blank=True)
    priority = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-priority']
    
    def __str__(self):
        status = "🟢" if self.is_active else "⚪"
        return f"{status} {self.name}"
    
    def get_start_node(self):
        return self.nodes.filter(node_type='start').first()


class ChatbotNode(models.Model):
    """Node in a chatbot flow"""
    NODE_TYPES = [
        ('start', 'Start'),
        ('message', 'Send Message'),
        ('buttons', 'Button Menu'),
        ('input', 'Wait for Input'),
        ('end', 'End Flow'),
    ]
    
    flow = models.ForeignKey(ChatbotFlow, on_delete=models.CASCADE, related_name='nodes')
    node_type = models.CharField(max_length=20, choices=NODE_TYPES)
    title = models.CharField(max_length=100)
    config = models.JSONField(default=dict)
    position_x = models.IntegerField(default=100)
    position_y = models.IntegerField(default=100)
    
    def __str__(self):
        return f"{self.get_node_type_display()}: {self.title}"


class ChatbotConnection(models.Model):
    """Connection between nodes"""
    from_node = models.ForeignKey(ChatbotNode, on_delete=models.CASCADE, related_name='outgoing')
    to_node = models.ForeignKey(ChatbotNode, on_delete=models.CASCADE, related_name='incoming')
    condition = models.JSONField(default=dict, blank=True)
    label = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"{self.from_node.title} → {self.to_node.title}"


class ChatbotSession(models.Model):
    """Active chatbot session"""
    customer = models.ForeignKey('whatsapp.Customer', on_delete=models.CASCADE)
    flow = models.ForeignKey(ChatbotFlow, on_delete=models.CASCADE)
    current_node = models.ForeignKey(ChatbotNode, on_delete=models.SET_NULL, null=True)
    context = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    waiting_for_input = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.customer.name} - {self.flow.name}"
    
    def end_session(self):
        self.is_active = False
        self.save()
