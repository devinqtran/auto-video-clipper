import os
import random
import json
import datetime
import argparse
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import subprocess
import requests
import time
from moviepy.video.io.VideoFileClip import VideoFileClip


# Configuration
CONFIG = {
    "youtube_api_key": "AIzaSyBlbPjOVITiwoWfL-S7CMri9KatU0aJr3g",
    "output_dir": "output_videos",
    "temp_dir": "temp",
    "background_videos_dir": "background_videos",
    "clip_duration": 30,  # in seconds
    "search_terms": ["trending", "viral", "popular"],
    "max_results": 10,
    "video_categories": ["10", "24", "23"],  # Music, Entertainment, Comedy
    "text_overlays": [
        "OMG!!", 
        "WATCH THIS!!", 
        "YOU WON'T BELIEVE!!",
        "TRENDING!!",
        "VIRAL!!"
    ],
    "youtube_credentials_file": "client_secrets.json",
    "youtube_token_file": "youtube_token.json",
    "tiktok_session_id": "YOUR_TIKTOK_SESSION_ID"  # For unofficial TikTok uploads
}

# Create necessary directories
for dir_name in [CONFIG["output_dir"], CONFIG["temp_dir"], CONFIG["background_videos_dir"]]:
    os.makedirs(dir_name, exist_ok=True)

def setup_youtube_api():
    """Set up YouTube API client."""
    youtube = build("youtube", "v3", developerKey=CONFIG["youtube_api_key"])
    return youtube

def get_trending_videos(youtube, max_results=10, region_code="US", category_id=None):
    """Get trending videos from YouTube."""
    videos = []
    
    # If category_id is provided, use it; otherwise, cycle through the configured categories
    categories = [category_id] if category_id else CONFIG["video_categories"]
    
    for cat_id in categories:
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            chart="mostPopular",
            regionCode=region_code,
            videoCategoryId=cat_id,
            maxResults=max_results // len(categories)
        )
        response = request.execute()
        videos.extend(response["items"])
    
    return videos

def search_videos(youtube, query, max_results=10, region_code="US"):
    """Search for videos on YouTube based on a query."""
    request = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        videoDefinition="high",
        maxResults=max_results,
        regionCode=region_code
    )
    response = request.execute()
    
    # Get full video details
    video_ids = [item["id"]["videoId"] for item in response["items"]]
    videos_request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id=",".join(video_ids)
    )
    return videos_request.execute()["items"]

