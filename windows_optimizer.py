"""
Windows-specific server optimizations for WiseNews
Optimizes performance for Windows Server environment
"""

import os
import sys
import subprocess
import winreg
import ctypes
from ctypes import wintypes
import psutil
import logging

class WindowsOptimizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def is_admin(self):
        """Check if script is running with admin privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
            
    def optimize_tcp_settings(self):
        """Optimize TCP settings for high concurrent connections"""
        try:
            if not self.is_admin():
                self.logger.warning("Admin privileges required for TCP optimization")
                return False
                
            # Optimize TCP settings for web server
            tcp_settings = [
                ('TcpMaxDataRetransmissions', 3),
                ('TcpAckFrequency', 1),
                ('TcpNoDelay', 1),
                ('DefaultTTL', 64),
                ('EnablePMTUDiscovery', 1),
                ('MaxConnectRetransmissions', 3),
                ('MaxConnectResponseRetransmissions', 3),
                ('KeepAliveInterval', 1000),
                ('KeepAliveTime', 7200000),
                ('TcpMaxConnectRetransmissions', 3)
            ]
            
            key_path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"
            
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
                for setting, value in tcp_settings:
                    try:
                        winreg.SetValueEx(key, setting, 0, winreg.REG_DWORD, value)
                        self.logger.info(f"Set {setting} = {value}")
                    except Exception as e:
                        self.logger.warning(f"Failed to set {setting}: {e}")
                        
            self.logger.info("TCP settings optimized (requires reboot)")
            return True
            
        except Exception as e:
            self.logger.error(f"TCP optimization failed: {e}")
            return False
            
    def optimize_memory_management(self):
        """Optimize Windows memory management"""
        try:
            # Get system memory info
            memory = psutil.virtual_memory()
            total_memory_gb = memory.total / (1024**3)
            
            self.logger.info(f"Total system memory: {total_memory_gb:.1f} GB")
            
            # Set appropriate memory settings
            if total_memory_gb >= 16:
                # For 16GB+ systems, optimize for server workload
                self.logger.info("Configuring for high-memory server workload")
                
                # These require admin privileges
                if self.is_admin():
                    try:
                        # Increase system cache size
                        key_path = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
                            # Optimize for server performance
                            winreg.SetValueEx(key, "LargeSystemCache", 0, winreg.REG_DWORD, 1)
                            self.logger.info("Enabled large system cache")
                            
                    except Exception as e:
                        self.logger.warning(f"Memory optimization failed: {e}")
                        
            return True
            
        except Exception as e:
            self.logger.error(f"Memory optimization failed: {e}")
            return False
            
    def optimize_process_priority(self):
        """Set optimal process priority for the application"""
        try:
            # Get current process
            current_process = psutil.Process()
            
            # Set high priority for better responsiveness
            current_process.nice(psutil.HIGH_PRIORITY_CLASS)
            self.logger.info("Set process priority to HIGH")
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Process priority optimization failed: {e}")
            return False
            
    def optimize_file_system(self):
        """Optimize file system settings"""
        try:
            # Create optimized directories with proper permissions
            directories = ['cache', 'logs', 'temp']
            
            for directory in directories:
                if not os.path.exists(directory):
                    os.makedirs(directory)
                    
                # Set directory to not be indexed by Windows Search
                try:
                    subprocess.run([
                        'attrib', '+S', directory
                    ], check=False, capture_output=True)
                    self.logger.info(f"Optimized directory: {directory}")
                except:
                    pass
                    
            return True
            
        except Exception as e:
            self.logger.error(f"File system optimization failed: {e}")
            return False
            
    def check_windows_features(self):
        """Check and recommend Windows features for web server"""
        recommendations = []
        
        try:
            # Check if IIS is installed (might conflict)
            result = subprocess.run([
                'dism', '/online', '/get-featureinfo', '/featurename:IIS-WebServerRole'
            ], capture_output=True, text=True)
            
            if 'State : Enabled' in result.stdout:
                recommendations.append("IIS is enabled - consider disabling if not needed to avoid port conflicts")
                
        except:
            pass
            
        try:
            # Check Windows Defender status
            result = subprocess.run([
                'powershell', '-Command', 'Get-MpComputerStatus'
            ], capture_output=True, text=True)
            
            if 'True' in result.stdout:
                recommendations.append("Add WiseNews directory to Windows Defender exclusions for better performance")
                
        except:
            pass
            
        return recommendations
        
    def create_performance_report(self):
        """Create Windows-specific performance report"""
        try:
            report = {
                'system_info': {
                    'os': f"{os.name} {sys.platform}",
                    'cpu_count': psutil.cpu_count(),
                    'memory_gb': psutil.virtual_memory().total / (1024**3),
                    'disk_usage': psutil.disk_usage('.').percent
                },
                'optimizations_applied': [],
                'recommendations': []
            }
            
            # CPU information
            try:
                result = subprocess.run(['wmic', 'cpu', 'get', 'name'], 
                                      capture_output=True, text=True)
                if result.stdout:
                    cpu_info = result.stdout.strip().split('\n')
                    if len(cpu_info) > 1:
                        report['system_info']['cpu'] = cpu_info[1].strip()
            except:
                pass
                
            # Network adapter information
            try:
                adapters = []
                for interface, addrs in psutil.net_if_addrs().items():
                    if not interface.startswith('Loopback'):
                        adapters.append(interface)
                report['system_info']['network_adapters'] = adapters
            except:
                pass
                
            # Get Windows version
            try:
                result = subprocess.run(['ver'], shell=True, capture_output=True, text=True)
                if result.stdout:
                    report['system_info']['windows_version'] = result.stdout.strip()
            except:
                pass
                
            # Check if running as admin
            report['system_info']['admin_privileges'] = self.is_admin()
            
            # Add recommendations
            report['recommendations'].extend(self.check_windows_features())
            
            if not self.is_admin():
                report['recommendations'].append("Run as Administrator for full system optimizations")
                
            # Performance recommendations based on system specs
            memory_gb = report['system_info']['memory_gb']
            if memory_gb < 8:
                report['recommendations'].append("Consider upgrading to at least 8GB RAM for optimal performance")
            elif memory_gb >= 16:
                report['recommendations'].append("System has sufficient RAM for high-performance operation")
                
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to create performance report: {e}")
            return None
            
    def run_windows_optimizations(self):
        """Run all Windows-specific optimizations"""
        self.logger.info("Running Windows-specific optimizations...")
        
        results = {}
        
        # File system optimization (always works)
        results['file_system'] = self.optimize_file_system()
        
        # Process priority (usually works)
        results['process_priority'] = self.optimize_process_priority()
        
        # Memory management (requires admin)
        results['memory_management'] = self.optimize_memory_management()
        
        # TCP settings (requires admin)
        results['tcp_settings'] = self.optimize_tcp_settings()
        
        # Create performance report
        report = self.create_performance_report()
        
        self.logger.info("Windows optimization completed")
        self.logger.info(f"Successful optimizations: {sum(results.values())}/{len(results)}")
        
        if not self.is_admin():
            self.logger.info("For full optimization, run as Administrator")
            
        return results, report

# Global instance
windows_optimizer = WindowsOptimizer()

if __name__ == "__main__":
    import json
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler('logs/windows_optimization.log'),
            logging.StreamHandler()
        ]
    )
    
    # Run optimizations
    results, report = windows_optimizer.run_windows_optimizations()
    
    # Save report
    if report:
        with open('logs/windows_performance_report.json', 'w') as f:
            json.dump(report, f, indent=2)
            
    print("\nWindows Optimization Summary:")
    print(f"✓ Optimizations applied: {sum(results.values())}/{len(results)}")
    print("📊 Performance report saved to logs/windows_performance_report.json")
    
    if report and report.get('recommendations'):
        print("\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
            
    print("\n🚀 Run start_optimized_server.bat to start the optimized server")
