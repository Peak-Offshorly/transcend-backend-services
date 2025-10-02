#!/usr/bin/env python3
"""
Standalone Transcript Viewer - Terminal interface for viewing Fireflies transcripts

This is a standalone version that doesn't require Firebase initialization
and can be run independently of the main application.

Usage:
    python standalone_transcript_viewer.py                    # List all transcripts
    python standalone_transcript_viewer.py --id TRANSCRIPT_ID # View specific transcript content
    python standalone_transcript_viewer.py --search "query"   # Search transcripts
"""

import os
import sys
import requests
import argparse
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class FirefliesAPI:
    """
    Standalone Fireflies API client for making GraphQL requests
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('FIREFLIES_API_KEY')
        self.base_url = "https://api.fireflies.ai/graphql"
        
        if not self.api_key:
            raise ValueError("FIREFLIES_API_KEY is required. Set it in your .env file.")
    
    def _make_request(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GraphQL request to the Fireflies API
        
        Args:
            query: GraphQL query string
            variables: Optional variables for the query
            
        Returns:
            Dict containing the API response
            
        Raises:
            requests.RequestException: If the API request fails
            ValueError: If the API returns an error
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        data = {
            'query': query
        }
        
        # Add variables if provided
        if variables:
            data['variables'] = variables
        
        try:
            response = requests.post(self.base_url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            # Check for GraphQL errors
            if "errors" in result:
                error_messages = [error.get("message", "Unknown error") for error in result["errors"]]
                raise ValueError(f"GraphQL errors: {', '.join(error_messages)}")
                
            return result
            
        except requests.RequestException as e:
            raise requests.RequestException(f"Fireflies API request failed: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        Test if the API connection and key are working
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            query = "{ users { name user_id } }"
            result = self._make_request(query)
            return "data" in result and "users" in result["data"]
        except Exception:
            return False


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
                participants
                sentences {{
                    speaker_name
                    speaker_id
                    text
                    start_time
                    end_time
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


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string to be used as a filename
    
    Args:
        filename: The string to sanitize
        
    Returns:
        A sanitized filename safe for use on most filesystems
    """
    # Remove or replace invalid characters (more comprehensive)
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    # Remove extra spaces and replace with single spaces
    filename = re.sub(r'\s+', ' ', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Remove consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    # Limit length to 200 characters
    if len(filename) > 200:
        filename = filename[:200]
    # Ensure we have a filename
    if not filename:
        filename = "untitled_transcript"
    return filename


def save_transcript_to_file(content: Dict[str, Any], transcript_id: str) -> str:
    """
    Save transcript content to a formatted text file
    
    Args:
        content: The transcript content dictionary
        transcript_id: The transcript ID for fallback naming
        
    Returns:
        The filename where the transcript was saved
    """
    if not content:
        print("No content to save")
        return ""
    
    try:
        # Generate filename from title
        title = content.get('title', 'Untitled Meeting')
        date = content.get('date', 0)
        
        # Handle date formatting more robustly
        if date and date != 0:
            try:
                date_str = format_timestamp(date).split(' ')[0]  # Get just the date part
            except:
                date_str = datetime.now().strftime("%Y-%m-%d")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Create filename: "YYYY-MM-DD - Meeting Title.txt"
        filename = f"{date_str} - {title}.txt"
        filename = sanitize_filename(filename)
        
        # Create transcripts directory if it doesn't exist
        transcripts_dir = "app/fireflies/transcripts"
        try:
            if not os.path.exists(transcripts_dir):
                os.makedirs(transcripts_dir)
                print(f"Created directory: {transcripts_dir}")
        except OSError as e:
            print(f"Error creating directory {transcripts_dir}: {str(e)}")
            # Try to save in current directory instead
            transcripts_dir = "."
            filename = f"transcript_{date_str}_{sanitize_filename(title)}.txt"
        
        filepath = os.path.join(transcripts_dir, filename)
        
        # Generate file content
        file_content = []
        
        # # Header
        # file_content.append("=" * 80)
        # file_content.append(f"TRANSCRIPT: {content.get('title', 'Untitled')}")
        # file_content.append("=" * 80)
        # file_content.append("")
        
        # # Meeting details
        # file_content.append("MEETING DETAILS:")
        # file_content.append(f"Date: {format_timestamp(content.get('date', 0))}")
        # file_content.append(f"Duration: {format_duration(content.get('duration', 0))}")
        
        # Handle participants safely
        # participants = content.get('participants', [])
        # if participants:
        #     file_content.append(f"Participants: {', '.join(participants)}")
        # else:
        #     file_content.append("Participants: Not specified")
        
        # file_content.append(f"Transcript ID: {transcript_id}")
        # file_content.append("")
        
        # Summary section
        summary = content.get('summary', {})
        if summary:
            file_content.append("-" * 60)
            file_content.append("SUMMARY")
            file_content.append("-" * 60)
            file_content.append("")
            
            if summary.get('overview'):
                file_content.append("OVERVIEW:")
                file_content.append(summary['overview'])
                file_content.append("")
            
            if summary.get('action_items'):
                action_items = summary['action_items']
                file_content.append("ACTION ITEMS:")
                
                # Handle both string and list formats
                if isinstance(action_items, str):
                    # If it's a string, split by common delimiters or show as single item
                    if '\n' in action_items:
                        items = [item.strip() for item in action_items.split('\n') if item.strip()]
                    elif ';' in action_items:
                        items = [item.strip() for item in action_items.split(';') if item.strip()]
                    elif '.' in action_items and len(action_items) > 50:  # Likely multiple sentences
                        items = [item.strip() + '.' for item in action_items.split('.') if item.strip()]
                    else:
                        items = [action_items]  # Single action item
                elif isinstance(action_items, list):
                    items = action_items
                else:
                    items = [str(action_items)]
                
                for i, item in enumerate(items, 1):
                    file_content.append(f"{i}. {item}")
                file_content.append("")
            
            if summary.get('keywords'):
                keywords = summary['keywords']
                if isinstance(keywords, list):
                    file_content.append(f"KEYWORDS: {', '.join(keywords)}")
                else:
                    file_content.append(f"KEYWORDS: {keywords}")
                file_content.append("")
            
            # Handle bullet_gist safely
            if summary.get('bullet_gist'):
                bullet_gist = summary['bullet_gist']
                file_content.append("KEY POINTS:")
                
                # Handle both string and list formats
                if isinstance(bullet_gist, str):
                    if '\n' in bullet_gist:
                        items = [item.strip() for item in bullet_gist.split('\n') if item.strip()]
                    elif ';' in bullet_gist:
                        items = [item.strip() for item in bullet_gist.split(';') if item.strip()]
                    elif '.' in bullet_gist and len(bullet_gist) > 50:  # Likely multiple sentences
                        items = [item.strip() + '.' for item in bullet_gist.split('.') if item.strip()]
                    else:
                        items = [bullet_gist]  # Single item
                elif isinstance(bullet_gist, list):
                    items = bullet_gist
                else:
                    items = [str(bullet_gist)]
                
                for i, point in enumerate(items, 1):
                    file_content.append(f"{i}. {point}")
                file_content.append("")
            
            # Handle gist safely
            if summary.get('gist'):
                file_content.append("GIST:")
                file_content.append(summary['gist'])
                file_content.append("")
            
            # Handle outline safely
            if summary.get('outline'):
                outline = summary['outline']
                file_content.append("OUTLINE:")
                if isinstance(outline, list):
                    for i, item in enumerate(outline, 1):
                        file_content.append(f"{i}. {item}")
                else:
                    file_content.append(str(outline))
                file_content.append("")
        
        # Transcript content
        sentences = content.get('sentences', [])
        if sentences:
            # file_content.append("-" * 60)
            # file_content.append("TRANSCRIPT CONTENT")
            # file_content.append("-" * 60)
            # file_content.append("")
            
            current_speaker = None
            for sentence in sentences:
                speaker = sentence.get('speaker_name', 'Unknown')
                text = sentence.get('text', '')
                start_time = sentence.get('start_time', 0)
                
                # Add speaker name only when it changes
                if speaker != current_speaker:
                    if current_speaker is not None:  # Add blank line between speakers
                        file_content.append("")
                    file_content.append(f"{speaker} [{format_time_seconds(start_time)}]:")
                    current_speaker = speaker
                
                file_content.append(f"  {text}")
            
            file_content.append("")
            # file_content.append(f"Total sentences: {len(sentences)}")
        else:
            file_content.append("No transcript content available.")
        
        # Footer
        # file_content.append("")
        # file_content.append("=" * 80)
        # file_content.append(f"Transcript exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        # file_content.append("Generated by Fireflies Transcript Viewer")
        # file_content.append("=" * 80)
        
        # Write to file with better error handling
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(file_content))
            print(f"Successfully saved transcript to: {filepath}")
            return filepath
        except PermissionError:
            print(f"Permission denied writing to: {filepath}")
            # Try alternative filename
            alt_filename = f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            alt_filepath = os.path.join(".", alt_filename)
            try:
                with open(alt_filepath, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(file_content))
                print(f"Saved to alternative location: {alt_filepath}")
                return alt_filepath
            except Exception as e:
                print(f"Failed to save to alternative location: {str(e)}")
                return ""
        except UnicodeEncodeError as e:
            print(f"Unicode encoding error: {str(e)}")
            # Try saving with different encoding
            try:
                with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                    f.write('\n'.join(file_content))
                print(f"Saved with unicode errors ignored: {filepath}")
                return filepath
            except Exception as e2:
                print(f"Failed even with unicode error handling: {str(e2)}")
                return ""
        except OSError as e:
            print(f"OS error writing file: {str(e)}")
            return ""
        except Exception as e:
            print(f"Unexpected error writing file: {str(e)}")
            return ""
    
    except Exception as e:
        print(f"Error in save_transcript_to_file: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return ""


def format_duration(duration_seconds: float) -> str:
    """Format duration from seconds to human-readable format"""
    if not duration_seconds:
        return "0m 0s"
    minutes = int(duration_seconds // 60)
    seconds = int(duration_seconds % 60)
    return f"{minutes}m {seconds}s"


def format_timestamp(timestamp_ms: int) -> str:
    """Format timestamp from milliseconds to readable date"""
    if not timestamp_ms or timestamp_ms == 0:
        return "Unknown date"
    try:
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError):
        return "Unknown date"


def format_time_seconds(seconds: float) -> str:
    """Format time in seconds to MM:SS format"""
    if not seconds:
        return "00:00"
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes:02d}:{remaining_seconds:02d}"


