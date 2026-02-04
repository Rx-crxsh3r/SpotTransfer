import os
import requests
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)




def get_spotify_access_token(client_id, client_secret):
    logger.debug("Requesting Spotify access token")
    logger.debug(f"Client ID present: {bool(client_id)}")
    logger.debug(f"Client secret present: {bool(client_secret)}")
    
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    response = requests.post(url, headers=headers, data=data)
    logger.debug(f"Spotify auth response status: {response.status_code}")
    
    if response.status_code != 200:
        logger.error(f"Failed to get Spotify access token: {response.json()}")
        raise Exception(f"Failed to get access token: {response.json()}")
    
    logger.info("Successfully obtained Spotify access token")
    return response.json()["access_token"]


def extract_playlist_id(playlist_url):
    logger.debug(f"Extracting playlist ID from URL: {playlist_url}")
    try:
        playlist_id = playlist_url.split("/playlist/")[1].split("?")[0]
        logger.debug(f"Extracted playlist ID: {playlist_id}")
        return playlist_id
    except Exception as e:
        logger.error(f"Failed to extract playlist ID from URL: {playlist_url}")
        raise

def get_all_tracks(link, market):
    logger.info(f"Fetching tracks from Spotify playlist for market: {market}")
    
    playlist_id = extract_playlist_id(link)
    
    # Check for bearer token first (temporary workaround)
    bearer_token = os.getenv('SPOTIFY_BEARER_TOKEN')
    if bearer_token:
        logger.warning("Using temporary SPOTIFY_BEARER_TOKEN (will expire soon!)")
        access_token = bearer_token
    else:
        client_id = os.getenv('SPOTIPY_CLIENT_ID')
        client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            logger.error("Spotify credentials not found in environment variables")
            raise Exception("SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET must be set (or use SPOTIFY_BEARER_TOKEN temporarily)")
        
        access_token = get_spotify_access_token(client_id, client_secret)
    
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?market={market}&limit=100"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    all_tracks = []
    page_count = 0
    
    while url:
        page_count += 1
        logger.debug(f"Fetching page {page_count} of tracks")
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch tracks. Status: {response.status_code}, Response: {response.text}")
            raise Exception(f"Failed to fetch tracks: {response.status_code}")
        
        data = response.json()
        logger.debug(f"Got {len(data.get('items', []))} items in page {page_count}")
        
        for item in data["items"]:
            track = item["track"]
            if not track or track.get("is_local") or track.get("restrictions"):
                logger.debug(f"Skipping track: local={track.get('is_local') if track else 'N/A'}, has_restrictions={bool(track.get('restrictions')) if track else 'N/A'}")
                continue
            all_tracks.append({
                "name": track["name"],
                "artists": [artist["name"] for artist in track["artists"]],
                "album": track["album"]["name"],
            })
        url = data.get("next")
        if url == 'null':
            break
    
    logger.info(f"Successfully fetched {len(all_tracks)} tracks from Spotify playlist")
    return all_tracks

def get_playlist_name(link):
    logger.debug("Fetching playlist name from Spotify")
    
    playlist_id = extract_playlist_id(link)
    
    # Check for bearer token first (temporary workaround)
    bearer_token = os.getenv('SPOTIFY_BEARER_TOKEN')
    if bearer_token:
        logger.warning("Using temporary SPOTIFY_BEARER_TOKEN (will expire soon!)")
        access_token = bearer_token
    else:
        client_id = os.getenv('SPOTIPY_CLIENT_ID')
        client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
        access_token = get_spotify_access_token(client_id, client_secret)
    
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to fetch playlist name. Status: {response.status_code}, Response: {response.text}")
        raise Exception(f"Failed to fetch playlist name: {response.status_code}")
    
    data = response.json()
    playlist_name = data["name"]
    logger.info(f"Playlist name: {playlist_name}")
    return playlist_name
    
    
    


