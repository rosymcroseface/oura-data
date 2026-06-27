import requests
import json
import os
from datetime import datetime, timedelta
from google.auth.oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle

OURA_ACCESS_TOKEN = os.getenv("OURA_ACCESS_TOKEN")
GOOGLE_OAUTH_CREDENTIALS = os.getenv("GOOGLE_OAUTH_CREDENTIALS")

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service():
    """Get authenticated Google Drive service"""
    creds = None
    
    # Try to load saved credentials
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid creds, use OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_string(
                GOOGLE_OAUTH_CREDENTIALS, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)

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

def upload_to_google_drive(data):
    """Upload data to Google Drive"""
    try:
        service = get_drive_service()
        
        filename = "oura_data_latest.json"
        content = json.dumps(data, indent=2)
        
        # Search for existing file
        results = service.files().list(
            q=f"name='{filename}' and trashed=false",
            spaces='drive',
            pageSize=1,
            fields='files(id, name)'
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            # Update existing file
            file_id = files[0]['id']
            media = MediaFileUpload(
                filename='temp.json',
                mimetype='application/json',
                chunksize=-1
            )
            # Write to temp file
            with open('temp.json', 'w') as f:
                f.write(content)
            
            service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
            print("✓ Updated file on Google Drive")
        else:
            # Create new file
            with open('temp.json', 'w') as f:
                f.write(content)
            
            file_metadata = {'name': filename}
            media = MediaFileUpload('temp.json', mimetype='application/json')
            
            service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            print("✓ Created file on Google Drive")
            
    except Exception as e:
        print(f"✗ Error uploading to Google Drive: {e}")

def main():
    print("Starting Oura data fetch...")
    data = fetch_oura_data()
    print("Uploading to Google Drive...")
    upload_to_google_drive(data)
    print("✓ Done!")

if __name__ == "__main__":
    main()
