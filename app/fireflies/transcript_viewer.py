#!/usr/bin/env python3
"""
Transcript Viewer - Terminal interface for viewing Fireflies transcripts

Usage:
    python transcript_viewer.py                    # List all transcripts
    python transcript_viewer.py --id TRANSCRIPT_ID # View specific transcript content
    python transcript_viewer.py --search "query"   # Search transcripts
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, List
import argparse

# Add the parent directories to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.fireflies.transcripts import TranscriptManager


def format_duration(duration_seconds: float) -> str:
    """Format duration from seconds to human-readable format"""
    minutes = int(duration_seconds // 60)
    seconds = int(duration_seconds % 60)
    return f"{minutes}m {seconds}s"


def format_timestamp(timestamp_ms: int) -> str:
    """Format timestamp from milliseconds to readable date"""
    try:
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError):
        return "Unknown date"


def format_time_seconds(seconds: float) -> str:
    """Format time in seconds to MM:SS format"""
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


def print_transcript_content(content: Dict[str, Any]):
    """Print formatted transcript content with sentences"""
    if not content:
        print("❌ No transcript content found.")
        return
    
    # Header information
    print_separator(f"TRANSCRIPT: {content.get('title', 'Untitled')}")
    print(f"ID: {content.get('id', 'N/A')}")
    print(f"Date: {format_timestamp(content.get('date', 0))}")
    print(f"Duration: {format_duration(content.get('duration', 0))}")
    print(f"Participants: {', '.join(content.get('participants', []))}")
    
    # Summary section
    summary = content.get('summary', {})
    if summary:
        print_separator("SUMMARY", "-", 60)
        
        if summary.get('overview'):
            print(f"📝 Overview:")
            print(f"   {summary['overview']}\n")
        
        if summary.get('action_items'):
            print(f"✅ Action Items:")
            for item in summary['action_items']:
                print(f"   • {item}")
            print()
        
        if summary.get('keywords'):
            print(f"🔑 Keywords: {', '.join(summary['keywords'])}\n")
        
        if summary.get('topics'):
            print(f"📋 Topics:")
            for topic in summary['topics']:
                print(f"   • {topic}")
            print()
    
    # Transcript content
    sentences = content.get('sentences', [])
    if sentences:
        print_separator("TRANSCRIPT CONTENT", "-", 60)
        
        current_speaker = None
        for sentence in sentences:
            speaker = sentence.get('speaker_name', 'Unknown Speaker')
            text = sentence.get('text', '')
            start_time = sentence.get('start_time', 0)
            confidence = sentence.get('confidence', 0)
            
            # Print speaker name if it changed
            if speaker != current_speaker:
                current_speaker = speaker
                print(f"\n🎤 {speaker} [{format_time_seconds(start_time)}]:")
            
            # Print the text with confidence indicator
            confidence_indicator = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"
            print(f"   {text} {confidence_indicator}")
    else:
        print("No transcript sentences available.")


def main():
    """Main function to handle command line arguments and execute actions"""
    parser = argparse.ArgumentParser(
        description="View and search Fireflies transcripts in terminal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python transcript_viewer.py                          # List all transcripts
  python transcript_viewer.py --limit 5                # List 5 most recent transcripts
  python transcript_viewer.py --id 01JYMZHCVG2MH8BW... # View specific transcript
  python transcript_viewer.py --search "planning"      # Search for transcripts containing "planning"
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
            print(f"🔍 Fetching transcript content for ID: {args.id}")
            content = manager.get_transcript_content(args.id)
            print_transcript_content(content)
            
        elif args.search:
            # Search transcripts
            print(f"🔍 Searching for transcripts containing: '{args.search}'")
            transcripts = manager.search_transcripts(args.search, args.limit)
            print_transcript_list(transcripts)
            
        else:
            # List all transcripts (default behavior)
            print(f"📋 Fetching {args.limit} most recent transcripts...")
            transcripts = manager.get_transcripts(args.limit)
            print_transcript_list(transcripts)
            
            if transcripts:
                print("\n💡 Tip: Use --id TRANSCRIPT_ID to view full transcript content")
                print("💡 Tip: Use --search 'query' to search transcripts")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check that your FIREFLIES_API_KEY is set in your .env file")
        print("2. Verify your API key has the correct permissions")
        print("3. Ensure the transcript ID is correct (if using --id)")
        sys.exit(1)


if __name__ == "__main__":
    main()