def print_separator(title: str, char: str = "=", width: int = 80):
    """Print a separator with title"""
    print(f"\n{char * width}")
    print(f" {title}")
    print(f"{char * width}")


def print_transcript_list(transcripts: List[Dict[str, Any]]):
    """Print a formatted list of transcripts"""
    print_separator("AVAILABLE TRANSCRIPTS")
    
    if not transcripts:
        print("No transcripts found.")
        return
    
    print(f"Found {len(transcripts)} transcript(s):\n")
    
    for i, transcript in enumerate(transcripts, 1):
        print(f"{i}. {transcript.get('title', 'Untitled Meeting')}")
        print(f"   ID: {transcript.get('id', 'N/A')}")
        print(f"   Date: {format_timestamp(transcript.get('date', 0))}")
        print(f"   Duration: {format_duration(transcript.get('duration', 0))}")
        print(f"   Participants: {', '.join(transcript.get('participants', []))}")
        print(f"   Organizer: {transcript.get('organizer_email', 'N/A')}")
        print(f"   URL: {transcript.get('transcript_url', 'N/A')}")
        print()


def print_transcript_content(content: Dict[str, Any], transcript_id: str):
    """Print formatted transcript content with sentences and save to file"""
    if not content:
        print("No transcript content found.")
        return
    
    print_separator(f"TRANSCRIPT: {content.get('title', 'Untitled')}")
    
    # Basic information
    print(f"Date: {format_timestamp(content.get('date', 0))}")
    print(f"Duration: {format_duration(content.get('duration', 0))}")
    participants = content.get('participants', [])
    if participants:
        print(f"👥 Participants: {', '.join(participants)}")
    else:
        print("👥 Participants: Not specified")
    
    # Summary section
    summary = content.get('summary', {})
    if summary:
        print_separator("SUMMARY", char="-", width=60)
        
        if summary.get('overview'):
            print(f"Overview:")
            print(f"   {summary['overview']}\n")
        
        if summary.get('action_items'):
            action_items = summary['action_items']
            print(f"Action Items:")
            
            # Handle both string and list formats
            if isinstance(action_items, str):
                # If it's a string, split by common delimiters or show as single item
                if '\n' in action_items:
                    items = [item.strip() for item in action_items.split('\n') if item.strip()]
                elif ';' in action_items:
                    items = [item.strip() for item in action_items.split(';') if item.strip()]
                elif '.' in action_items and len(action_items) > 50:  # Likely multiple sentences
                    items = [item.strip() + '.' for item in action_items.split('.') if item.strip()]
                else:
                    items = [action_items]  # Single action item
            elif isinstance(action_items, list):
                items = action_items
            else:
                items = [str(action_items)]
            
            for i, item in enumerate(items, 1):
                print(f"   {i}. {item}")
            print()
        
        if summary.get('keywords'):
            keywords = summary['keywords']
            if isinstance(keywords, list):
                print(f"Keywords: {', '.join(keywords)}\n")
            else:
                print(f"Keywords: {keywords}\n")
        
        if summary.get('bullet_gist'):
            bullet_gist = summary['bullet_gist']
            print(f"Key Points:")
            
            # Handle both string and list formats
            if isinstance(bullet_gist, str):
                if '\n' in bullet_gist:
                    items = [item.strip() for item in bullet_gist.split('\n') if item.strip()]
                elif ';' in bullet_gist:
                    items = [item.strip() for item in bullet_gist.split(';') if item.strip()]
                elif '.' in bullet_gist and len(bullet_gist) > 50:  # Likely multiple sentences
                    items = [item.strip() + '.' for item in bullet_gist.split('.') if item.strip()]
                else:
                    items = [bullet_gist]  # Single item
            elif isinstance(bullet_gist, list):
                items = bullet_gist
            else:
                items = [str(bullet_gist)]
            
            for i, point in enumerate(items, 1):
                print(f"   {i}. {point}")
            print()
    
    # Transcript content
    sentences = content.get('sentences', [])
    if sentences:
        print_separator("TRANSCRIPT CONTENT", char="-", width=60)
        print(f"Total sentences: {len(sentences)}\n")
        
        current_speaker = None
        for sentence in sentences:
            speaker = sentence.get('speaker_name', 'Unknown')
            text = sentence.get('text', '')
            start_time = sentence.get('start_time', 0)
            
            # Print speaker name only when it changes
            if speaker != current_speaker:
                print(f"\n{speaker} [{format_time_seconds(start_time)}]:")
                current_speaker = speaker
            
            print(f"   {text}")
    else:
        print("No transcript sentences found.")
    
    # Save to file
    print("\n" + "=" * 60)
    print("Saving transcript to file...")
    
    filepath = save_transcript_to_file(content, transcript_id)
    if filepath:
        print(f"Transcript saved to: {filepath}")
        try:
            file_size = os.path.getsize(filepath)
            print(f"File size: {file_size} bytes")
        except:
            print("File created successfully")
    else:
        print("Failed to save transcript to file")


