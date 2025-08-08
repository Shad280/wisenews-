"""
WiseNews Server Performance Monitor and Status
Real-time monitoring and optimization status
"""

import psutil
import sqlite3
import time
import json
import os
from datetime import datetime, timedelta
import threading
import logging

class PerformanceMonitor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.monitoring = False
        self.stats_history = []
        self.max_history = 100
        
    def get_system_stats(self):
        """Get current system performance statistics"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('.')
            
            # Network
            network = psutil.net_io_counters()
            
            # Process specific
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            stats = {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_total_gb': memory.total / (1024**3),
                    'memory_used_gb': memory.used / (1024**3),
                    'memory_available_gb': memory.available / (1024**3),
                    'memory_percent': memory.percent,
                    'disk_used_gb': disk.used / (1024**3),
                    'disk_free_gb': disk.free / (1024**3),
                    'disk_percent': (disk.used / disk.total) * 100
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'process': {
                    'cpu_percent': process_cpu,
                    'memory_mb': process_memory.rss / (1024**2),
                    'memory_percent': process.memory_percent(),
                    'threads': process.num_threads(),
                    'connections': len(process.connections())
                }
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get system stats: {e}")
            return None
            
    def get_database_stats(self):
        """Get database performance statistics"""
        try:
            conn = sqlite3.connect('news_database.db', timeout=30)
            cursor = conn.cursor()
            
            stats = {}
            
            # Database size
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            stats['size_mb'] = (page_count * page_size) / (1024**2)
            
            # Record counts
            tables = ['articles', 'users', 'user_subscriptions', 'user_daily_usage', 'live_events']
            stats['table_counts'] = {}
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    stats['table_counts'][table] = count
                except:
                    stats['table_counts'][table] = 0
                    
            # Check database health
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            stats['integrity'] = integrity == 'ok'
            
            # WAL mode status
            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            stats['wal_mode'] = journal_mode.upper() == 'WAL'
            
            conn.close()
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return None
            
    def get_application_stats(self):
        """Get application-specific statistics"""
        try:
            stats = {
                'cache_directory_size': 0,
                'log_directory_size': 0,
                'cache_files_count': 0,
                'log_files_count': 0
            }
            
            # Cache directory stats
            if os.path.exists('cache'):
                for root, dirs, files in os.walk('cache'):
                    stats['cache_files_count'] += len(files)
                    for file in files:
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            stats['cache_directory_size'] += os.path.getsize(file_path)
                            
            # Log directory stats
            if os.path.exists('logs'):
                for root, dirs, files in os.walk('logs'):
                    stats['log_files_count'] += len(files)
                    for file in files:
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            stats['log_directory_size'] += os.path.getsize(file_path)
                            
            # Convert to MB
            stats['cache_directory_size'] /= (1024**2)
            stats['log_directory_size'] /= (1024**2)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get application stats: {e}")
            return None
            
    def generate_status_report(self):
        """Generate comprehensive status report"""
        try:
            system_stats = self.get_system_stats()
            database_stats = self.get_database_stats()
            app_stats = self.get_application_stats()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'system': system_stats,
                'database': database_stats,
                'application': app_stats,
                'optimization_status': self.check_optimization_status(),
                'health_status': self.get_health_status(system_stats, database_stats),
                'recommendations': []
            }
            
            # Generate recommendations
            if system_stats:
                if system_stats['system']['memory_percent'] > 80:
                    report['recommendations'].append("High memory usage - consider restarting or optimizing cache")
                    
                if system_stats['system']['cpu_percent'] > 80:
                    report['recommendations'].append("High CPU usage - check for resource-intensive operations")
                    
                if system_stats['process']['memory_mb'] > 512:
                    report['recommendations'].append("Application memory usage is high - consider optimization")
                    
            if database_stats:
                if database_stats['size_mb'] > 1000:
                    report['recommendations'].append("Database is large - consider archiving old data")
                    
                if not database_stats.get('wal_mode'):
                    report['recommendations'].append("Database not in WAL mode - performance could be improved")
                    
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate status report: {e}")
            return None
            
    def check_optimization_status(self):
        """Check which optimizations are active"""
        status = {
            'cache_directory': os.path.exists('cache'),
            'logs_directory': os.path.exists('logs'),
            'optimization_log': os.path.exists('logs/optimization.log'),
            'server_optimizer': os.path.exists('server_optimizer.py'),
            'production_config': os.path.exists('production_config.py'),
            'database_exists': os.path.exists('news_database.db')
        }
        
        # Check if database is in WAL mode
        try:
            conn = sqlite3.connect('news_database.db', timeout=30)
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            status['database_wal_mode'] = journal_mode.upper() == 'WAL'
            conn.close()
        except:
            status['database_wal_mode'] = False
            
        return status
        
    def get_health_status(self, system_stats, database_stats):
        """Determine overall system health"""
        if not system_stats or not database_stats:
            return 'UNKNOWN'
            
        issues = []
        
        # Check system health
        if system_stats['system']['memory_percent'] > 90:
            issues.append('Critical memory usage')
            
        if system_stats['system']['cpu_percent'] > 90:
            issues.append('Critical CPU usage')
            
        if system_stats['system']['disk_percent'] > 90:
            issues.append('Critical disk usage')
            
        # Check database health
        if not database_stats.get('integrity', False):
            issues.append('Database integrity issues')
            
        # Determine status
        if len(issues) == 0:
            return 'HEALTHY'
        elif len(issues) <= 2:
            return 'WARNING'
        else:
            return 'CRITICAL'
            
    def start_monitoring(self, interval=60):
        """Start continuous performance monitoring"""
        def monitor_worker():
            self.monitoring = True
            self.logger.info(f"Started performance monitoring (interval: {interval}s)")
            
            while self.monitoring:
                try:
                    report = self.generate_status_report()
                    if report:
                        # Add to history
                        self.stats_history.append(report)
                        
                        # Limit history size
                        if len(self.stats_history) > self.max_history:
                            self.stats_history.pop(0)
                            
                        # Save latest report
                        with open('logs/latest_status.json', 'w') as f:
                            json.dump(report, f, indent=2)
                            
                        # Log health status
                        health = report.get('health_status', 'UNKNOWN')
                        if health == 'CRITICAL':
                            self.logger.error(f"System health: {health}")
                        elif health == 'WARNING':
                            self.logger.warning(f"System health: {health}")
                        else:
                            self.logger.info(f"System health: {health}")
                            
                    time.sleep(interval)
                    
                except Exception as e:
                    self.logger.error(f"Monitoring error: {e}")
                    time.sleep(interval)
                    
            self.logger.info("Performance monitoring stopped")
            
        # Start monitoring thread
        thread = threading.Thread(target=monitor_worker, daemon=True)
        thread.start()
        
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        
    def get_current_status(self):
        """Get current system status"""
        return self.generate_status_report()
        
    def save_performance_history(self, filename='logs/performance_history.json'):
        """Save performance history to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.stats_history, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save performance history: {e}")
            return False

