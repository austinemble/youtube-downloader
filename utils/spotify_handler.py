"""
Spotify Handler - Manages Spotify track and playlist operations
Uses spotdl for downloading and spotipy for API access
"""
import os
import tempfile
import subprocess
import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import timedelta


@dataclass
class SpotifyTrack:
    """Data class for Spotify track information"""
    id: str
    name: str
    artists: List[str]
    album: str
    duration_ms: int
    preview_url: Optional[str]
    external_url: str
    image_url: str


@dataclass
class SpotifyPlaylist:
    """Data class for Spotify playlist information"""
    id: str
    name: str
    owner: str
    description: str
    total_tracks: int
    tracks: List[SpotifyTrack]
    total_duration_ms: int
    image_url: str


class SpotifyHandler:
    """Handles Spotify track and playlist operations using spotdl"""
    
    AUDIO_FORMATS = ['mp3', 'm4a', 'flac', 'opus', 'ogg', 'wav']
    AUDIO_QUALITY = ['8k', '16k', '24k', '32k', '48k', '64k', '96k', '128k', '160k', '192k', '256k', '320k']
    PLAYBACK_SPEEDS = [1.0, 1.25, 1.5, 1.75, 2.0]
    
    def __init__(self):
        self._check_spotdl_installed()
    
    def _check_spotdl_installed(self):
        """Check if spotdl is installed"""
        try:
            result = subprocess.run(
                ['spotdl', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise Exception("spotdl is not properly installed")
        except FileNotFoundError:
            raise Exception("spotdl is not installed. Please install it with: pip install spotdl")
        except subprocess.TimeoutExpired:
            raise Exception("spotdl check timed out")
    
    @staticmethod
    def format_duration(ms: int) -> str:
        """Format duration from milliseconds to human readable string"""
        if ms is None or ms == 0:
            return "Unknown"
        seconds = ms // 1000
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
    def is_spotify_url(url: str) -> bool:
        """Check if URL is a valid Spotify URL"""
        spotify_patterns = [
            'open.spotify.com/track/',
            'open.spotify.com/album/',
            'open.spotify.com/playlist/',
            'open.spotify.com/artist/',
            'spotify.com/track/',
            'spotify.com/album/',
            'spotify.com/playlist/',
        ]
        return any(pattern in url for pattern in spotify_patterns)
    
    @staticmethod
    def get_spotify_type(url: str) -> str:
        """Get the type of Spotify content from URL"""
        if '/track/' in url:
            return 'track'
        elif '/album/' in url:
            return 'album'
        elif '/playlist/' in url:
            return 'playlist'
        elif '/artist/' in url:
            return 'artist'
        return 'unknown'
    
    def get_track_info(self, url: str) -> Optional[Dict]:
        """Get information about a Spotify track/playlist/album using spotdl"""
        try:
            result = subprocess.run(
                ['spotdl', 'save', url, '--save-file', 'temp_info.spotdl'],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=tempfile.gettempdir()
            )
            
            info_file = os.path.join(tempfile.gettempdir(), 'temp_info.spotdl')
            
            if os.path.exists(info_file):
                with open(info_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                os.remove(info_file)
                return data
            else:
                # Parse from stdout if file wasn't created
                return self._parse_spotdl_output(result.stdout, url)
                
        except subprocess.TimeoutExpired:
            raise Exception("Request timed out while fetching Spotify info")
        except Exception as e:
            raise Exception(f"Error fetching Spotify info: {str(e)}")
    
    def _parse_spotdl_output(self, output: str, url: str) -> Dict:
        """Parse spotdl output for basic info"""
        # Basic fallback parsing
        return {
            'url': url,
            'type': self.get_spotify_type(url),
            'parsed': True
        }
    
    def get_playlist_info_detailed(self, url: str, progress_callback=None) -> Optional[SpotifyPlaylist]:
        """Get detailed playlist information"""
        try:
            # Use spotdl to get track list
            temp_dir = tempfile.mkdtemp()
            save_file = os.path.join(temp_dir, 'playlist_info.spotdl')
            
            result = subprocess.run(
                ['spotdl', 'save', url, '--save-file', save_file],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            tracks = []
            total_duration = 0
            
            if os.path.exists(save_file):
                with open(save_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for idx, track_data in enumerate(data):
                    if progress_callback:
                        progress_callback(idx + 1, len(data))
                    
                    duration = track_data.get('duration', 0) * 1000  # Convert to ms
                    
                    track = SpotifyTrack(
                        id=track_data.get('song_id', ''),
                        name=track_data.get('name', 'Unknown'),
                        artists=track_data.get('artists', ['Unknown']),
                        album=track_data.get('album_name', 'Unknown'),
                        duration_ms=duration,
                        preview_url=track_data.get('download_url'),
                        external_url=track_data.get('url', url),
                        image_url=track_data.get('cover_url', '')
                    )
                    tracks.append(track)
                    total_duration += duration
                
                os.remove(save_file)
            
            return SpotifyPlaylist(
                id=self._extract_id_from_url(url),
                name=self._extract_name_from_url(url) or "Spotify Playlist",
                owner="Spotify User",
                description="",
                total_tracks=len(tracks),
                tracks=tracks,
                total_duration_ms=total_duration,
                image_url=""
            )
            
        except subprocess.TimeoutExpired:
            raise Exception("Request timed out while fetching playlist info")
        except Exception as e:
            raise Exception(f"Error fetching playlist info: {str(e)}")
    
    def _extract_id_from_url(self, url: str) -> str:
        """Extract Spotify ID from URL"""
        match = re.search(r'/(track|album|playlist|artist)/([a-zA-Z0-9]+)', url)
        if match:
            return match.group(2)
        return ""
    
    def _extract_name_from_url(self, url: str) -> str:
        """Extract name hint from URL"""
        return None
    
    def get_duration_at_speeds(self, total_ms: int) -> Dict[float, str]:
        """Calculate duration at different playback speeds"""
        durations = {}
        for speed in self.PLAYBACK_SPEEDS:
            adjusted_ms = int(total_ms / speed)
            durations[speed] = self.format_duration(adjusted_ms)
        return durations
    
    def download_track(
        self,
        url: str,
        output_format: str = 'mp3',
        audio_quality: str = '320k',
        output_dir: str = None,
        progress_callback=None
    ) -> Tuple[str, str]:
        """
        Download a Spotify track
        Returns: (file_path, filename)
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        
        if output_format not in self.AUDIO_FORMATS:
            output_format = 'mp3'
        
        try:
            cmd = [
                'spotdl', 'download', url,
                '--output', output_dir,
                '--format', output_format,
                '--bitrate', audio_quality,
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if progress_callback:
                progress_callback('100%')
            
            # Find the downloaded file
            for f in os.listdir(output_dir):
                if f.endswith(f'.{output_format}'):
                    filepath = os.path.join(output_dir, f)
                    return filepath, f
            
            # If no file found, check for any audio file
            for f in os.listdir(output_dir):
                for ext in self.AUDIO_FORMATS:
                    if f.endswith(f'.{ext}'):
                        filepath = os.path.join(output_dir, f)
                        return filepath, f
            
            raise Exception("Download completed but file not found")
            
        except subprocess.TimeoutExpired:
            raise Exception("Download timed out")
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")
    
    def download_multiple(
        self,
        tracks: List[SpotifyTrack],
        output_format: str = 'mp3',
        audio_quality: str = '320k',
        output_dir: str = None,
        progress_callback=None
    ) -> List[Tuple[str, str]]:
        """
        Download multiple Spotify tracks
        Returns: List of (file_path, filename) tuples
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        
        results = []
        total = len(tracks)
        
        for idx, track in enumerate(tracks):
            if progress_callback:
                progress_callback(idx + 1, total, track.name)
            
            try:
                filepath, filename = self.download_track(
                    track.external_url,
                    output_format,
                    audio_quality,
                    output_dir
                )
                results.append((filepath, filename))
            except Exception as e:
                results.append((None, f"Error: {str(e)}"))
        
        return results
    
    def download_playlist(
        self,
        url: str,
        output_format: str = 'mp3',
        audio_quality: str = '320k',
        output_dir: str = None,
        progress_callback=None
    ) -> List[Tuple[str, str]]:
        """
        Download entire Spotify playlist at once (more efficient)
        Returns: List of (file_path, filename) tuples
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        
        try:
            cmd = [
                'spotdl', 'download', url,
                '--output', output_dir,
                '--format', output_format,
                '--bitrate', audio_quality,
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes for large playlists
            )
            
            if progress_callback:
                progress_callback('100%')
            
            # Collect all downloaded files
            results = []
            for f in os.listdir(output_dir):
                if f.endswith(f'.{output_format}'):
                    filepath = os.path.join(output_dir, f)
                    results.append((filepath, f))
            
            return results
            
        except subprocess.TimeoutExpired:
            raise Exception("Download timed out")
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")
