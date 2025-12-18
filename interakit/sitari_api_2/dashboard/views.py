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
    """Chat conversation"""
    customer = get_object_or_404(Customer, id=customer_id)
    customers = Customer.objects.annotate(
        last_msg_time=Max('messages__timestamp')
    ).order_by('-last_msg_time')
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            from whatsapp.whatsapp_api import send_whatsapp_message
            result = send_whatsapp_message(customer.phone_number, text=content)
            
            Message.objects.create(
                customer=customer,
                content=content,
                direction='sent',
                status='sent',
                whatsapp_message_id=result.get('messages', [{}])[0].get('id', '')
            )
            return redirect('chat', customer_id=customer_id)
    
    messages = customer.messages.order_by('timestamp')
    
    context = {
        'customer': customer,
        'customers': customers,
        'messages': messages,
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
