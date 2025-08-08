"""
WiseNews Database Optimizer
Implements comprehensive database optimizations for improved performance
"""

import sqlite3
import time
import os
from datetime import datetime

class DatabaseOptimizer:
    def __init__(self, db_path='news_database.db'):
        self.db_path = db_path
        self.optimization_log = []
    
    def log_optimization(self, message):
        """Log optimization steps with timestamps"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.optimization_log.append(log_entry)
        print(f"🔧 {message}")
    
    def analyze_current_performance(self):
        """Analyze current database performance and structure"""
        self.log_optimization("Analyzing current database performance...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get database size
        db_size = os.path.getsize(self.db_path) / (1024 * 1024)  # MB
        self.log_optimization(f"Database size: {db_size:.2f} MB")
        
        # Get article count
        cursor.execute("SELECT COUNT(*) FROM articles")
        article_count = cursor.fetchone()[0]
        self.log_optimization(f"Total articles: {article_count:,}")
        
        # Check existing indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='articles'")
        existing_indexes = [row[0] for row in cursor.fetchall()]
        self.log_optimization(f"Existing indexes on articles: {len(existing_indexes)}")
        
        # Test query performance before optimization
        start_time = time.time()
        cursor.execute("SELECT * FROM articles ORDER BY date_added DESC LIMIT 50")
        cursor.fetchall()
        baseline_time = (time.time() - start_time) * 1000
        self.log_optimization(f"Baseline query time (50 articles): {baseline_time:.2f}ms")
        
        conn.close()
        return {
            'db_size_mb': db_size,
            'article_count': article_count,
            'existing_indexes': existing_indexes,
            'baseline_query_time': baseline_time
        }
    
    def create_performance_indexes(self):
        """Create optimized indexes for common queries"""
        self.log_optimization("Creating performance indexes...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Critical indexes for the most common queries
        indexes_to_create = [
            # Core performance indexes
            ('idx_articles_date_added_desc', 'CREATE INDEX IF NOT EXISTS idx_articles_date_added_desc ON articles(date_added DESC)'),
            ('idx_articles_category', 'CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category)'),
            ('idx_articles_source_name', 'CREATE INDEX IF NOT EXISTS idx_articles_source_name ON articles(source_name)'),
            ('idx_articles_source_type', 'CREATE INDEX IF NOT EXISTS idx_articles_source_type ON articles(source_type)'),
            
            # Composite indexes for common filter combinations
            ('idx_articles_date_category', 'CREATE INDEX IF NOT EXISTS idx_articles_date_category ON articles(date_added DESC, category)'),
            ('idx_articles_date_source', 'CREATE INDEX IF NOT EXISTS idx_articles_date_source ON articles(date_added DESC, source_name)'),
            
            # Full-text search optimization (if using LIKE queries)
            ('idx_articles_title_lower', 'CREATE INDEX IF NOT EXISTS idx_articles_title_lower ON articles(LOWER(title))'),
            
            # Duplicate detection optimization
            ('idx_articles_url_hash', 'CREATE INDEX IF NOT EXISTS idx_articles_url_hash ON articles(url_hash)'),
            ('idx_articles_content_hash', 'CREATE INDEX IF NOT EXISTS idx_articles_content_hash ON articles(content_hash)'),
            
            # Read status for user queries
            ('idx_articles_read_status', 'CREATE INDEX IF NOT EXISTS idx_articles_read_status ON articles(read_status)'),
            
            # Filename for file operations
            ('idx_articles_filename', 'CREATE INDEX IF NOT EXISTS idx_articles_filename ON articles(filename)'),
        ]
        
        created_count = 0
        for index_name, index_sql in indexes_to_create:
            try:
                start_time = time.time()
                cursor.execute(index_sql)
                creation_time = (time.time() - start_time) * 1000
                self.log_optimization(f"Created index {index_name} ({creation_time:.2f}ms)")
                created_count += 1
            except sqlite3.Error as e:
                self.log_optimization(f"Failed to create index {index_name}: {e}")
        
        conn.commit()
        conn.close()
        
        self.log_optimization(f"Successfully created {created_count} indexes")
        return created_count
    
    def optimize_database_settings(self):
        """Apply SQLite optimization settings"""
        self.log_optimization("Optimizing database settings...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Apply performance optimizations
        optimizations = [
            # Increase cache size (default is 2MB, we'll use 64MB)
            ('PRAGMA cache_size = -65536', 'Increased cache size to 64MB'),
            
            # Use WAL mode for better concurrency
            ('PRAGMA journal_mode = WAL', 'Enabled WAL journal mode'),
            
            # Optimize synchronous mode for better performance
            ('PRAGMA synchronous = NORMAL', 'Set synchronous mode to NORMAL'),
            
            # Optimize temp store
            ('PRAGMA temp_store = MEMORY', 'Store temp tables in memory'),
            
            # Optimize mmap size (use memory mapping)
            ('PRAGMA mmap_size = 268435456', 'Set memory mapping to 256MB'),
            
            # Optimize page size (only effective on new databases)
            ('PRAGMA page_size = 4096', 'Set page size to 4KB'),
            
            # Auto vacuum for space optimization
            ('PRAGMA auto_vacuum = INCREMENTAL', 'Enabled incremental auto vacuum'),
        ]
        
        applied_count = 0
        for pragma_sql, description in optimizations:
            try:
                cursor.execute(pragma_sql)
                result = cursor.fetchone()
                self.log_optimization(f"{description} - Result: {result}")
                applied_count += 1
            except sqlite3.Error as e:
                self.log_optimization(f"Failed to apply {description}: {e}")
        
        conn.commit()
        conn.close()
        
        self.log_optimization(f"Applied {applied_count} database optimizations")
        return applied_count
    
    def analyze_query_performance(self):
        """Analyze and test optimized query performance"""
        self.log_optimization("Testing optimized query performance...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        test_queries = [
            ("Recent articles", "SELECT * FROM articles ORDER BY date_added DESC LIMIT 50"),
            ("Category filter", "SELECT * FROM articles WHERE category = 'Technology' ORDER BY date_added DESC LIMIT 20"),
            ("Source filter", "SELECT * FROM articles WHERE source_name LIKE '%BBC%' ORDER BY date_added DESC LIMIT 20"),
            ("Title search", "SELECT * FROM articles WHERE LOWER(title) LIKE '%news%' LIMIT 20"),
            ("Article count", "SELECT COUNT(*) FROM articles"),
            ("Category stats", "SELECT category, COUNT(*) FROM articles GROUP BY category"),
        ]
        
        performance_results = {}
        
        for query_name, query_sql in test_queries:
            try:
                # Run query multiple times for accurate timing
                times = []
                for _ in range(3):
                    start_time = time.time()
                    cursor.execute(query_sql)
                    cursor.fetchall()
                    times.append((time.time() - start_time) * 1000)
                
                avg_time = sum(times) / len(times)
                performance_results[query_name] = avg_time
                self.log_optimization(f"{query_name}: {avg_time:.2f}ms (avg of 3 runs)")
                
            except sqlite3.Error as e:
                self.log_optimization(f"Failed to test {query_name}: {e}")
                performance_results[query_name] = None
        
        conn.close()
        return performance_results
    
    def run_vacuum_and_analyze(self):
        """Run VACUUM and ANALYZE for database optimization"""
        self.log_optimization("Running database maintenance...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # ANALYZE to update query planner statistics
            start_time = time.time()
            cursor.execute("ANALYZE")
            analyze_time = (time.time() - start_time) * 1000
            self.log_optimization(f"ANALYZE completed in {analyze_time:.2f}ms")
            
            # VACUUM to reorganize database file (optional, takes longer)
            # Uncomment if database fragmentation is suspected
            # start_time = time.time()
            # cursor.execute("VACUUM")
            # vacuum_time = (time.time() - start_time) * 1000
            # self.log_optimization(f"VACUUM completed in {vacuum_time:.2f}ms")
            
        except sqlite3.Error as e:
            self.log_optimization(f"Maintenance operation failed: {e}")
        
        conn.close()
    
    def optimize_database(self):
        """Run complete database optimization"""
        self.log_optimization("Starting comprehensive database optimization...")
        
        # Step 1: Analyze current performance
        baseline_stats = self.analyze_current_performance()
        
        # Step 2: Create performance indexes
        self.create_performance_indexes()
        
        # Step 3: Optimize database settings
        self.optimize_database_settings()
        
        # Step 4: Run maintenance
        self.run_vacuum_and_analyze()
        
        # Step 5: Test optimized performance
        optimized_performance = self.analyze_query_performance()
        
        # Step 6: Generate optimization report
        self.generate_optimization_report(baseline_stats, optimized_performance)
        
        self.log_optimization("Database optimization completed!")
        return self.optimization_log
    
    def generate_optimization_report(self, baseline_stats, optimized_performance):
        """Generate a comprehensive optimization report"""
        self.log_optimization("Generating optimization report...")
        
        report = [
            "\n" + "="*60,
            "DATABASE OPTIMIZATION REPORT",
            "="*60,
            f"Database: {self.db_path}",
            f"Size: {baseline_stats['db_size_mb']:.2f} MB",
            f"Articles: {baseline_stats['article_count']:,}",
            "",
            "PERFORMANCE IMPROVEMENTS:",
            "-" * 30,
        ]
        
        if optimized_performance:
            for query_name, time_ms in optimized_performance.items():
                if time_ms is not None:
                    if time_ms < 100:
                        status = "EXCELLENT"
                    elif time_ms < 300:
                        status = "GOOD"
                    else:
                        status = "NEEDS ATTENTION"
                    
                    report.append(f"{query_name}: {time_ms:.2f}ms {status}")
        
        report.extend([
            "",
            "OPTIMIZATION RECOMMENDATIONS:",
            "-" * 30,
            "* Database indexes optimized",
            "* SQLite settings tuned",
            "* Query performance analyzed",
            "",
            "NEXT STEPS:",
            "• Monitor query performance in production",
            "• Consider Redis caching for frequently accessed data",
            "• Implement query result caching in application layer",
            "• Regular ANALYZE maintenance (weekly)",
            "="*60
        ])
        
        # Write report to file
        report_file = f"database_optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        self.log_optimization(f"Report saved to {report_file}")
        
        # Print summary to console
        for line in report:
            print(line)

def main():
    """Run database optimization"""
    print("🚀 WiseNews Database Optimizer")
    print("=" * 50)
    
    optimizer = DatabaseOptimizer()
    optimization_log = optimizer.optimize_database()
    
    print("\n🎉 Optimization completed successfully!")
    print("Check the generated report for detailed results.")

if __name__ == "__main__":
    main()
