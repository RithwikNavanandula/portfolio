"""
whatsapp/whatsapp_api.py - WhatsApp API functions
"""
import requests
import logging
import os

logger = logging.getLogger(__name__)

def get_config():
    """Get WhatsApp config from database"""
    from .models import WhatsAppConfig
    return WhatsAppConfig.objects.first()

def get_access_token():
    """Get access token"""
    config = get_config()
    return config.access_token if config else None

def send_whatsapp_message(to_number, text=None, template_name=None, media_path=None, media_type='image'):
    """
    Send WhatsApp message via Meta API
    
    Args:
        to_number: Phone number to send to
        text: Text message content
        template_name: Template name (optional)
        media_path: Local file path for media (optional)
        media_type: Type of media - 'image', 'document', 'audio', 'video'
    
    Returns:
        dict: API response or error
    """
    config = get_config()
    if not config or not config.access_token:
        logger.error("WhatsApp not configured")
        return {'error': 'WhatsApp not configured', 'success': False}
    
    # Normalize phone number
    phone = str(to_number).strip().replace(' ', '').replace('-', '')
    if phone.startswith('+'):
        phone = phone[1:]
    
    headers = {
        "Authorization": f"Bearer {config.access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # If media is provided, upload it first
        if media_path and os.path.exists(media_path):
            logger.info(f"Uploading media: {media_path}")
            media_id = upload_media(config, media_path, media_type)
            if media_id:
                return send_media_message(config, phone, media_id, media_type, text, headers)
            else:
                logger.error(f"Media upload failed for: {media_path}")
                return {'error': 'Failed to upload media to WhatsApp', 'success': False}
        elif media_path:
            logger.error(f"Media file not found: {media_path}")
            return {'error': f'Media file not found: {media_path}', 'success': False}
        
        # Send text or template message
        url = f"https://graph.facebook.com/v19.0/{config.phone_number_id}/messages"
        
        if text:
            payload = {
                "messaging_product": "whatsapp",
                "to": phone,
                "type": "text",
                "text": {"body": text}
            }
        elif template_name:
            payload = {
                "messaging_product": "whatsapp",
                "to": phone,
                "type": "template",
                "template": {"name": template_name, "language": {"code": "en"}}
            }
        else:
            return {'error': 'No text or template provided', 'success': False}
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        result = response.json()
        
        if response.status_code >= 400:
            logger.error(f"WhatsApp API error: {result}")
            return {'error': result.get('error', {}).get('message', 'Unknown error'), 'success': False, 'response': result}
        
        logger.info(f"WhatsApp message sent: {result}")
        return {'success': True, **result}
        
    except requests.Timeout:
        logger.error("WhatsApp API timeout")
        return {'error': 'Request timeout', 'success': False}
    except requests.RequestException as e:
        logger.error(f"WhatsApp API request error: {e}")
        return {'error': str(e), 'success': False}
    except Exception as e:
        logger.error(f"WhatsApp API error: {e}")
        return {'error': str(e), 'success': False}


def upload_media(config, file_path, media_type='image'):
    """Upload media to WhatsApp and return media ID"""
    url = f"https://graph.facebook.com/v19.0/{config.phone_number_id}/media"
    
    # Log file info
    file_size = os.path.getsize(file_path)
    logger.info(f"Uploading: {file_path} ({file_size} bytes, type: {media_type})")
    
    # Determine mime type
    mime_types = {
        'image': 'image/jpeg',
        'document': 'application/pdf',
        'audio': 'audio/mpeg',
        'video': 'video/mp4',
    }
    
    # Get extension and determine mime type
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.png']:
        mime_type = 'image/png'
    elif ext in ['.jpg', '.jpeg']:
        mime_type = 'image/jpeg'
    elif ext in ['.pdf']:
        mime_type = 'application/pdf'
    elif ext in ['.mp3']:
        mime_type = 'audio/mpeg'
    elif ext in ['.mp4']:
        mime_type = 'video/mp4'
    else:
        mime_type = mime_types.get(media_type, 'application/octet-stream')
    
    logger.info(f"Mime type: {mime_type}")
    
    headers = {"Authorization": f"Bearer {config.access_token}"}
    
    try:
        with open(file_path, 'rb') as f:
            files = {
                'file': (os.path.basename(file_path), f, mime_type),
                'messaging_product': (None, 'whatsapp'),
                'type': (None, mime_type),
            }
            logger.info(f"Sending to: {url}")
            response = requests.post(url, headers=headers, files=files, timeout=60)
            
            logger.info(f"Response status: {response.status_code}")
            result = response.json()
            logger.info(f"Response body: {result}")
            
            if 'id' in result:
                logger.info(f"Media uploaded successfully: {result['id']}")
                return result['id']
            else:
                logger.error(f"Media upload failed: {result}")
                return None
    except Exception as e:
        logger.error(f"Media upload error: {e}")
        return None


def send_media_message(config, phone, media_id, media_type, caption, headers):
    """Send a media message using uploaded media ID"""
    url = f"https://graph.facebook.com/v19.0/{config.phone_number_id}/messages"
    
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": media_type,
    }
    
    # Add media object with optional caption
    media_obj = {"id": media_id}
    if caption and media_type in ['image', 'document', 'video']:
        media_obj["caption"] = caption
    
    payload[media_type] = media_obj
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        result = response.json()
        
        if response.status_code >= 400:
            logger.error(f"WhatsApp media send error: {result}")
            return {'error': result.get('error', {}).get('message', 'Unknown error'), 'success': False}
        
        logger.info(f"WhatsApp media message sent: {result}")
        return {'success': True, **result}
    except Exception as e:
        logger.error(f"WhatsApp media send error: {e}")
        return {'error': str(e), 'success': False}