def main():
    """Main function to handle command line arguments and execute actions"""
    parser = argparse.ArgumentParser(
        description="View and search Fireflies transcripts in terminal (Standalone version)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python standalone_transcript_viewer.py                          # List all transcripts
  python standalone_transcript_viewer.py --limit 5                # List 5 most recent transcripts
  python standalone_transcript_viewer.py --id 01JYMZHCVG2MH8BW... # View specific transcript
  python standalone_transcript_viewer.py --search "planning"      # Search for transcripts containing "planning"
        """
    )
    
    parser.add_argument('--id', help='Transcript ID to view content')
    parser.add_argument('--search', help='Search query for transcripts')
    parser.add_argument('--limit', type=int, default=10, help='Limit number of results (default: 10)')
    
    args = parser.parse_args()
    
    try:
        manager = TranscriptManager()
        
        if args.id:
            # View specific transcript content
            print(f"Fetching transcript content for ID: {args.id}")
            content = manager.get_transcript_content(args.id)
            print_transcript_content(content, args.id)
            
        elif args.search:
            # Search transcripts
            print(f"Searching for transcripts containing: '{args.search}'")
            transcripts = manager.search_transcripts(args.search, args.limit)
            print_transcript_list(transcripts)
            
        else:
            # List all transcripts (default behavior)
            print(f"Fetching {args.limit} most recent transcripts...")
            transcripts = manager.get_transcripts(args.limit)
            print_transcript_list(transcripts)
            
            if transcripts: 
                print("\nTip: Use --id TRANSCRIPT_ID to view full transcript content")
                print("Tip: Use --search 'query' to search transcripts")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check that your FIREFLIES_API_KEY is set in your .env file")
        print("2. Verify your API key has the correct permissions")
        print("3. Ensure the transcript ID is correct (if using --id)")
        print("4. Check write permissions in the current directory")
        sys.exit(1)


if __name__ == "__main__":
    main()