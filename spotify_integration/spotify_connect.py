from flask import Flask, request, redirect
import requests
import time
from urllib.parse import urlencode
import random
import spotipy

CLIENT_ID = 'efe5dc5025aa447cadcd7fbeaab6550d'
CLIENT_SECRET = 'a51c4dfa608c4f62924a81d285954ad3'
REDIRECT_URI = 'http://localhost:8080/callback'
SCOPE = 'user-modify-playback-state'

# Will set later on in the application
access_token = 0
access_token_issued_at = 0
access_token_expires_in = 0

# For redirect request
TEMPORARY_REDIRECT_CODE = 302

# TODO: Receive the bpm from mediapipe
target_bpm = 100
seed_genres = 'pop'
PLAYLIST_ID = '6vI3xbpdPYYJmicjBieLcr'

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

def get_access_token(code):
    # ABOUT: Get the access token from Spotify
    global access_token_expires_in
    token_url = 'https://accounts.spotify.com/api/token'

    # Use the code we got from the previous request to get an access token
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    # Make the request; code 200 is success
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        # Save refresh token to file
        refresh_token = response.json()['refresh_token']
        with open('refresh_token.txt', 'w') as f:
            f.write(refresh_token)
            f.close()
        
        # Store how long it takes for access token to expire
        access_token_expires_in = response.json()['expires_in']
        
        # Return access token
        return response.json()['access_token']
    else:
        print(f"Failed to get access token: {response.json()}")
        return None
    
def get_refresh_token():
    global access_token_issued_at
    refresh_token = None

    # Get the refresh token from the file
    try:
        with open('refresh_token.txt', 'r') as f:
            refresh_token = f.read()
            f.close()
    except FileNotFoundError:
        print("Refresh token not found. Please authenticate again.")
        return None
    
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    response = requests.post('https://accounts.spotify.com/api/token', data=data)
    if response.status_code == 200:
        access_token_issued_at = time.time()
        return response.json()['access_token']
    else:
        print(f"Failed to refresh access token: {response.json()}")
        return None
    
@app.route('/play', methods=['POST', 'GET'])
def play():
    target_bpm = request.json.get("bpm")
    track_uri = get_song_from_playlist(target_bpm=target_bpm, 
                                      seed_genres=seed_genres)
    print(track_uri)
    return track_uri

def get_song_from_playlist(target_bpm, seed_genres):
    # ABOUT: Get a song from Spotify based on the target_bpm and seed_genres
    global access_token_expires_in, access_token_issued_at, access_token

    # Check if the access token has expired
    if (access_token == 0) or (access_token_issued_at == 0) or (time.time() > 
                                            access_token_issued_at + 
                                            access_token_expires_in):
        access_token = get_refresh_token()

    print("Access token: ", access_token)

    # Initialize Spotify client
    sp = spotipy.Spotify(auth=access_token)    

    # Get tracks from playlist
    tracks = sp.playlist_tracks(PLAYLIST_ID)['items']
    matched_tracks = []

    for track in tracks:
        # Get the audio features for the track
        audio_features = sp.audio_features(track['track']['id'])[0]
        tempo = audio_features['tempo']

        # If the tempo is within the target range, start playback
        if target_bpm - 15 <= tempo <= target_bpm + 15:
            matched_tracks.append(track)
        
        if len(matched_tracks) == 5:
            break
        
    print("Matched tracks: ", len(matched_tracks))
    # Choose a random track in matched_tracks to begin playback
    chosen_track_number = random.randint(0, len(matched_tracks) - 1)
    sp.start_playback(uris=[matched_tracks[chosen_track_number]['track']['uri']])
        
    return matched_tracks[chosen_track_number]['track']['uri']

'''
def get_song_from_spotify(target_bpm, seed_genres):
    # ABOUT: Get a song from Spotify based on the target_bpm and seed_genres
    global access_token_expires_in, access_token_issued_at, access_token
    
    # Check if the access token has expired
    if (access_token == 0) or (access_token_issued_at == 0) or (time.time() > 
                                            access_token_issued_at + 
                                            access_token_expires_in):
        access_token = get_refresh_token()

    print("Access token: ", access_token)
    headers = {'Authorization': f'Bearer {access_token}', 
               'Content-Type': 'application/json'}
    params = {'target_tempo': target_bpm, 'min_tempo': (target_bpm - 10), 
              'max_tempo': (target_bpm + 15), 'seed_genres': seed_genres, 
              'limit': 10}

    # Make the request
    response = requests.get(recommendation_url, headers=headers, 
                            params=params)
    recommendation = response.json()
    print(recommendation)
    return recommendation
'''

'''
def play_song_on_spotify(recommendation):
    # ABOUT: Play the song on Spotify
    global access_token_expires_in, access_token_issued_at, access_token
    playback_url = "https://api.spotify.com/v1/me/player/play"
    chosen_track_number = random.randint(0, len(recommendation['tracks']) - 1)
    
    # Check if the access token has expired
    if (access_token == 0) or (access_token_issued_at == 0) or (time.time() > 
                                            access_token_issued_at + 
                                            access_token_expires_in):
        access_token = get_refresh_token()

    print("Access token: ", access_token)

    headers = {'Authorization': f'Bearer {access_token}', 
               'Content-Type': 'application/json'}
    data = {'uris': [recommendation['tracks'][0]['uri']]}

    # Make API request to start playback
    playback_response = requests.put(playback_url, headers=headers, json=data)

    if playback_response.status_code == 204:
        print("Success!")
        # print(f"Playback started successfully. Playing "
        #       f"{recommendation['tracks'][0]['name']}, by" 
        #       f"{recommendation['artists'][0]['name']}.")
    else:
        print("Error starting playback:", playback_response.json())
'''
        
if __name__ == "__main__":
    app.run(debug=True, port=8080)