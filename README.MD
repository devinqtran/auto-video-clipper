# Auto Video Clipper

A Python utility that automatically clips trending YouTube videos, processes them with custom backgrounds, and uploads them as shorts to platforms like YouTube and TikTok.

## Features

- 🔍 Find trending videos from YouTube based on categories or search terms
- ✂️ Automatically clip segments from videos at optimal points
- 🖼️ Process clips with background videos for vertical format
- 📤 Upload processed clips to YouTube as shorts
- 🤖 Support for TikTok uploads (requires implementation)
- 🔄 Batch processing of multiple videos

## Requirements

- Python 3.6+
- FFmpeg (for video processing)
- yt-dlp (for downloading YouTube videos)
- Google API credentials (for YouTube API access)

## Installation

1. Clone this repository:
   ```
   git clone <your-repository-url>
   cd auto-video-clipper
   ```

2. Install required Python packages:
   ```
   pip install google-api-python-client google-auth-oauthlib google-auth-httplib2 moviepy requests
   ```

3. Install FFmpeg and yt-dlp:
   - **FFmpeg**: Follow instructions at [ffmpeg.org](https://ffmpeg.org/download.html)
   - **yt-dlp**: `pip install yt-dlp`

4. Set up YouTube API credentials:
   - Create a project in the [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the YouTube Data API v3
   - Create OAuth 2.0 credentials and download as `client_secrets.json`
   - Place `client_secrets.json` in the project directory

5. Create the required directories:
   ```
   mkdir -p output_videos temp background_videos
   ```

6. Add background videos:
   - Place vertical (9:16) background videos in the `background_videos` directory

## Configuration

Edit the `CONFIG` dictionary in `auto-video-clipper.py`:

```python
CONFIG = {
    "youtube_api_key": "YOUR_API_KEY",
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
```

## Usage

Run the script with different options:

```
# Get and process trending videos
python auto-video-clipper.py --trending --count 5

# Search for specific videos
python auto-video-clipper.py --search "funny cats" --count 3

# Process videos from a specific category
python auto-video-clipper.py --category 10 --count 5  # Music category

# Process and upload videos
python auto-video-clipper.py --trending --count 3 --upload
```

### Command-line Arguments

- `--search TEXT`: Search term for videos
- `--trending`: Use trending videos (default if no search term)
- `--category ID`: YouTube video category ID
- `--count N`: Number of videos to process (default: 5)
- `--upload`: Upload processed videos to platforms

## How It Works

1. The script searches for trending or specific videos on YouTube
2. It downloads the source videos using yt-dlp
3. From each video, it clips a segment of specified duration
4. The clip is overlaid on a background video to create a vertical format
5. If requested, the processed video is uploaded to YouTube as a short
6. The TikTok upload functionality is provided as a template for implementation

## YouTube Categories

Some commonly used YouTube category IDs:

- 1: Film & Animation
- 2: Autos & Vehicles
- 10: Music
- 15: Pets & Animals
- 17: Sports
- 20: Gaming
- 23: Comedy
- 24: Entertainment
- 25: News & Politics

## TikTok Upload Note

TikTok doesn't provide an official API for uploads. The current implementation is a placeholder. To implement TikTok uploads, you would need to:

1. Use browser automation (e.g., Selenium) 
2. Use a third-party service
3. Implement an unofficial API client

## License

[Your License Here]

## Disclaimer

This tool should be used responsibly and in accordance with YouTube and TikTok's terms of service. Always respect copyright and fair use guidelines when creating derivative content.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.