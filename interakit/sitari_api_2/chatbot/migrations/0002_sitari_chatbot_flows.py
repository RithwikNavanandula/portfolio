"""
Data migration to create Sitari Solutions chatbot flows
"""
from django.db import migrations


def create_chatbot_flows(apps, schema_editor):
    """Create chatbot flows for Sitari Solutions"""
    ChatbotFlow = apps.get_model('chatbot', 'ChatbotFlow')
    ChatbotNode = apps.get_model('chatbot', 'ChatbotNode')
    ChatbotConnection = apps.get_model('chatbot', 'ChatbotConnection')
    
    # ============================================
    # FLOW 1: Welcome Flow (First Message)
    # ============================================
    welcome_flow = ChatbotFlow.objects.create(
        name='Welcome Flow',
        description='Greets new customers with welcome message and main menu',
        is_active=True,
        trigger_type='first_message',
        trigger_keywords=[],
        priority=10
    )
    
    # Nodes for Welcome Flow
    welcome_start = ChatbotNode.objects.create(
        flow=welcome_flow,
        node_type='start',
        title='Start',
        config={},
        position_x=100,
        position_y=100
    )
    
    welcome_msg = ChatbotNode.objects.create(
        flow=welcome_flow,
        node_type='message',
        title='Welcome Message',
        config={
            'message': '''🙏 *Welcome to Sitari Solutions!*

Your one-stop center for government services in Nizamabad.

How can we help you today?

1️⃣ View Our Services
2️⃣ Check Required Documents
3️⃣ Location & Timings
4️⃣ Talk to Agent

_Reply with a number or type your query_'''
        },
        position_x=100,
        position_y=200
    )
    
    welcome_end = ChatbotNode.objects.create(
        flow=welcome_flow,
        node_type='end',
        title='End Welcome',
        config={},
        position_x=100,
        position_y=300
    )
    
    # Connections for Welcome Flow
    ChatbotConnection.objects.create(from_node=welcome_start, to_node=welcome_msg, label='next')
    ChatbotConnection.objects.create(from_node=welcome_msg, to_node=welcome_end, label='done')
    
    # ============================================
    # FLOW 2: Services Menu Flow
    # ============================================
    services_flow = ChatbotFlow.objects.create(
        name='Services Menu',
        description='Shows all service categories',
        is_active=True,
        trigger_type='keyword',
        trigger_keywords=['hi', 'hello', 'services', 'menu', 'help', '1', 'service'],
        priority=5
    )
    
    services_start = ChatbotNode.objects.create(
        flow=services_flow,
        node_type='start',
        title='Start',
        config={},
        position_x=100,
        position_y=100
    )
    
    services_msg = ChatbotNode.objects.create(
        flow=services_flow,
        node_type='message',
        title='Services Menu',
        config={
            'message': '''📋 *Our Services:*

1️⃣ *Aadhaar* - New, Update, PVC Card
2️⃣ *PAN Card* - New, Correction
3️⃣ *Passport* - Fresh, Renewal, Tatkal
4️⃣ *Voter ID* - New, Correction
5️⃣ *Driving License* - LL, DL, RC
6️⃣ *EPFO/PF* - UAN, Withdrawal, KYC
7️⃣ *Certificates* - Income, Caste, Residence
8️⃣ *Welfare Schemes* - Kalyanalaxmi, Shaadi Mubarak
9️⃣ *Travel* - IRCTC, TTD, Tours
🔟 *Business* - MSME, FSSAI, Stamp Papers

_Reply with a number for more details or type "agent" to talk to us_'''
        },
        position_x=100,
        position_y=200
    )
    
    services_end = ChatbotNode.objects.create(
        flow=services_flow,
        node_type='end',
        title='End Services',
        config={},
        position_x=100,
        position_y=300
    )
    
    ChatbotConnection.objects.create(from_node=services_start, to_node=services_msg, label='next')
    ChatbotConnection.objects.create(from_node=services_msg, to_node=services_end, label='done')
    
    # ============================================
    # FLOW 3: Location & Hours Flow
    # ============================================
    location_flow = ChatbotFlow.objects.create(
        name='Location & Hours',
        description='Shows office location and business hours',
        is_active=True,
        trigger_type='keyword',
        trigger_keywords=['location', 'address', 'where', 'timing', 'hours', 'open', '3', 'map'],
        priority=8
    )
    
    location_start = ChatbotNode.objects.create(
        flow=location_flow,
        node_type='start',
        title='Start',
        config={},
        position_x=100,
        position_y=100
    )
    
    location_msg = ChatbotNode.objects.create(
        flow=location_flow,
        node_type='message',
        title='Location Info',
        config={
            'message': '''📍 *Sitari Solutions*

*Address:*
H.No 6-12-55, opp Jain Mandir,
Shivaji Chowk, Nizamabad - 503002
Telangana, India

*Timings:*
🕘 Mon-Sat: 9:00 AM - 8:00 PM
🕙 Sunday: 10:00 AM - 2:00 PM

*Contact:*
📞 +91 9701629320
📞 +91 9032916616
📞 +91 9581909826

📍 Google Maps: https://maps.google.com/?q=Sitari+Solutions+Nizamabad'''
        },
        position_x=100,
        position_y=200
    )
    
    location_end = ChatbotNode.objects.create(
        flow=location_flow,
        node_type='end',
        title='End Location',
        config={},
        position_x=100,
        position_y=300
    )
    
    ChatbotConnection.objects.create(from_node=location_start, to_node=location_msg, label='next')
    ChatbotConnection.objects.create(from_node=location_msg, to_node=location_end, label='done')
    
    # ============================================
    # FLOW 4: Document Check Flow
    # ============================================
    docs_flow = ChatbotFlow.objects.create(
        name='Document Check',
        description='Shows required documents for services',
        is_active=True,
        trigger_type='keyword',
        trigger_keywords=['documents', 'required', 'papers', 'what need', '2', 'docs'],
        priority=7
    )
    
    docs_start = ChatbotNode.objects.create(
        flow=docs_flow,
        node_type='start',
        title='Start',
        config={},
        position_x=100,
        position_y=100
    )
    
    docs_msg = ChatbotNode.objects.create(
        flow=docs_flow,
        node_type='message',
        title='Documents Info',
        config={
            'message': '''📋 *Common Documents Required:*

*Aadhaar:* Any valid ID proof, Photo
*PAN Card:* Aadhaar, Passport photo
*Passport:* Aadhaar, Birth certificate, Photos
*Voter ID:* Aadhaar, Address proof
*Driving License:* Aadhaar, Age proof
*EPFO:* Aadhaar-linked mobile number
*Certificates:* Aadhaar, Ration Card

💡 _Tip: Bring original documents + 2 photocopies_

Type your service name for specific requirements, or reply "agent" to ask our team.'''
        },
        position_x=100,
        position_y=200
    )
    
    docs_end = ChatbotNode.objects.create(
        flow=docs_flow,
        node_type='end',
        title='End Documents',
        config={},
        position_x=100,
        position_y=300
    )
    
    ChatbotConnection.objects.create(from_node=docs_start, to_node=docs_msg, label='next')
    ChatbotConnection.objects.create(from_node=docs_msg, to_node=docs_end, label='done')
    
    # ============================================
    # FLOW 5: Human Handoff Flow
    # ============================================
    handoff_flow = ChatbotFlow.objects.create(
        name='Human Handoff',
        description='Transfers chat to human agent',
        is_active=True,
        trigger_type='keyword',
        trigger_keywords=['agent', 'human', 'talk', 'call', 'problem', 'issue', '4', 'staff', 'person'],
        priority=9
    )
    
    handoff_start = ChatbotNode.objects.create(
        flow=handoff_flow,
        node_type='start',
        title='Start',
        config={},
        position_x=100,
        position_y=100
    )
    
    handoff_msg = ChatbotNode.objects.create(
        flow=handoff_flow,
        node_type='message',
        title='Handoff Message',
        config={
            'message': '''👤 *Connecting you to our team...*

Our agent will respond shortly during business hours (9 AM - 8 PM).

For urgent help, please call:
📞 +91 9701629320

Thank you for your patience! 🙏'''
        },
        position_x=100,
        position_y=200
    )
    
    handoff_end = ChatbotNode.objects.create(
        flow=handoff_flow,
        node_type='end',
        title='End Handoff',
        config={'message': ''},
        position_x=100,
        position_y=300
    )
    
    ChatbotConnection.objects.create(from_node=handoff_start, to_node=handoff_msg, label='next')
    ChatbotConnection.objects.create(from_node=handoff_msg, to_node=handoff_end, label='done')
    
    # ============================================
    # SERVICE-SPECIFIC FLOWS (Quick Info)
    # ============================================
    
    # Aadhaar Services Flow
    aadhaar_flow = ChatbotFlow.objects.create(
        name='Aadhaar Info',
        description='Aadhaar service details',
        is_active=True,
        trigger_type='keyword',
        trigger_keywords=['aadhaar', 'aadhar', 'uid'],
        priority=6
    )
    
    aadhaar_start = ChatbotNode.objects.create(
        flow=aadhaar_flow, node_type='start', title='Start', config={}, position_x=100, position_y=100
    )
    aadhaar_msg = ChatbotNode.objects.create(
        flow=aadhaar_flow, node_type='message', title='Aadhaar Info',
        config={'message': '''🆔 *Aadhaar Services:*

✅ New Aadhaar Enrollment
✅ Aadhaar Update (Name, Address, Mobile)
✅ PVC Aadhaar Card
✅ Aadhaar Correction

*Documents Required:*
• Any valid ID proof (Voter ID, PAN, etc.)
• Passport size photo
• Mobile number for OTP

*Time:* 15-30 minutes
*Visit:* Mon-Sat, 9 AM - 8 PM

Reply "location" for address or "agent" to talk to us.'''},
        position_x=100, position_y=200
    )
    aadhaar_end = ChatbotNode.objects.create(
        flow=aadhaar_flow, node_type='end', title='End', config={}, position_x=100, position_y=300
    )
    ChatbotConnection.objects.create(from_node=aadhaar_start, to_node=aadhaar_msg, label='next')
    ChatbotConnection.objects.create(from_node=aadhaar_msg, to_node=aadhaar_end, label='done')
    
    # PAN Card Flow
    pan_flow = ChatbotFlow.objects.create(
        name='PAN Card Info',
        description='PAN card service details',
        is_active=True,
        trigger_type='keyword',
        trigger_keywords=['pan', 'pancard', 'pan card'],
        priority=6
    )
    
    pan_start = ChatbotNode.objects.create(
        flow=pan_flow, node_type='start', title='Start', config={}, position_x=100, position_y=100
    )
    pan_msg = ChatbotNode.objects.create(
        flow=pan_flow, node_type='message', title='PAN Info',
        config={'message': '''💳 *PAN Card Services:*

✅ New PAN Card Application
✅ PAN Correction/Update
✅ Lost PAN Card Reprint
✅ Link PAN to Aadhaar

*Documents Required:*
• Aadhaar Card
• Passport size photo
• Signature on white paper

*Time:* 7-15 working days
*Fee:* As per government rates

Reply "location" for address or "agent" to talk to us.'''},
        position_x=100, position_y=200
    )
    pan_end = ChatbotNode.objects.create(
        flow=pan_flow, node_type='end', title='End', config={}, position_x=100, position_y=300
    )
    ChatbotConnection.objects.create(from_node=pan_start, to_node=pan_msg, label='next')
    ChatbotConnection.objects.create(from_node=pan_msg, to_node=pan_end, label='done')
    
    # Passport Flow
    passport_flow = ChatbotFlow.objects.create(
        name='Passport Info',
        description='Passport service details',
        is_active=True,
        trigger_type='keyword',
        trigger_keywords=['passport'],
        priority=6
    )
    
    passport_start = ChatbotNode.objects.create(
        flow=passport_flow, node_type='start', title='Start', config={}, position_x=100, position_y=100
    )
    passport_msg = ChatbotNode.objects.create(
        flow=passport_flow, node_type='message', title='Passport Info',
        config={'message': '''🛂 *Passport Services:*

✅ Fresh Passport Application
✅ Passport Renewal
✅ Tatkal Passport
✅ Minor Passport

*Documents Required:*
• Aadhaar Card
• Birth Certificate
• Passport size photos (white background)
• Old passport (for renewal)

*Appointment:* We help with PSK slot booking
*Time:* Depends on police verification

Reply "location" for address or "agent" to talk to us.'''},
        position_x=100, position_y=200
    )
    passport_end = ChatbotNode.objects.create(
        flow=passport_flow, node_type='end', title='End', config={}, position_x=100, position_y=300
    )
    ChatbotConnection.objects.create(from_node=passport_start, to_node=passport_msg, label='next')
    ChatbotConnection.objects.create(from_node=passport_msg, to_node=passport_end, label='done')


def reverse_chatbot_flows(apps, schema_editor):
    """Remove all chatbot flows"""
    ChatbotFlow = apps.get_model('chatbot', 'ChatbotFlow')
    ChatbotFlow.objects.filter(name__in=[
        'Welcome Flow', 'Services Menu', 'Location & Hours', 
        'Document Check', 'Human Handoff',
        'Aadhaar Info', 'PAN Card Info', 'Passport Info'
    ]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('chatbot', '0001_initial'),
    ]
    
    operations = [
        migrations.RunPython(create_chatbot_flows, reverse_chatbot_flows),
    ]