# Global monitor instance
performance_monitor = PerformanceMonitor()

def print_status_summary():
    """Print a formatted status summary"""
    try:
        report = performance_monitor.get_current_status()
        if not report:
            print("❌ Failed to generate status report")
            return
            
        print("\n" + "="*60)
        print("🚀 WISENEWS SERVER STATUS REPORT")
        print("="*60)
        
        # System info
        if report.get('system'):
            sys_info = report['system']['system']
            print(f"\n📊 SYSTEM PERFORMANCE:")
            print(f"   CPU Usage:     {sys_info['cpu_percent']:.1f}%")
            print(f"   Memory Usage:  {sys_info['memory_percent']:.1f}% ({sys_info['memory_used_gb']:.1f}/{sys_info['memory_total_gb']:.1f} GB)")
            print(f"   Disk Usage:    {sys_info['disk_percent']:.1f}% ({sys_info['disk_free_gb']:.1f} GB free)")
            
        # Database info
        if report.get('database'):
            db_info = report['database']
            print(f"\n💾 DATABASE STATUS:")
            print(f"   Size:          {db_info['size_mb']:.1f} MB")
            print(f"   WAL Mode:      {'✓' if db_info.get('wal_mode') else '✗'}")
            print(f"   Integrity:     {'✓' if db_info.get('integrity') else '✗'}")
            
            if db_info.get('table_counts'):
                print(f"   Articles:      {db_info['table_counts'].get('articles', 0):,}")
                print(f"   Users:         {db_info['table_counts'].get('users', 0):,}")
                
        # Application info
        if report.get('application'):
            app_info = report['application']
            print(f"\n🔧 APPLICATION STATUS:")
            print(f"   Cache Size:    {app_info['cache_directory_size']:.1f} MB ({app_info['cache_files_count']} files)")
            print(f"   Logs Size:     {app_info['log_directory_size']:.1f} MB ({app_info['log_files_count']} files)")
            
        # Health status
        health = report.get('health_status', 'UNKNOWN')
        health_icon = {'HEALTHY': '🟢', 'WARNING': '🟡', 'CRITICAL': '🔴', 'UNKNOWN': '⚪'}.get(health, '⚪')
        print(f"\n{health_icon} OVERALL HEALTH: {health}")
        
        # Recommendations
        if report.get('recommendations'):
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in report['recommendations']:
                print(f"   • {rec}")
                
        # Optimization status
        if report.get('optimization_status'):
            opt_status = report['optimization_status']
            print(f"\n⚙️  OPTIMIZATION STATUS:")
            for opt, status in opt_status.items():
                status_icon = '✓' if status else '✗'
                print(f"   {status_icon} {opt.replace('_', ' ').title()}")
                
        print("\n" + "="*60)
        print(f"📅 Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error generating status summary: {e}")

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s'
    )
    
    # Print current status
    print_status_summary()
    
    # Optionally start monitoring
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--monitor':
        try:
            performance_monitor.start_monitoring(interval=60)
            print("\n🔄 Continuous monitoring started (60-second intervals)")
            print("📁 Status reports saved to: logs/latest_status.json")
            print("⌨️  Press Ctrl+C to stop monitoring\n")
            
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            performance_monitor.stop_monitoring()
            performance_monitor.save_performance_history()
            print("\n✅ Monitoring stopped and history saved")
    else:
        print("\n💡 Run with --monitor flag to start continuous monitoring")
        print("   python performance_monitor.py --monitor")
