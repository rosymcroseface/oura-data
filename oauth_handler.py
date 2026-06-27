from flask import Flask, request
import requests
import os

app = Flask(__name__)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    
    if not code:
        return "Error: No code received"
    
    response = requests.post(
        'https://api.ouraring.com/oauth/token',
        data={
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': os.getenv('OURA_CLIENT_ID'),
            'client_secret': os.getenv('OURA_CLIENT_SECRET'),
            'redirect_uri': os.getenv('REDIRECT_URI')
        }
    )
    
    if response.status_code == 200:
        token = response.json().get('access_token')
        return f"<h1>Success!</h1><p>Your Access Token:</p><code>{token}</code><p>Copy this and save it.</p>"
    else:
        return f"Error: {response.text}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
