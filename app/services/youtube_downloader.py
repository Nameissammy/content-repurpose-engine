import yt_dlp
import os
from pathlib import Path
import structlog

logger = structlog.get_logger()


class YouTubeDownloader:
    """Service to download YouTube videos and extract metadata"""
    
    def __init__(self, output_dir: str = "uploads/audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def get_metadata(self, video_url: str, video_id: str) -> dict:
        """
        Get video metadata without downloading.
        
        Returns:
            dict with title, description, duration, etc.
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        
        try:
            logger.info("fetching_metadata", video_id=video_id)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                metadata = {
                    'title': info.get('title'),
                    'description': info.get('description'),
                    'duration': info.get('duration'),  # in seconds
                    'uploader': info.get('uploader'),
                    'upload_date': info.get('upload_date'),
                    'view_count': info.get('view_count'),
                    'like_count': info.get('like_count'),
                }
                
                logger.info(
                    "metadata_fetched",
                    video_id=video_id,
                    title=metadata['title'],
                    duration=metadata['duration']
                )
                
                return metadata
                
        except Exception as e:
            logger.error("metadata_fetch_failed", video_id=video_id, error=str(e))
            raise
    
    def download_audio(self, video_url: str, video_id: str) -> dict:
        """
        Download audio from YouTube video using yt-dlp.
        (Kept for backward compatibility or optional use)
        
        Returns:
            dict with audio_path, title, description, duration
        """
        output_path = self.output_dir / f"{video_id}.mp3"
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': str(self.output_dir / f"{video_id}.%(ext)s"),
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info("downloading_video", video_id=video_id)
                info = ydl.extract_info(video_url, download=True)
                
                metadata = {
                    'audio_path': str(output_path),
                    'title': info.get('title'),
                    'description': info.get('description'),
                    'duration': info.get('duration'),  # in seconds
                    'uploader': info.get('uploader'),
                    'upload_date': info.get('upload_date'),
                    'view_count': info.get('view_count'),
                    'like_count': info.get('like_count'),
                }
                
                logger.info(
                    "video_downloaded",
                    video_id=video_id,
                    title=metadata['title'],
                    duration=metadata['duration']
                )
                
                return metadata
                
        except Exception as e:
            logger.error("download_failed", video_id=video_id, error=str(e))
            raise
    
    def cleanup(self, audio_path: str):
        """Remove downloaded audio file"""
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
                logger.info("audio_file_deleted", path=audio_path)
        except Exception as e:
            logger.warning("cleanup_failed", path=audio_path, error=str(e))
