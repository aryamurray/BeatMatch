from flask import Flask, request, redirect
import requests
from urllib.parse import urlencode

CLIENT_ID = 'efe5dc5025aa447cadcd7fbeaab6550d'
CLIENT_SECRET = 'a51c4dfa608c4f62924a81d285954ad3'
REDIRECT_URI = 'http://localhost:8080/callback'
SCOPE = 'user-modify-playback-state'

# Will set later on in the application
access_token = None
refresh_token = None
access_token_expires = 0

# For redirect request
TEMPORARY_REDIRECT_CODE = 302

# TODO: Receive the bpm from mediapipe
target_bpm = 120
seed_genres = 'pop'

app = Flask(__name__)

@app.route('/')
def get_auth_url():
    # ABOUT: Build authorization URL to direct user to authenticate
    auth_url = 'https://accounts.spotify.com/authorize?' + urlencode({
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'scope': SCOPE,
        'redirect_uri': REDIRECT_URI
    })
    return redirect(auth_url, code=TEMPORARY_REDIRECT_CODE)

@app.route('/callback')
def callback():
    # ABOUT: Get the authorization code from Spotify
    # Declaring that we're using the global variable access_token
    global access_token
    code = request.args.get('code')
    print("Code:", code)
    if code:
        access_token = get_access_token(code=code)
        print("Access token:", access_token)
        return redirect('/play', code=TEMPORARY_REDIRECT_CODE)
    else:
        return 'Error retrieving authorization code. Please try again.'

@app.route('/play')
def play():
    track_uri = get_song_from_spotify(target_bpm=target_bpm, 
                                      seed_genres=seed_genres)
    print(track_uri)
    return track_uri
    # play_song_on_spotify(track_uri)

def get_access_token(refresh_token=None, code=None):
    # ABOUT: Get the access token from Spotify
    token_url = 'https://accounts.spotify.com/api/token'

    # Use the code we got from the previous request to get an access token
    # If there is no code, we're refreshing the token
    if code:
        payload = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
    elif refresh_token:
        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

    # Make the request; code 200 is success
    response = requests.post(token_url, data=payload)
    if response.status_code == 200:
        refresh_token = response.json()['refresh_token']
        with open('refresh_token.txt', 'w') as f:
            f.write(refresh_token)
            f.close()
        return response.json()['access_token']
    else:
        print(f"Failed to get access token: {response.json()}")
        return None

def get_song_from_spotify(target_bpm, seed_genres):
    # ABOUT: Get a song from Spotify based on the target_bpm and seed_genres
    print("Access token: ", access_token)
    recommendation_url = 'https://api.spotify.com/v1/recommendations'
    headers = {'Authorization': f'Bearer {access_token}', 
               'Content-Type': 'application/json'}
    params = {'target_tempo': target_bpm, 'seed_genres': seed_genres, 
              'limit': 1}

    # Make the request
    response = requests.get(recommendation_url, headers=headers, 
                            params=params)
    recommendation = response.json()
    print(recommendation)
    return recommendation

def play_song_on_spotify(recommendation):
    # ABOUT: Play the song on Spotify
    playback_url = "https://api.spotify.com/v1/me/player/play"
    headers = {'Authorization': f'Bearer {access_token}', 
               'Content-Type': 'application/json'}
    data = {'uris': recommendation['tracks'][0]['uri']}

    # Make API request to start playback
    playback_response = requests.put(playback_url, headers=headers, json=data)

    if playback_response.status_code == 204:
        print(f"Playback started successfully. Playing "
              f"{recommendation['tracks'][0]['name']}, by" 
              f"{recommendation['artists'][0]['name']}.")
    else:
        print("Error starting playback:", playback_response.json())

if __name__ == "__main__":
    app.run(debug=True, port=8080)