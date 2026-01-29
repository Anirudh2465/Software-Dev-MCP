import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.services.sentinel import SentinelService

def check_health():
    """
    Checks system and service health and prints a report.
    """
    try:
        sentinel = SentinelService()
        report = sentinel.generate_report()
        print(report)
        return report
    except Exception as e:
        print(f"Error checking health: {e}")
        return str(e)

if __name__ == "__main__":
    check_health()
