from typing import Dict, Any, List, Optional
from .api import FirefliesAPI


class TranscriptManager:
    """
    Manages transcript operations including fetching transcript content
    """
    
    def __init__(self):
        self.api = FirefliesAPI()
    
    def get_transcripts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get list of transcripts with basic metadata
        
        Args:
            limit: Number of transcripts to fetch (default: 10)
            
        Returns:
            List of transcript dictionaries with metadata
        """
        query = f"""
        query Transcripts {{
            transcripts(limit: {limit}) {{
                id
                title
                host_email
                organizer_email
                fireflies_users
                privacy
                participants
                date
                duration
                transcript_url
                dateString
                calendar_id
                cal_id
                calendar_type
                meeting_link
            }}
        }}
        """
        
        result = self.api._make_request(query)
        return result.get("data", {}).get("transcripts", [])
    
    def get_transcript_content(self, transcript_id: str) -> Dict[str, Any]:
        """
        Get the full transcript content including sentences and speakers
        
        Args:
            transcript_id: The ID of the transcript to fetch
            
        Returns:
            Dict containing transcript content with sentences
        """
        query = f"""
        query GetTranscriptContent {{
            transcript(id: "{transcript_id}") {{
                id
                title
                date
                duration
                participants
                sentences {{
                    speaker_name
                    speaker_id
                    text
                    start_time
                    end_time
                    confidence
                }}
                summary {{
                    overview
                    action_items
                    keywords
                    topics
                    bullet_points
                    outline
                }}
            }}
        }}
        """
        
        result = self.api._make_request(query)
        return result.get("data", {}).get("transcript", {})
    
    def search_transcripts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search transcripts by content or metadata
        
        Args:
            query: Search query string
            limit: Number of results to return
            
        Returns:
            List of matching transcripts
        """
        search_query = f"""
        query SearchTranscripts {{
            transcripts(limit: {limit}, search: "{query}") {{
                id
                title
                host_email
                organizer_email
                participants
                date
                duration
                transcript_url
                dateString
            }}
        }}
        """
        
        result = self.api._make_request(search_query)
        return result.get("data", {}).get("transcripts", [])


def get_transcripts(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Convenience function to get transcripts
    
    Args:
        limit: Number of transcripts to fetch
        
    Returns:
        List of transcript dictionaries
    """
    manager = TranscriptManager()
    return manager.get_transcripts(limit)


def get_transcript_content(transcript_id: str) -> Dict[str, Any]:
    """
    Convenience function to get transcript content
    
    Args:
        transcript_id: The ID of the transcript to fetch
        
    Returns:
        Dict containing full transcript content
    """
    manager = TranscriptManager()
    return manager.get_transcript_content(transcript_id)


def search_transcripts(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Convenience function to search transcripts
    
    Args:
        query: Search query string
        limit: Number of results to return
        
    Returns:
        List of matching transcripts
    """
    manager = TranscriptManager()
    return manager.search_transcripts(query, limit)