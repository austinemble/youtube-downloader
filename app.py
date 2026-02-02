"""
YouTube & Spotify Downloader - Streamlit Application
A modern web interface for downloading videos and music from YouTube and Spotify
"""
import streamlit as st
import os
import tempfile
import zipfile
from io import BytesIO
from utils.youtube_handler import YouTubeHandler, VideoInfo, PlaylistInfo
from utils.spotify_handler import SpotifyHandler, SpotifyTrack, SpotifyPlaylist

# Page configuration
st.set_page_config(
    page_title="Media Downloader",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #ff0000, #1DB954);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
    .video-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .duration-table {
        font-size: 0.9rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #e7f3ff;
        border: 1px solid #b6d4fe;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'youtube_handler' not in st.session_state:
        st.session_state.youtube_handler = YouTubeHandler()
    if 'spotify_handler' not in st.session_state:
        try:
            st.session_state.spotify_handler = SpotifyHandler()
            st.session_state.spotify_available = True
        except Exception as e:
            st.session_state.spotify_handler = None
            st.session_state.spotify_available = False
            st.session_state.spotify_error = str(e)
    if 'video_info' not in st.session_state:
        st.session_state.video_info = None
    if 'playlist_info' not in st.session_state:
        st.session_state.playlist_info = None
    if 'spotify_info' not in st.session_state:
        st.session_state.spotify_info = None
    if 'selected_videos' not in st.session_state:
        st.session_state.selected_videos = []
    if 'selected_tracks' not in st.session_state:
        st.session_state.selected_tracks = []


def display_duration_table(total_seconds: int, handler):
    """Display duration at different playback speeds"""
    durations = handler.get_duration_at_speeds(total_seconds)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    cols = [col1, col2, col3, col4, col5]
    
    for idx, (speed, duration) in enumerate(durations.items()):
        with cols[idx]:
            st.metric(f"{speed}x Speed", duration)


def create_download_zip(files: list) -> BytesIO:
    """Create a zip file from multiple files"""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filepath, filename in files:
            if filepath and os.path.exists(filepath):
                zip_file.write(filepath, filename)
    zip_buffer.seek(0)
    return zip_buffer


def youtube_tab():
    """YouTube downloader tab"""
    st.header("YouTube / YouTube Music Downloader")
    
    # URL input
    url = st.text_input(
        "Enter YouTube or YouTube Music URL",
        placeholder="https://www.youtube.com/watch?v=... or https://music.youtube.com/watch?v=...",
        key="youtube_url"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        fetch_btn = st.button("Fetch Info", type="primary", key="youtube_fetch")
    
    if fetch_btn and url:
        if not st.session_state.youtube_handler.is_youtube_url(url):
            st.error("Please enter a valid YouTube URL")
            return
        
        with st.spinner("Fetching information..."):
            try:
                if st.session_state.youtube_handler.is_playlist(url):
                    # Progress bar for playlist
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    def update_progress(current, total):
                        progress = current / total
                        progress_bar.progress(progress)
                        status_text.text(f"Fetching video {current}/{total}...")
                    
                    st.session_state.playlist_info = st.session_state.youtube_handler.get_playlist_info(
                        url, progress_callback=update_progress
                    )
                    st.session_state.video_info = None
                    progress_bar.empty()
                    status_text.empty()
                else:
                    st.session_state.video_info = st.session_state.youtube_handler.get_video_info(url)
                    st.session_state.playlist_info = None
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # Display video info
    if st.session_state.video_info:
        display_single_video(st.session_state.video_info)
    
    # Display playlist info
    if st.session_state.playlist_info:
        display_playlist(st.session_state.playlist_info)


def display_single_video(video: VideoInfo):
    """Display single video information and download options"""
    st.subheader(f"Video: {video.title or 'Unknown'}")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if video.thumbnail:
            st.image(video.thumbnail, width="stretch")
    
    with col2:
        st.markdown(f"**Uploader:** {video.uploader or 'Unknown'}")
        st.markdown(f"**Duration:** {YouTubeHandler.format_duration(video.duration)}")
        st.markdown(f"**Views:** {video.view_count:,}")
        
        if video.duration > 0:
            st.markdown("**Duration at different speeds:**")
            display_duration_table(video.duration, st.session_state.youtube_handler)
    
    st.divider()
    
    # Download options
    st.subheader("Download Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        format_type = st.radio(
            "Format Type",
            ["Video", "Audio"],
            key="single_video_format_type"
        )
    
    with col2:
        if format_type == "Video":
            format_options = list(YouTubeHandler.VIDEO_FORMATS.keys())
            format_labels = {
                'mp4_1080p': 'MP4 - 1080p (Full HD)',
                'mp4_720p': 'MP4 - 720p (HD)',
                'mp4_480p': 'MP4 - 480p (SD)',
                'mp4_360p': 'MP4 - 360p (Low)',
                'webm_1080p': 'WebM - 1080p',
                'webm_720p': 'WebM - 720p',
                'best': 'Best Available Quality'
            }
            selected_format = st.selectbox(
                "Select Quality",
                format_options,
                index=0,
                key="single_video_quality",
                format_func=lambda x: format_labels.get(x, x)
            )
        else:
            format_options = list(YouTubeHandler.AUDIO_FORMATS.keys())
            format_labels = {
                'mp3': 'MP3 (192kbps)',
                'aac': 'AAC (192kbps)',
                'wav': 'WAV (Lossless)',
                'flac': 'FLAC (Lossless)',
                'm4a': 'M4A (192kbps)'
            }
            selected_format = st.selectbox(
                "Select Format",
                format_options,
                key="single_audio_format",
                format_func=lambda x: format_labels.get(x, x)
            )
    
    if st.button("Download", type="primary", key="download_single"):
        with st.spinner("Downloading... This may take a while."):
            try:
                progress_container = st.empty()
                
                def update_download_progress(percent):
                    progress_container.text(f"Download progress: {percent}")
                
                filepath, filename = st.session_state.youtube_handler.download_video(
                    video.url,
                    selected_format,
                    progress_callback=update_download_progress
                )
                
                progress_container.empty()
                
                with open(filepath, 'rb') as f:
                    file_data = f.read()
                
                # Clean up temp file
                os.remove(filepath)
                
                st.success("Download ready!")
                st.download_button(
                    label=f"Save {filename}",
                    data=file_data,
                    file_name=filename,
                    mime="application/octet-stream",
                    key="save_single_file"
                )
            except Exception as e:
                st.error(f"Download failed: {str(e)}")


def display_playlist(playlist: PlaylistInfo):
    """Display playlist information and selection options"""
    st.subheader(f"Playlist: {playlist.title}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Videos", playlist.video_count)
    with col2:
        st.metric("Total Duration", YouTubeHandler.format_duration(playlist.total_duration))
    with col3:
        st.metric("Uploader", playlist.uploader)
    
    # Duration at different speeds
    if playlist.total_duration > 0:
        st.markdown("### Duration at Different Playback Speeds")
        display_duration_table(playlist.total_duration, st.session_state.youtube_handler)
    
    st.divider()
    
    # Video selection
    st.subheader("Select Videos to Download")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Select All", key="select_all_videos"):
            st.session_state.selected_videos = list(range(len(playlist.videos)))
            st.rerun()
    with col2:
        if st.button("Deselect All", key="deselect_all_videos"):
            st.session_state.selected_videos = []
            st.rerun()
    
    # Display videos with checkboxes
    selected = []
    for idx, video in enumerate(playlist.videos):
        col1, col2, col3, col4 = st.columns([0.5, 3, 1, 1])
        
        with col1:
            is_selected = st.checkbox(
                f"Select video {idx + 1}",
                value=idx in st.session_state.selected_videos,
                key=f"video_checkbox_{idx}",
                label_visibility="collapsed"
            )
            if is_selected:
                selected.append(idx)
        
        with col2:
            st.markdown(f"**{idx + 1}.** {video.title or 'Unknown'}")
        
        with col3:
            st.text(YouTubeHandler.format_duration(video.duration))
        
        with col4:
            uploader = video.uploader or "Unknown"
            st.text(uploader[:20] + "..." if len(uploader) > 20 else uploader)
    
    st.session_state.selected_videos = selected
    
    # Calculate selected duration
    if selected:
        selected_duration = sum(playlist.videos[i].duration for i in selected)
        st.info(f"Selected: {len(selected)} videos | Duration: {YouTubeHandler.format_duration(selected_duration)}")
    
    st.divider()
    
    # Download options
    st.subheader("Download Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        format_type = st.radio(
            "Format Type",
            ["Video", "Audio"],
            key="playlist_format_type"
        )
    
    with col2:
        if format_type == "Video":
            format_options = list(YouTubeHandler.VIDEO_FORMATS.keys())
            format_labels = {
                'mp4_1080p': 'MP4 - 1080p (Full HD)',
                'mp4_720p': 'MP4 - 720p (HD)',
                'mp4_480p': 'MP4 - 480p (SD)',
                'mp4_360p': 'MP4 - 360p (Low)',
                'webm_1080p': 'WebM - 1080p',
                'webm_720p': 'WebM - 720p',
                'best': 'Best Available Quality'
            }
            selected_format = st.selectbox(
                "Select Quality",
                format_options,
                key="playlist_video_quality",
                format_func=lambda x: format_labels.get(x, x)
            )
        else:
            format_options = list(YouTubeHandler.AUDIO_FORMATS.keys())
            format_labels = {
                'mp3': 'MP3 (192kbps)',
                'aac': 'AAC (192kbps)',
                'wav': 'WAV (Lossless)',
                'flac': 'FLAC (Lossless)',
                'm4a': 'M4A (192kbps)'
            }
            selected_format = st.selectbox(
                "Select Format",
                format_options,
                key="playlist_audio_format",
                format_func=lambda x: format_labels.get(x, x)
            )
    
    if st.button("Download Selected", type="primary", key="download_playlist", disabled=len(selected) == 0):
        if not selected:
            st.warning("Please select at least one video to download.")
            return
        
        videos_to_download = [playlist.videos[i] for i in selected]
        
        with st.spinner(f"Downloading {len(videos_to_download)} videos..."):
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()
                temp_dir = tempfile.mkdtemp()
                
                def update_progress(current, total, title):
                    progress = current / total
                    progress_bar.progress(progress)
                    status_text.text(f"Downloading {current}/{total}: {title[:50]}...")
                
                results = st.session_state.youtube_handler.download_multiple(
                    videos_to_download,
                    selected_format,
                    temp_dir,
                    progress_callback=update_progress
                )
                
                progress_bar.empty()
                status_text.empty()
                
                # Filter successful downloads
                successful = [(fp, fn) for fp, fn in results if fp and os.path.exists(fp)]
                
                if len(successful) == 0:
                    st.error("No files were successfully downloaded.")
                    return
                
                if len(successful) == 1:
                    # Single file download
                    with open(successful[0][0], 'rb') as f:
                        file_data = f.read()
                    
                    st.success("Download ready!")
                    st.download_button(
                        label=f"Save {successful[0][1]}",
                        data=file_data,
                        file_name=successful[0][1],
                        mime="application/octet-stream",
                        key="save_playlist_single"
                    )
                else:
                    # Create zip for multiple files
                    zip_data = create_download_zip(successful)
                    
                    st.success(f"Successfully prepared {len(successful)} files!")
                    st.download_button(
                        label=f"Save All ({len(successful)} files as ZIP)",
                        data=zip_data,
                        file_name=f"{playlist.title[:30]}_downloads.zip",
                        mime="application/zip",
                        key="save_playlist_zip"
                    )
                
                # Clean up
                for fp, _ in successful:
                    if os.path.exists(fp):
                        os.remove(fp)
                        
            except Exception as e:
                st.error(f"Download failed: {str(e)}")


def spotify_tab():
    """Spotify downloader tab"""
    st.header("Spotify Downloader")
    
    if not st.session_state.spotify_available:
        st.warning(f"Spotify functionality is not available: {st.session_state.spotify_error}")
        st.info("To enable Spotify downloads, please install spotdl: `pip install spotdl`")
        return
    
    # URL input
    url = st.text_input(
        "Enter Spotify URL",
        placeholder="https://open.spotify.com/track/... or playlist/album URL",
        key="spotify_url"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        fetch_btn = st.button("Fetch Info", type="primary", key="spotify_fetch")
    
    if fetch_btn and url:
        if not st.session_state.spotify_handler.is_spotify_url(url):
            st.error("Please enter a valid Spotify URL")
            return
        
        with st.spinner("Fetching information from Spotify..."):
            try:
                content_type = st.session_state.spotify_handler.get_spotify_type(url)
                
                if content_type in ['playlist', 'album']:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    def update_progress(current, total):
                        progress = current / total
                        progress_bar.progress(progress)
                        status_text.text(f"Fetching track {current}/{total}...")
                    
                    st.session_state.spotify_info = st.session_state.spotify_handler.get_playlist_info_detailed(
                        url, progress_callback=update_progress
                    )
                    progress_bar.empty()
                    status_text.empty()
                else:
                    st.session_state.spotify_info = {
                        'type': 'track',
                        'url': url
                    }
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # Display Spotify info
    if st.session_state.spotify_info:
        if isinstance(st.session_state.spotify_info, SpotifyPlaylist):
            display_spotify_playlist(st.session_state.spotify_info)
        elif isinstance(st.session_state.spotify_info, dict):
            display_spotify_track(st.session_state.spotify_info)


def display_spotify_track(track_info: dict):
    """Display single Spotify track and download options"""
    st.subheader("Spotify Track")
    
    st.info("Ready to download the track")
    
    col1, col2 = st.columns(2)
    
    with col1:
        output_format = st.selectbox(
            "Audio Format",
            SpotifyHandler.AUDIO_FORMATS,
            index=0,
            key="spotify_track_format"
        )
    
    with col2:
        audio_quality = st.selectbox(
            "Audio Quality",
            SpotifyHandler.AUDIO_QUALITY,
            index=SpotifyHandler.AUDIO_QUALITY.index('320k'),
            key="spotify_track_quality"
        )
    
    if st.button("Download", type="primary", key="download_spotify_track"):
        with st.spinner("Downloading... This may take a while."):
            try:
                filepath, filename = st.session_state.spotify_handler.download_track(
                    track_info['url'],
                    output_format,
                    audio_quality
                )
                
                with open(filepath, 'rb') as f:
                    file_data = f.read()
                
                os.remove(filepath)
                
                st.success("Download ready!")
                st.download_button(
                    label=f"Save {filename}",
                    data=file_data,
                    file_name=filename,
                    mime="audio/mpeg",
                    key="save_spotify_track"
                )
            except Exception as e:
                st.error(f"Download failed: {str(e)}")


def display_spotify_playlist(playlist: SpotifyPlaylist):
    """Display Spotify playlist information and selection options"""
    st.subheader(f"Playlist: {playlist.name}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Tracks", playlist.total_tracks)
    with col2:
        st.metric("Total Duration", SpotifyHandler.format_duration(playlist.total_duration_ms))
    
    # Duration at different speeds
    if playlist.total_duration_ms > 0:
        st.markdown("### Duration at Different Playback Speeds")
        durations = st.session_state.spotify_handler.get_duration_at_speeds(playlist.total_duration_ms)
        
        cols = st.columns(5)
        for idx, (speed, duration) in enumerate(durations.items()):
            with cols[idx]:
                st.metric(f"{speed}x Speed", duration)
    
    st.divider()
    
    # Track selection
    st.subheader("Select Tracks to Download")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Select All", key="select_all_tracks"):
            st.session_state.selected_tracks = list(range(len(playlist.tracks)))
            st.rerun()
    with col2:
        if st.button("Deselect All", key="deselect_all_tracks"):
            st.session_state.selected_tracks = []
            st.rerun()
    
    # Display tracks with checkboxes
    selected = []
    for idx, track in enumerate(playlist.tracks):
        col1, col2, col3, col4 = st.columns([0.5, 3, 2, 1])
        
        with col1:
            is_selected = st.checkbox(
                f"Select track {idx + 1}",
                value=idx in st.session_state.selected_tracks,
                key=f"track_checkbox_{idx}",
                label_visibility="collapsed"
            )
            if is_selected:
                selected.append(idx)
        
        with col2:
            st.markdown(f"**{idx + 1}.** {track.name}")
        
        with col3:
            artists = ", ".join(track.artists) if track.artists else "Unknown"
            st.text(artists[:30] + "..." if len(artists) > 30 else artists)
        
        with col4:
            st.text(SpotifyHandler.format_duration(track.duration_ms))
    
    st.session_state.selected_tracks = selected
    
    # Calculate selected duration
    if selected:
        selected_duration = sum(playlist.tracks[i].duration_ms for i in selected)
        st.info(f"Selected: {len(selected)} tracks | Duration: {SpotifyHandler.format_duration(selected_duration)}")
    
    st.divider()
    
    # Download options
    st.subheader("Download Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        output_format = st.selectbox(
            "Audio Format",
            SpotifyHandler.AUDIO_FORMATS,
            index=0,
            key="spotify_playlist_format"
        )
    
    with col2:
        audio_quality = st.selectbox(
            "Audio Quality",
            SpotifyHandler.AUDIO_QUALITY,
            index=SpotifyHandler.AUDIO_QUALITY.index('320k'),
            key="spotify_playlist_quality"
        )
    
    if st.button("Download Selected", type="primary", key="download_spotify_playlist", disabled=len(selected) == 0):
        if not selected:
            st.warning("Please select at least one track to download.")
            return
        
        tracks_to_download = [playlist.tracks[i] for i in selected]
        
        with st.spinner(f"Downloading {len(tracks_to_download)} tracks..."):
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()
                temp_dir = tempfile.mkdtemp()
                
                def update_progress(current, total, title):
                    progress = current / total
                    progress_bar.progress(progress)
                    status_text.text(f"Downloading {current}/{total}: {title[:50]}...")
                
                results = st.session_state.spotify_handler.download_multiple(
                    tracks_to_download,
                    output_format,
                    audio_quality,
                    temp_dir,
                    progress_callback=update_progress
                )
                
                progress_bar.empty()
                status_text.empty()
                
                # Filter successful downloads
                successful = [(fp, fn) for fp, fn in results if fp and os.path.exists(fp)]
                
                if len(successful) == 0:
                    st.error("No files were successfully downloaded.")
                    return
                
                if len(successful) == 1:
                    with open(successful[0][0], 'rb') as f:
                        file_data = f.read()
                    
                    st.success("Download ready!")
                    st.download_button(
                        label=f"Save {successful[0][1]}",
                        data=file_data,
                        file_name=successful[0][1],
                        mime="audio/mpeg",
                        key="save_spotify_single"
                    )
                else:
                    zip_data = create_download_zip(successful)
                    
                    st.success(f"Successfully prepared {len(successful)} files!")
                    st.download_button(
                        label=f"Save All ({len(successful)} files as ZIP)",
                        data=zip_data,
                        file_name=f"{playlist.name[:30]}_downloads.zip",
                        mime="application/zip",
                        key="save_spotify_zip"
                    )
                
                # Clean up
                for fp, _ in successful:
                    if os.path.exists(fp):
                        os.remove(fp)
                        
            except Exception as e:
                st.error(f"Download failed: {str(e)}")


def main():
    """Main application entry point"""
    init_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">Media Downloader</h1>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Download videos and music from YouTube and Spotify</p>", unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("About")
        st.markdown("""
        This application allows you to download:
        - **YouTube** videos and playlists
        - **YouTube Music** tracks and playlists
        - **Spotify** tracks and playlists
        
        ### Features
        - Multiple output formats (video & audio)
        - Playlist support with selection
        - Duration calculations at different speeds
        - Direct download to your device
        
        ### Supported Formats
        
        **Video:** MP4, WebM (various qualities)
        
        **Audio:** MP3, AAC, WAV, FLAC, M4A
        """)
        
        st.divider()
        
        st.header("Instructions")
        st.markdown("""
        1. Select YouTube or Spotify tab
        2. Paste the URL
        3. Click "Fetch Info"
        4. Select videos/tracks (for playlists)
        5. Choose output format
        6. Click Download
        """)
        
        st.divider()
        
        # Clear session button
        if st.button("Clear Session", type="secondary"):
            for key in ['video_info', 'playlist_info', 'spotify_info', 'selected_videos', 'selected_tracks']:
                if key in st.session_state:
                    st.session_state[key] = None if 'info' in key else []
            st.rerun()
    
    # Main content tabs
    tab1, tab2 = st.tabs(["YouTube", "Spotify"])
    
    with tab1:
        youtube_tab()
    
    with tab2:
        spotify_tab()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: gray; font-size: 0.8rem;'>"
        "Note: Please respect copyright laws and only download content you have the right to access."
        "</p>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
