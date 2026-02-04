from ytmusicapi import YTMusic
import ytmusicapi
from spotify import get_all_tracks, get_playlist_name
import logging

logger = logging.getLogger(__name__)


def parse_headers(headers_text):
    """
    Convert headers from plain text format to proper HTTP header format.
    Supports both formats:
    - Standard format: "header: value"
    - Plain format: "header\\nvalue\\nheader2\\nvalue2"
    """
    logger.debug("Parsing YouTube Music headers")
    logger.debug(f"Headers text length: {len(headers_text) if headers_text else 0}")
    
    if not headers_text or not headers_text.strip():
        logger.error("Headers text is empty")
        raise Exception("Headers cannot be empty")
    
    lines = [line.strip() for line in headers_text.strip().split('\n') if line.strip()]
    logger.debug(f"Split headers into {len(lines)} lines")
    
    # Check if headers are already in correct format
    first_line = lines[0] if lines else ""
    colon_pos = first_line.find(': ')
    
    if colon_pos > 0 and colon_pos < 50:
        logger.debug("Headers already in correct format")
        return headers_text
    
    # Filter out the "Decoded:" section - skip lines that are part of decoded content
    cleaned_lines = []
    skip_mode = False
    
    for line in lines:
        # Start skipping when we hit "Decoded:"
        if line == 'Decoded:':
            skip_mode = True
            continue
        
        # Skip lines that look like decoded protobuf content
        if skip_mode:
            # These are characteristics of the decoded section
            if (line.startswith('message ') or 
                line.startswith('//') or 
                line.startswith('repeated ') or
                line == '}' or
                line.startswith('int32 ') or
                '{' in line):
                continue
            else:
                # Looks like a real header again, stop skipping
                skip_mode = False
        
        if not skip_mode:
            cleaned_lines.append(line)
    
    lines = cleaned_lines
    logger.debug(f"After cleaning, have {len(lines)} lines")
    
    if len(lines) % 2 != 0:
        logger.error(f"Invalid headers format: {len(lines)} lines (should be even)")
        logger.error(f"Last line: '{lines[-1] if lines else 'none'}'")
        raise Exception(f"Invalid headers format. Each header name must have a corresponding value. Got {len(lines)} lines (should be even). Last line: '{lines[-1] if lines else 'none'}'")
    
    formatted_headers = []
    for i in range(0, len(lines), 2):
        header_name = lines[i]
        header_value = lines[i + 1]
        formatted_line = f"{header_name}: {header_value}"
        formatted_headers.append(formatted_line)
    
    logger.info(f"Successfully formatted {len(formatted_headers)} headers")
    return '\n'.join(formatted_headers)


def get_video_ids(ytmusic,tracks):
    logger.info(f"Searching for {len(tracks)} tracks on YouTube Music")
    video_ids = []
    missed_tracks = {
        "count": 0,
        "tracks": []
    }
    
    for idx, track in enumerate(tracks, 1):
        try:
            search_string = f"{track['name']} {track['artists'][0]}"
            logger.debug(f"[{idx}/{len(tracks)}] Searching: {search_string}")
            
            search_results = ytmusic.search(search_string, filter="songs")
            if not search_results:
                logger.warning(f"No results for: {search_string}")
                missed_tracks["count"] += 1
                missed_tracks["tracks"].append(f"{track['name']} {track['artists'][0]}")
                continue
                
            video_id = search_results[0]["videoId"]
            video_ids.append(video_id)
            logger.debug(f"Found video ID: {video_id}")
        except Exception as e:
            logger.warning(f"Failed to find track: {track['name']} {track['artists'][0]} - Error: {str(e)}")
            missed_tracks["count"] += 1
            missed_tracks["tracks"].append(f"{track['name']} {track['artists'][0]}")
    
    logger.info(f"Found {len(video_ids)}/{len(tracks)} songs on YouTube Music")
    logger.info(f"Missed {missed_tracks['count']} tracks")
    
    if len(video_ids) == 0:
        logger.error("No songs found on YouTube Music")
        raise Exception("No songs found on YouTube Music")
    return video_ids, missed_tracks


def create_ytm_playlist(playlist_link, headers):
    logger.info(f"Starting YouTube Music playlist creation for: {playlist_link}")
    
    try:
        # Parse and format headers
        logger.debug("Parsing and formatting headers")
        formatted_headers = parse_headers(headers)
        
        logger.debug("Setting up YouTube Music API")
        ytmusicapi.setup(filepath="header_auth.json", headers_raw=formatted_headers)
        logger.info("YouTube Music API setup successful")
    except Exception as e:
        logger.error(f"Failed to setup YouTube Music API: {str(e)}", exc_info=True)
        raise Exception(f"Failed to setup YouTube Music API: {str(e)}")
    
    try:
        ytmusic = YTMusic("header_auth.json")
        logger.debug("YouTube Music client initialized")
        
        tracks = get_all_tracks(playlist_link, "IN")
        name = get_playlist_name(playlist_link)
        
        logger.info(f"Processing playlist '{name}' with {len(tracks)} tracks")
        
        video_ids, missed_tracks = get_video_ids(ytmusic, tracks)
        
        logger.info(f"Creating YouTube Music playlist: {name} with {len(video_ids)} songs")
        ytmusic.create_playlist(name, "", "PRIVATE", video_ids)
        logger.info("YouTube Music playlist created successfully!")
        
        return missed_tracks
    except Exception as e:
        logger.error(f"Error during playlist creation: {str(e)}", exc_info=True)
        raise

