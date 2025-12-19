"""
chatbot/engine.py - Chatbot engine for auto-triggering flows
"""
import logging
from .models import ChatbotFlow, ChatbotNode, ChatbotSession

logger = logging.getLogger(__name__)


class ChatbotEngine:
    """Engine for processing chatbot flows"""
    
    def process_message(self, customer, message_text, button_payload=None):
        """Process an incoming message from a customer"""
        
        # Check for active session first
        session = self.get_active_session(customer)
        
        if session:
            return self.continue_session(session, message_text, button_payload)
        
        # No active session - check if message triggers a flow
        flow = self.find_matching_flow(customer, message_text)
        
        if flow:
            return self.start_flow(customer, flow, message_text)
        
        return {'handled': False, 'response': None}
    
    def get_active_session(self, customer):
        """Get active chatbot session for customer"""
        return ChatbotSession.objects.filter(
            customer=customer,
            is_active=True
        ).first()
    
    def find_matching_flow(self, customer, message_text):
        """Find a flow that matches the message"""
        message_lower = message_text.lower().strip()
        
        # Get all active flows ordered by priority
        active_flows = ChatbotFlow.objects.filter(is_active=True).order_by('-priority')
        
        for flow in active_flows:
            if self.flow_matches(flow, customer, message_lower):
                return flow
        
        return None
    
    def flow_matches(self, flow, customer, message_lower):
        """Check if a flow matches the given message"""
        
        if flow.trigger_type == 'all':
            return True
        
        if flow.trigger_type == 'keyword':
            keywords = flow.trigger_keywords or []
            for keyword in keywords:
                if keyword.lower() in message_lower:
                    return True
        
        if flow.trigger_type == 'first_message':
            # Only trigger if customer has no previous messages
            from whatsapp.models import Message
            # Count is 1 because current message was just saved
            if Message.objects.filter(customer=customer).count() <= 1:
                return True
        
        return False
    
    def start_flow(self, customer, flow, message_text):
        """Start a new chatbot flow for a customer"""
        start_node = flow.get_start_node()
        
        if not start_node:
            logger.warning(f"Flow {flow.name} has no start node")
            return {'handled': False, 'response': None}
        
        # Create session
        session = ChatbotSession.objects.create(
            customer=customer,
            flow=flow,
            current_node=start_node,
            context={'original_message': message_text}
        )
        
        # Execute first node
        return self.execute_node(session, start_node)
    
    def continue_session(self, session, message_text, button_payload=None):
        """Continue an existing chatbot session"""
        if not session.current_node:
            session.end_session()
            return {'handled': False, 'response': None}
        
        # Store user input in context
        session.context['last_input'] = message_text
        session.context['button_payload'] = button_payload
        session.save()
        
        # Find next node based on input
        next_node = self.get_next_node(session, message_text, button_payload)
        
        if next_node:
            session.current_node = next_node
            session.save()
            return self.execute_node(session, next_node)
        
        # No matching next node - end session
        session.end_session()
        return {'handled': False, 'response': None}
    
    def get_next_node(self, session, message_text, button_payload):
        """Get the next node based on current state and user input"""
        current_node = session.current_node
        connections = current_node.outgoing.all()
        
        # If button payload, find matching connection
        if button_payload:
            for conn in connections:
                if conn.condition.get('button_id') == button_payload:
                    return conn.to_node
        
        # If there's only one connection, follow it
        if connections.count() == 1:
            return connections.first().to_node
        
        # Default: return first connection
        return connections.first().to_node if connections.exists() else None
    
    def execute_node(self, session, node):
        """Execute a node and return the response"""
        
        if node.node_type == 'start':
            # Start nodes just transition to next
            next_node = self.get_next_node(session, '', None)
            if next_node:
                session.current_node = next_node
                session.save()
                return self.execute_node(session, next_node)
        
        elif node.node_type == 'message':
            message = node.config.get('message', '')
            self.send_message(session.customer, message)
            
            # Auto-advance to next node
            next_node = self.get_next_node(session, '', None)
            if next_node:
                session.current_node = next_node
                session.save()
                return self.execute_node(session, next_node)
            
            return {'handled': True, 'response': message}
        
        elif node.node_type == 'buttons':
            message = node.config.get('message', '')
            buttons = node.config.get('buttons', [])
            self.send_buttons(session.customer, message, buttons)
            session.waiting_for_input = True
            session.save()
            return {'handled': True, 'response': message, 'buttons': buttons}
        
        elif node.node_type == 'input':
            message = node.config.get('prompt', 'Please reply:')
            self.send_message(session.customer, message)
            session.waiting_for_input = True
            session.save()
            return {'handled': True, 'response': message, 'waiting_input': True}
        
        elif node.node_type == 'end':
            message = node.config.get('message', '')
            if message:
                self.send_message(session.customer, message)
            session.end_session()
            self.create_notification(session.customer, f"Chatbot ended: {session.flow.name}")
            return {'handled': True, 'response': message, 'ended': True}
        
        return {'handled': True, 'response': None}
    
    def send_message(self, customer, message):
        """Send a text message to customer"""
        from whatsapp.whatsapp_api import send_whatsapp_message
        from whatsapp.models import Message
        
        result = send_whatsapp_message(customer.phone_number, text=message)
        
        # Save sent message
        Message.objects.create(
            customer=customer,
            content=message,
            direction='sent',
            status='sent',
            whatsapp_message_id=result.get('messages', [{}])[0].get('id', '')
        )
        
        logger.info(f"Chatbot sent: {message[:50]}")
    
    def send_buttons(self, customer, message, buttons):
        """Send a message with buttons - falls back to text for now"""
        # For now, send as text with numbered options
        button_text = "\n".join([f"{i+1}. {b.get('title', b)}" for i, b in enumerate(buttons)])
        full_message = f"{message}\n\n{button_text}"
        self.send_message(customer, full_message)
    
    def create_notification(self, customer, message):
        """Create admin notification"""
        try:
            from agents.models import AdminNotification
            AdminNotification.objects.create(
                customer=customer,
                message=message
            )
        except Exception as e:
            logger.error(f"Error creating notification: {e}")


# Global engine instance
engine = ChatbotEngine()


def process_incoming_message(customer, message_text, button_payload=None):
    """Convenience function to process incoming messages"""
    return engine.process_message(customer, message_text, button_payload)
