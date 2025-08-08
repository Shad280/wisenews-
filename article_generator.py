"""
Automatic Article Generator for WiseNews
Generates comprehensive articles for major events when news coverage is insufficient
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re
from database_manager import db_manager

logger = logging.getLogger(__name__)

class ArticleGenerator:
    def __init__(self):
        self.article_templates = {
            'earnings': self._get_earnings_template(),
            'regulatory': self._get_regulatory_template(),
            'market': self._get_market_template(),
            'corporate': self._get_corporate_template(),
            'general': self._get_general_template()
        }
    
    def check_coverage_gaps(self) -> List[Dict]:
        """Check for major events that lack sufficient news coverage"""
        try:
            # Find high-impact events from the last 48 hours with minimal coverage
            rows = db_manager.execute_query('''
                SELECT 
                    le.id, le.event_name, le.category, le.metadata,
                    leu.title, leu.content, leu.importance,
                    COUNT(n.id) as coverage_count
                FROM live_events le
                JOIN live_event_updates leu ON le.id = leu.event_id
                LEFT JOIN news n ON (
                    n.title LIKE '%' || SUBSTR(le.event_name, 1, 20) || '%' OR
                    n.content LIKE '%' || SUBSTR(le.event_name, 1, 20) || '%'
                ) AND n.published_date > datetime('now', '-48 hours')
                WHERE leu.timestamp > datetime('now', '-48 hours')
                AND leu.importance > 0.75
                GROUP BY le.id, le.event_name, le.category, le.metadata, leu.title, leu.content, leu.importance
                HAVING coverage_count < 3  -- Less than 3 related articles
                ORDER BY leu.importance DESC, leu.timestamp DESC
                LIMIT 10
            ''', fetch='all')
            
            coverage_gaps = []
            if rows:
                for row in rows:
                    event_id, event_name, category, metadata_json, update_title, update_content, importance, coverage_count = row
                    metadata = json.loads(metadata_json) if metadata_json else {}
                    
                    coverage_gaps.append({
                        'event_id': event_id,
                        'event_name': event_name,
                        'category': category,
                        'metadata': metadata,
                        'update_title': update_title,
                        'update_content': update_content,
                        'importance': importance,
                        'coverage_count': coverage_count
                    })
            
            return coverage_gaps
            
        except Exception as e:
            logger.error(f"Error checking coverage gaps: {e}")
            return []
    
    def generate_article_for_event(self, event_data: Dict) -> Optional[Dict]:
        """Generate a comprehensive article for an under-covered event"""
        try:
            # Debug logging
            logger.info(f"Generating article for event: {event_data}")
            
            category = event_data.get('category', 'general')
            
            # Determine article type based on category and metadata
            article_type = self._determine_article_type(category, event_data.get('metadata', {}))
            
            # Generate article using appropriate template
            article = self._generate_article_content(article_type, event_data)
            
            if article:
                # Store the article in the database
                return self._store_generated_article(event_data.get('event_id', 0), article)
            else:
                logger.error(f"Failed to generate article content for event: {event_data}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating article for event {event_data}: {e}", exc_info=True)
            return None
    
    def _determine_article_type(self, category: str, metadata: Dict) -> str:
        """Determine the appropriate article type based on category and metadata"""
        
        if category in ['earnings', 'corporate'] or metadata.get('event_type') in ['earnings_release', 'leadership_change', 'product_launch', 'acquisition']:
            return 'corporate'
        elif category in ['federal_reserve', 'sec_filing', 'treasury', 'cftc', 'fdic']:
            return 'regulatory'
        elif category in ['stocks', 'crypto', 'forex'] or metadata.get('symbol'):
            return 'market'
        elif category in ['earnings']:
            return 'earnings'
        else:
            return 'general'
    
    def _generate_article_content(self, article_type: str, event_data: Dict) -> Optional[Dict]:
        """Generate article content using the appropriate template"""
        
        template = self.article_templates.get(article_type, self.article_templates['general'])
        
        # Extract key information with validation
        event_name = event_data.get('event_name', '').strip()
        metadata = event_data.get('metadata', {})
        update_content = event_data.get('update_content', '').strip()
        importance = event_data.get('importance', 0.5)
        
        # Validate required data
        if not event_name:
            logger.warning("Empty event_name in article generation, using fallback")
            event_name = f"Market Event #{event_data.get('event_id', 'Unknown')}"
        
        # Generate title
        title = self._generate_title(article_type, event_name, metadata)
        
        # Generate sections
        sections = []
        for section in template['sections']:
            section_content = self._generate_section_content(
                section, event_name, metadata, update_content, importance
            )
            if section_content and section_content.strip():
                sections.append(section_content.strip())
        
        # Ensure we have content
        if not sections:
            logger.warning("No sections generated, creating basic content")
            sections = [f"**Breaking Update**\n\n{event_name} has been making headlines in the financial markets."]
        
        # Combine into full article
        full_content = "\n\n".join(sections)
        
        # Ensure content is not empty
        if not full_content.strip():
            logger.error("Generated article content is empty, using fallback")
            full_content = f"**{title}**\n\nThis is a developing story. More details will be provided as they become available."
        
        # Generate summary
        summary = self._generate_summary(event_name, metadata, importance)
        
        # Generate keywords
        keywords = self._generate_keywords(event_name, metadata, article_type)
        
        # Calculate reading metrics
        word_count = len(full_content.split())
        reading_time = max(1, word_count // 200)  # 200 words per minute
        
        return {
            'title': title,
            'content': full_content,
            'summary': summary,
            'keywords': keywords,
            'word_count': word_count,
            'reading_time': reading_time,
            'article_type': article_type
        }
    
    def _generate_title(self, article_type: str, event_name: str, metadata: Dict) -> str:
        """Generate an appropriate title for the article"""
        
        # Ensure we have a valid event name
        if not event_name or not event_name.strip():
            event_name = "Major Market Event"
            logger.warning("Empty event_name provided to _generate_title, using fallback")
        
        event_name = event_name.strip()
        
        if article_type == 'corporate':
            company = metadata.get('company', 'Major Corporation')
            ticker = metadata.get('ticker', 'TICKER')
            event_type = metadata.get('event_type', 'announcement')
            
            if event_type == 'earnings_release':
                quarter = metadata.get('quarter', 'Latest Quarter')
                return f"Market Analysis: {company} ({ticker}) {quarter} Earnings Results and Strategic Outlook"
            elif event_type == 'leadership_change':
                return f"Corporate Strategy: {company} ({ticker}) Leadership Changes Signal New Direction"
            elif event_type == 'product_launch':
                return f"Innovation Focus: {company} ({ticker}) Unveils Breakthrough Technology"
            elif event_type == 'acquisition':
                deal_value = metadata.get('deal_value', 'Major')
                return f"M&A Analysis: {company} ({ticker}) ${deal_value} Acquisition Reshapes Industry"
            else:
                return f"Corporate News: {company} ({ticker}) Major Announcement Impacts Market"
        
        elif article_type == 'regulatory':
            institution = metadata.get('institution', 'Regulatory Authority')
            regulation_type = metadata.get('announcement_type', metadata.get('regulation_type', 'policy'))
            return f"Regulatory Update: {institution} Announces Major {regulation_type.replace('_', ' ').title()} Changes"
        
        elif article_type == 'market':
            symbol = metadata.get('symbol', 'Market')
            change_percent = metadata.get('change_percent', 0)
            direction = "Surge" if change_percent > 0 else "Decline"
            return f"Market Analysis: {symbol} {direction} Signals Broader Market Trends"
        
        elif article_type == 'earnings':
            company = metadata.get('company', event_name)
            return f"Earnings Analysis: {company} Financial Results and Market Implications"
        
        else:
            return f"Breaking Analysis: {event_name} - Comprehensive Coverage and Impact Assessment"
    
    def _generate_section_content(self, section: Dict, event_name: str, metadata: Dict, 
                                 update_content: str, importance: float) -> str:
        """Generate content for a specific section"""
        
        section_title = section['title']
        content_type = section['type']
        
        if content_type == 'introduction':
            return self._generate_introduction(section_title, event_name, metadata, importance)
        elif content_type == 'analysis':
            return self._generate_analysis_section(section_title, event_name, metadata, update_content)
        elif content_type == 'market_impact':
            return self._generate_market_impact_section(section_title, metadata)
        elif content_type == 'implications':
            return self._generate_implications_section(section_title, event_name, metadata)
        elif content_type == 'outlook':
            return self._generate_outlook_section(section_title, event_name, metadata)
        elif content_type == 'conclusion':
            return self._generate_conclusion(section_title, event_name, metadata)
        else:
            return self._generate_generic_section(section_title, event_name, metadata, update_content)
    
    def _generate_introduction(self, title: str, event_name: str, metadata: Dict, importance: float) -> str:
        """Generate introduction section"""
        urgency = "critical" if importance > 0.9 else "significant" if importance > 0.8 else "important"
        
        return f"""**{title}**

