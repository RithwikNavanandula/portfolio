"""
whatsapp/whatsapp_api.py - WhatsApp API functions
"""
import requests
import logging

logger = logging.getLogger(__name__)

def get_config():
    """Get WhatsApp config from database"""
    from .models import WhatsAppConfig
    return WhatsAppConfig.objects.first()

def get_access_token():
    """Get access token"""
    config = get_config()
    return config.access_token if config else None

def send_whatsapp_message(to_number, text=None, template_name=None):
    """Send WhatsApp message via Meta API"""
    config = get_config()
    if not config or not config.access_token:
        logger.error("WhatsApp not configured")
        return {'error': 'WhatsApp not configured'}
    
    # Normalize phone number
    phone = str(to_number).strip().replace(' ', '').replace('-', '')
    if phone.startswith('+'):
        phone = phone[1:]
    
    url = f"https://graph.facebook.com/v19.0/{config.phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {config.access_token}",
        "Content-Type": "application/json"
    }
    
    if text:
        # Send text message
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": text}
        }
    elif template_name:
        # Send template
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {"name": template_name, "language": {"code": "en"}}
        }
    else:
        return {'error': 'No text or template provided'}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        result = response.json()
        logger.info(f"WhatsApp API response: {result}")
        return result
    except Exception as e:
        logger.error(f"WhatsApp API error: {e}")
        return {'error': str(e)}
