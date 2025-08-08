"""
Live Events Manager for WiseNews
Handles real-time event tracking, updates, and notifications
"""

import sqlite3
import json
import requests
import time
import threading
import random
from datetime import datetime, timedelta
import logging
import sys
from typing import Dict, List, Optional, Tuple
from database_manager import db_manager

# Configure logging to handle Unicode properly on Windows
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Handle Windows encoding issues
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

logger = logging.getLogger(__name__)

class LiveEventsManager:
    def __init__(self):
        self.update_threads = {}
        self.running = False
        
        # API configurations (you'll need to get actual API keys)
        self.api_configs = {
            'sports': {
                'api_key': 'your_sports_api_key',  # Replace with actual key
                'base_url': 'https://api.sportscores.com/v1',
                'endpoints': {
                    'football': '/football/matches',
                    'basketball': '/basketball/games',
                    'tennis': '/tennis/matches'
                }
            },
            'finance': {
                'api_key': 'your_finance_api_key',  # Replace with actual key
                'base_url': 'https://api.marketdata.com/v1',
                'endpoints': {
                    'stocks': '/stocks/quotes',
                    'crypto': '/crypto/quotes',
                    'forex': '/forex/quotes'
                }
            },
            'news': {
                'api_key': 'your_news_api_key',  # Replace with actual key
                'base_url': 'https://api.newsapi.org/v2',
                'endpoints': {
                    'breaking': '/top-headlines',
                    'everything': '/everything'
                }
            }
        }
    
    def start_live_tracking(self):
        """Start live event tracking system"""
        if self.running:
            return
        
        self.running = True
        logger.info("Starting live events tracking system")
        
        # Start update threads for each category
        categories = self.get_active_categories()
        for category in categories:
            thread = threading.Thread(
                target=self._category_update_loop,
                args=(category,),
                daemon=True
            )
            thread.start()
            self.update_threads[category['name']] = thread
    
    def stop_live_tracking(self):
        """Stop live event tracking system"""
        self.running = False
        logger.info("Stopping live events tracking system")
    
    def get_active_categories(self) -> List[Dict]:
        """Get all active event categories"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT name, display_name, event_type, icon, api_endpoint, 
                       update_interval, api_key_required
                FROM event_categories 
                WHERE is_active = TRUE
            ''')
            
            categories = []
            for row in cursor.fetchall():
                categories.append({
                    'name': row[0],
                    'display_name': row[1],
                    'event_type': row[2],
                    'icon': row[3],
                    'api_endpoint': row[4],
                    'update_interval': row[5],
                    'api_key_required': row[6]
                })
            
            conn.close()
            return categories
            
        except Exception as e:
            logger.error(f"Error getting active categories: {e}")
            return []
    
    def create_event(self, event_data: Dict) -> Optional[int]:
        """Create a new live event"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO live_events 
                (event_name, event_type, category, status, start_time, end_time, 
                 venue, description, external_id, data_source, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_data.get('name'),
                event_data.get('type'),
                event_data.get('category'),
                event_data.get('status', 'upcoming'),
                event_data.get('start_time'),
                event_data.get('end_time'),
                event_data.get('venue'),
                event_data.get('description'),
                event_data.get('external_id'),
                event_data.get('data_source'),
                json.dumps(event_data.get('metadata', {}))
            ))
            
            event_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Created live event: {event_data.get('name')} (ID: {event_id})")
            return event_id
            
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return None
    
    def add_event_update(self, event_id: int, update_data: Dict) -> bool:
        """Add an update to a live event"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO live_event_updates 
                (event_id, update_type, title, content, importance, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                event_id,
                update_data.get('type'),
                update_data.get('title'),
                update_data.get('content'),
                update_data.get('importance', 0.5),
                json.dumps(update_data.get('metadata', {}))
            ))
            
            # Update event last_updated timestamp
            cursor.execute('''
                UPDATE live_events 
                SET last_updated = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (event_id,))
            
            conn.commit()
            conn.close()
            
            # Trigger notifications for subscribed users
            self._trigger_event_notifications(event_id, update_data)
            
            # Safe logging that handles unicode characters
            title = update_data.get('title', '').encode('ascii', errors='ignore').decode('ascii')
            logger.info(f"Added update to event {event_id}: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding event update: {e}")
            return False
    
    def subscribe_user_to_event(self, user_id: int, event_id: int, notification_types: List[str]) -> bool:
        """Subscribe user to live event updates"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_event_subscriptions 
                (user_id, event_id, notification_types, is_active)
                VALUES (?, ?, ?, TRUE)
            ''', (user_id, event_id, json.dumps(notification_types)))
            
            conn.commit()
            conn.close()
            
            logger.info(f"User {user_id} subscribed to event {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing user to event: {e}")
            return False
    
    def get_live_events(self, category: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
        """Get live events with optional filtering"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            query = '''
                SELECT id, event_name, event_type, category, status, start_time, 
                       end_time, venue, description, metadata, last_updated
                FROM live_events 
            '''
            params = []
            conditions = []
            
            if category:
                conditions.append('category = ?')
                params.append(category)
            
            if status:
                conditions.append('status = ?')
                params.append(status)
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            query += ' ORDER BY start_time DESC'
            
            cursor.execute(query, params)
            
            events = []
            for row in cursor.fetchall():
                metadata = json.loads(row[9]) if row[9] else {}
                events.append({
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'category': row[3],
                    'status': row[4],
                    'start_time': row[5],
                    'end_time': row[6],
                    'venue': row[7],
                    'description': row[8],
                    'metadata': metadata,
                    'last_updated': row[10]
                })
            
            conn.close()
            return events
            
        except Exception as e:
            logger.error(f"Error getting live events: {e}")
            return []
    
    def get_event_updates(self, event_id: int, limit: int = 50) -> List[Dict]:
        """Get updates for a specific event"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, update_type, title, content, timestamp, importance, metadata
                FROM live_event_updates 
                WHERE event_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (event_id, limit))
            
            updates = []
            for row in cursor.fetchall():
                metadata = json.loads(row[6]) if row[6] else {}
                updates.append({
                    'id': row[0],
                    'type': row[1],
                    'title': row[2],
                    'content': row[3],
                    'timestamp': row[4],
                    'importance': row[5],
                    'metadata': metadata
                })
            
            conn.close()
            return updates
            
        except Exception as e:
            logger.error(f"Error getting event updates: {e}")
            return []
    
    def search_events(self, query: str) -> List[Dict]:
        """Search for events by name or description"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            search_query = f'%{query}%'
            cursor.execute('''
                SELECT id, event_name, event_type, category, status, start_time, 
                       end_time, venue, description, metadata
                FROM live_events 
                WHERE event_name LIKE ? OR description LIKE ?
                ORDER BY start_time DESC
                LIMIT 50
            ''', (search_query, search_query))
            
            events = []
            for row in cursor.fetchall():
                metadata = json.loads(row[9]) if row[9] else {}
                events.append({
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'category': row[3],
                    'status': row[4],
                    'start_time': row[5],
                    'end_time': row[6],
                    'venue': row[7],
                    'description': row[8],
                    'metadata': metadata
                })
            
            conn.close()
            return events
            
        except Exception as e:
            logger.error(f"Error searching events: {e}")
            return []
    
    def _category_update_loop(self, category: Dict):
        """Main update loop for a category"""
        category_name = category['name']
        update_interval = category['update_interval']
        
        logger.info(f"Starting update loop for category: {category_name}")
        
        cleanup_counter = 0
        
        while self.running:
            try:
                # Clean up old events every 10 iterations (approximately every 10 minutes)
                cleanup_counter += 1
                if cleanup_counter >= 10:
                    self._cleanup_old_events()
                    cleanup_counter = 0
                
                # Fetch updates for this category
                if category['event_type'] == 'sports':
                    self._update_sports_events(category_name)
                elif category['event_type'] == 'finance':
                    self._update_finance_events(category_name)
                elif category['event_type'] == 'breaking_news':
                    self._update_breaking_news()
                
                # Wait for next update
                time.sleep(update_interval)
                
            except Exception as e:
                logger.error(f"Error in update loop for {category_name}: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def _update_sports_events(self, category: str):
        """Update sports events from API"""
        try:
            # Mock sports data for demonstration
            # In production, you'd call actual sports APIs
            mock_events = [
                {
                    'name': 'Liverpool vs Manchester United',
                    'type': 'sports',
                    'category': 'football',
                    'status': 'live',
                    'start_time': datetime.now().isoformat(),
                    'venue': 'Anfield Stadium',
                    'description': 'Premier League Match',
                    'external_id': 'mock_12345',
                    'data_source': 'mock_sports_api',
                    'metadata': {
                        'home_team': 'Liverpool',
                        'away_team': 'Manchester United',
                        'score': {'home': 2, 'away': 1},
                        'minute': 67
                    }
                }
            ]
            
            for event_data in mock_events:
                # Check if event exists
                event_id = self._get_or_create_event(event_data)
                
                # Add random updates for demonstration
                if event_id and event_data['status'] == 'live':
                    self._generate_mock_sports_update(event_id, event_data)
                    
        except Exception as e:
            logger.error(f"Error updating sports events: {e}")
    
    def _update_finance_events(self, category: str):
        """Update financial events from API"""
        try:
            # Mock financial data for demonstration
            mock_events = [
                {
                    'name': 'Bitcoin Price Movement',
                    'type': 'finance',
                    'category': 'crypto',
                    'status': 'live',
                    'start_time': datetime.now().isoformat(),
                    'description': 'Live Bitcoin price tracking',
                    'external_id': 'btc_usd',
                    'data_source': 'mock_crypto_api',
                    'metadata': {
                        'symbol': 'BTC/USD',
                        'price': 65432.50,
                        'change_24h': 3.45
                    }
                }
            ]
            
            for event_data in mock_events:
                event_id = self._get_or_create_event(event_data)
                
                if event_id:
                    self._generate_mock_finance_update(event_id, event_data)
                    
        except Exception as e:
            logger.error(f"Error updating finance events: {e}")
    
    def _update_breaking_news(self):
        """Update breaking news from API"""
        try:
            import random
            
            # Mock breaking news for demonstration with detailed context
            if random.random() < 0.05:  # 5% chance of breaking news
                breaking_news_events = [
                    {
                        'name': 'Major Economic Announcement',
                        'type': 'breaking_news',
                        'category': 'breaking_news',
                        'status': 'live',
                        'start_time': datetime.now().isoformat(),
                        'description': 'Federal Reserve announces unexpected policy changes',
                        'external_id': f'breaking_{int(time.time())}',
                        'data_source': 'mock_news_api',
                        'metadata': {
                            'severity': 'high',
                            'impact': 'global',
                            'sectors_affected': ['finance', 'real_estate', 'technology']
                        }
                    },
                    {
                        'name': 'Technology Industry Disruption',
                        'type': 'breaking_news',
                        'category': 'breaking_news',
                        'status': 'live',
                        'start_time': datetime.now().isoformat(),
                        'description': 'Major tech company announces revolutionary product',
                        'external_id': f'breaking_{int(time.time())}',
                        'data_source': 'mock_news_api',
                        'metadata': {
                            'severity': 'medium',
                            'impact': 'industry',
                            'sectors_affected': ['technology', 'artificial_intelligence']
                        }
                    }
                ]
                
                for news_event in breaking_news_events:
                    event_id = self._get_or_create_event(news_event)
                    
                    if event_id:
                        # Create detailed breaking news update
                        update = {
                            'type': 'breaking_announcement',
                            'title': f"[BREAKING] {news_event['name']}",
                            'content': f"[URGENT UPDATE] {news_event['description']}. This developing story has significant implications for multiple sectors and markets worldwide. Our newsroom is gathering additional details and will provide comprehensive coverage as the situation unfolds. The announcement has already begun to influence trading patterns and market sentiment. Key stakeholders are expected to respond within the coming hours. This story represents a major development that could reshape industry dynamics and regulatory approaches. Stay tuned for expert analysis and reaction from market leaders.",
                            'importance': 0.95,
                            'metadata': {
                                'announcement_type': 'policy_change',
                                'expected_impact': 'high',
                                'follow_up_expected': True,
                                'market_reaction': 'anticipated',
                                'expert_analysis_coming': True
                            }
                        }
                        
                        self.add_event_update(event_id, update)
                        logger.info(f"Created breaking news event: {news_event['name']}")
            
            # Add corporate events tracking
            self._update_corporate_events()
            
            # Add regulatory and institutional announcements
            self._update_regulatory_events()
            
            # Generate automatic articles for major events without coverage
            self._generate_missing_coverage_articles()
            
            # Auto-post to social media for breaking news
            self._auto_share_breaking_news()
            
            logger.info("Checking for breaking news updates...")
            
        except Exception as e:
            logger.error(f"Error updating breaking news: {e}")
    
    def _update_corporate_events(self):
        """Update corporate events and data"""
        try:
            import random
            
            # Mock corporate events for demonstration
            if random.random() < 0.08:  # 8% chance of corporate event
                corporate_events = [
                    {
                        'name': 'Apple Inc. Quarterly Earnings Release',
                        'type': 'corporate',
                        'category': 'earnings',
                        'status': 'live',
                        'start_time': datetime.now().isoformat(),
                        'description': 'Apple reports Q3 2025 financial results',
                        'external_id': f'corp_aapl_{int(time.time())}',
                        'data_source': 'mock_corporate_api',
                        'metadata': {
                            'company': 'Apple Inc.',
                            'ticker': 'AAPL',
                            'sector': 'Technology',
                            'market_cap': '3.2T',
                            'event_type': 'earnings_release',
                            'quarter': 'Q3 2025',
                            'expected_revenue': '85.2B',
                            'expected_eps': '1.85'
                        }
                    },
                    {
                        'name': 'Microsoft CEO Leadership Announcement',
                        'type': 'corporate',
                        'category': 'leadership',
                        'status': 'live',
                        'start_time': datetime.now().isoformat(),
                        'description': 'Microsoft announces major organizational restructuring',
                        'external_id': f'corp_msft_{int(time.time())}',
                        'data_source': 'mock_corporate_api',
                        'metadata': {
                            'company': 'Microsoft Corporation',
                            'ticker': 'MSFT',
                            'sector': 'Technology',
                            'event_type': 'leadership_change',
                            'announcement_type': 'restructuring',
                            'impact_level': 'high'
                        }
                    },
                    {
                        'name': 'Tesla Product Launch Event',
                        'type': 'corporate',
                        'category': 'product_launch',
                        'status': 'live',
                        'start_time': datetime.now().isoformat(),
                        'description': 'Tesla unveils next-generation autonomous vehicle technology',
                        'external_id': f'corp_tsla_{int(time.time())}',
                        'data_source': 'mock_corporate_api',
                        'metadata': {
                            'company': 'Tesla Inc.',
                            'ticker': 'TSLA',
                            'sector': 'Automotive',
                            'event_type': 'product_launch',
                            'product_category': 'autonomous_vehicles',
                            'market_significance': 'revolutionary',
                            'expected_market_impact': 'high'
                        }
                    },
                    {
                        'name': 'Amazon Acquisition Announcement',
                        'type': 'corporate',
                        'category': 'merger_acquisition',
                        'status': 'live',
                        'start_time': datetime.now().isoformat(),
                        'description': 'Amazon announces strategic acquisition in AI sector',
                        'external_id': f'corp_amzn_{int(time.time())}',
                        'data_source': 'mock_corporate_api',
                        'metadata': {
                            'company': 'Amazon.com Inc.',
                            'ticker': 'AMZN',
                            'sector': 'Technology',
                            'event_type': 'acquisition',
                            'deal_value': '12.5B',
                            'target_sector': 'artificial_intelligence',
                            'strategic_rationale': 'ai_capabilities_expansion'
                        }
                    }
                ]
                
                for corp_event in corporate_events:
                    event_id = self._get_or_create_event(corp_event)
                    
                    if event_id:
                        # Generate detailed corporate update
                        self._generate_corporate_update(event_id, corp_event)
                        logger.info(f"Created corporate event: {corp_event['name']}")
                        
        except Exception as e:
            logger.error(f"Error updating corporate events: {e}")
    
    def _generate_corporate_update(self, event_id: int, event_data: Dict):
        """Generate detailed corporate event updates"""
        import random
        
        company = event_data['metadata']['company']
        ticker = event_data['metadata']['ticker']
        sector = event_data['metadata']['sector']
        event_type = event_data['metadata']['event_type']
        
        if event_type == 'earnings_release':
            # Generate earnings update
            expected_revenue = event_data['metadata']['expected_revenue']
            expected_eps = event_data['metadata']['expected_eps']
            quarter = event_data['metadata']['quarter']
            
            # Simulate actual vs expected results
            revenue_beat = random.choice([True, False])
            eps_beat = random.choice([True, False])
            
            actual_revenue = f"{float(expected_revenue[:-1]) * random.uniform(0.95, 1.08):.1f}B"
            actual_eps = f"{float(expected_eps) * random.uniform(0.9, 1.15):.2f}"
            
            update = {
                'type': 'earnings_results',
                'title': f"[CHART] {company} ({ticker}) {quarter} Earnings Results",
                'content': f"[MONEY] CORPORATE EARNINGS: {company} has reported {quarter} financial results that {'exceeded' if revenue_beat and eps_beat else 'met' if revenue_beat or eps_beat else 'missed'} Wall Street expectations. Revenue came in at ${actual_revenue} {'beating' if revenue_beat else 'missing'} estimates of ${expected_revenue}. Earnings per share (EPS) reached ${actual_eps} {'surpassing' if eps_beat else 'falling short of'} the expected ${expected_eps}. This performance reflects the company's {'strong operational execution' if revenue_beat else 'challenging market conditions'} in the {sector.lower()} sector. Key business segments showed {'robust growth' if revenue_beat else 'mixed performance'} with management providing {'optimistic' if revenue_beat and eps_beat else 'cautious' if revenue_beat or eps_beat else 'conservative'} guidance for the upcoming quarter. Investors and analysts are closely watching the company's strategic initiatives and market positioning. The results will likely impact stock price movement and analyst ratings in the coming days.",
                'importance': 0.85,
                'metadata': {
                    'company': company,
                    'ticker': ticker,
                    'quarter': quarter,
                    'revenue_actual': actual_revenue,
                    'revenue_expected': expected_revenue,
                    'revenue_beat': revenue_beat,
                    'eps_actual': actual_eps,
                    'eps_expected': expected_eps,
                    'eps_beat': eps_beat,
                    'overall_performance': 'beat' if revenue_beat and eps_beat else 'mixed' if revenue_beat or eps_beat else 'miss',
                    'market_reaction_expected': 'positive' if revenue_beat and eps_beat else 'neutral' if revenue_beat or eps_beat else 'negative'
                }
            }
            
        elif event_type == 'leadership_change':
            announcement_type = event_data['metadata']['announcement_type']
            
            update = {
                'type': 'leadership_announcement',
                'title': f"👔 {company} ({ticker}) Leadership Update",
                'content': f"🏢 CORPORATE LEADERSHIP: {company} has announced significant {announcement_type} that will reshape the organization's strategic direction. This leadership development comes at a crucial time for the {sector.lower()} sector and demonstrates the company's commitment to operational excellence and innovation. The changes are designed to enhance decision-making processes, improve market responsiveness, and drive long-term shareholder value. Industry analysts view this move as {random.choice(['strategically sound', 'necessary for growth', 'aligned with market trends'])} given the current competitive landscape. The transition is expected to {random.choice(['strengthen market position', 'improve operational efficiency', 'accelerate innovation initiatives'])}. Stakeholders including employees, customers, and investors will be watching closely for the implementation timeline and expected outcomes. The company's board of directors has expressed full confidence in these changes and their potential impact on future performance.",
                'importance': 0.75,
                'metadata': {
                    'company': company,
                    'ticker': ticker,
                    'change_type': announcement_type,
                    'sector_impact': 'medium',
                    'investor_sentiment': random.choice(['positive', 'neutral', 'cautiously optimistic']),
                    'implementation_timeline': 'Q4 2025'
                }
            }
            
        elif event_type == 'product_launch':
            product_category = event_data['metadata']['product_category']
            market_significance = event_data['metadata']['market_significance']
            
            update = {
                'type': 'product_announcement',
                'title': f"🚀 {company} ({ticker}) Product Innovation",
                'content': f"🔬 PRODUCT LAUNCH: {company} has unveiled groundbreaking {product_category.replace('_', ' ')} technology that represents a {market_significance} advancement in the {sector.lower()} industry. This innovation demonstrates the company's continued commitment to research and development excellence and positions them at the forefront of technological evolution. The new product features cutting-edge capabilities that address key market demands and customer pain points. Early industry reactions suggest this could be a game-changing development with potential to {random.choice(['disrupt existing markets', 'create new market segments', 'establish new industry standards'])}. The technology incorporates advanced engineering and design principles that reflect years of investment in innovation. Market analysts expect this launch to {random.choice(['drive significant revenue growth', 'enhance competitive positioning', 'attract new customer segments'])} over the coming quarters. The company plans to begin commercial deployment and expects widespread adoption across target markets.",
                'importance': 0.8,
                'metadata': {
                    'company': company,
                    'ticker': ticker,
                    'product_type': product_category,
                    'innovation_level': market_significance,
                    'market_potential': 'high',
                    'commercial_timeline': 'Q1 2026',
                    'competitive_advantage': 'significant'
                }
            }
            
        elif event_type == 'acquisition':
            deal_value = event_data['metadata']['deal_value']
            target_sector = event_data['metadata']['target_sector']
            strategic_rationale = event_data['metadata']['strategic_rationale']
            
            update = {
                'type': 'acquisition_announcement',
                'title': f"🤝 {company} ({ticker}) Strategic Acquisition",
                'content': f"💼 MERGER & ACQUISITION: {company} has announced a strategic ${deal_value} acquisition in the {target_sector.replace('_', ' ')} sector, representing a major expansion of their business capabilities. This transaction aligns with the company's {strategic_rationale.replace('_', ' ')} strategy and demonstrates their commitment to growth through strategic investments. The acquisition will provide access to specialized expertise, innovative technologies, and new market opportunities that complement existing operations. Industry experts view this move as {random.choice(['strategically sound', 'well-timed', 'competitively necessary'])} given the evolving market dynamics in both the {sector.lower()} and {target_sector.replace('_', ' ')} sectors. The deal is expected to create significant synergies through {random.choice(['operational efficiencies', 'technology integration', 'market expansion'])} and enhance the combined entity's competitive position. Regulatory approval processes are underway with completion expected in the coming months. This acquisition reinforces the company's position as a leader in strategic value creation and long-term growth planning.",
                'importance': 0.9,
                'metadata': {
                    'company': company,
                    'ticker': ticker,
                    'deal_value': deal_value,
                    'target_sector': target_sector,
                    'strategic_focus': strategic_rationale,
                    'completion_timeline': 'Q4 2025',
                    'regulatory_status': 'pending_approval',
                    'synergy_potential': 'high'
                }
            }
        
        else:
            # Generic corporate update
            update = {
                'type': 'corporate_announcement',
                'title': f"🏢 {company} ({ticker}) Corporate Update",
                'content': f"[ANNOUNCEMENT] CORPORATE NEWS: {company} has made an important announcement that impacts their business operations and strategic direction. This development reflects the company's ongoing efforts to adapt to market conditions and enhance stakeholder value. The announcement addresses key business priorities and demonstrates management's focus on operational excellence and long-term growth.",
                'importance': 0.6,
                'metadata': {
                    'company': company,
                    'ticker': ticker,
                    'announcement_type': 'general',
                    'impact_level': 'medium'
                }
            }
        
        self.add_event_update(event_id, update)
    
    def _update_regulatory_events(self):
        """Update regulatory and institutional announcements that can impact markets"""
        try:
            
            # Mock regulatory events for demonstration - these would be major market-moving announcements
            if random.random() < 0.06:  # 6% chance of regulatory event
                regulatory_events = [
                    {
                        'name': 'Federal Reserve Policy Decision',
                        'type': 'regulatory',
                        'category': 'federal_reserve',
                        'status': 'live',
                        'start_time': datetime.now().isoformat(),
                        'description': 'Federal Reserve announces key interest rate decision and monetary policy changes',
                        'external_id': f'fed_{int(time.time())}',
                        'data_source': 'mock_fed_api',
                        'metadata': {
                            'institution': 'Federal Reserve',
                            'announcement_type': 'monetary_policy',
                            'market_impact': 'high',
                            'current_rate': '5.25%',
                            'previous_rate': '5.00%',
                            'decision': 'rate_increase',
                            'sectors_affected': ['banking', 'real_estate', 'bonds', 'equity_markets']
                        }
                    },
                    {
                        'name': 'SEC Major Enforcement Action',
                        'type': 'regulatory',
                        'category': 'sec_filing',
                        'status': 'live',
                        'start_time': datetime.now().isoformat(),
                        'description': 'Securities and Exchange Commission announces significant enforcement action against major corporation',
                        'external_id': f'sec_{int(time.time())}',
                        'data_source': 'mock_sec_api',
                        'metadata': {
                            'institution': 'Securities and Exchange Commission',
                            'filing_type': 'enforcement_action',
                            'target_company': 'Major Tech Corporation',
                            'violation_type': 'disclosure_violations',
                            'fine_amount': '250M',
                            'market_impact': 'high'
                        }
                    },
                    {
                        'name': 'Treasury Department Economic Outlook',
                        'type': 'regulatory',
                        'category': 'treasury',
                        'status': 'live',
                        'start_time': datetime.now().isoformat(),
                        'description': 'U.S. Treasury releases quarterly economic outlook and fiscal policy updates',
                        'external_id': f'treasury_{int(time.time())}',
                        'data_source': 'mock_treasury_api',
                        'metadata': {
                            'institution': 'U.S. Department of Treasury',
                            'report_type': 'economic_outlook',
                            'gdp_forecast': '2.8%',
                            'inflation_projection': '2.1%',
                            'unemployment_forecast': '3.9%',
                            'debt_ceiling_status': 'stable'
                        }
                    },
                    {
                        'name': 'CFTC Commodity Market Regulations',
                        'type': 'regulatory',
                        'category': 'cftc',
                        'status': 'live',
                        'start_time': datetime.now().isoformat(),
                        'description': 'Commodity Futures Trading Commission implements new derivatives market regulations',
                        'external_id': f'cftc_{int(time.time())}',
                        'data_source': 'mock_cftc_api',
                        'metadata': {
                            'institution': 'Commodity Futures Trading Commission',
                            'regulation_type': 'derivatives_oversight',
                            'effective_date': '2025-09-01',
                            'affected_markets': ['commodities', 'derivatives', 'futures'],
                            'compliance_deadline': '2025-12-01'
                        }
                    },
                    {
                        'name': 'FDIC Banking Sector Assessment',
                        'type': 'regulatory',
                        'category': 'fdic',
                        'status': 'live',
                        'start_time': datetime.now().isoformat(),
                        'description': 'Federal Deposit Insurance Corporation releases banking sector stability assessment',
                        'external_id': f'fdic_{int(time.time())}',
                        'data_source': 'mock_fdic_api',
                        'metadata': {
                            'institution': 'Federal Deposit Insurance Corporation',
                            'assessment_type': 'banking_stability',
                            'sector_health': 'stable',
                            'stress_test_results': 'passed',
                            'capital_adequacy': 'well_capitalized',
                            'systemic_risk': 'low'
                        }
                    }
                ]
                
                for reg_event in regulatory_events:
                    event_id = self._get_or_create_event(reg_event)
                    
                    if event_id:
                        # Generate detailed regulatory update
                        self._generate_regulatory_update(event_id, reg_event)
                        logger.info(f"Created regulatory event: {reg_event['name']}")
                        
        except Exception as e:
            logger.error(f"Error updating regulatory events: {e}")
    
    def _generate_regulatory_update(self, event_id: int, event_data: Dict):
        """Generate detailed regulatory event updates"""
        
        institution = event_data['metadata']['institution']
        announcement_type = event_data['metadata'].get('announcement_type', event_data['metadata'].get('filing_type', event_data['metadata'].get('report_type', event_data['metadata'].get('regulation_type', event_data['metadata'].get('assessment_type', 'announcement')))))
        category = event_data['category']
        
        if category == 'federal_reserve':
            current_rate = event_data['metadata']['current_rate']
            previous_rate = event_data['metadata']['previous_rate']
            decision = event_data['metadata']['decision']
            
            update = {
                'type': 'monetary_policy_decision',
                'title': f"[BANK] Federal Reserve: Interest Rate {'Increase' if decision == 'rate_increase' else 'Decrease' if decision == 'rate_decrease' else 'Hold'}",
                'content': f"🏛️ FEDERAL RESERVE DECISION: The Federal Open Market Committee (FOMC) has announced a significant monetary policy decision, {'raising' if decision == 'rate_increase' else 'lowering' if decision == 'rate_decrease' else 'maintaining'} the federal funds rate {'to' if decision != 'rate_hold' else 'at'} {current_rate} (from {previous_rate}). This decision reflects the Fed's assessment of current economic conditions, inflation trends, and employment data. The rate {'increase signals tighter monetary policy aimed at controlling inflation and managing economic growth' if decision == 'rate_increase' else 'decrease indicates accommodative policy to stimulate economic activity' if decision == 'rate_decrease' else 'hold maintains current policy stance pending further economic data'}. Financial markets are responding immediately with significant movements in bond yields, equity indices, and currency valuations. Banking sector stocks are particularly sensitive to this announcement as net interest margins will be directly impacted. Real estate markets will see immediate effects on mortgage rates and property valuations. The decision also influences corporate borrowing costs, affecting capital expenditure plans across industries. Chairman Powell's accompanying statement provides crucial forward guidance for market participants and economic forecasters.",
                'importance': 0.95,
                'metadata': {
                    'institution': institution,
                    'policy_tool': 'federal_funds_rate',
                    'current_rate': current_rate,
                    'previous_rate': previous_rate,
                    'decision_impact': 'market_wide',
                    'effective_date': 'immediate',
                    'next_meeting_date': '2025-09-15'
                }
            }
            
        elif category == 'sec_filing':
            target_company = event_data['metadata']['target_company']
            violation_type = event_data['metadata']['violation_type']
            fine_amount = event_data['metadata']['fine_amount']
            
            update = {
                'type': 'sec_enforcement_action',
                'title': f"[LEGAL] SEC Enforcement: ${fine_amount} Action Against Major Corporation",
                'content': f"🏛️ SEC ENFORCEMENT: The Securities and Exchange Commission has announced a major enforcement action against {target_company}, imposing a ${fine_amount} penalty for {violation_type.replace('_', ' ')}. This action demonstrates the SEC's continued commitment to market integrity and investor protection. The violations relate to failure to properly disclose material information that could have influenced investor decisions and market pricing. The enforcement action includes remedial measures requiring the company to implement enhanced compliance programs, independent monitoring, and improved disclosure procedures. This case sets an important precedent for corporate governance standards and regulatory compliance in the financial markets. The penalty amount reflects the severity of the violations and the potential harm to investors and market confidence. Other publicly traded companies are likely to review their own disclosure practices in light of this action. The enforcement action may trigger additional shareholder litigation and could impact the company's stock price, credit ratings, and business relationships. Industry analysts expect this to lead to increased scrutiny of similar practices across the sector.",
                'importance': 0.9,
                'metadata': {
                    'institution': institution,
                    'enforcement_type': 'financial_penalty',
                    'target_entity': target_company,
                    'penalty_amount': fine_amount,
                    'violation_category': violation_type,
                    'market_sector_impact': 'technology',
                    'compliance_deadline': '2025-12-31'
                }
            }
            
        elif category == 'treasury':
            gdp_forecast = event_data['metadata']['gdp_forecast']
            inflation_projection = event_data['metadata']['inflation_projection']
            unemployment_forecast = event_data['metadata']['unemployment_forecast']
            
            update = {
                'type': 'economic_outlook_report',
                'title': f"[CHART] Treasury Economic Outlook: GDP {gdp_forecast}, Inflation {inflation_projection}",
                'content': f"🏛️ TREASURY ECONOMIC OUTLOOK: The U.S. Department of Treasury has released its quarterly economic assessment, projecting GDP growth of {gdp_forecast} for the upcoming period, with inflation expected to moderate to {inflation_projection} and unemployment forecasted at {unemployment_forecast}. This comprehensive analysis incorporates recent economic data, global market conditions, and fiscal policy impacts. The Treasury's outlook provides crucial guidance for fiscal planning, government spending priorities, and debt management strategies. The GDP forecast reflects expectations for consumer spending, business investment, and government expenditure contributions to economic growth. The inflation projection considers supply chain developments, energy costs, labor market dynamics, and monetary policy effects. Employment forecasts account for demographic trends, technological disruption, and sectoral shifts in the labor market. These projections influence federal budget planning, social security calculations, and debt ceiling discussions. Financial markets use this data for asset allocation decisions, sector rotation strategies, and risk management frameworks. The outlook also provides context for international trade negotiations and economic diplomacy initiatives.",
                'importance': 0.85,
                'metadata': {
                    'institution': institution,
                    'forecast_period': 'Q4_2025',
                    'gdp_projection': gdp_forecast,
                    'inflation_target': inflation_projection,
                    'employment_outlook': unemployment_forecast,
                    'fiscal_policy_stance': 'balanced',
                    'publication_frequency': 'quarterly'
                }
            }
            
        elif category == 'cftc':
            regulation_type = event_data['metadata']['regulation_type']
            effective_date = event_data['metadata']['effective_date']
            affected_markets = event_data['metadata']['affected_markets']
            
            update = {
                'type': 'regulatory_implementation',
                'title': f"[DOCUMENT] CFTC New Regulations: {regulation_type.replace('_', ' ').title()} Rules",
                'content': f"🏛️ CFTC REGULATORY UPDATE: The Commodity Futures Trading Commission has implemented comprehensive new regulations governing {regulation_type.replace('_', ' ')}, effective {effective_date}. These regulations enhance market transparency, reduce systemic risk, and strengthen investor protections across {', '.join(affected_markets)} markets. The new rules require enhanced reporting standards, improved risk management protocols, and increased capital requirements for market participants. Compliance frameworks must be updated to meet stringent oversight requirements, including real-time transaction reporting and comprehensive audit trails. The regulations address market manipulation concerns, improve price discovery mechanisms, and ensure fair access to trading platforms. Trading firms, hedge funds, and institutional investors must adapt their operations to meet the new regulatory standards. The implementation timeline provides adequate preparation time while ensuring market stability during the transition. These changes align with international regulatory best practices and strengthen the overall integrity of U.S. commodity markets. Market participants should expect increased compliance costs but benefit from reduced counterparty risks and improved market efficiency.",
                'importance': 0.8,
                'metadata': {
                    'institution': institution,
                    'regulation_scope': regulation_type,
                    'implementation_date': effective_date,
                    'affected_sectors': affected_markets,
                    'compliance_cost': 'moderate',
                    'market_benefit': 'enhanced_stability'
                }
            }
            
        elif category == 'fdic':
            sector_health = event_data['metadata']['sector_health']
            stress_test_results = event_data['metadata']['stress_test_results']
            capital_adequacy = event_data['metadata']['capital_adequacy']
            
            update = {
                'type': 'banking_assessment_report',
                'title': f"[BANK] FDIC Banking Assessment: Sector {sector_health.title()}, Tests {stress_test_results.title()}",
                'content': f"🏛️ FDIC BANKING ASSESSMENT: The Federal Deposit Insurance Corporation has completed its comprehensive banking sector evaluation, determining the overall health as {sector_health} with stress test results showing institutions have {stress_test_results}. The assessment reveals that banks maintain {capital_adequacy.replace('_', ' ')} capital positions, demonstrating resilience against potential economic shocks. This evaluation examines asset quality, liquidity positions, operational risk management, and regulatory compliance across the banking sector. The stress testing scenarios included severe recession conditions, market volatility, and credit loss scenarios to ensure banks can maintain operations during adverse conditions. Capital adequacy assessments confirm that institutions exceed minimum regulatory requirements and maintain sufficient buffers for unexpected losses. The stable sector outlook supports continued lending activity, economic growth financing, and financial system stability. These results provide confidence to depositors, investors, and regulators about the banking system's ability to support economic recovery and growth. The assessment methodology incorporates lessons learned from previous financial crises and evolving risk factors in the modern banking environment.",
                'importance': 0.8,
                'metadata': {
                    'institution': institution,
                    'assessment_outcome': sector_health,
                    'stress_test_status': stress_test_results,
                    'capital_status': capital_adequacy,
                    'system_stability': 'maintained',
                    'next_assessment': '2025-Q4'
                }
            }
        
        else:
            # Generic regulatory update
            update = {
                'type': 'regulatory_announcement',
                'title': f"🏛️ {institution}: Important {announcement_type.replace('_', ' ').title()}",
                'content': f"[ANNOUNCEMENT] REGULATORY UPDATE: {institution} has announced important {announcement_type.replace('_', ' ')} that will impact market participants and regulatory compliance requirements. This development demonstrates ongoing efforts to maintain market integrity, protect investors, and ensure financial system stability. The announcement addresses key regulatory priorities and reflects evolving market conditions and risk factors.",
                'importance': 0.7,
                'metadata': {
                    'institution': institution,
                    'announcement_category': announcement_type,
                    'regulatory_impact': 'medium'
                }
            }
        
        self.add_event_update(event_id, update)
    
    def _generate_missing_coverage_articles(self):
        """Generate comprehensive articles for major events that lack media coverage"""
        try:
            # TEMPORARY: Disable automatic article generation to resolve database errors
            logger.info("Automatic article generation temporarily disabled for debugging")
            return
            
            from article_generator import article_generator
            
            # Check for coverage gaps
            coverage_gaps = article_generator.check_coverage_gaps()
            
            for gap in coverage_gaps:
                # Generate article for under-covered event
                generated_article = article_generator.generate_article_for_event(gap)
                
                if generated_article:
                    logger.info(f"Generated article for under-covered event: {gap['event_name']}")
                    
                    # Trigger notification for premium users about new analysis
                    self._notify_premium_users_of_new_analysis(gap['event_id'], generated_article)
                    
                    # Auto-share generated article to social media
                    self._share_generated_article_to_social(generated_article)
            
        except Exception as e:
            logger.error(f"Error generating missing coverage articles: {e}")
    
    def _notify_premium_users_of_new_analysis(self, event_id: int, article_info: Dict):
        """Notify premium users about newly generated analysis articles"""
        try:
            from notification_manager import NotificationManager
            notification_manager = NotificationManager()
            
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            # Get premium users who are interested in comprehensive analysis
            cursor.execute('''
                SELECT DISTINCT u.id, u.email, u.full_name
                FROM users u
                JOIN user_subscriptions us ON u.id = us.user_id
                JOIN subscription_plans sp ON us.plan_id = sp.id
                JOIN user_notification_preferences unp ON u.id = unp.user_id
                WHERE us.status IN ('active', 'trial')
                AND sp.name IN ('Premium', 'Standard')
                AND (unp.categories LIKE '%analysis%' OR unp.categories LIKE '%comprehensive%' OR unp.categories LIKE '%all%')
            ''')
            
            premium_users = cursor.fetchall()
            conn.close()
            
            # Create notification about new analysis
            notification_data = {
                'id': 0,
                'title': f"[CHART] New Analysis Available: {article_info['title'][:50]}...",
                'content': f"🔍 EXCLUSIVE ANALYSIS: Our team has generated a comprehensive {article_info['word_count']}-word analysis article covering important developments that were under-reported in mainstream media. This {article_info['reading_time']}-minute read provides in-depth insights, market implications, and strategic considerations that you won't find elsewhere. As a valued subscriber, you have early access to this detailed analysis before it becomes widely available. Our AI-powered analysis team continuously monitors for important events that lack sufficient coverage and creates comprehensive reports to keep you fully informed.",
                'category': 'analysis',
                'source_name': 'WiseNews Analysis Team',
                'keywords': ['exclusive', 'analysis', 'comprehensive', 'insight'],
                'url': article_info['url'],
                'metadata': {
                    'article_type': 'generated_analysis',
                    'word_count': article_info['word_count'],
                    'reading_time': article_info['reading_time'],
                    'exclusive_access': True
                }
            }
            
            for user_id, email, full_name in premium_users:
                notification_manager.queue_notification(user_id, notification_data, 'both')
                logger.info(f"Notified premium user {user_id} about new analysis article")
            
        except Exception as e:
            logger.error(f"Error notifying users about new analysis: {e}")
    
    def _get_or_create_event(self, event_data: Dict) -> Optional[int]:
        """Get existing event or create new one with enhanced duplicate detection"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            event_name = event_data.get('name', '')
            category = event_data.get('category', '')
            data_source = event_data.get('data_source', '')
            external_id = event_data.get('external_id')
            
            # First check by external_id if available
            if external_id and data_source:
                cursor.execute('''
                    SELECT id FROM live_events 
                    WHERE external_id = ? AND data_source = ?
                ''', (external_id, data_source))
                
                result = cursor.fetchone()
                if result:
                    event_id = result[0]
                    # Update existing event
                    cursor.execute('''
                        UPDATE live_events 
                        SET status = ?, metadata = ?, last_updated = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (
                        event_data.get('status'),
                        json.dumps(event_data.get('metadata', {})),
                        event_id
                    ))
                    conn.commit()
                    conn.close()
                    return event_id
            
            # Enhanced duplicate detection: check by name and category within 1 minute for active events
            if event_name and category:
                cursor.execute('''
                    SELECT id FROM live_events 
                    WHERE event_name = ? AND category = ? 
                    AND (status = 'active' OR status = 'live')
                    AND start_time >= datetime('now', '-1 minutes')
                    ORDER BY start_time DESC LIMIT 1
                ''', (event_name, category))
                
                result = cursor.fetchone()
                if result:
                    event_id = result[0]
                    logger.info(f"Found existing active event: {event_name} (ID: {event_id}) - skipping duplicate creation")
                    # Update the existing event instead of creating duplicate
                    cursor.execute('''
                        UPDATE live_events 
                        SET status = ?, metadata = ?, last_updated = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (
                        event_data.get('status', 'active'),
                        json.dumps(event_data.get('metadata', {})),
                        event_id
                    ))
                    conn.commit()
                    conn.close()
                    return event_id
            
            # Only create new event if no duplicate found
            event_id = self.create_event(event_data)
            conn.close()
            return event_id
            
        except Exception as e:
            logger.error(f"Error getting or creating event: {e}")
            return None
    
    def _generate_mock_sports_update(self, event_id: int, event_data: Dict):
        """Generate enhanced sports updates with specific details"""
        import random
        
        if random.random() < 0.15:  # 15% chance of update
            current_score = event_data['metadata']['score']
            minute = event_data['metadata']['minute']
            home_team = event_data['metadata']['home_team']
            away_team = event_data['metadata']['away_team']
            
            # Enhanced update types with specific details
            updates = [
                {
                    'type': 'goal',
                    'title': f"GOAL! {home_team} {current_score['home'] + 1}-{current_score['away']} {away_team}",
                    'content': f"⚽ GOAL: {home_team} scores in the {minute}' - {self._get_goal_scorer()} finds the net! Score: {current_score['home'] + 1}-{current_score['away']}",
                    'importance': 0.9,
                    'metadata': {
                        'minute': minute,
                        'scorer': self._get_goal_scorer(),
                        'assist': self._get_assist_player(),
                        'score': {'home': current_score['home'] + 1, 'away': current_score['away']},
                        'goal_type': random.choice(['header', 'left foot', 'right foot', 'penalty', 'free kick']),
                        'update_type': 'goal'
                    }
                },
                {
                    'type': 'goal',
                    'title': f"GOAL! {home_team} {current_score['home']}-{current_score['away'] + 1} {away_team}",
                    'content': f"⚽ GOAL: {away_team} scores in the {minute}' - {self._get_goal_scorer()} converts! Score: {current_score['home']}-{current_score['away'] + 1}",
                    'importance': 0.9,
                    'metadata': {
                        'minute': minute,
                        'scorer': self._get_goal_scorer(),
                        'assist': self._get_assist_player(),
                        'score': {'home': current_score['home'], 'away': current_score['away'] + 1},
                        'goal_type': random.choice(['header', 'left foot', 'right foot', 'penalty', 'free kick']),
                        'update_type': 'goal'
                    }
                },
                {
                    'type': 'card',
                    'title': f"Yellow Card - {random.choice([home_team, away_team])}",
                    'content': f"🟨 Yellow Card: {self._get_player_name()} booked for {random.choice(['foul', 'unsporting behavior', 'dissent'])} in the {minute}'",
                    'importance': 0.3,
                    'metadata': {
                        'minute': minute,
                        'player': self._get_player_name(),
                        'card_type': 'yellow',
                        'reason': random.choice(['foul', 'unsporting behavior', 'dissent']),
                        'update_type': 'card'
                    }
                },
                {
                    'type': 'red_card',
                    'title': f"RED CARD! {random.choice([home_team, away_team])} down to 10 men",
                    'content': f"🟥 RED CARD: {self._get_player_name()} sent off in the {minute}' for serious foul play!",
                    'importance': 0.8,
                    'metadata': {
                        'minute': minute,
                        'player': self._get_player_name(),
                        'card_type': 'red',
                        'reason': 'serious foul play',
                        'update_type': 'red_card'
                    }
                },
                {
                    'type': 'substitution',
                    'title': f"Substitution - {random.choice([home_team, away_team])}",
                    'content': f"🔄 SUB: {self._get_player_name()} comes on for {self._get_player_name()} in the {minute}'",
                    'importance': 0.4,
                    'metadata': {
                        'minute': minute,
                        'player_on': self._get_player_name(),
                        'player_off': self._get_player_name(),
                        'update_type': 'substitution'
                    }
                },
                {
                    'type': 'penalty',
                    'title': f"PENALTY! {random.choice([home_team, away_team])} awarded spot kick",
                    'content': f"🎯 PENALTY: {random.choice([home_team, away_team])} awarded penalty in the {minute}' - foul in the box!",
                    'importance': 0.7,
                    'metadata': {
                        'minute': minute,
                        'awarded_to': random.choice([home_team, away_team]),
                        'update_type': 'penalty'
                    }
                },
                {
                    'type': 'near_miss',
                    'title': f"Close Call! {random.choice([home_team, away_team])} nearly scores",
                    'content': f"💥 CLOSE: {self._get_player_name()} hits the {random.choice(['post', 'crossbar', 'side netting'])} in the {minute}'!",
                    'importance': 0.5,
                    'metadata': {
                        'minute': minute,
                        'player': self._get_player_name(),
                        'outcome': random.choice(['post', 'crossbar', 'side netting']),
                        'update_type': 'near_miss'
                    }
                },
                {
                    'type': 'goal',
                    'title': f"[FOOTBALL] GOAL! {home_team} {current_score['home'] + 1} - {current_score['away']} {away_team}",
                    'content': f"🔥 BREAKING: {home_team} has scored a spectacular goal in the {minute}th minute! The striker found the bottom corner with a powerful shot from outside the box, leaving the goalkeeper with no chance. This goal could be crucial for the match outcome as we approach the final stages. The home crowd is absolutely electric! Current score: {home_team} {current_score['home'] + 1} - {current_score['away']} {away_team}. This puts {home_team} {'ahead' if current_score['home'] + 1 > current_score['away'] else 'level' if current_score['home'] + 1 == current_score['away'] else 'behind'} in this thrilling encounter.",
                    'importance': 0.9,
                    'metadata': {
                        'minute': minute,
                        'team': home_team,
                        'score': {'home': current_score['home'] + 1, 'away': current_score['away']},
                        'goal_type': 'spectacular strike',
                        'assist': 'midfield playmaker',
                        'crowd_reaction': 'electric'
                    }
                },
                {
                    'type': 'card',
                    'title': f"[YELLOW] Yellow Card - Tactical Foul",
                    'content': f"⚠️ A player from {random.choice([home_team, away_team])} receives a yellow card in the {minute}th minute for a tactical foul. The referee had no choice but to book the player who deliberately brought down the opponent just outside the penalty area to stop a dangerous counter-attack. This was a calculated decision by the player to prevent what could have been a clear goal-scoring opportunity. The tension is building as both teams are playing more aggressively in the crucial stages of the match.",
                    'importance': 0.4,
                    'metadata': {
                        'minute': minute,
                        'foul_type': 'tactical',
                        'location': 'outside penalty area',
                        'reason': 'stopping counter-attack'
                    }
                },
                {
                    'type': 'substitution',
                    'title': f"[REFRESH] Strategic Substitution",
                    'content': f"[DOCUMENT] TACTICAL CHANGE: The manager makes a crucial substitution in the {minute}th minute, bringing on a fresh striker to add more attacking threat. This substitution signals an intent to push forward and find the winning goal. The new player brings pace and energy that could be decisive in the final minutes. The crowd approves of this attacking mindset from the coaching staff.",
                    'importance': 0.6,
                    'metadata': {
                        'minute': minute,
                        'type': 'attacking_substitution',
                        'reason': 'tactical_change'
                    }
                },
                {
                    'type': 'chance',
                    'title': f"[TARGET] Close Call! Almost a Goal",
                    'content': f"💔 SO CLOSE! {random.choice([home_team, away_team])} nearly scored in the {minute}th minute with a brilliant shot that rattled the crossbar! The striker did everything right - controlled the ball perfectly, created space with a clever turn, and unleashed a powerful shot that had the goalkeeper beaten. The ball struck the crossbar with such force that it bounced back into play. Just inches away from what would have been a spectacular goal! The players and fans hold their heads in disbelief.",
                    'importance': 0.7,
                    'metadata': {
                        'minute': minute,
                        'shot_type': 'crossbar',
                        'quality': 'spectacular_attempt',
                        'outcome': 'unlucky'
                    }
                },
                {
                    'type': 'basketball_score',
                    'title': f"Score Update: {home_team} {current_score['home'] + 2}-{current_score['away']} {away_team}",
                    'content': f"🏀 {self._get_player_name()} drains a 3-pointer! {home_team} extends lead {current_score['home'] + 2}-{current_score['away']}",
                    'importance': 0.6,
                    'metadata': {
                        'minute': minute,
                        'scorer': self._get_player_name(),
                        'score': {'home': current_score['home'] + 2, 'away': current_score['away']},
                        'shot_type': '3-pointer',
                        'update_type': 'basketball_score'
                    }
                }
            ]
            
            update = random.choice(updates)
            self.add_event_update(event_id, update)

    def _get_goal_scorer(self):
        """Get random player name for goal scorer"""
        import random
        scorers = [
            'Johnson', 'Smith', 'Rodriguez', 'Williams', 'Brown', 'Davis', 'Miller', 
            'Wilson', 'Moore', 'Taylor', 'Anderson', 'Thomas', 'Jackson', 'White', 
            'Harris', 'Martin', 'Thompson', 'Garcia', 'Martinez', 'Robinson'
        ]
        return random.choice(scorers)

    def _get_assist_player(self):
        """Get random player name for assist"""
        return self._get_goal_scorer()  # Use same pool

    def _get_player_name(self):
        """Get random player name"""
        return self._get_goal_scorer()  # Use same pool
    
    def _generate_mock_finance_update(self, event_id: int, event_data: Dict):
        """Generate mock finance updates for demonstration"""
        import random
        
        if random.random() < 0.2:  # 20% chance of update
            current_price = event_data['metadata']['price']
            symbol = event_data['metadata']['symbol']
            
            # Generate realistic price movements
            volatility_factors = {
                'BTC/USD': 0.05,  # Bitcoin can be quite volatile
                'ETH/USD': 0.04,
                'AAPL': 0.02,
                'TSLA': 0.03
            }
            
            volatility = volatility_factors.get(symbol.split('/')[0], 0.03)
            price_change = random.uniform(-current_price * volatility, current_price * volatility)
            new_price = current_price + price_change
            change_percent = (price_change / current_price) * 100
            
            # Determine significance
            is_major_move = abs(change_percent) > 3
            direction = "surge" if price_change > 0 else "drop"
            intensity = "massive" if abs(change_percent) > 5 else "significant" if abs(change_percent) > 2 else "moderate"
            
            # Generate contextual reasons
            reasons = [
                "institutional buying pressure",
                "market sentiment shift",
                "technical breakout pattern",
                "regulatory news impact",
                "earnings expectations",
                "global economic indicators",
                "whale movements detected",
                "options expiry effects"
            ]
            
            reason = random.choice(reasons)
            
            # Create detailed update based on movement size
            if is_major_move:
                title = f"[MAJOR {direction.upper()}] {symbol} {intensity} movement"
                content = f"[ALERT] {symbol} has experienced a {intensity} {direction} of {abs(change_percent):.2f}% in the last update! Price moved from ${current_price:.2f} to ${new_price:.2f}, representing a ${abs(price_change):.2f} change. This movement appears to be driven by {reason} and has caught the attention of traders worldwide. Trading volumes are spiking as investors react to this significant price action. Market analysts are closely monitoring support and resistance levels at ${new_price * 0.95:.2f} and ${new_price * 1.05:.2f} respectively. This could signal the start of a larger trend reversal or continuation pattern."
                importance = 0.9
            else:
                title = f"[UP] {symbol} Price Update - {direction.title()}"
                content = f"[MARKET] {symbol} has moved {change_percent:+.2f}% to ${new_price:.2f} (from ${current_price:.2f}). This {direction} of ${abs(price_change):.2f} appears to be influenced by {reason}. While not a dramatic movement, it's worth noting for investors tracking this asset. Current market conditions suggest {'bullish momentum building' if price_change > 0 else 'bearish pressure increasing'}. Traders should watch for potential {'breakout above' if price_change > 0 else 'breakdown below'} key technical levels."
                importance = 0.6 if abs(change_percent) > 1 else 0.3
            
            update = {
                'type': 'price_change',
                'title': title,
                'content': content,
                'importance': importance,
                'metadata': {
                    'symbol': symbol,
                    'old_price': current_price,
                    'new_price': new_price,
                    'change': price_change,
                    'change_percent': change_percent,
                    'reason': reason,
                    'trading_volume': 'high' if is_major_move else 'normal',
                    'market_sentiment': 'bullish' if price_change > 0 else 'bearish',
                    'technical_levels': {
                        'support': new_price * 0.95,
                        'resistance': new_price * 1.05
                    }
                }
            }
            
            self.add_event_update(event_id, update)
    
    def _trigger_event_notifications(self, event_id: int, update_data: Dict):
        """Trigger notifications for users subscribed to this event"""
        try:
            from notification_manager import NotificationManager
            notification_manager = NotificationManager()
            
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            # Get users subscribed to this event with Premium access
            cursor.execute('''
                SELECT ues.user_id, ues.notification_types, sp.real_time_notifications
                FROM user_event_subscriptions ues
                JOIN user_subscriptions us ON ues.user_id = us.user_id
                JOIN subscription_plans sp ON us.plan_id = sp.id
                WHERE ues.event_id = ? AND ues.is_active = TRUE
                AND us.status IN ('active', 'trial')
                AND sp.real_time_notifications = TRUE
            ''', (event_id,))
            
            subscribed_users = cursor.fetchall()
            
            # Get event details
            cursor.execute('''
                SELECT event_name, category, venue, metadata FROM live_events WHERE id = ?
            ''', (event_id,))
            
            event_info = cursor.fetchone()
            conn.close()
            
            if not event_info:
                return
            
            event_name, category, venue, metadata_json = event_info
            event_metadata = json.loads(metadata_json) if metadata_json else {}
            
            # Send detailed notifications to Premium subscribers only
            for user_id, notification_types_json, has_real_time in subscribed_users:
                if has_real_time:  # Only Premium users get real-time event notifications
                    notification_types = json.loads(notification_types_json)
                    
                    # Check if user wants this type of update
                    if ('all' in notification_types or 
                        update_data.get('type') in notification_types or
                        (update_data.get('importance', 0) > 0.7 and 'major' in notification_types)):
                        
                        # Create enhanced notification with detailed context
                        if category in ['football', 'basketball', 'tennis', 'baseball', 'soccer']:
                            # Enhanced sports notification
                            notification_title = self._create_enhanced_sports_notification_title(
                                event_name, update_data, event_metadata
                            )
                            
                            notification_content = self._create_enhanced_sports_notification_content(
                                update_data, event_metadata
                            )
                            
                            # Add priority indicators for sports events
                            update_type = update_data.get('metadata', {}).get('update_type', update_data.get('type'))
                            if update_type in ['goal', 'red_card', 'penalty', 'basketball_score']:
                                priority_level = "🚨 MAJOR"
                            elif update_type in ['card', 'substitution']:
                                priority_level = "📝 UPDATE"
                            else:
                                priority_level = "ℹ️ INFO"
                            
                            notification_title = f"{priority_level}: {notification_title}"
                            
                        else:
                            # Standard notification for non-sports
                            notification_title = self._create_detailed_notification_title(
                                event_name, category, update_data, event_metadata
                            )
                            
                            notification_content = self._create_detailed_notification_content(
                                event_name, category, venue, update_data, event_metadata
                            )
                        
                        # Add urgency indicators for high-importance updates
                        urgency_prefix = ""
                        if update_data.get('importance', 0) > 0.8:
                            urgency_prefix = "� URGENT: "
                        elif update_data.get('importance', 0) > 0.6:
                            urgency_prefix = "⚡ BREAKING: "
                        elif update_data.get('importance', 0) > 0.4:
                            urgency_prefix = "[ANNOUNCEMENT] UPDATE: "
                        
                        # Create comprehensive notification
                        notification_data = {
                            'id': 0,  # Special ID for live events
                            'title': f"{urgency_prefix}{notification_title}",
                            'content': notification_content,
                            'category': category,
                            'source_name': 'WiseNews Live Events',
                            'keywords': [category, 'live', 'breaking', update_data.get('type', 'update')],
                            'url': f'/live-events/{event_id}',
                            'metadata': {
                                'event_id': event_id,
                                'update_type': update_data.get('type'),
                                'importance': update_data.get('importance'),
                                'venue': venue,
                                'timestamp': datetime.now().isoformat()
                            }
                        }
                        
                        notification_manager.queue_notification(user_id, notification_data, 'both')
                        logger.info(f"Sent detailed live event notification to Premium user {user_id} for {event_name}")
            
        except Exception as e:
            logger.error(f"Error triggering event notifications: {e}")
    
    def _create_detailed_notification_title(self, event_name: str, category: str, update_data: Dict, event_metadata: Dict) -> str:
        """Create a detailed, context-aware notification title"""
        update_type = update_data.get('type', 'update')
        
        # Corporate events have priority in title creation
        if update_type in ['earnings_results', 'leadership_announcement', 'product_announcement', 'acquisition_announcement']:
            company = update_data.get('metadata', {}).get('company', 'Company')
            ticker = update_data.get('metadata', {}).get('ticker', 'N/A')
            
            if update_type == 'earnings_results':
                performance = update_data.get('metadata', {}).get('overall_performance', 'mixed')
                quarter = update_data.get('metadata', {}).get('quarter', 'Q3')
                performance_emoji = "[UP]" if performance == 'beat' else "[CHART]" if performance == 'mixed' else "[DOWN]"
                return f"{performance_emoji} {ticker} {quarter} Earnings: {performance.title()} Expectations"
            
            elif update_type == 'leadership_announcement':
                return f"👔 {ticker} Leadership: Strategic Organizational Changes"
            
            elif update_type == 'product_announcement':
                innovation_level = update_data.get('metadata', {}).get('innovation_level', 'significant')
                return f"🚀 {ticker} Innovation: {innovation_level.title()} Product Launch"
            
            elif update_type == 'acquisition_announcement':
                deal_value = update_data.get('metadata', {}).get('deal_value', 'Major')
                return f"🤝 {ticker} M&A: ${deal_value} Strategic Acquisition"
        
        # Sports events - Use enhanced formatting
        elif category in ['football', 'basketball', 'tennis', 'baseball']:
            return self._create_enhanced_sports_notification_title(event_name, update_data, event_metadata)
        
        # Financial markets (non-corporate)
        elif category in ['stocks', 'crypto', 'forex']:
            symbol = event_metadata.get('symbol', 'Unknown')
            change_percent = update_data.get('metadata', {}).get('change_percent', 0)
            direction = "[UP]" if change_percent > 0 else "[DOWN]"
            return f"{direction} {symbol} {abs(change_percent):.1f}% Movement"
        
        # Conferences and events
        elif category in ['politics', 'tech_conference', 'earnings']:
            return f"🎤 {event_name} - Conference Update"
        
        else:
            return f"🔴 {event_name} - Live Update"

    def _create_enhanced_sports_notification_title(self, event_name: str, update_data: Dict, event_metadata: Dict) -> str:
        """Create enhanced sports notification titles"""
        update_type = update_data.get('metadata', {}).get('update_type', update_data.get('type', 'update'))
        
        if update_type == 'goal':
            score = update_data.get('metadata', {}).get('score', {})
            scorer = update_data.get('metadata', {}).get('scorer', 'Player')
            return f"⚽ GOAL: {scorer} scores! {score.get('home', 0)}-{score.get('away', 0)}"
        
        elif update_type == 'card':
            player = update_data.get('metadata', {}).get('player', 'Player')
            card_type = update_data.get('metadata', {}).get('card_type', 'yellow')
            minute = update_data.get('metadata', {}).get('minute', '?')
            emoji = '🟨' if card_type == 'yellow' else '🟥'
            return f"{emoji} {card_type.title()} Card: {player} ({minute}')"
        
        elif update_type == 'red_card':
            player = update_data.get('metadata', {}).get('player', 'Player')
            minute = update_data.get('metadata', {}).get('minute', '?')
            return f"🟥 RED CARD: {player} sent off ({minute}')"
        
        elif update_type == 'substitution':
            player_on = update_data.get('metadata', {}).get('player_on', 'Player')
            minute = update_data.get('metadata', {}).get('minute', '?')
            return f"🔄 SUB: {player_on} comes on ({minute}')"
        
        elif update_type == 'penalty':
            awarded_to = update_data.get('metadata', {}).get('awarded_to', 'Team')
            minute = update_data.get('metadata', {}).get('minute', '?')
            return f"🎯 PENALTY: {awarded_to} awarded ({minute}')"
        
        elif update_type == 'near_miss':
            player = update_data.get('metadata', {}).get('player', 'Player')
            outcome = update_data.get('metadata', {}).get('outcome', 'post')
            minute = update_data.get('metadata', {}).get('minute', '?')
            return f"💥 CLOSE: {player} hits {outcome} ({minute}')"
        
        elif update_type == 'basketball_score':
            scorer = update_data.get('metadata', {}).get('scorer', 'Player')
            shot_type = update_data.get('metadata', {}).get('shot_type', 'basket')
            score = update_data.get('metadata', {}).get('score', {})
            return f"🏀 {shot_type.upper()}: {scorer} scores! {score.get('home', 0)}-{score.get('away', 0)}"
        
        else:
            return f"🏆 {event_name} - {update_type.replace('_', ' ').title()}"
    
    def _create_detailed_notification_content(self, event_name: str, category: str, venue: str, update_data: Dict, event_metadata: Dict) -> str:
        """Create comprehensive notification content with context and implications"""
        base_content = update_data.get('content', '')
        update_metadata = update_data.get('metadata', {})
        
        # Add location context if available
        location_context = f" at {venue}" if venue else ""
        
        # Add category-specific context
        if category in ['football', 'basketball', 'tennis', 'baseball']:
            return self._create_enhanced_sports_notification_content(update_data, event_metadata)
        
        elif category in ['stocks', 'crypto', 'forex']:
            finance_context = self._get_finance_context(update_data, event_metadata, update_metadata)
            return f"{base_content}\n\n{finance_context}"
        
        elif category in ['politics', 'tech_conference', 'earnings']:
            conference_context = self._get_conference_context(update_data, event_metadata, update_metadata)
            return f"{base_content}{location_context}\n\n{conference_context}"
        
        else:
            return f"{base_content}{location_context}\n\nStay tuned for more updates on this developing story."

    def _create_enhanced_sports_notification_content(self, update_data: Dict, event_metadata: Dict) -> str:
        """Create enhanced sports notification content with minimal, relevant details"""
        update_type = update_data.get('metadata', {}).get('update_type', update_data.get('type', 'update'))
        minute = update_data.get('metadata', {}).get('minute', '?')
        
        if update_type == 'goal':
            scorer = update_data.get('metadata', {}).get('scorer', 'Player')
            assist = update_data.get('metadata', {}).get('assist', '')
            goal_type = update_data.get('metadata', {}).get('goal_type', 'shot')
            score = update_data.get('metadata', {}).get('score', {})
            
            content = f"⚽ {scorer} scores with {goal_type} in the {minute}'"
            if assist:
                content += f" (assist: {assist})"
            content += f" • Score: {score.get('home', 0)}-{score.get('away', 0)}"
            return content
        
        elif update_type in ['card', 'red_card']:
            player = update_data.get('metadata', {}).get('player', 'Player')
            reason = update_data.get('metadata', {}).get('reason', 'foul')
            card_type = update_data.get('metadata', {}).get('card_type', 'yellow')
            emoji = '🟨' if card_type == 'yellow' else '🟥'
            return f"{emoji} {player} booked for {reason} ({minute}')"
        
        elif update_type == 'substitution':
            player_on = update_data.get('metadata', {}).get('player_on', 'Player A')
            player_off = update_data.get('metadata', {}).get('player_off', 'Player B')
            return f"🔄 {player_on} replaces {player_off} ({minute}')"
        
        elif update_type == 'penalty':
            awarded_to = update_data.get('metadata', {}).get('awarded_to', 'Team')
            return f"🎯 Penalty awarded to {awarded_to} for foul in box ({minute}')"
        
        elif update_type == 'near_miss':
            player = update_data.get('metadata', {}).get('player', 'Player')
            outcome = update_data.get('metadata', {}).get('outcome', 'post')
            return f"💥 {player} strikes the {outcome} - so close! ({minute}')"
        
        elif update_type == 'basketball_score':
            scorer = update_data.get('metadata', {}).get('scorer', 'Player')
            shot_type = update_data.get('metadata', {}).get('shot_type', 'basket')
            score = update_data.get('metadata', {}).get('score', {})
            return f"🏀 {scorer} makes {shot_type} • Score: {score.get('home', 0)}-{score.get('away', 0)} ({minute}')"
        
        else:
            return update_data.get('content', f"Live update from {minute}'")
    
    def _get_sports_context(self, update_data: Dict, event_metadata: Dict, update_metadata: Dict) -> str:
        """Generate sports-specific context and implications"""
        context_parts = []
        
        # Add time context
        minute = update_metadata.get('minute')
        if minute:
            if minute < 45:
                context_parts.append(f"⏰ Still in the first half ({minute}'), plenty of time remaining.")
            elif minute < 90:
                context_parts.append(f"⏰ Second half action ({minute}'), crucial period of the match.")
            else:
                context_parts.append(f"⏰ Stoppage time ({minute}'), every second counts!")
        
        # Add score implications
        score = update_metadata.get('score')
        if score:
            home_score, away_score = score.get('home', 0), score.get('away', 0)
            if home_score == away_score:
                context_parts.append("[LEGAL] The match is perfectly balanced - either team could take the lead!")
            elif abs(home_score - away_score) == 1:
                context_parts.append("🔥 It's a tight game with just one goal separating the teams!")
            else:
                context_parts.append(f"[CHART] {'Commanding' if abs(home_score - away_score) > 2 else 'Comfortable'} lead established.")
        
        # Add tactical context
        if update_data.get('type') == 'goal':
            goal_type = update_metadata.get('goal_type', 'strike')
            context_parts.append(f"[FOOTBALL] This {goal_type} showcases the attacking quality on display today.")
        elif update_data.get('type') == 'card':
            foul_type = update_metadata.get('foul_type', 'standard')
            context_parts.append(f"⚠️ The referee is keeping tight control - this {foul_type} foul couldn't go unpunished.")
        
        return " ".join(context_parts) if context_parts else "🏆 This match continues to deliver excitement for fans!"
    
    def _get_finance_context(self, update_data: Dict, event_metadata: Dict, update_metadata: Dict) -> str:
        """Generate finance-specific context and implications"""
        context_parts = []
        
        # Check if this is a corporate event
        if update_data.get('type') in ['earnings_results', 'leadership_announcement', 'product_announcement', 'acquisition_announcement']:
            return self._get_corporate_context(update_data, event_metadata, update_metadata)
        
        # Regular financial market context
        change_percent = update_metadata.get('change_percent', 0)
        reason = update_metadata.get('reason', 'market dynamics')
        
        if abs(change_percent) > 5:
            context_parts.append(f"[ALERT] This {abs(change_percent):.1f}% movement is highly significant and may trigger automated trading systems.")
        elif abs(change_percent) > 2:
            context_parts.append(f"[UP] A {abs(change_percent):.1f}% move indicates strong market sentiment and increased trading activity.")
        
        context_parts.append(f"[ANALYSIS] Primary driver: {reason.replace('_', ' ').title()}.")
        
        # Add technical analysis context
        technical_levels = update_metadata.get('technical_levels', {})
        if technical_levels:
            support = technical_levels.get('support', 0)
            resistance = technical_levels.get('resistance', 0)
            context_parts.append(f"[CHART] Key levels to watch: Support at ${support:.2f}, Resistance at ${resistance:.2f}.")
        
        # Add trading implications
        sentiment = update_metadata.get('market_sentiment', 'neutral')
        volume = update_metadata.get('trading_volume', 'normal')
        
        if volume == 'high':
            context_parts.append(f"[CHART] High trading volume confirms strong {sentiment} sentiment among investors.")
        else:
            context_parts.append(f"💡 Traders are showing {sentiment} sentiment despite normal volume levels.")
        
        return " ".join(context_parts)
    
    def _get_corporate_context(self, update_data: Dict, event_metadata: Dict, update_metadata: Dict) -> str:
        """Generate corporate-specific context and implications"""
        context_parts = []
        update_type = update_data.get('type')
        company = update_metadata.get('company', 'Company')
        ticker = update_metadata.get('ticker', 'N/A')
        
        if update_type == 'earnings_results':
            # Earnings-specific context
            revenue_beat = update_metadata.get('revenue_beat', False)
            eps_beat = update_metadata.get('eps_beat', False)
            overall_performance = update_metadata.get('overall_performance', 'mixed')
            market_reaction = update_metadata.get('market_reaction_expected', 'neutral')
            
            context_parts.append(f"💼 CORPORATE IMPACT: {company} ({ticker}) earnings results will likely trigger {market_reaction} market reaction.")
            
            if revenue_beat and eps_beat:
                context_parts.append("[UP] This strong performance demonstrates operational excellence and may lead to analyst upgrades and increased institutional investment.")
            elif revenue_beat or eps_beat:
                context_parts.append("[LEGAL] Mixed results suggest selective strength in business segments, warranting careful analysis of management guidance.")
            else:
                context_parts.append("[DOWN] Disappointing results may pressure stock valuation and prompt strategic reassessment by management.")
            
            context_parts.append("[MONEY] INVESTOR IMPLICATIONS: Portfolio managers will reassess position sizing based on guidance and competitive positioning.")
            context_parts.append("🔍 ANALYST COVERAGE: Expect updated price targets and recommendation changes within 24-48 hours.")
            
        elif update_type == 'leadership_announcement':
            # Leadership change context
            change_type = update_metadata.get('change_type', 'restructuring')
            investor_sentiment = update_metadata.get('investor_sentiment', 'neutral')
            
            context_parts.append(f"👔 LEADERSHIP IMPACT: This {change_type} signals strategic evolution and commitment to enhanced performance.")
            context_parts.append(f"[CHART] MARKET SENTIMENT: Early investor reaction appears {investor_sentiment}, reflecting confidence in strategic direction.")
            context_parts.append("[TARGET] OPERATIONAL FOCUS: Leadership changes typically drive improved execution and market responsiveness.")
            context_parts.append("[UP] VALUATION IMPACT: Well-executed transitions often lead to multiple expansion and improved investor confidence.")
            
        elif update_type == 'product_announcement':
            # Product launch context
            innovation_level = update_metadata.get('innovation_level', 'significant')
            market_potential = update_metadata.get('market_potential', 'medium')
            competitive_advantage = update_metadata.get('competitive_advantage', 'moderate')
            
            context_parts.append(f"🚀 INNOVATION IMPACT: This {innovation_level} product launch demonstrates R&D effectiveness and market positioning.")
            context_parts.append(f"💡 MARKET OPPORTUNITY: {market_potential.title()} market potential suggests substantial revenue contribution potential.")
            context_parts.append(f"🏆 COMPETITIVE POSITION: {competitive_advantage.title()} competitive advantage may drive market share gains.")
            context_parts.append("[CHART] REVENUE IMPLICATIONS: Successful launches typically contribute 10-25% of incremental growth within 18 months.")
            
        elif update_type == 'acquisition_announcement':
            # M&A context
            deal_value = update_metadata.get('deal_value', 'Undisclosed')
            synergy_potential = update_metadata.get('synergy_potential', 'medium')
            strategic_focus = update_metadata.get('strategic_focus', 'growth')
            
            context_parts.append(f"🤝 M&A STRATEGY: ${deal_value} acquisition represents strategic {strategic_focus.replace('_', ' ')} initiative.")
            context_parts.append(f"⚡ SYNERGY OUTLOOK: {synergy_potential.title()} synergy potential suggests strong value creation opportunity.")
            context_parts.append("💼 INTEGRATION FOCUS: Successful M&A execution requires disciplined integration management and cultural alignment.")
            context_parts.append("[UP] VALUATION IMPACT: Market will evaluate deal economics, strategic rationale, and management execution capability.")
            
        else:
            # Generic corporate context
            context_parts.append(f"🏢 CORPORATE DEVELOPMENT: {company} announcement reflects ongoing strategic evolution and market adaptation.")
            context_parts.append("[CHART] STAKEHOLDER IMPACT: Employees, customers, and investors will monitor implementation and performance metrics.")
        
        # Add sector-wide implications
        context_parts.append("🌐 SECTOR IMPLICATIONS: This development may influence competitive dynamics and industry best practices.")
        context_parts.append("📱 PREMIUM INSIGHT: WiseNews subscribers receive comprehensive corporate analysis and market impact assessment.")
        
        return " ".join(context_parts)
    
    def _get_conference_context(self, update_data: Dict, event_metadata: Dict, update_metadata: Dict) -> str:
        """Generate conference-specific context and implications"""
        context_parts = []
        
        # Add relevance context
        context_parts.append("[TARGET] This development could have significant implications for stakeholders.")
        
        # Add timing context
        context_parts.append("⏰ We'll continue monitoring for additional announcements and reactions.")
        
        # Add follow-up context
        context_parts.append("📱 Premium subscribers will receive instant updates as the situation develops.")
        
        return " ".join(context_parts)
    
    def _auto_share_breaking_news(self):
        """Automatically share breaking news to social media platforms"""
        try:
            from social_media_manager import social_media_manager
            
            # Get recent breaking news that hasn't been shared yet
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT n.id, n.title, n.content, n.category, n.url, n.image_url
                FROM news n
                LEFT JOIN social_media_posts smp ON n.id = smp.article_id
                WHERE n.category = 'breaking_news'
                AND n.published_date > datetime('now', '-1 hour')
                AND smp.id IS NULL
                ORDER BY n.published_date DESC
                LIMIT 5
            ''')
            
            unshared_news = cursor.fetchall()
            conn.close()
            
            for news_item in unshared_news:
                article_data = {
                    'id': news_item[0],
                    'title': news_item[1],
                    'content': news_item[2],
                    'category': news_item[3],
                    'url': news_item[4] or f"http://localhost:5000/article/{news_item[0]}",
                    'image_url': news_item[5]
                }
                
                # Determine platforms based on content type
                platforms = ['twitter', 'linkedin']
                if 'market' in article_data['title'].lower() or 'stock' in article_data['title'].lower():
                    platforms.append('facebook')
                
                # Auto-post to social media
                success = social_media_manager.auto_post_breaking_news(article_data, platforms)
                
                if success:
                    logger.info(f"Auto-shared breaking news to social media: {article_data['title']}")
                
        except Exception as e:
            logger.error(f"Error auto-sharing breaking news: {e}")
    
    def _share_generated_article_to_social(self, article_data: Dict):
        """Share newly generated articles to social media"""
        try:
            from social_media_manager import social_media_manager
            
            # Enhanced sharing for generated articles
            platforms = ['twitter', 'linkedin', 'facebook']
            
            # Create special content for generated articles
            article_data['generated'] = True
            article_data['exclusive'] = True
            
            success = social_media_manager.auto_post_breaking_news(article_data, platforms)
            
            if success:
                logger.info(f"Shared generated article to social media: {article_data.get('title', 'Untitled')}")
            
        except Exception as e:
            logger.error(f"Error sharing generated article to social: {e}")
    
    def _cleanup_old_events(self):
        """Clean up old events and mark them as completed"""
        try:
            conn = sqlite3.connect('news_database.db')
            cursor = conn.cursor()
            
            # Mark events older than 5 minutes as completed
            cursor.execute('''
                UPDATE live_events 
                SET status = 'completed' 
                WHERE start_time < datetime('now', '-5 minutes') 
                AND status = 'active'
            ''')
            
            updated_count = cursor.rowcount
            
            if updated_count > 0:
                logger.info(f"Marked {updated_count} old events as completed")
            
            # Remove very old completed events (older than 24 hours) to prevent database bloat
            cursor.execute('''
                DELETE FROM live_events 
                WHERE start_time < datetime('now', '-24 hours') 
                AND status = 'completed'
            ''')
            
            deleted_count = cursor.rowcount
            
            if deleted_count > 0:
                logger.info(f"Removed {deleted_count} old completed events from database")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error cleaning up old events: {e}")

# Global instance
live_events_manager = LiveEventsManager()
