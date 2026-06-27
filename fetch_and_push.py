import requests
import json
import os
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

OURA_ACCESS_TOKEN = os.getenv("OURA_ACCESS_TOKEN")
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
SHEET_ID = "1qDaRZJqjmso403aD1A-uSJ0S_YJwA0wt6-_pJ1JlyF4"

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_sheets_service():
    """Get authenticated Google Sheets service"""
    creds_dict = json.loads(GOOGLE_SHEETS_CREDENTIALS)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return build('sheets', 'v4', credentials=creds)

def fetch_oura_data():
    """Fetch all Oura data for last 30 days"""
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    all_data = {}
    
    endpoints = {
        "daily_sleep": "daily_sleep",
        "daily_activity": "daily_activity",
        "daily_readiness": "daily_readiness",
        "daily_heart_rate": "daily_heart_rate",
        "daily_stress": "daily_stress",
        "daily_resilience": "daily_resilience"
    }
    
    for endpoint in endpoints:
        try:
            response = requests.get(
                f"https://api.ouraring.com/v2/usercollection/{endpoint}?start_date={start_date}&end_date={end_date}",
                headers={"Authorization": f"Bearer {OURA_ACCESS_TOKEN}"}
            )
            if response.status_code == 200:
                all_data[endpoint] = response.json().get("data", [])
                print(f"✓ Fetched {endpoint}")
            else:
                print(f"✗ Failed {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"✗ Error {endpoint}: {e}")
    
    return all_data

def append_to_sheet(service, data):
    """Append Oura data rows to Google Sheet"""
    try:
        # Build a dict of data by date for easy lookup
        by_date = {}
        
        # Sleep data
        for item in data.get("daily_sleep", []):
            date = item.get("day")
            if date not in by_date:
                by_date[date] = {}
            by_date[date]["sleep_score"] = item.get("score", "")
            by_date[date]["total_sleep_mins"] = item.get("total_sleep_duration", 0) // 60
            by_date[date]["sleep_efficiency"] = item.get("efficiency", "")
        
        # Activity data
        for item in data.get("daily_activity", []):
            date = item.get("day")
            if date not in by_date:
                by_date[date] = {}
            by_date[date]["activity_score"] = item.get("score", "")
        
        # Readiness data
        for item in data.get("daily_readiness", []):
            date = item.get("day")
            if date not in by_date:
                by_date[date] = {}
            by_date[date]["readiness_score"] = item.get("score", "")
        
        # Heart rate data
        for item in data.get("daily_heart_rate", []):
            date = item.get("day")
            if date not in by_date:
                by_date[date] = {}
            by_date[date]["heart_rate"] = item.get("resting_heart_rate", "")
            by_date[date]["hrv"] = item.get("heart_rate_variability", "")
        
        # Stress data
        for item in data.get("daily_stress", []):
            date = item.get("day")
            if date not in by_date:
                by_date[date] = {}
            by_date[date]["stress"] = item.get("stress_level", "")
        
        # Resilience data
        for item in data.get("daily_resilience", []):
            date = item.get("day")
            if date not in by_date:
                by_date[date] = {}
            by_date[date]["resilience"] = item.get("resilience_level", "")
        
        # Convert to rows
        rows = []
        for date in sorted(by_date.keys()):
            d = by_date[date]
            row = [
                date,
                d.get("sleep_score", ""),
                d.get("activity_score", ""),
                d.get("readiness_score", ""),
                d.get("heart_rate", ""),
                d.get("hrv", ""),
                d.get("stress", ""),
                d.get("resilience", ""),
                d.get("total_sleep_mins", ""),
                d.get("sleep_efficiency", "")
            ]
            rows.append(row)
        
        if not rows:
            print("No data to append")
            return
        
        # Append to sheet
        service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range="Sheet1!A2",
            valueInputOption="RAW",
            body={"values": rows}
        ).execute()
        
        print(f"✓ Appended {len(rows)} rows to Google Sheet")
        
    except Exception as e:
        print(f"✗ Error appending to sheet: {e}")

def main():
    print("Starting Oura data fetch...")
    data = fetch_oura_data()
    print("Appending to Google Sheet...")
    service = get_sheets_service()
    append_to_sheet(service, data)
    print("✓ Done!")

if __name__ == "__main__":
    main()
