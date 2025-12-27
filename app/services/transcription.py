from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from typing import Optional
import structlog
from app.config import settings

logger = structlog.get_logger()


class TranscriptionService:
    """Service to fetch transcripts from YouTube"""
    
    def __init__(self):
        pass
    
    def get_transcript(self, video_id: str, language: str = 'en') -> dict:
        """
        Fetch transcript from YouTube.
        
        Args:
            video_id: YouTube video ID
            language: Preferred language code (default: 'en')
        
        Returns:
            dict with 'text' and 'segments' for timestamped transcript
        """
        try:
            logger.info("fetching_youtube_transcript", video_id=video_id)
            
            # Try to get transcript in specified language
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # Try to find manually created transcript first (better quality)
                try:
                    transcript = transcript_list.find_manually_created_transcript([language])
                except:
                    # Fall back to auto-generated
                    transcript = transcript_list.find_generated_transcript([language])
                
                transcript_data = transcript.fetch()
                
            except (TranscriptsDisabled, NoTranscriptFound) as e:
                logger.error(
                    "transcript_not_available",
                    video_id=video_id,
                    error=str(e)
                )
                raise ValueError(f"No transcript available for video {video_id}")
            
            # Format the transcript
            segments = []
            full_text_parts = []
            
            for entry in transcript_data:
                segments.append({
                    'start': entry['start'],
                    'end': entry['start'] + entry['duration'],
                    'text': entry['text'].strip()
                })
                full_text_parts.append(entry['text'].strip())
            
            full_text = ' '.join(full_text_parts)
            
            word_count = len(full_text.split())
            logger.info(
                "transcript_fetched",
                video_id=video_id,
                word_count=word_count,
                segment_count=len(segments)
            )
            
            return {
                'text': full_text,
                'language': language,
                'segments': segments
            }
            
        except Exception as e:
            logger.error("transcript_fetch_failed", video_id=video_id, error=str(e))
            raise
