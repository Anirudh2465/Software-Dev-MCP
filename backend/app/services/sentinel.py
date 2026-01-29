import psutil
import requests
import os
import time

class SentinelService:
    def __init__(self):
        self.services = {
            "backend": "http://localhost:8001/health",
            "chroma": os.getenv("CHROMA_HOST", "http://localhost:8000") + "/api/v1/heartbeat", # Adjust based on version
            # Mongo and Redis are harder to HTTP check without internal clients or exposed metrics.
            # For V1, we just check Backend and Chroma which are HTTP.
        }

    def check_system_metrics(self):
        """
        Returns basic system metrics.
        """
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_usage,
                "memory_percent": memory_info.percent,
                "disk_percent": disk_info.percent,
                "memory_available_mb": round(memory_info.available / 1024 / 1024, 2)
            }
        except Exception as e:
            return {"error": str(e)}

    def check_services(self):
        """
        Pings defined services.
        """
        status = {}
        for name, url in self.services.items():
            try:
                # Short timeout
                r = requests.get(url, timeout=2)
                if r.status_code == 200:
                    status[name] = "OK"
                else:
                    status[name] = f"WARN ({r.status_code})"
            except Exception as e:
                 status[name] = f"DOWN ({str(e)})"
        return status

    def generate_report(self):
        """
        Generates a human-readable health report.
        """
        sys_metrics = self.check_system_metrics()
        svc_status = self.check_services()
        
        report = [
            "--- Sentinel System Health Report ---",
            f"CPU Usage: {sys_metrics.get('cpu_percent')}%",
            f"RAM Usage: {sys_metrics.get('memory_percent')}% ({sys_metrics.get('memory_available_mb')} MB free)",
            f"Disk Usage: {sys_metrics.get('disk_percent')}%",
            "--- Service Status ---"
        ]
        
        for name, state in svc_status.items():
            report.append(f"{name.upper()}: {state}")
            
        return "\n".join(report)

if __name__ == "__main__":
    s = SentinelService()
    print(s.generate_report())
