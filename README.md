# Media Downloader

A Streamlit-based web application for downloading videos and music from YouTube and Spotify.

## Features

### YouTube

- Download single videos or entire playlists
- View playlist information (total videos, duration)
- See duration at different playback speeds (1x, 1.25x, 1.5x, 1.75x, 2x)
- Select specific videos from playlists
- Multiple output formats:
  - **Video:** MP4 (1080p, 720p, 480p, 360p), WebM (1080p, 720p), Best Quality
  - **Audio:** MP3, AAC, WAV, FLAC, M4A

### Spotify

- Download single tracks, albums, or playlists
- View playlist/album information
- Select specific tracks to download
- Audio formats: MP3, M4A, FLAC, OPUS, OGG, WAV
- Configurable audio quality (up to 320kbps)

## Prerequisites

1. **Python 3.8+**
2. **FFmpeg** - Required for audio/video conversion

   **Windows:**

   ```bash
   # Using Chocolatey
   choco install ffmpeg

   # Or download from https://ffmpeg.org/download.html
   # Add to PATH
   ```

   **macOS:**

   ```bash
   brew install ffmpeg
   ```

   **Linux:**

   ```bash
   sudo apt install ffmpeg
   ```

## Installation

1. **Clone or navigate to the project directory:**

   ```bash
   cd "youtube downloader"
   ```

2. **Create a virtual environment (recommended):**

   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`.

## Usage

### YouTube Downloads

1. Go to the **YouTube** tab
2. Paste a YouTube URL:
   - Single video: `https://www.youtube.com/watch?v=VIDEO_ID`
   - Playlist: `https://www.youtube.com/playlist?list=PLAYLIST_ID`
3. Click **Fetch Info**
4. For playlists:
   - View total videos and duration at different speeds
   - Use "Select All" or choose specific videos
5. Choose format type (Video/Audio) and quality
6. Click **Download**
7. Save the file when prompted

### Spotify Downloads

1. Go to the **Spotify** tab
2. Paste a Spotify URL:
   - Track: `https://open.spotify.com/track/TRACK_ID`
   - Playlist: `https://open.spotify.com/playlist/PLAYLIST_ID`
   - Album: `https://open.spotify.com/album/ALBUM_ID`
3. Click **Fetch Info**
4. For playlists/albums:
   - Select tracks to download
5. Choose audio format and quality
6. Click **Download**
7. Save the file(s) when prompted

## Project Structure

```
youtube downloader/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── utils/
    ├── __init__.py
    ├── youtube_handler.py # YouTube download logic
    └── spotify_handler.py # Spotify download logic
```

## Output Formats

### Video Formats

| Format     | Description               |
| ---------- | ------------------------- |
| MP4 1080p  | Full HD quality           |
| MP4 720p   | HD quality                |
| MP4 480p   | Standard definition       |
| MP4 360p   | Low quality               |
| WebM 1080p | Full HD (open format)     |
| WebM 720p  | HD (open format)          |
| Best       | Highest available quality |

### Audio Formats

| Format | Description              |
| ------ | ------------------------ |
| MP3    | Most compatible, 192kbps |
| AAC    | Good quality, 192kbps    |
| WAV    | Lossless, large files    |
| FLAC   | Lossless, compressed     |
| M4A    | Apple format, 192kbps    |

## Troubleshooting

### FFmpeg not found

Make sure FFmpeg is installed and added to your system PATH.

### Spotify downloads not working

Ensure `spotdl` is properly installed:

```bash
pip install spotdl --upgrade
```

### Slow downloads

- Video downloads depend on your internet connection
- Large playlists may take considerable time
- Consider selecting fewer videos/tracks at once

### Download fails

- Check if the video/track is available in your region
- Some content may have download restrictions
- Try a different format or quality

## Legal Notice

This tool is for personal use only. Please respect copyright laws and only download content you have the right to access. Do not use this tool to download copyrighted material without permission.

## Dependencies

- `streamlit` - Web interface
- `yt-dlp` - YouTube downloading
- `spotdl` - Spotify downloading
- `spotipy` - Spotify API
- `ffmpeg-python` - Audio/video processing