In a {urgency} development that is capturing widespread market attention, {event_name} represents a major milestone with far-reaching implications across multiple sectors and stakeholder groups. This comprehensive analysis examines the key details, underlying factors, and potential consequences of this pivotal announcement.

The timing and scope of this development reflect careful strategic planning and demonstrate the evolving dynamics within the relevant markets and regulatory environments. Understanding the full implications requires examining both immediate impacts and longer-term strategic considerations."""
    
    def _generate_analysis_section(self, title: str, event_name: str, metadata: Dict, update_content: str) -> str:
        """Generate detailed analysis section"""
        
        # Extract key themes from update content
        key_themes = self._extract_key_themes(update_content)
        
        return f"""**{title}**

The development surrounding {event_name} reveals several critical factors that market participants and stakeholders must carefully consider. {key_themes['primary_theme']}

Key analytical points include the strategic rationale behind this development, the implementation timeline and associated challenges, and the competitive implications within the broader market context. The announcement addresses several market dynamics that have been evolving over recent periods.

{key_themes['secondary_theme']} This comprehensive approach demonstrates sophisticated planning and risk management consideration, while positioning for future growth and adaptation to changing market conditions."""
    
    def _generate_market_impact_section(self, title: str, metadata: Dict) -> str:
        """Generate market impact analysis section"""
        
        return f"""**{title}**

