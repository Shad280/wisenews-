"""
Customer Support Chat Routes for WiseNews
Handles chatbot interactions and support ticket management
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from auth_decorators import login_required, get_current_user
from chatbot_support import support_chatbot
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Create blueprint
support_bp = Blueprint('support', __name__)

@support_bp.route('/support')
def support_center():
    """Support center landing page"""
    return render_template('support_center.html')

@support_bp.route('/support/chat')
@login_required
def chat_interface():
    """Chat interface for logged-in users"""
    user = get_current_user()
    
    # Create new chat session
    session_id = support_chatbot.create_chat_session(user['id'] if user else None)
    session['chat_session_id'] = session_id
    
    return render_template('chat_interface.html', user=user, session_id=session_id)

@support_bp.route('/support/chat/guest')
def guest_chat():
    """Chat interface for guest users"""
    # Create guest chat session
    session_id = support_chatbot.create_chat_session()
    session['chat_session_id'] = session_id
    
    return render_template('chat_interface.html', user=None, session_id=session_id)

@support_bp.route('/api/chat/send', methods=['POST'])
def send_message():
    """Send message to chatbot"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get or create session
        session_id = session.get('chat_session_id')
        if not session_id:
            session_id = support_chatbot.create_chat_session()
            session['chat_session_id'] = session_id
        
        # Get user info if logged in
        user = get_current_user()
        user_id = user['id'] if user else None
        user_email = user['email'] if user else None
        
        # Process message through chatbot
        response = support_chatbot.process_message(
            session_id, message, user_id, user_email
        )
        
        return jsonify({
            'response': response['message'],
            'escalated': response['escalated'],
            'ticket_id': response['ticket_id'],
            'suggestions': response['suggestions'],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in chat send: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@support_bp.route('/api/chat/history')
def get_chat_history():
    """Get chat history for current session"""
    try:
        session_id = session.get('chat_session_id')
        if not session_id:
            return jsonify({'messages': []})
        
        messages = support_chatbot.get_chat_history(session_id)
        return jsonify({'messages': messages})
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@support_bp.route('/api/chat/end', methods=['POST'])
def end_chat():
    """End current chat session"""
    try:
        session_id = session.get('chat_session_id')
        if session_id:
            # Update session end time
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE chat_sessions 
                SET session_end = CURRENT_TIMESTAMP, resolved = TRUE
                WHERE id = ?
            ''', (session_id,))
            conn.commit()
            conn.close()
            
            # Clear session
            session.pop('chat_session_id', None)
        
        return jsonify({'status': 'Chat ended successfully'})
        
    except Exception as e:
        logger.error(f"Error ending chat: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@support_bp.route('/api/chat/feedback', methods=['POST'])
def submit_feedback():
    """Submit chat satisfaction feedback"""
    try:
        data = request.get_json()
        session_id = session.get('chat_session_id')
        satisfaction = data.get('satisfaction', 3)  # 1-5 scale
        
        if session_id:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE chat_sessions 
                SET satisfaction_score = ?
                WHERE id = ?
            ''', (satisfaction, session_id))
            conn.commit()
            conn.close()
        
        return jsonify({'status': 'Feedback submitted'})
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@support_bp.route('/support/tickets')
@login_required
def my_tickets():
    """View user's support tickets"""
    user = get_current_user()
    
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, subject, description, category, priority, status, created_at, updated_at
            FROM support_tickets
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user['id'],))
        
        tickets = []
        for row in cursor.fetchall():
            tickets.append({
                'id': row[0],
                'subject': row[1],
                'description': row[2],
                'category': row[3],
                'priority': row[4],
                'status': row[5],
                'created_at': row[6],
                'updated_at': row[7]
            })
        
        conn.close()
        return render_template('support_tickets.html', tickets=tickets)
        
    except Exception as e:
        logger.error(f"Error loading tickets: {e}")
        return render_template('support_tickets.html', tickets=[], error="Error loading tickets")

@support_bp.route('/support/faq')
def faq():
    """Frequently Asked Questions page"""
    try:
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT question, answer, category
            FROM knowledge_base
            ORDER BY category, usage_count DESC
        ''')
        
        faqs = {}
        for row in cursor.fetchall():
            category = row[2]
            if category not in faqs:
                faqs[category] = []
            faqs[category].append({
                'question': row[0],
                'answer': row[1]
            })
        
        conn.close()
        return render_template('faq.html', faqs=faqs)
        
    except Exception as e:
        logger.error(f"Error loading FAQ: {e}")
        return render_template('faq.html', faqs={}, error="Error loading FAQ")

@support_bp.route('/support/contact')
def contact_form():
    """Contact form for general inquiries"""
    return render_template('contact_form.html')

@support_bp.route('/api/contact/submit', methods=['POST'])
def submit_contact():
    """Submit contact form"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        subject = data.get('subject', '').strip()
        message = data.get('message', '').strip()
        
        if not all([name, email, subject, message]):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Create a support ticket for contact form submission
        conn = sqlite3.connect('news_database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO support_tickets (user_id, subject, description, category, priority)
            VALUES (NULL, ?, ?, 'contact_form', 'medium')
        ''', (f"{subject} - From: {name} ({email})", f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"))
        
        ticket_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Send email notification (when configured)
        support_chatbot.send_escalation_email(ticket_id, email, subject, message)
        
        return jsonify({
            'status': 'Message sent successfully',
            'ticket_id': ticket_id
        })
        
    except Exception as e:
        logger.error(f"Error submitting contact form: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Initialize chatbot when blueprint is loaded
try:
    # This ensures the database tables are created
    support_chatbot.setup_database()
    logger.info("Support chatbot initialized successfully")
except Exception as e:
    logger.error(f"Error initializing support chatbot: {e}")
