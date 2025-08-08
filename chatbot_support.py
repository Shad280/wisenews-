"""
WiseNews Customer Support Chatbot
Handles user queries, provides assistance, and escalates issues requiring human intervention
"""

import sqlite3
import json
import logging
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import threading
import time

logger = logging.getLogger(__name__)

class SupportChatbot:
    def __init__(self):
        self.setup_database()
        self.load_knowledge_base()
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email': 'your_support_email@gmail.com',  # Configure with your email
            'password': 'your_app_password',  # Use app password for Gmail
            'support_team_email': 'support@wisenews.com'  # Your support team email
        }
        
        # Keywords that trigger human escalation
        self.escalation_keywords = [
            'refund', 'billing', 'payment', 'charge', 'subscription', 'cancel',
            'legal', 'lawsuit', 'court', 'violation', 'complaint', 'dispute',
            'bug', 'error', 'broken', 'not working', 'crash', 'issue',
            'manager', 'supervisor', 'human', 'person', 'staff', 'team'
        ]
        
        # Common responses for quick help
        self.quick_responses = {
            'greeting': [
                "Hello! I'm the WiseNews support assistant. How can I help you today?",
                "Hi there! Welcome to WiseNews support. What can I assist you with?",
                "Greetings! I'm here to help with any questions about WiseNews."
            ],
            'farewell': [
                "Thank you for using WiseNews! Have a great day!",
                "You're welcome! Feel free to reach out if you need more help.",
                "Glad I could help! Enjoy using WiseNews!"
            ]
        }

    def setup_database(self):
        """Initialize the support database tables"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            # Chat sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_start DATETIME DEFAULT CURRENT_TIMESTAMP,
                    session_end DATETIME,
                    messages_count INTEGER DEFAULT 0,
                    satisfaction_score INTEGER,
                    escalated BOOLEAN DEFAULT FALSE,
                    resolved BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Chat messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    sender TEXT, -- 'user' or 'bot'
                    message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    intent TEXT,
                    confidence REAL,
                    escalated BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
                )
            ''')
            
            # Support tickets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS support_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_id INTEGER,
                    subject TEXT,
                    description TEXT,
                    category TEXT,
                    priority TEXT, -- 'low', 'medium', 'high', 'urgent'
                    status TEXT DEFAULT 'open', -- 'open', 'pending', 'resolved', 'closed'
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    assigned_to TEXT,
                    resolution TEXT,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
                )
            ''')
            
            # Knowledge base table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT,
                    answer TEXT,
                    category TEXT,
                    keywords TEXT,
                    usage_count INTEGER DEFAULT 0,
                    last_used DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Support chatbot database tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Error setting up support database: {e}")

    def load_knowledge_base(self):
        """Load or create the knowledge base with common Q&A"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            # Check if knowledge base is empty
            cursor.execute("SELECT COUNT(*) FROM knowledge_base")
            count = cursor.fetchone()[0]
            
            if count == 0:
                # Populate with initial knowledge base
                knowledge_data = [
                    {
                        'question': 'How do I access the live feeds?',
                        'answer': 'You can access live feeds by going to the "Live Feeds" section in the main menu or visiting /live-feeds. The page shows real-time updates from news, sports, and financial markets.',
                        'category': 'navigation',
                        'keywords': 'live feeds, access, navigation, real-time'
                    },
                    {
                        'question': 'How do I create an account?',
                        'answer': 'Click on "Sign Up" in the top right corner, fill in your details (username, email, password), and click "Create Account". You\'ll receive a confirmation email.',
                        'category': 'account',
                        'keywords': 'account, signup, register, create'
                    },
                    {
                        'question': 'How do I reset my password?',
                        'answer': 'Click "Forgot Password" on the login page, enter your email address, and we\'ll send you a reset link. Follow the instructions in the email.',
                        'category': 'account',
                        'keywords': 'password, reset, forgot, login'
                    },
                    {
                        'question': 'How do I customize my news preferences?',
                        'answer': 'Go to your Profile > News Preferences. You can select categories, sources, and set up personalized alerts for topics that interest you.',
                        'category': 'preferences',
                        'keywords': 'preferences, customize, settings, categories'
                    },
                    {
                        'question': 'How do I save articles?',
                        'answer': 'Click the bookmark icon on any article to save it to your "Saved Articles" collection. You can access saved articles from your profile menu.',
                        'category': 'features',
                        'keywords': 'save, bookmark, articles, collection'
                    },
                    {
                        'question': 'How do I share articles on social media?',
                        'answer': 'Each article has social sharing buttons (Twitter, Facebook, LinkedIn). Click the share icon and select your preferred platform.',
                        'category': 'features',
                        'keywords': 'share, social media, twitter, facebook'
                    },
                    {
                        'question': 'What are live events?',
                        'answer': 'Live events are real-time updates for sports, financial markets, breaking news, and other ongoing events. They update automatically every few minutes.',
                        'category': 'features',
                        'keywords': 'live events, real-time, sports, financial'
                    },
                    {
                        'question': 'How do I report inappropriate content?',
                        'answer': 'Click the "Report" button on any article or use the contact form. Our moderation team reviews all reports within 24 hours.',
                        'category': 'moderation',
                        'keywords': 'report, inappropriate, content, moderation'
                    },
                    {
                        'question': 'How do I change my notification settings?',
                        'answer': 'Go to Profile > Notification Settings. You can enable/disable email notifications, push notifications, and breaking news alerts.',
                        'category': 'notifications',
                        'keywords': 'notifications, settings, email, alerts'
                    },
                    {
                        'question': 'How do I search for specific topics?',
                        'answer': 'Use the search bar at the top of the page. You can search by keywords, topics, sources, or dates. Use filters to narrow down results.',
                        'category': 'search',
                        'keywords': 'search, topics, keywords, filters'
                    },
                    {
                        'question': 'How do I contact customer support?',
                        'answer': 'You can use this chat system, email us at support@wisenews.com, or use the contact form in the Help section.',
                        'category': 'support',
                        'keywords': 'contact, support, help, customer service'
                    },
                    {
                        'question': 'Is my data secure?',
                        'answer': 'Yes! We use industry-standard encryption, secure servers, and never share your personal data with third parties. Read our Privacy Policy for more details.',
                        'category': 'security',
                        'keywords': 'security, data, privacy, encryption'
                    }
                ]
                
                for item in knowledge_data:
                    cursor.execute('''
                        INSERT INTO knowledge_base (question, answer, category, keywords)
                        VALUES (?, ?, ?, ?)
                    ''', (item['question'], item['answer'], item['category'], item['keywords']))
                
                conn.commit()
                logger.info("Knowledge base populated with initial data")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")

    def create_chat_session(self, user_id: Optional[int] = None) -> int:
        """Create a new chat session"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO chat_sessions (user_id)
                VALUES (?)
            ''', (user_id,))
            
            session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            return None

    def add_message(self, session_id: int, sender: str, message: str, intent: str = None, confidence: float = 0.0):
        """Add a message to the chat session"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO chat_messages (session_id, sender, message, intent, confidence)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, sender, message, intent, confidence))
            
            # Update session message count
            cursor.execute('''
                UPDATE chat_sessions 
                SET messages_count = messages_count + 1
                WHERE id = ?
            ''', (session_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")

    def analyze_intent(self, message: str) -> Tuple[str, float]:
        """Analyze user message to determine intent"""
        message_lower = message.lower()
        
        # Greeting patterns
        greeting_words = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
        if any(word in message_lower for word in greeting_words):
            return 'greeting', 0.9
        
        # Farewell patterns
        farewell_words = ['bye', 'goodbye', 'thank you', 'thanks', 'that\'s all']
        if any(word in message_lower for word in farewell_words):
            return 'farewell', 0.9
        
        # Help/question patterns
        question_words = ['how', 'what', 'where', 'when', 'why', 'can you', 'help']
        if any(word in message_lower for word in question_words):
            return 'question', 0.8
        
        # Problem/issue patterns
        problem_words = ['problem', 'issue', 'error', 'not working', 'broken', 'bug']
        if any(word in message_lower for word in problem_words):
            return 'problem', 0.8
        
        # Account-related patterns
        account_words = ['account', 'login', 'password', 'profile', 'register']
        if any(word in message_lower for word in account_words):
            return 'account', 0.7
        
        return 'general', 0.5

    def check_escalation_needed(self, message: str) -> bool:
        """Check if the message requires human intervention"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.escalation_keywords)

    def search_knowledge_base(self, query: str) -> Optional[Dict]:
        """Search the knowledge base for relevant answers"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            # Simple keyword matching (can be improved with better NLP)
            query_words = query.lower().split()
            
            cursor.execute('''
                SELECT id, question, answer, category, keywords, usage_count
                FROM knowledge_base
            ''')
            
            knowledge_items = cursor.fetchall()
            best_match = None
            best_score = 0
            
            for item in knowledge_items:
                item_id, question, answer, category, keywords, usage_count = item
                
                # Calculate relevance score
                score = 0
                keywords_list = keywords.lower().split()
                question_words = question.lower().split()
                
                for word in query_words:
                    if word in keywords_list:
                        score += 2
                    elif word in question_words:
                        score += 1
                    elif word in answer.lower():
                        score += 0.5
                
                if score > best_score:
                    best_score = score
                    best_match = {
                        'id': item_id,
                        'question': question,
                        'answer': answer,
                        'category': category,
                        'score': score
                    }
            
            # Update usage count if we found a good match
            if best_match and best_score > 1:
                cursor.execute('''
                    UPDATE knowledge_base 
                    SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (best_match['id'],))
                conn.commit()
            
            conn.close()
            
            return best_match if best_score > 1 else None
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return None

    def create_support_ticket(self, user_id: int, session_id: int, subject: str, description: str, category: str = 'general') -> int:
        """Create a support ticket for issues requiring human intervention"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            # Determine priority based on keywords
            priority = 'medium'
            description_lower = description.lower()
            
            if any(word in description_lower for word in ['urgent', 'emergency', 'critical', 'broken']):
                priority = 'high'
            elif any(word in description_lower for word in ['refund', 'billing', 'legal']):
                priority = 'high'
            elif any(word in description_lower for word in ['question', 'how to', 'help']):
                priority = 'low'
            
            cursor.execute('''
                INSERT INTO support_tickets (user_id, session_id, subject, description, category, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, session_id, subject, description, category, priority))
            
            ticket_id = cursor.lastrowid
            
            # Mark session as escalated
            cursor.execute('''
                UPDATE chat_sessions 
                SET escalated = TRUE
                WHERE id = ?
            ''', (session_id,))
            
            conn.commit()
            conn.close()
            
            return ticket_id
            
        except Exception as e:
            logger.error(f"Error creating support ticket: {e}")
            return None

    def send_escalation_email(self, ticket_id: int, user_email: str, subject: str, description: str):
        """Send email notification for escalated issues"""
        try:
            # Email template for support team
            email_body = f"""
            New Support Ticket Created - WiseNews

            Ticket ID: #{ticket_id}
            User Email: {user_email}
            Subject: {subject}
            
            Description:
            {description}
            
            Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Please review and respond to this ticket as soon as possible.
            
            Best regards,
            WiseNews Support System
            """
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.email_config['email']
            msg['To'] = self.email_config['support_team_email']
            msg['Subject'] = f"Support Ticket #{ticket_id} - {subject}"
            
            msg.attach(MIMEText(email_body, 'plain'))
            
            # Send email (commented out for security - configure when ready)
            # server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            # server.starttls()
            # server.login(self.email_config['email'], self.email_config['password'])
            # text = msg.as_string()
            # server.sendmail(self.email_config['email'], self.email_config['support_team_email'], text)
            # server.quit()
            
            logger.info(f"Escalation email prepared for ticket #{ticket_id}")
            
        except Exception as e:
            logger.error(f"Error sending escalation email: {e}")

    def process_message(self, session_id: int, user_message: str, user_id: int = None, user_email: str = None) -> Dict:
        """Process user message and generate response"""
        try:
            # Add user message to database
            intent, confidence = self.analyze_intent(user_message)
            self.add_message(session_id, 'user', user_message, intent, confidence)
            
            # Check if escalation is needed
            needs_escalation = self.check_escalation_needed(user_message)
            
            response = {
                'message': '',
                'escalated': False,
                'ticket_id': None,
                'suggestions': []
            }
            
            if needs_escalation:
                # Create support ticket and escalate
                ticket_id = self.create_support_ticket(
                    user_id, session_id, 
                    f"User Query: {user_message[:100]}...", 
                    user_message,
                    'escalation'
                )
                
                if user_email:
                    self.send_escalation_email(ticket_id, user_email, "Support Request", user_message)
                
                response['message'] = "I understand you need specialized assistance. I've created a support ticket for you and our team will get back to you within 24 hours. Is there anything else I can help you with in the meantime?"
                response['escalated'] = True
                response['ticket_id'] = ticket_id
                
                # Add bot response to database
                self.add_message(session_id, 'bot', response['message'], 'escalation', 1.0)
                
            elif intent == 'greeting':
                response['message'] = "Hello! I'm the WiseNews support assistant. How can I help you today? I can assist with:\n\n• How to use WiseNews features\n• Account and login issues\n• Navigation and settings\n• General questions about the platform\n\nWhat would you like to know?"
                self.add_message(session_id, 'bot', response['message'], 'greeting', 1.0)
                
            elif intent == 'farewell':
                response['message'] = "Thank you for using WiseNews! If you need any more help, just start a new chat. Have a great day! 😊"
                self.add_message(session_id, 'bot', response['message'], 'farewell', 1.0)
                
                # Mark session as ended
                conn = sqlite3.connect('news_database.db')
                cursor = conn.cursor()
                cursor.execute('UPDATE chat_sessions SET session_end = CURRENT_TIMESTAMP WHERE id = ?', (session_id,))
                conn.commit()
                conn.close()
                
            else:
                # Search knowledge base for relevant answer
                knowledge_match = self.search_knowledge_base(user_message)
                
                if knowledge_match:
                    response['message'] = f"{knowledge_match['answer']}\n\nWas this helpful? If you need more specific assistance, feel free to ask!"
                    
                    # Add related suggestions
                    conn = sqlite3.connect('news_database.db')
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT question FROM knowledge_base 
                        WHERE category = ? AND id != ?
                        ORDER BY usage_count DESC LIMIT 3
                    ''', (knowledge_match['category'], knowledge_match['id']))
                    
                    suggestions = [row[0] for row in cursor.fetchall()]
                    response['suggestions'] = suggestions
                    conn.close()
                    
                else:
                    response['message'] = "I'm not sure I understand that specific question. Could you please rephrase it or try asking about:\n\n• How to use a specific feature\n• Account or login issues\n• Navigation help\n• Technical problems\n\nOr if you'd prefer, I can connect you with our human support team."
                
                self.add_message(session_id, 'bot', response['message'], 'response', confidence)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                'message': "I'm sorry, I'm experiencing some technical difficulties. Please try again or contact our support team directly.",
                'escalated': False,
                'ticket_id': None,
                'suggestions': []
            }

    def get_chat_history(self, session_id: int) -> List[Dict]:
        """Get chat history for a session"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT sender, message, timestamp, escalated
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
            ''', (session_id,))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'sender': row[0],
                    'message': row[1],
                    'timestamp': row[2],
                    'escalated': bool(row[3])
                })
            
            conn.close()
            return messages
            
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []

# Initialize the chatbot
support_chatbot = SupportChatbot()