Financial markets are responding to this development with heightened volatility and increased trading activity across multiple asset classes. Institutional investors are rapidly reassessing their portfolios and risk management strategies in light of the new information and changed market dynamics.

The immediate market reaction includes adjustments in sector allocations, options positioning, and currency hedging strategies. Trading volumes have increased significantly above normal levels, indicating strong institutional interest and active position management.

Credit markets are also reflecting the changed risk profile, with spread adjustments and rating implications being evaluated by market participants. The broader economic implications extend beyond immediate price movements to include structural changes in market relationships and risk assessments."""
    
    def _generate_implications_section(self, title: str, event_name: str, metadata: Dict) -> str:
        """Generate implications analysis section"""
        
        return f"""**{title}**

The implications of {event_name} extend across multiple dimensions, affecting various stakeholder groups through different mechanisms and timeframes. Immediate impacts are already becoming apparent in market pricing and institutional positioning.

Strategic implications include changes in competitive dynamics, regulatory considerations, and operational requirements that will influence decision-making processes across affected industries. The development also creates new opportunities and challenges that market participants must carefully evaluate.

Long-term structural changes may emerge as markets adapt to the new environment and participants adjust their strategies accordingly. The interconnected nature of modern financial systems means that effects will propagate through various channels and geographic regions."""
    
    def _generate_outlook_section(self, title: str, event_name: str, metadata: Dict) -> str:
        """Generate future outlook section"""
        
        return f"""**{title}**

Looking ahead, the development of {event_name} sets the stage for continued evolution and adaptation across affected markets and industries. Key indicators to monitor include market performance metrics, regulatory responses, and stakeholder adaptation strategies.

The success of implementation will depend on effective coordination among various parties, adequate preparation and resource allocation, and continued dialogue to address emerging challenges and opportunities. Market participants should prepare for ongoing developments and potential adjustments.

Future policy considerations and strategic planning must account for the changed landscape created by this development. The lessons learned and precedents established will inform future decision-making and risk management approaches across the broader market ecosystem."""
    
    def _generate_conclusion(self, title: str, event_name: str, metadata: Dict) -> str:
        """Generate conclusion section"""
        
        return f"""**{title}**

The announcement of {event_name} represents a watershed moment that will likely be remembered as a significant turning point in the relevant markets and industries. The comprehensive nature of the development demonstrates the complexity and interconnectedness of modern financial and business systems.

Market participants, regulatory authorities, and other stakeholders should continue monitoring the situation closely and preparing appropriate responses to the evolving circumstances. The insights gained from this analysis provide a foundation for understanding and navigating the changed environment.

