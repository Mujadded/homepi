#!/usr/bin/env python3
"""
HomePi Watchdog Service
Monitors system health and automatically fixes common issues
"""

import os
import sys
import time
import json
import subprocess
import logging
import requests
import psutil
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
WATCHDOG_CONFIG = {
    'check_interval': 30,  # seconds
    'max_failures': 3,     # max failures before action
    'service_name': 'homepi.service',
    'app_port': 5000,
    'app_url': 'http://localhost:5000',
    'log_file': '/var/log/homepi-watchdog.log',
    'max_log_size': 10 * 1024 * 1024,  # 10MB
    'max_log_files': 5,
    'enable_network_fix': True,
    'enable_bluetooth_fix': True,
    'enable_service_restart': True,
    'enable_system_reboot': True,
    'max_reboots_per_hour': 2,
    'network_timeout': 10,
    'bluetooth_devices': ['hci0'],  # Bluetooth devices to check
    'critical_services': ['homepi.service', 'bluetooth.service'],
    'network_interface': 'eth0',  # or 'wlan0' for WiFi
    'dns_servers': ['8.8.8.8', '1.1.1.1'],
    'test_urls': ['http://192.168.0.26:5000/', 'http://google.com', 'http://cloudflare.com']
}

class HomePiWatchdog:
    def __init__(self):
        self.setup_logging()
        self.failure_count = 0
        self.last_reboot = None
        self.reboot_count = 0
        self.reboot_window_start = None
        self.logger.info("HomePi Watchdog Service Started")
        
    def setup_logging(self):
        """Setup logging with rotation"""
        log_dir = Path(WATCHDOG_CONFIG['log_file']).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(WATCHDOG_CONFIG['log_file']),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def log_rotate(self):
        """Rotate log files if they get too large"""
        log_file = Path(WATCHDOG_CONFIG['log_file'])
        if log_file.exists() and log_file.stat().st_size > WATCHDOG_CONFIG['max_log_size']:
            # Rotate existing logs
            for i in range(WATCHDOG_CONFIG['max_log_files'] - 1, 0, -1):
                old_log = f"{WATCHDOG_CONFIG['log_file']}.{i}"
                new_log = f"{WATCHDOG_CONFIG['log_file']}.{i + 1}"
                if Path(old_log).exists():
                    Path(old_log).rename(new_log)
            
            # Move current log
            log_file.rename(f"{WATCHDOG_CONFIG['log_file']}.1")
            
            # Recreate log file
            log_file.touch()
            self.logger.info("Log rotated")
    
    def run_command(self, command, timeout=30):
        """Run a shell command with timeout"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out: {command}")
            return False, "", "Command timed out"
        except Exception as e:
            self.logger.error(f"Command failed: {command}, Error: {e}")
            return False, "", str(e)
    
    def check_service_status(self):
        """Check if homepi service is running"""
        try:
            success, stdout, stderr = self.run_command(f"systemctl is-active {WATCHDOG_CONFIG['service_name']}")
            if success and stdout.strip() == 'active':
                return True
            else:
                self.logger.warning(f"Service {WATCHDOG_CONFIG['service_name']} is not active: {stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Error checking service status: {e}")
            return False
    
    def check_app_health(self):
        """Check if the Flask app is responding"""
        try:
            response = requests.get(
                f"{WATCHDOG_CONFIG['app_url']}/api/health", 
                timeout=WATCHDOG_CONFIG['network_timeout']
            )
            if response.status_code == 200:
                return True
            else:
                self.logger.warning(f"App health check failed: HTTP {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"App health check failed: {e}")
            return False
    
    def check_network_connectivity(self):
        """Check network connectivity"""
        for url in WATCHDOG_CONFIG['test_urls']:
            try:
                response = requests.get(url, timeout=WATCHDOG_CONFIG['network_timeout'])
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                continue
        
        self.logger.warning("Network connectivity check failed")
        return False
    
    def check_bluetooth_status(self):
        """Check Bluetooth status"""
        if not WATCHDOG_CONFIG['enable_bluetooth_fix']:
            return True
            
        try:
            success, stdout, stderr = self.run_command("systemctl is-active bluetooth")
            if not success or stdout.strip() != 'active':
                self.logger.warning("Bluetooth service is not active")
                return False
            
            # Check if Bluetooth devices are available
            for device in WATCHDOG_CONFIG['bluetooth_devices']:
                success, stdout, stderr = self.run_command(f"hciconfig {device}")
                if not success or 'UP' not in stdout:
                    self.logger.warning(f"Bluetooth device {device} is not up")
                    return False
            
            # Check if Bluetooth audio sink is available (run as user)
            success, stdout, stderr = self.run_command("sudo -u mujadded PULSE_RUNTIME_PATH=/run/user/1000/pulse pactl list short sinks | grep bluez")
            if not success or not stdout.strip():
                self.logger.warning("No Bluetooth audio sink found")
                return False
            
            # Check if the sink is actually running (not suspended)
            success, stdout, stderr = self.run_command("sudo -u mujadded PULSE_RUNTIME_PATH=/run/user/1000/pulse pactl list short sinks | grep bluez | grep RUNNING")
            if not success or not stdout.strip():
                self.logger.warning("Bluetooth audio sink found but not running")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"Error checking Bluetooth status: {e}")
            return False
    
    def check_system_resources(self):
        """Check system resources (CPU, memory, disk)"""
        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                self.logger.warning(f"High CPU usage: {cpu_percent}%")
                return False
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                self.logger.warning(f"High memory usage: {memory.percent}%")
                return False
            
            # Check disk usage
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                self.logger.warning(f"High disk usage: {disk.percent}%")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"Error checking system resources: {e}")
            return False
    
    def restart_service(self):
        """Restart the homepi service"""
        if not WATCHDOG_CONFIG['enable_service_restart']:
            return False
            
        self.logger.info("Restarting homepi service...")
        try:
            # Stop service
            self.run_command(f"systemctl stop {WATCHDOG_CONFIG['service_name']}")
            time.sleep(5)
            
            # Start service
            success, stdout, stderr = self.run_command(f"systemctl start {WATCHDOG_CONFIG['service_name']}")
            if success:
                self.logger.info("Service restarted successfully")
                return True
            else:
                self.logger.error(f"Failed to restart service: {stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Error restarting service: {e}")
            return False
    
    def fix_network(self):
        """Fix network connectivity issues"""
        if not WATCHDOG_CONFIG['enable_network_fix']:
            return False
            
        self.logger.info("Attempting to fix network connectivity...")
        
        try:
            # Restart networking service
            self.run_command("systemctl restart networking")
            time.sleep(10)
            
            # Restart network interface
            interface = WATCHDOG_CONFIG['network_interface']
            self.run_command(f"ifdown {interface}")
            time.sleep(2)
            self.run_command(f"ifup {interface}")
            time.sleep(10)
            
            # Flush DNS cache
            self.run_command("systemctl flush-dns")
            
            # Test connectivity
            if self.check_network_connectivity():
                self.logger.info("Network connectivity restored")
                return True
            else:
                self.logger.warning("Network fix attempt failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error fixing network: {e}")
            return False
    
    def fix_bluetooth(self):
        """Fix Bluetooth connectivity issues"""
        if not WATCHDOG_CONFIG['enable_bluetooth_fix']:
            return False
            
        self.logger.info("Attempting to fix Bluetooth...")
        
        try:
            # Check if this is a post-reboot fix
            reboot_flag_file = '/tmp/homepi-watchdog-reboot'
            is_post_reboot = os.path.exists(reboot_flag_file)
            
            if is_post_reboot:
                self.logger.info("Post-reboot Bluetooth fix detected")
                # Remove the reboot flag
                try:
                    os.remove(reboot_flag_file)
                except:
                    pass
            
            # Restart Bluetooth service
            self.run_command("systemctl restart bluetooth")
            time.sleep(5)
            
            # Reset Bluetooth adapters
            for device in WATCHDOG_CONFIG['bluetooth_devices']:
                self.run_command(f"hciconfig {device} down")
                time.sleep(1)
                self.run_command(f"hciconfig {device} up")
                time.sleep(2)
            
            # Run the bluetooth fix script if it exists
            bluetooth_fix_script = "/home/mujadded/homepi/fix-pipewire-bluetooth.sh"
            if os.path.exists(bluetooth_fix_script):
                self.logger.info("Running Bluetooth fix script...")
                success, stdout, stderr = self.run_command(f"bash {bluetooth_fix_script}", timeout=120)
                if success:
                    self.logger.info("Bluetooth fix script completed successfully")
                else:
                    self.logger.warning(f"Bluetooth fix script had issues: {stderr}")
            else:
                self.logger.warning("Bluetooth fix script not found")
            
            time.sleep(10)  # Give more time for audio system to initialize
            
            # Check if Bluetooth sink is now available and running (run as user)
            success, stdout, stderr = self.run_command("sudo -u mujadded PULSE_RUNTIME_PATH=/run/user/1000/pulse pactl list short sinks | grep bluez | grep RUNNING")
            if success and stdout.strip():
                sink_line = stdout.strip()
                sink_name = sink_line.split()[1]
                self.logger.info(f"Bluetooth sink found and running: {sink_name}")
                
                # Set as default sink and adjust volume (run as user)
                self.run_command(f"sudo -u mujadded PULSE_RUNTIME_PATH=/run/user/1000/pulse pactl set-default-sink {sink_name}")
                self.run_command(f"sudo -u mujadded PULSE_RUNTIME_PATH=/run/user/1000/pulse pactl set-sink-volume {sink_name} 70%")
                
                if self.check_bluetooth_status():
                    self.logger.info("Bluetooth connectivity restored")
                    return True
            
            self.logger.warning("Bluetooth fix attempt failed - no audio sink found")
            return False
                
        except Exception as e:
            self.logger.error(f"Error fixing Bluetooth: {e}")
            return False
    
    def reboot_system(self):
        """Reboot the system as last resort"""
        if not WATCHDOG_CONFIG['enable_system_reboot']:
            return False
            
        # Check reboot rate limiting
        now = datetime.now()
        if self.reboot_window_start is None:
            self.reboot_window_start = now
            self.reboot_count = 0
        
        # Reset counter if window has passed
        if now - self.reboot_window_start > timedelta(hours=1):
            self.reboot_window_start = now
            self.reboot_count = 0
        
        if self.reboot_count >= WATCHDOG_CONFIG['max_reboots_per_hour']:
            self.logger.error("Maximum reboots per hour reached, skipping reboot")
            return False
        
        self.logger.critical("Rebooting system as last resort...")
        self.reboot_count += 1
        
        try:
            # Create a flag file to indicate watchdog-initiated reboot
            with open('/tmp/homepi-watchdog-reboot', 'w') as f:
                f.write(f"{datetime.now().isoformat()}\n")
            
            # Schedule reboot in 30 seconds to allow logging
            self.run_command("shutdown -r +1 'HomePi Watchdog initiated reboot'")
            return True
        except Exception as e:
            self.logger.error(f"Error scheduling reboot: {e}")
            return False
    
    def perform_health_check(self):
        """Perform comprehensive health check"""
        checks = {
            'service': self.check_service_status(),
            'app': self.check_app_health(),
            'network': self.check_network_connectivity(),
            'bluetooth': self.check_bluetooth_status(),
            'resources': self.check_system_resources()
        }
        
        self.logger.info(f"Health check results: {checks}")
        return all(checks.values()), checks
    
    def attempt_fixes(self, failed_checks):
        """Attempt to fix failed checks"""
        fixes_applied = []
        
        # Fix service issues
        if not failed_checks.get('service', True):
            if self.restart_service():
                fixes_applied.append('service_restart')
        
        # Fix network issues
        if not failed_checks.get('network', True):
            if self.fix_network():
                fixes_applied.append('network_fix')
        
        # Fix Bluetooth issues
        if not failed_checks.get('bluetooth', True):
            if self.fix_bluetooth():
                fixes_applied.append('bluetooth_fix')
        
        return fixes_applied
    
    def run_watchdog_cycle(self):
        """Run one watchdog cycle"""
        try:
            # Perform health check
            is_healthy, check_results = self.perform_health_check()
            
            if is_healthy:
                self.failure_count = 0
                self.logger.debug("System is healthy")
                return True
            
            # System is unhealthy
            self.failure_count += 1
            self.logger.warning(f"System health check failed (attempt {self.failure_count}/{WATCHDOG_CONFIG['max_failures']})")
            
            # Attempt fixes
            fixes_applied = self.attempt_fixes(check_results)
            if fixes_applied:
                self.logger.info(f"Applied fixes: {fixes_applied}")
                # Wait a bit for fixes to take effect
                time.sleep(30)
                
                # Re-check after fixes
                is_healthy_after_fix, _ = self.perform_health_check()
                if is_healthy_after_fix:
                    self.failure_count = 0
                    self.logger.info("System recovered after fixes")
                    return True
            
            # If we've reached max failures, consider reboot
            if self.failure_count >= WATCHDOG_CONFIG['max_failures']:
                self.logger.critical("Maximum failures reached, considering system reboot")
                if self.reboot_system():
                    self.failure_count = 0
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in watchdog cycle: {e}")
            return False
    
    def check_post_reboot_status(self):
        """Check if we need to run post-reboot fixes"""
        reboot_flag_file = '/tmp/homepi-watchdog-reboot'
        
        if os.path.exists(reboot_flag_file):
            self.logger.info("Post-reboot detected, checking system status...")
            
            # Wait a bit for system to fully boot
            time.sleep(30)
            
            # Check Bluetooth status first
            if not self.check_bluetooth_status():
                self.logger.info("Running post-reboot Bluetooth fix...")
                if self.fix_bluetooth():
                    self.logger.info("Post-reboot Bluetooth fix successful")
                else:
                    self.logger.warning("Post-reboot Bluetooth fix failed")
            
            # Check other services
            is_healthy, check_results = self.perform_health_check()
            if not is_healthy:
                self.logger.info("Running post-reboot system fixes...")
                fixes_applied = self.attempt_fixes(check_results)
                if fixes_applied:
                    self.logger.info(f"Post-reboot fixes applied: {fixes_applied}")
            
            # Remove reboot flag
            try:
                os.remove(reboot_flag_file)
                self.logger.info("Reboot flag removed")
            except:
                pass

    def run(self):
        """Main watchdog loop"""
        self.logger.info("Starting HomePi Watchdog Service")
        
        # Check for post-reboot fixes first
        self.check_post_reboot_status()
        
        while True:
            try:
                # Rotate logs if needed
                self.log_rotate()
                
                # Run watchdog cycle
                self.run_watchdog_cycle()
                
                # Wait before next check
                time.sleep(WATCHDOG_CONFIG['check_interval'])
                
            except KeyboardInterrupt:
                self.logger.info("Watchdog service stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in watchdog loop: {e}")
                time.sleep(60)  # Wait a minute before retrying

if __name__ == "__main__":
    watchdog = HomePiWatchdog()
    watchdog.run()
