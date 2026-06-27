import requests
import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

OURA_ACCESS_TOKEN = os.getenv("OURA_ACCESS_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = "oura-data"
GITHUB_OWNER = os.getenv("GITHUB_USERNAME")

def fetch_oura_data():
    """Fetch all Oura data for last 30 days"""
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    all_data = {
        "timestamp": datetime.now().isoformat(),
        "date_range": f"{start_date} to {end_date}",
        "data": {}
    }
    
    endpoints = [
        "daily_sleep",
        "daily_activity",
        "daily_readiness",
        "daily_heart_rate",
        "daily_spo2",
        "daily_stress",
        "daily_resilience",
        "sessions",
        "workouts",
        "tags"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(
                f"https://api.ouraring.com/v2/usercollection/{endpoint}?start_date={start_date}&end_date={end_date}",
                headers={"Authorization": f"Bearer {OURA_ACCESS_TOKEN}"}
            )
            if response.status_code == 200:
                all_data["data"][endpoint] = response.json().get("data", [])
                print(f"✓ Fetched {endpoint}")
            else:
                print(f"✗ Failed {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"✗ Error {endpoint}: {e}")
    
    return all_data

def push_to_github(data):
    """Save data to GitHub repo"""
    try:
        filename = "oura_data_latest.json"
        
        # Save locally
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Configure git
        subprocess.run(["git", "config", "user.email", "automation@oura.local"], check=True)
        subprocess.run(["git", "config", "user.name", "Oura Automation"], check=True)
        
        # Add and commit
        subprocess.run(["git", "add", filename], check=True)
        subprocess.run(["git", "commit", "-m", f"Update Oura data - {datetime.now().isoformat()}"], check=True)
        
        # Push (uses GITHUB_TOKEN from environment)
        subprocess.run(["git", "push"], check=True)
        
        print(f"✓ Pushed to GitHub")
        
    except Exception as e:
        print(f"✗ Error pushing to GitHub: {e}")

def main():
    print("Starting Oura data fetch...")
    data = fetch_oura_data()
    print("Pushing to GitHub...")
    push_to_github(data)
    print("✓ Done!")

if __name__ == "__main__":
    main()