Success in adapting to these developments will require continued vigilance, strategic thinking, and collaborative approaches among all stakeholders. The precedents set and lessons learned will contribute to more resilient and adaptive market structures going forward."""
    
    def _generate_generic_section(self, title: str, event_name: str, metadata: Dict, update_content: str) -> str:
        """Generate generic section content"""
        
        return f"""**{title}**

The development of {event_name} continues to unfold with significant implications for all stakeholders involved. The comprehensive nature of this situation requires careful analysis and strategic consideration from multiple perspectives.

Key factors influencing the current situation include market conditions, regulatory environment, and stakeholder expectations. The complexity of the interconnected systems involved necessitates coordinated responses and continued monitoring of emerging developments.

As the situation evolves, maintaining awareness of new information and changing circumstances will be essential for effective decision-making and risk management across all affected parties and market segments."""
    
    def _extract_key_themes(self, content: str) -> Dict[str, str]:
        """Extract key themes from update content"""
        
        # Simple theme extraction based on keywords and content patterns
        themes = {
            'primary_theme': "The strategic implications of this development are substantial and require careful consideration.",
            'secondary_theme': "Market participants are closely monitoring the situation for additional developments."
        }
        
        # Look for specific financial or corporate themes
        if any(word in content.lower() for word in ['earnings', 'revenue', 'profit', 'financial']):
            themes['primary_theme'] = "The financial performance implications demonstrate strong operational execution and strategic positioning."
        elif any(word in content.lower() for word in ['regulatory', 'compliance', 'policy', 'federal']):
            themes['primary_theme'] = "The regulatory implications require comprehensive compliance and strategic planning adjustments."
        elif any(word in content.lower() for word in ['market', 'trading', 'volatility', 'price']):
            themes['primary_theme'] = "The market dynamics reflect changing investor sentiment and risk assessment factors."
        
        return themes
    
    def _generate_summary(self, event_name: str, metadata: Dict, importance: float) -> str:
        """Generate article summary"""
        
        impact_level = "high" if importance > 0.8 else "moderate" if importance > 0.6 else "significant"
        
        return f"Comprehensive analysis of {event_name} examining the {impact_level}-impact implications, market reactions, and strategic considerations for stakeholders across multiple sectors and investment categories."
    
    def _generate_keywords(self, event_name: str, metadata: Dict, article_type: str) -> List[str]:
        """Generate relevant keywords for the article"""
        
        keywords = [
            article_type,
            'market_analysis',
            'comprehensive_coverage',
            'strategic_implications'
        ]
        
        # Add specific keywords based on metadata
        if metadata.get('company'):
            keywords.append(metadata['company'].lower().replace(' ', '_'))
        if metadata.get('ticker'):
            keywords.append(metadata['ticker'].lower())
        if metadata.get('sector'):
            keywords.append(metadata['sector'].lower())
        if metadata.get('institution'):
            keywords.append(metadata['institution'].lower().replace(' ', '_'))
        
        # Add event name components
        event_words = [word.lower() for word in event_name.split() if len(word) > 3]
        keywords.extend(event_words[:3])  # Limit to top 3 words
        
        return list(set(keywords))  # Remove duplicates
    
    def _store_generated_article(self, event_id: int, article: Dict) -> Optional[Dict]:
        """Store the generated article in the database"""
        try:
            # Validate article data with detailed logging
            title = article.get('title', '').strip()
            content = article.get('content', '').strip()
            
            if not title:
                logger.error(f"Cannot store article: missing or empty title. Article data: {article}")
                return None
                
            if not content:
                logger.error(f"Cannot store article: missing or empty content. Title: {title}")
                return None
                
            if len(title) < 10:
                logger.warning(f"Article title is very short: '{title}'. Generating fallback title.")
                title = f"Breaking News Update: Event #{event_id} Analysis"
            
            # Store in generated_articles table
            article_id = db_manager.execute_query('''
                INSERT INTO generated_articles 
                (event_id, article_title, article_content, article_summary, keywords, 
                 category, importance, word_count, reading_time, publication_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_id,
                article['title'][:500],  # Limit title length
                article['content'],
                article.get('summary', '')[:1000],  # Limit summary length
                ','.join(article.get('keywords', [])),
                article.get('article_type', 'general'),
                0.9,  # High importance for generated articles
                article.get('word_count', 0),
                article.get('reading_time', 5),
                'published'
            ))
            
            if not article_id:
                logger.error("Failed to insert article into generated_articles table")
                return None
            
            # Also add to main news table for user access
            db_manager.execute_query('''
                INSERT INTO news (title, content, category, source, url, tags, published_date)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                article['title'][:500],  # Limit title length
                article['content'],
                article.get('article_type', 'general'),
                'WiseNews Analysis Team',
                f'/generated-article/{article_id}',
                ','.join(article.get('keywords', []))
            ))
            
            logger.info(f"Generated and stored article: {article['title']}")
            
            return {
                'article_id': article_id,
                'title': article['title'],
                'url': f'/generated-article/{article_id}',
                'word_count': article['word_count'],
                'reading_time': article['reading_time']
            }
            
        except Exception as e:
            logger.error(f"Error storing generated article: {e}")
            return None
    
    def _get_earnings_template(self) -> Dict:
        """Get template for earnings articles"""
        return {
            'sections': [
                {'title': 'Executive Summary', 'type': 'introduction'},
                {'title': 'Financial Performance Analysis', 'type': 'analysis'},
                {'title': 'Market Impact and Investor Response', 'type': 'market_impact'},
                {'title': 'Strategic Implications and Business Outlook', 'type': 'implications'},
                {'title': 'Industry Context and Competitive Positioning', 'type': 'analysis'},
                {'title': 'Future Outlook and Investment Considerations', 'type': 'outlook'},
                {'title': 'Conclusion and Key Takeaways', 'type': 'conclusion'}
            ]
        }
    
    def _get_regulatory_template(self) -> Dict:
        """Get template for regulatory articles"""
        return {
            'sections': [
                {'title': 'Regulatory Overview', 'type': 'introduction'},
                {'title': 'Policy Analysis and Implementation Details', 'type': 'analysis'},
                {'title': 'Market Impact and Industry Response', 'type': 'market_impact'},
                {'title': 'Compliance Requirements and Timeline', 'type': 'implications'},
                {'title': 'Economic Implications and Stakeholder Effects', 'type': 'analysis'},
                {'title': 'Future Regulatory Outlook', 'type': 'outlook'},
                {'title': 'Strategic Considerations and Conclusion', 'type': 'conclusion'}
            ]
        }
    
    def _get_market_template(self) -> Dict:
        """Get template for market analysis articles"""
        return {
            'sections': [
                {'title': 'Market Overview', 'type': 'introduction'},
                {'title': 'Technical and Fundamental Analysis', 'type': 'analysis'},
                {'title': 'Sector Impact and Cross-Asset Effects', 'type': 'market_impact'},
                {'title': 'Risk Assessment and Portfolio Implications', 'type': 'implications'},
                {'title': 'Economic Context and Policy Considerations', 'type': 'analysis'},
                {'title': 'Trading Outlook and Strategic Positioning', 'type': 'outlook'},
                {'title': 'Investment Summary and Recommendations', 'type': 'conclusion'}
            ]
        }
    
    def _get_corporate_template(self) -> Dict:
        """Get template for corporate news articles"""
        return {
            'sections': [
                {'title': 'Corporate Development Overview', 'type': 'introduction'},
                {'title': 'Strategic Analysis and Business Impact', 'type': 'analysis'},
                {'title': 'Market Reaction and Valuation Effects', 'type': 'market_impact'},
                {'title': 'Operational and Financial Implications', 'type': 'implications'},
                {'title': 'Industry Context and Competitive Analysis', 'type': 'analysis'},
                {'title': 'Future Business Outlook', 'type': 'outlook'},
                {'title': 'Investment Implications and Conclusion', 'type': 'conclusion'}
            ]
        }
    
    def _get_general_template(self) -> Dict:
        """Get template for general news articles"""
        return {
            'sections': [
                {'title': 'Situation Overview', 'type': 'introduction'},
                {'title': 'Detailed Analysis and Key Factors', 'type': 'analysis'},
                {'title': 'Broader Impact Assessment', 'type': 'market_impact'},
                {'title': 'Stakeholder Implications', 'type': 'implications'},
                {'title': 'Context and Background Considerations', 'type': 'analysis'},
                {'title': 'Future Developments and Outlook', 'type': 'outlook'},
                {'title': 'Summary and Key Points', 'type': 'conclusion'}
            ]
        }

# Global instance for use throughout the application
article_generator = ArticleGenerator()
