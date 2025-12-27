import yt_dlp
import structlog

logger = structlog.get_logger()


class YouTubeDownloader:
    """Service to download YouTube videos and extract metadata"""
    
    def __init__(self):
        pass
    
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
