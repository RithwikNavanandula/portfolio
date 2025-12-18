"""
whatsapp/views.py - Webhook handler for WhatsApp
"""
import json
import logging
import requests
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Customer, Message, WhatsAppConfig

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(View):
    """Handle WhatsApp webhook requests"""
    
    def get(self, request):
        """Verify webhook (called by Meta to verify endpoint)"""
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        config = WhatsAppConfig.objects.first()
        verify_token = config.webhook_verify_token if config else 'sitari_verify_123'
        
        if mode == 'subscribe' and token == verify_token:
            logger.info("Webhook verified successfully")
            return HttpResponse(challenge)
        
        logger.warning(f"Webhook verification failed: mode={mode}, token={token}")
        return HttpResponse("Verification failed", status=403)
    
    def post(self, request):
        """Handle incoming WhatsApp messages"""
        try:
            data = json.loads(request.body)
            logger.info(f"Webhook received: {json.dumps(data)[:500]}")
            
            entry = data.get('entry', [])
            for ent in entry:
                changes = ent.get('changes', [])
                for change in changes:
                    value = change.get('value', {})
                    messages = value.get('messages', [])
                    
                    for msg in messages:
                        self.process_message(msg, value)
            
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            logger.exception(f"Webhook error: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    def process_message(self, msg, value):
        """Process a single incoming message"""
        phone = msg.get('from', '')
        wa_id = msg.get('id', '')
        msg_type = msg.get('type', 'text')
        
        # Get or create customer
        contact_info = value.get('contacts', [{}])[0]
        name = contact_info.get('profile', {}).get('name', phone)
        
        customer, _ = Customer.objects.get_or_create(
            phone_number=phone,
            defaults={'name': name}
        )
        
        # Update name if changed
        if customer.name == 'Unknown' or customer.name == phone:
            customer.name = name
            customer.save()
        
        # Extract message content
        text = ''
        if msg_type == 'text':
            text = msg.get('text', {}).get('body', '')
        elif msg_type == 'button':
            text = msg.get('button', {}).get('text', '')
        elif msg_type == 'interactive':
            interactive = msg.get('interactive', {})
            if 'button_reply' in interactive:
                text = interactive['button_reply'].get('title', '')
        
        # Prevent duplicates
        if not Message.objects.filter(whatsapp_message_id=wa_id).exists():
            Message.objects.create(
                customer=customer,
                content=text,
                direction='received',
                status='delivered',
                whatsapp_message_id=wa_id
            )
            logger.info(f"Saved message from {phone}: {text[:50]}")
