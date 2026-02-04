from flask import Flask, request
from flask_cors import CORS
from ytm import create_ytm_playlist
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()
logger.debug("Environment variables loaded")

app = Flask(__name__)
frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
logger.info(f"Configured CORS for frontend URL: {frontend_url}")

CORS(app, resources={
    r"/*" : {
        "origins": [frontend_url],
        "methods" : ["POST", "GET"],
        
    }
})


@app.route('/create', methods=['POST'])
def create_playlist():
    logger.info("Received POST request to /create endpoint")
    
    try:
        data = request.get_json()
        logger.debug(f"Request data keys: {list(data.keys()) if data else 'None'}")
        
        playlist_link = data.get('playlist_link')
        auth_headers = data.get('auth_headers')
        
        logger.info(f"Processing playlist: {playlist_link}")
        logger.debug(f"Auth headers present: {bool(auth_headers)}")
        logger.debug(f"Auth headers length: {len(auth_headers) if auth_headers else 0}")
        
        missed_tracks = create_ytm_playlist(playlist_link, auth_headers)
        logger.info(f"Playlist created successfully! Missed {missed_tracks.get('count', 0)} tracks")
        
        return {"message": "Playlist created successfully!",
                "missed_tracks": missed_tracks
        }, 200
    except Exception as e:
        logger.error(f"Error creating playlist: {str(e)}", exc_info=True)
        return {"message": str(e)}, 500
    
@app.route('/', methods=['GET'])
def home():
    # Render health check endpoint
    logger.debug("Health check endpoint called")
    return {"message": "Server Online"}, 200

if __name__ == '__main__':
    logger.info("Starting Flask application on port 8080")
    app.run(port=8080, debug=True)