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
from django.core.files.base import ContentFile

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
        """Handle incoming WhatsApp messages and status updates"""
        try:
            # Validate webhook signature if app_secret is configured
            config = WhatsAppConfig.objects.first()
            if config and config.app_secret:
                import hmac
                import hashlib
                
                signature = request.headers.get('X-Hub-Signature-256', '')
                expected_signature = 'sha256=' + hmac.new(
                    config.app_secret.encode(),
                    request.body,
                    hashlib.sha256
                ).hexdigest()
                
                if not hmac.compare_digest(signature, expected_signature):
                    logger.warning("Webhook signature validation failed")
                    return JsonResponse({'error': 'Invalid signature'}, status=403)
            
            data = json.loads(request.body)
            logger.info(f"Webhook received: {json.dumps(data)[:500]}")
            
            entry = data.get('entry', [])
            for ent in entry:
                changes = ent.get('changes', [])
                for change in changes:
                    value = change.get('value', {})
                    
                    # Handle incoming messages
                    messages = value.get('messages', [])
                    for msg in messages:
                        self.process_message(msg, value)
                    
                    # Handle status updates
                    statuses = value.get('statuses', [])
                    for status in statuses:
                        self.process_status(status)
            
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            logger.exception(f"Webhook error: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    def process_status(self, status):
        """Process message status updates (sent, delivered, read)"""
        wa_id = status.get('id', '')
        new_status = status.get('status', '')  # sent, delivered, read, failed
        
        if not wa_id:
            return
        
        # Map WhatsApp status to our status
        status_map = {
            'sent': 'sent',
            'delivered': 'delivered',
            'read': 'read',
            'failed': 'failed',
        }
        
        # Status order for comparison (higher = more progressed)
        status_order = {'pending': 0, 'sent': 1, 'delivered': 2, 'read': 3, 'failed': -1}
        
        mapped_status = status_map.get(new_status)
        if not mapped_status:
            return
        
        # Update message status
        try:
            message = Message.objects.filter(whatsapp_message_id=wa_id).first()
            if message:
                current_order = status_order.get(message.status, 0)
                new_order = status_order.get(mapped_status, 0)
                
                # Only update if new status is more progressed, or if it's a failure
                if mapped_status == 'failed' or new_order > current_order:
                    message.status = mapped_status
                    message.save()
                    logger.info(f"Updated message {wa_id} status to {mapped_status}")
        except Exception as e:
            logger.error(f"Error updating status: {e}")
    
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
        
        # Prevent duplicates
        if Message.objects.filter(whatsapp_message_id=wa_id).exists():
            return
        
        # Extract message content based on type
        text = ''
        media_id = None
        media_type = None
        
        if msg_type == 'text':
            text = msg.get('text', {}).get('body', '')
        elif msg_type == 'button':
            text = msg.get('button', {}).get('text', '')
        elif msg_type == 'interactive':
            interactive = msg.get('interactive', {})
            if 'button_reply' in interactive:
                text = interactive['button_reply'].get('title', '')
        elif msg_type == 'image':
            media_id = msg.get('image', {}).get('id')
            media_type = 'image'
            text = msg.get('image', {}).get('caption', '')
        elif msg_type == 'document':
            media_id = msg.get('document', {}).get('id')
            media_type = 'document'
            text = msg.get('document', {}).get('caption', '')
        elif msg_type == 'audio':
            media_id = msg.get('audio', {}).get('id')
            media_type = 'audio'
        elif msg_type == 'video':
            media_id = msg.get('video', {}).get('id')
            media_type = 'video'
        
        # Create message
        message = Message.objects.create(
            customer=customer,
            content=text,
            direction='received',
            status='delivered',
            whatsapp_message_id=wa_id
        )
        
        # Download and save media if present
        if media_id:
            try:
                self.download_media(message, media_id, media_type)
            except Exception as e:
                logger.error(f"Error downloading media: {e}")
        
        logger.info(f"Saved message from {phone}: {text[:50]}")
        
        # Process through chatbot engine
        try:
            from chatbot.engine import process_incoming_message
            result = process_incoming_message(customer, text)
            if result.get('handled'):
                logger.info(f"Chatbot handled message: {result}")
        except Exception as e:
            logger.error(f"Chatbot error: {e}")
    
    def download_media(self, message, media_id, media_type):
        """Download media from WhatsApp and save to message"""
        config = WhatsAppConfig.objects.first()
        if not config or not config.access_token:
            return
        
        headers = {"Authorization": f"Bearer {config.access_token}"}
        
        # Get media URL
        url_response = requests.get(
            f"https://graph.facebook.com/v19.0/{media_id}",
            headers=headers
        )
        media_url = url_response.json().get('url')
        
        if not media_url:
            return
        
        # Download media
        media_response = requests.get(media_url, headers=headers)
        
        # Determine extension
        ext_map = {'image': 'jpg', 'document': 'pdf', 'audio': 'mp3', 'video': 'mp4'}
        ext = ext_map.get(media_type, 'bin')
        filename = f"{media_id}.{ext}"
        
        # Save to message
        message.media.save(filename, ContentFile(media_response.content))
        message.save()
        logger.info(f"Downloaded media: {filename}")
