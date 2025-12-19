"""
dashboard/views.py - All dashboard views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Max, Count

from whatsapp.models import Customer, Message
from agents.models import Agent, ChatAssignment, AdminNotification


def login_view(request):
    """Login page"""
    if request.user.is_authenticated:
        return redirect('inbox')
    
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('inbox')
        else:
            error = 'Invalid username or password'
    
    return render(request, 'dashboard/login.html', {'error': error})


def logout_view(request):
    """Logout"""
    logout(request)
    return redirect('login')


@login_required
def inbox_view(request):
    """Main inbox - all customer chats"""
    customers = Customer.objects.annotate(
        last_msg_time=Max('messages__timestamp'),
        msg_count=Count('messages')
    ).order_by('-last_msg_time')
    
    assignments = {
        a.customer_id: a 
        for a in ChatAssignment.objects.filter(status__in=['pending', 'active']).select_related('agent')
    }
    
    agents = Agent.objects.filter(is_available=True)
    notifications = AdminNotification.objects.filter(is_read=False)[:5]
    
    customer_data = []
    for c in customers:
        last_msg = c.messages.order_by('-timestamp').first()
        customer_data.append({
            'customer': c,
            'assignment': assignments.get(c.id),
            'last_message': last_msg
        })
    
    unassigned = len([cd for cd in customer_data if not cd['assignment']])
    
    context = {
        'customer_data': customer_data,
        'agents': agents,
        'notifications': notifications,
        'unassigned_count': unassigned,
        'total_count': len(customer_data),
        'notification_count': AdminNotification.objects.filter(is_read=False).count(),
    }
    return render(request, 'dashboard/inbox.html', context)


@login_required
def chat_view(request, customer_id):
    """Chat conversation with media support and error handling"""
    customer = get_object_or_404(Customer, id=customer_id)
    customers = Customer.objects.annotate(
        last_msg_time=Max('messages__timestamp')
    ).order_by('-last_msg_time')
    
    error_message = None
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        media_file = request.FILES.get('media')
        
        # Validate - need either content or media
        if not content and not media_file:
            error_message = "Please enter a message or attach a file"
        else:
            from whatsapp.whatsapp_api import send_whatsapp_message
            import os
            from django.conf import settings
            
            # Handle media upload
            media_path = None
            try:
                if media_file:
                    # Save media file temporarily
                    media_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
                    os.makedirs(media_dir, exist_ok=True)
                    media_path = os.path.join(media_dir, media_file.name)
                    
                    with open(media_path, 'wb+') as f:
                        for chunk in media_file.chunks():
                            f.write(chunk)
                    
                    # Determine media type
                    ext = os.path.splitext(media_file.name)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                        media_type = 'image'
                    elif ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']:
                        media_type = 'document'
                    elif ext in ['.mp4', '.mov', '.avi']:
                        media_type = 'video'
                    elif ext in ['.mp3', '.wav', '.ogg']:
                        media_type = 'audio'
                    else:
                        media_type = 'document'
                else:
                    media_type = None
                
                # Send message
                result = send_whatsapp_message(
                    customer.phone_number, 
                    text=content or None,
                    media_path=media_path,
                    media_type=media_type
                )
                
                # Check if send was successful
                if result.get('success'):
                    # Create message record
                    message = Message.objects.create(
                        customer=customer,
                        content=content or '',
                        direction='sent',
                        status='sent',
                        whatsapp_message_id=result.get('messages', [{}])[0].get('id', '')
                    )
                    
                    # Save uploaded media to message
                    if media_file:
                        message.media = media_file
                        message.save()
                else:
                    # Send failed - save as failed message with error details
                    error_message = result.get('error', 'Failed to send message')
                    
                    Message.objects.create(
                        customer=customer,
                        content=content or f'[Media: {media_file.name if media_file else ""}]',
                        direction='sent',
                        status='failed',
                        error_detail=error_message,
                    )
            finally:
                # Always clean up temp file
                if media_path and os.path.exists(media_path):
                    os.remove(media_path)
        
        if not error_message:
            return redirect('chat', customer_id=customer_id)
    
    messages = customer.messages.order_by('timestamp')
    assignment = ChatAssignment.objects.filter(customer=customer, status__in=['pending', 'active']).first()
    agents = Agent.objects.filter(is_available=True)
    
    context = {
        'customer': customer,
        'customers': customers,
        'messages': messages,
        'assignment': assignment,
        'agents': agents,
        'error_message': error_message,
    }
    return render(request, 'dashboard/chat.html', context)


@login_required
def chat_messages_api(request, customer_id):
    """API for fetching messages"""
    customer = get_object_or_404(Customer, id=customer_id)
    messages = customer.messages.order_by('timestamp')
    
    data = []
    for m in messages:
        media_url = None
        if m.media:
            media_url = m.media.url
        
        data.append({
            'id': m.id,
            'content': m.content,
            'direction': m.direction,
            'timestamp': m.timestamp.strftime('%b %d, %H:%M'),
            'status': m.status,
            'media_url': media_url,
        })
    
    return JsonResponse({'messages': data})


def privacy_view(request):
    """Privacy policy page - public, no login required"""
    return render(request, 'dashboard/privacy.html')


def terms_view(request):
    """Terms of service page - public, no login required"""
    return render(request, 'dashboard/terms.html')


@login_required
def quick_replies_api(request):
    """API to get quick reply templates"""
    from agents.models import CannedResponse
    
    responses = CannedResponse.objects.all()
    data = [
        {
            'id': r.id,
            'title': r.title,
            'shortcut': r.shortcut,
            'content': r.content,
            'category': r.category,
        }
        for r in responses
    ]
    return JsonResponse({'replies': data})


@login_required
def assign_chat(request, customer_id):
    """Assign a chat to an agent"""
    if request.method == 'POST':
        customer = get_object_or_404(Customer, id=customer_id)
        agent_id = request.POST.get('agent_id')
        
        if agent_id:
            agent = get_object_or_404(Agent, id=agent_id)
            
            # Close existing assignment
            ChatAssignment.objects.filter(
                customer=customer, 
                status__in=['pending', 'active']
            ).update(status='resolved')
            
            # Create new assignment
            ChatAssignment.objects.create(
                customer=customer,
                agent=agent,
                status='active'
            )
        
        return redirect('chat', customer_id=customer_id)
    
    return redirect('inbox')


@login_required
def search_messages(request):
    """Search messages across all conversations"""
    query = request.GET.get('q', '').strip()
    
    results = []
    if query and len(query) >= 2:
        from django.db.models import Q
        messages_found = Message.objects.filter(
            Q(content__icontains=query) |
            Q(customer__name__icontains=query) |
            Q(customer__phone_number__icontains=query)
        ).select_related('customer').order_by('-timestamp')[:50]
        
        results = [
            {
                'id': m.id,
                'content': m.content[:100],
                'customer_id': m.customer_id,
                'customer_name': m.customer.name,
                'timestamp': m.timestamp.strftime('%b %d, %H:%M'),
                'direction': m.direction,
            }
            for m in messages_found
        ]
    
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({'results': results, 'query': query})
    
    return render(request, 'dashboard/search.html', {
        'results': results,
        'query': query,
    })
