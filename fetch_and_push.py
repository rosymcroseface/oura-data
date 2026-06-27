import requests
import json
import os
import base64
from datetime import datetime, timedelta

OURA_ACCESS_TOKEN = os.getenv("OURA_ACCESS_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

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
    """Push data to GitHub using API"""
    try:
        filename = "oura_data_latest.json"
        content = json.dumps(data, indent=2)
        
        # GitHub API URL
        url = f"https://api.github.com/repos/{GITHUB_USERNAME}/oura-data/contents/{filename}"
        
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Encode content
        encoded_content = base64.b64encode(content.encode()).decode()
        
        # Try to get existing file (to get sha for update)
        existing = requests.get(url, headers=headers)
        
        payload = {
            "message": f"Update Oura data - {datetime.now().isoformat()}",
            "content": encoded_content
        }
        
        if existing.status_code == 200:
            # File exists, need sha to update
            payload["sha"] = existing.json()["sha"]
        
        # Create or update
        response = requests.put(url, headers=headers, json=payload)
        
        if response.status_code in [201, 200]:
            print("✓ Pushed to GitHub")
        else:
            print(f"✗ GitHub error: {response.status_code} - {response.text}")
            
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
