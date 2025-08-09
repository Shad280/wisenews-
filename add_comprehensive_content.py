#!/usr/bin/env python3
"""
Database Content Checker
Check current articles and add comprehensive content
"""

import sqlite3
from datetime import datetime, timedelta
import random

def check_current_content():
    """Check what's currently in the database"""
    try:
        conn = sqlite3.connect('wisenews.db')
        cursor = conn.cursor()
        
        # Check articles
        cursor.execute('SELECT COUNT(*) FROM articles')
        article_count = cursor.fetchone()[0]
        print(f"📰 Current articles: {article_count}")
        
        if article_count > 0:
            cursor.execute('SELECT title, source, category FROM articles LIMIT 5')
            articles = cursor.fetchall()
            print("Sample articles:")
            for i, article in enumerate(articles, 1):
                print(f"  {i}. {article[0][:50]}... ({article[1]} - {article[2]})")
        
        # Check categories
        cursor.execute('SELECT name FROM categories')
        categories = cursor.fetchall()
        print(f"\n📊 Categories: {len(categories)}")
        for cat in categories:
            print(f"  - {cat[0]}")
        
        conn.close()
        return article_count
        
    except Exception as e:
        print(f"Error checking content: {e}")
        return 0

def add_comprehensive_articles():
    """Add comprehensive sample articles covering all categories"""
    try:
        conn = sqlite3.connect('wisenews.db')
        cursor = conn.cursor()
        
        # Comprehensive article set
        comprehensive_articles = [
            # Technology Articles
            ("Artificial Intelligence Breakthrough: New Language Model Surpasses Human Performance", 
             "Researchers at leading tech companies have developed an AI system that demonstrates human-level performance across multiple cognitive tasks, marking a significant milestone in artificial intelligence development.", 
             "https://techcrunch.com/ai-breakthrough", "Dr. Sarah Chen", "TechCrunch", "technology", 
             datetime.now() - timedelta(hours=2), 45),
            
            ("Quantum Computing Milestone: Error-Corrected Quantum Processor Achieved", 
             "Scientists have successfully created a quantum processor with error correction capabilities, bringing practical quantum computing significantly closer to reality and opening new possibilities for complex calculations.", 
             "https://nature.com/quantum-milestone", "Prof. Michael Rodriguez", "Nature", "technology", 
             datetime.now() - timedelta(hours=4), 67),
            
            ("Cybersecurity Alert: New Vulnerability Discovered in Popular Software", 
             "Security researchers have identified a critical vulnerability affecting millions of users worldwide. Companies are urged to update their systems immediately to prevent potential security breaches.", 
             "https://securitynews.com/vulnerability-alert", "Alex Thompson", "Security News", "technology", 
             datetime.now() - timedelta(hours=6), 123),
            
            # Business Articles
            ("Global Markets Rally as Economic Indicators Show Strong Growth", 
             "Stock markets worldwide experienced significant gains following the release of positive economic data, with technology and healthcare sectors leading the charge in what analysts call a broad-based recovery.", 
             "https://reuters.com/markets-rally", "Maria Santos", "Reuters", "business", 
             datetime.now() - timedelta(hours=1), 89),
            
            ("Major Tech Company Announces $50 Billion Investment in Green Energy", 
             "In a landmark announcement, the technology giant revealed plans to invest heavily in renewable energy infrastructure, signaling a major shift toward sustainable business practices across the industry.", 
             "https://bloomberg.com/green-investment", "James Wilson", "Bloomberg", "business", 
             datetime.now() - timedelta(hours=3), 156),
            
            ("Cryptocurrency Market Sees Significant Volatility Amid Regulatory Changes", 
             "Digital currencies experienced dramatic price swings following announcements of new regulatory frameworks in major economies, highlighting the ongoing evolution of the cryptocurrency landscape.", 
             "https://coindesk.com/crypto-volatility", "Lisa Park", "CoinDesk", "business", 
             datetime.now() - timedelta(hours=5), 201),
            
            # Health Articles
            ("Breakthrough Cancer Treatment Shows 95% Success Rate in Clinical Trials", 
             "A revolutionary new cancer treatment has demonstrated remarkable effectiveness in phase III clinical trials, offering hope to millions of patients worldwide and potentially transforming cancer care.", 
             "https://nejm.org/cancer-breakthrough", "Dr. Robert Kim", "New England Journal of Medicine", "health", 
             datetime.now() - timedelta(hours=8), 78),
            
            ("Global Health Organization Reports Significant Decline in Infectious Diseases", 
             "The World Health Organization released data showing a substantial reduction in infectious disease cases globally, crediting improved vaccination programs and public health measures for the positive trend.", 
             "https://who.int/disease-decline", "Dr. Priya Patel", "WHO", "health", 
             datetime.now() - timedelta(hours=12), 234),
            
            ("Mental Health: New Study Reveals Effective Digital Therapy Approaches", 
             "Researchers have found that digital mental health interventions can be as effective as traditional therapy for many conditions, potentially making mental health care more accessible to underserved populations.", 
             "https://psychiatry.org/digital-therapy", "Dr. Amanda Foster", "American Journal of Psychiatry", "health", 
             datetime.now() - timedelta(hours=10), 167),
            
            # Science Articles
            ("NASA's James Webb Telescope Discovers Potentially Habitable Exoplanet", 
             "The space telescope has identified a planet in the habitable zone of its star system, with atmospheric conditions that could potentially support liquid water and life as we know it.", 
             "https://nasa.gov/webb-discovery", "Dr. Elena Rodriguez", "NASA", "science", 
             datetime.now() - timedelta(hours=7), 345),
            
            ("Climate Change: New Carbon Capture Technology Shows Promise", 
             "Scientists have developed an innovative carbon capture system that can remove CO2 from the atmosphere more efficiently than previous methods, offering a potential tool in the fight against climate change.", 
             "https://science.org/carbon-capture", "Dr. Mark Johnson", "Science Magazine", "science", 
             datetime.now() - timedelta(hours=14), 189),
            
            ("Breakthrough in Renewable Energy: Solar Panel Efficiency Reaches 50%", 
             "Engineers have achieved a new record in solar panel efficiency, developing cells that can convert 50% of sunlight into electricity, potentially revolutionizing renewable energy adoption.", 
             "https://energy.gov/solar-breakthrough", "Dr. Sophie Zhang", "Department of Energy", "science", 
             datetime.now() - timedelta(hours=16), 267),
            
            # Sports Articles
            ("Olympic Games: Record-Breaking Performances Highlight Athletic Excellence", 
             "Athletes continue to push the boundaries of human performance at the ongoing Olympic Games, with multiple world records broken across various disciplines in what's being called an exceptional competition.", 
             "https://olympic.org/records", "Sports Correspondent", "Olympic News", "sports", 
             datetime.now() - timedelta(hours=3), 198),
            
            ("Championship Final: Underdog Team Achieves Historic Victory", 
             "In a stunning upset that captivated fans worldwide, the underdog team overcame significant odds to claim their first championship title in franchise history, marking a momentous achievement.", 
             "https://espn.com/championship-upset", "Mike Anderson", "ESPN", "sports", 
             datetime.now() - timedelta(hours=18), 456),
            
            ("Sports Science: New Training Methods Improve Athlete Performance by 30%", 
             "Revolutionary training techniques based on cutting-edge sports science research have shown remarkable results in improving athletic performance, potentially changing how professional athletes prepare.", 
             "https://sportscience.org/training-methods", "Dr. Kevin Brown", "Sports Science Journal", "sports", 
             datetime.now() - timedelta(hours=24), 134),
            
            # Entertainment Articles
            ("Film Industry: Independent Movie Wins Major International Awards", 
             "A small-budget independent film has garnered critical acclaim and major awards, demonstrating the continuing importance of innovative storytelling and artistic vision in cinema.", 
             "https://variety.com/indie-film-success", "Entertainment Reporter", "Variety", "entertainment", 
             datetime.now() - timedelta(hours=6), 287),
            
            ("Streaming Wars: New Platform Launches with Exclusive Content", 
             "The entertainment landscape continues to evolve as a new streaming service enters the market with high-profile exclusive content, intensifying competition in the digital entertainment space.", 
             "https://hollywood.com/streaming-launch", "Rachel Green", "Hollywood Reporter", "entertainment", 
             datetime.now() - timedelta(hours=9), 156),
            
            ("Music Industry: Virtual Reality Concerts Gain Popularity", 
             "Virtual reality technology is transforming live music experiences, with artists and fans embracing immersive concert experiences that blur the lines between physical and digital entertainment.", 
             "https://musicnews.com/vr-concerts", "David Lee", "Music News", "entertainment", 
             datetime.now() - timedelta(hours=15), 223),
            
            # General News Articles
            ("International Summit Addresses Global Climate Action", 
             "World leaders gathered for a historic climate summit, announcing ambitious new commitments to reduce carbon emissions and transition to renewable energy sources over the next decade.", 
             "https://un.org/climate-summit", "International Correspondent", "UN News", "general", 
             datetime.now() - timedelta(hours=4), 178),
            
            ("Educational Innovation: New Learning Platform Reaches 10 Million Students", 
             "A groundbreaking educational technology platform has achieved a milestone of serving 10 million students globally, demonstrating the growing impact of digital learning solutions.", 
             "https://education.org/platform-milestone", "Dr. Jennifer Liu", "Education Weekly", "general", 
             datetime.now() - timedelta(hours=20), 145),
            
            ("Space Exploration: Private Company Successfully Launches Mars Mission", 
             "A private space company has successfully launched an ambitious mission to Mars, marking a significant milestone in commercial space exploration and planetary science research.", 
             "https://space.com/mars-mission", "Space Reporter", "Space.com", "general", 
             datetime.now() - timedelta(hours=11), 389)
        ]
        
        # Insert articles
        saved_count = 0
        for article in comprehensive_articles:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO articles 
                    (title, summary, url, author, source, category, published_date, views)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', article)
                saved_count += 1
            except Exception as e:
                print(f"Error saving article: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Added {saved_count} comprehensive articles to database")
        return saved_count
        
    except Exception as e:
        print(f"❌ Error adding articles: {e}")
        return 0

if __name__ == '__main__':
    print("🔍 Checking current database content...")
    current_count = check_current_content()
    
    print(f"\n📰 Adding comprehensive articles...")
    added_count = add_comprehensive_articles()
    
    print(f"\n✅ Database now has comprehensive content!")
    print(f"📊 Total articles added: {added_count}")