def download_video(video_id, output_path):
    """Download a video using yt-dlp."""
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        subprocess.run([
            "yt-dlp", 
            "--format", "mp4", 
            "--output", output_path,
            video_url
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error downloading video {video_id}: {e}")
        return False

def get_video_duration(file_path):
    """Get the duration of a video in seconds using FFmpeg."""
    result = subprocess.run([
        "ffprobe", 
        "-v", "error", 
        "-show_entries", "format=duration", 
        "-of", "default=noprint_wrappers=1:nokey=1", 
        file_path
    ], capture_output=True, text=True)
    
    return float(result.stdout.strip())

def clip_video(input_path, output_path, start_time, duration):
    """Clip a segment from a video using FFmpeg."""
    try:
        subprocess.run([
            "ffmpeg",
            "-i", input_path,
            "-ss", str(start_time),
            "-t", str(duration),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-strict", "experimental",
            output_path
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error clipping video: {e}")
        return False

def get_random_background_video():
    """Get a random background video from the backgrounds directory."""
    bg_videos = [f for f in os.listdir(CONFIG["background_videos_dir"]) 
                 if f.endswith((".mp4", ".mov"))]
    
    if not bg_videos:
        return None
        
    return os.path.join(CONFIG["background_videos_dir"], random.choice(bg_videos))

def process_with_background(clip_path, output_path, background_path=None):
    """Process the clip with a background video."""
    if background_path is None:
        background_path = get_random_background_video()
        
    if background_path is None:
        print("No background videos found. Skipping background processing.")
        return False
        
    try:
        # Use FFmpeg to overlay the clip on the background
        subprocess.run([
            "ffmpeg",
            "-i", background_path,  # Background video
            "-i", clip_path,        # Main clip
            "-filter_complex", "[0:v]scale=1080:1920,setsar=1[bg];[1:v]scale=720:-1[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-map", "1:a",  # Use audio from the main clip
            "-shortest",
            output_path
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error processing with background: {e}")
        return False

def prepare_for_youtube(title, description, video_path):
    """Prepares the video metadata for YouTube upload."""
    tags = CONFIG["search_terms"] + ["short", "shorts", "trending", "viral"]
    
    metadata = {
        "snippet": {
            "title": title[:100],  # YouTube title limit
            "description": description[:5000],  # YouTube description limit
            "tags": tags,
            "categoryId": random.choice(CONFIG["video_categories"]),
            "defaultLanguage": "en"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }
    
    return metadata

def upload_to_youtube(video_path, metadata):
    """Upload a video to YouTube using the API."""
    # This requires OAuth authentication setup
    # Check if token exists and is valid
    creds = None
    token_file = CONFIG["youtube_token_file"]
    
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_info(
            json.load(open(token_file)), 
            ["https://www.googleapis.com/auth/youtube.upload"]
        )
    
    # If credentials don't exist or are invalid, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CONFIG["youtube_credentials_file"],
                ["https://www.googleapis.com/auth/youtube.upload"]
            )
            creds = flow.run_local_server(port=0)
        
        # Save credentials for future use
        with open(token_file, "w") as token:
            token.write(creds.to_json())
    
    # Build the YouTube service
    youtube = build("youtube", "v3", credentials=creds)
    
    # Prepare the media file for upload
    media = MediaFileUpload(video_path, resumable=True)
    
    # Create the request
    request = youtube.videos().insert(
        part=",".join(metadata.keys()),
        body=metadata,
        media_body=media
    )
    
    # Execute the request
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")
    
    print(f"Upload complete! Video ID: {response['id']}")
    return response["id"]

def upload_to_tiktok(video_path, description):
    """
    Example function to upload to TikTok.
    Note: TikTok doesn't have an official API for uploads.
    This would need to be implemented using unofficial methods or third-party services.
    """
    print("TikTok upload functionality would be implemented here.")
    # In a real implementation, you'd need to use browser automation
    # or a third-party service to handle TikTok uploads
    return "tiktok_video_id"

def main():
    """Main function that orchestrates the entire process."""
    parser = argparse.ArgumentParser(description="Automated Video Clipper and Uploader")
    parser.add_argument("--search", type=str, help="Search term for videos")
    parser.add_argument("--trending", action="store_true", help="Use trending videos")
    parser.add_argument("--category", type=str, help="Video category ID")
    parser.add_argument("--count", type=int, default=5, help="Number of videos to process")
    parser.add_argument("--upload", action="store_true", help="Upload videos to platforms")
    
    args = parser.parse_args()
    
    # Initialize YouTube API
    youtube = setup_youtube_api()
    
    # Get videos based on command line args
    if args.search:
        videos = search_videos(youtube, args.search, max_results=args.count)
    else:  # Default to trending
        videos = get_trending_videos(youtube, max_results=args.count, category_id=args.category)
    
    processed_videos = []
    
    # Process each video
    for video in videos:
        video_id = video["id"]
        video_title = video["snippet"]["title"]
        video_desc = video["snippet"].get("description", "")
        
        print(f"Processing: {video_title}")
        
        # Create temp filenames
        timestamp = int(time.time())
        original_file = os.path.join(CONFIG["temp_dir"], f"original_{video_id}_{timestamp}.mp4")
        clipped_file = os.path.join(CONFIG["temp_dir"], f"clipped_{video_id}_{timestamp}.mp4")
        final_file = os.path.join(CONFIG["output_dir"], f"final_{video_id}_{timestamp}.mp4")
        
        # Download the video
        if not download_video(video_id, original_file):
            print(f"Skipping {video_id} due to download error")
            continue
            
        # Get video duration to find a good clip point
        try:
            duration = get_video_duration(original_file)
            
            # Skip videos that are too short
            if duration < CONFIG["clip_duration"] + 5:
                print(f"Video {video_id} is too short ({duration}s), skipping")
                os.remove(original_file)
                continue
                
            # Find a random start point (avoiding the very beginning and end)
            max_start = max(0, duration - CONFIG["clip_duration"] - 5)
            start_time = random.uniform(5, max_start) if max_start > 5 else 0
            
            # Clip the video
            if not clip_video(original_file, clipped_file, start_time, CONFIG["clip_duration"]):
                print(f"Failed to clip video {video_id}")
                continue
                
            # Skip text overlay processing and use clipped file for background processing or final output
            
            # Apply background processing if background videos are available
            if os.listdir(CONFIG["background_videos_dir"]):
                if not process_with_background(clipped_file, final_file):
                    # If background processing fails, use the clipped file as final
                    os.rename(clipped_file, final_file)
            else:
                # No background videos, use clipped file as final
                os.rename(clipped_file, final_file)
                
            # Clean up temp files
            if os.path.exists(original_file):
                os.remove(original_file)
            
            # If clipped file still exists and isn't the final file (rename happened)
            if os.path.exists(clipped_file) and os.path.exists(final_file):
                os.remove(clipped_file)
                
            # Prepare upload metadata
            short_title = f"{video_title[:50]} #shorts"
            short_desc = f"{video_desc[:200]}\n\n#shorts #trending #viral"
            
            processed_videos.append({
                "original_id": video_id,
                "title": short_title,
                "description": short_desc,
                "file_path": final_file
            })
            
            print(f"Successfully processed: {short_title}")
            
        except Exception as e:
            print(f"Error processing {video_id}: {str(e)}")
            # Clean up any existing temp files
            for f in [original_file, clipped_file]:
                if os.path.exists(f):
                    os.remove(f)
    
    # Upload videos if requested
    if args.upload and processed_videos:
        print("\nUploading videos to platforms...")
        
        for video in processed_videos:
            # Prepare metadata for YouTube
            yt_metadata = prepare_for_youtube(video["title"], video["description"], video["file_path"])
            
            try:
                # Upload to YouTube
                yt_video_id = upload_to_youtube(video["file_path"], yt_metadata)
                print(f"Uploaded to YouTube: https://www.youtube.com/watch?v={yt_video_id}")
                
                # Upload to TikTok
                # This is a placeholder - actual implementation would depend on how you access TikTok
                tiktok_id = upload_to_tiktok(video["file_path"], video["description"])
                print(f"Uploaded to TikTok (ID: {tiktok_id})")
                
                # Wait between uploads to avoid rate limits
                time.sleep(10)
                
            except Exception as e:
                print(f"Error uploading {video['title']}: {str(e)}")
    
    print(f"\nProcessed {len(processed_videos)} videos successfully!")

if __name__ == "__main__":
    main()