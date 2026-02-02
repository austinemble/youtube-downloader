"""
YouTube Handler - Manages YouTube video and playlist operations
"""
import yt_dlp
import os
import tempfile
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import timedelta


@dataclass
class VideoInfo:
    """Data class for video information"""
    id: str
    title: str
    duration: int  # in seconds
    thumbnail: str
    url: str
    uploader: str
    view_count: int
    upload_date: str


@dataclass
class PlaylistInfo:
    """Data class for playlist information"""
    id: str
    title: str
    uploader: str
    video_count: int
    videos: List[VideoInfo]
    total_duration: int  # in seconds


class YouTubeHandler:
    """Handles YouTube video and playlist operations"""
    
    # Available formats for download
    AUDIO_FORMATS = {
        'mp3': {'format': 'bestaudio/best', 'postprocessor': 'mp3', 'quality': '192'},
        'aac': {'format': 'bestaudio/best', 'postprocessor': 'aac', 'quality': '192'},
        'wav': {'format': 'bestaudio/best', 'postprocessor': 'wav', 'quality': None},
        'flac': {'format': 'bestaudio/best', 'postprocessor': 'flac', 'quality': None},
        'm4a': {'format': 'bestaudio/best', 'postprocessor': 'm4a', 'quality': '192'},
    }
    
    VIDEO_FORMATS = {
        'mp4_1080p': {'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best', 'ext': 'mp4'},
        'mp4_720p': {'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best', 'ext': 'mp4'},
        'mp4_480p': {'format': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best', 'ext': 'mp4'},
        'mp4_360p': {'format': 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best', 'ext': 'mp4'},
        'webm_1080p': {'format': 'bestvideo[height<=1080][ext=webm]+bestaudio[ext=webm]/best[height<=1080][ext=webm]/best', 'ext': 'webm'},
        'webm_720p': {'format': 'bestvideo[height<=720][ext=webm]+bestaudio[ext=webm]/best[height<=720][ext=webm]/best', 'ext': 'webm'},
        'best': {'format': 'bestvideo+bestaudio/best', 'ext': 'mp4'},
    }
    
    PLAYBACK_SPEEDS = [1.0, 1.25, 1.5, 1.75, 2.0]
    
    def __init__(self):
        self.ydl_opts_info = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration from seconds to human readable string"""
        if seconds is None or seconds == 0:
            return "Unknown"
        td = timedelta(seconds=seconds)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        if td.days > 0:
            return f"{td.days}d {hours}h {minutes}m {secs}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    @staticmethod
    def is_playlist(url: str) -> bool:
        """Check if URL is a playlist"""
        return 'list=' in url
    
    @staticmethod
    def is_youtube_url(url: str) -> bool:
        """Check if URL is a valid YouTube URL"""
        youtube_patterns = [
            'youtube.com/watch',
            'youtube.com/playlist',
            'youtu.be/',
            'youtube.com/shorts/',
        ]
        return any(pattern in url for pattern in youtube_patterns)
    
    def get_video_info(self, url: str) -> Optional[VideoInfo]:
        """Get information about a single video"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts_info) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return VideoInfo(
                    id=info.get('id', ''),
                    title=info.get('title', 'Unknown'),
                    duration=info.get('duration', 0) or 0,
                    thumbnail=info.get('thumbnail', ''),
                    url=url,
                    uploader=info.get('uploader', 'Unknown'),
                    view_count=info.get('view_count', 0) or 0,
                    upload_date=info.get('upload_date', 'Unknown'),
                )
        except Exception as e:
            raise Exception(f"Error fetching video info: {str(e)}")
    
    def get_playlist_info(self, url: str, progress_callback=None) -> Optional[PlaylistInfo]:
        """Get information about a playlist"""
        try:
            opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': 'in_playlist',
            }
            
            # First, get basic playlist info
            with yt_dlp.YoutubeDL(opts) as ydl:
                playlist_info = ydl.extract_info(url, download=False)
            
            if 'entries' not in playlist_info:
                raise Exception("No entries found in playlist")
            
            videos = []
            total_duration = 0
            entries = list(playlist_info.get('entries', []))
            total_videos = len(entries)
            
            # Get detailed info for each video
            for idx, entry in enumerate(entries):
                if entry is None:
                    continue
                    
                if progress_callback:
                    progress_callback(idx + 1, total_videos)
                
                video_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                
                try:
                    # Try to get duration from flat extraction first
                    duration = entry.get('duration', 0) or 0
                    
                    video = VideoInfo(
                        id=entry.get('id', ''),
                        title=entry.get('title', 'Unknown'),
                        duration=duration,
                        thumbnail=entry.get('thumbnail', '') or entry.get('thumbnails', [{}])[0].get('url', '') if entry.get('thumbnails') else '',
                        url=video_url,
                        uploader=entry.get('uploader', playlist_info.get('uploader', 'Unknown')),
                        view_count=entry.get('view_count', 0) or 0,
                        upload_date=entry.get('upload_date', 'Unknown'),
                    )
                    videos.append(video)
                    total_duration += duration
                except Exception:
                    continue
            
            return PlaylistInfo(
                id=playlist_info.get('id', ''),
                title=playlist_info.get('title', 'Unknown Playlist'),
                uploader=playlist_info.get('uploader', 'Unknown'),
                video_count=len(videos),
                videos=videos,
                total_duration=total_duration,
            )
        except Exception as e:
            raise Exception(f"Error fetching playlist info: {str(e)}")
    
    def get_duration_at_speeds(self, total_seconds: int) -> Dict[float, str]:
        """Calculate playlist duration at different playback speeds"""
        durations = {}
        for speed in self.PLAYBACK_SPEEDS:
            adjusted_seconds = int(total_seconds / speed)
            durations[speed] = self.format_duration(adjusted_seconds)
        return durations
    
    def download_video(
        self,
        url: str,
        output_format: str,
        output_dir: str = None,
        progress_callback=None
    ) -> Tuple[str, str]:
        """
        Download a video in the specified format
        Returns: (file_path, filename)
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        
        is_audio = output_format in self.AUDIO_FORMATS
        
        if is_audio:
            format_config = self.AUDIO_FORMATS[output_format]
            ydl_opts = {
                'format': format_config['format'],
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': format_config['postprocessor'],
                }],
                'quiet': True,
                'no_warnings': True,
            }
            if format_config['quality']:
                ydl_opts['postprocessors'][0]['preferredquality'] = format_config['quality']
        else:
            format_config = self.VIDEO_FORMATS.get(output_format, self.VIDEO_FORMATS['best'])
            ydl_opts = {
                'format': format_config['format'],
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'merge_output_format': format_config['ext'],
                'quiet': True,
                'no_warnings': True,
            }
        
        if progress_callback:
            def progress_hook(d):
                if d['status'] == 'downloading':
                    percent = d.get('_percent_str', '0%').strip()
                    progress_callback(percent)
                elif d['status'] == 'finished':
                    progress_callback('100%')
            ydl_opts['progress_hooks'] = [progress_hook]
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Find the downloaded file
                if is_audio:
                    filename = f"{info['title']}.{output_format}"
                else:
                    filename = f"{info['title']}.{format_config['ext']}"
                
                # Clean filename of invalid characters
                filename = self._sanitize_filename(filename)
                filepath = os.path.join(output_dir, filename)
                
                # Find actual file (yt-dlp may have sanitized differently)
                if not os.path.exists(filepath):
                    for f in os.listdir(output_dir):
                        if f.endswith(f".{output_format}" if is_audio else f".{format_config['ext']}"):
                            filepath = os.path.join(output_dir, f)
                            filename = f
                            break
                
                return filepath, filename
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Remove invalid characters from filename"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename
    
    def download_multiple(
        self,
        videos: List[VideoInfo],
        output_format: str,
        output_dir: str = None,
        progress_callback=None
    ) -> List[Tuple[str, str]]:
        """
        Download multiple videos
        Returns: List of (file_path, filename) tuples
        """
        results = []
        total = len(videos)
        
        for idx, video in enumerate(videos):
            if progress_callback:
                progress_callback(idx + 1, total, video.title)
            
            try:
                filepath, filename = self.download_video(
                    video.url,
                    output_format,
                    output_dir
                )
                results.append((filepath, filename))
            except Exception as e:
                results.append((None, f"Error: {str(e)}"))
        
        return results
