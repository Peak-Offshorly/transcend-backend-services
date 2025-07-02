#!/usr/bin/env python3
"""
Test script for Fireflies transcript functionality

This script demonstrates how to:
1. List available transcripts
2. Get transcript content
3. Display transcript content in terminal
"""

import sys
import os
from datetime import datetime

# Add the parent directories to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.fireflies.transcripts import TranscriptManager


def print_separator(title: str):
    """Print a nice separator with title"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


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


def test_get_transcripts():
    """Test getting list of transcripts"""
    print_separator("TESTING: Get Transcripts List")
    
    try:
        manager = TranscriptManager()
        transcripts = manager.get_transcripts(limit=3)
        
        if transcripts:
            print(f"✅ Successfully retrieved {len(transcripts)} transcript(s):")
            
            for i, transcript in enumerate(transcripts, 1):
                print(f"\n{i}. {transcript.get('title', 'Untitled')}")
                print(f"   ID: {transcript.get('id')}")
                print(f"   Date: {format_timestamp(transcript.get('date', 0))}")
                print(f"   Duration: {format_duration(transcript.get('duration', 0))}")
                print(f"   Participants: {', '.join(transcript.get('participants', []))}")
                print(f"   URL: {transcript.get('transcript_url')}")
            
            # Return the first transcript ID for testing content retrieval
            return transcripts[0].get('id') if transcripts else None
        else:
            print("❌ No transcripts found")
            return None
            
    except Exception as e:
        print(f"❌ Error getting transcripts: {str(e)}")
        return None


def test_get_transcript_content(transcript_id: str):
    """Test getting transcript content"""
    print_separator(f"TESTING: Get Transcript Content (ID: {transcript_id[:20]}...)")
    
    try:
        manager = TranscriptManager()
        content = manager.get_transcript_content(transcript_id)
        
        if content:
            print(f"✅ Successfully retrieved transcript content:")
            print(f"   Title: {content.get('title', 'Untitled')}")
            print(f"   Duration: {format_duration(content.get('duration', 0))}")
            print(f"   Participants: {', '.join(content.get('participants', []))}")
            
            # Display summary if available
            summary = content.get('summary', {})
            if summary:
                print(f"\n📋 Summary Available:")
                if summary.get('overview'):
                    print(f"   Overview: {summary['overview'][:100]}...")
                if summary.get('action_items'):
                    print(f"   Action Items: {len(summary['action_items'])} items")
                if summary.get('keywords'):
                    print(f"   Keywords: {', '.join(summary['keywords'][:5])}")
            
            # Display sentence count
            sentences = content.get('sentences', [])
            if sentences:
                print(f"\n💬 Transcript Content:")
                print(f"   Total sentences: {len(sentences)}")
                print(f"   Sample (first 3 sentences):")
                
                for i, sentence in enumerate(sentences[:3], 1):
                    speaker = sentence.get('speaker_name', 'Unknown')
                    text = sentence.get('text', '')[:80] + '...' if len(sentence.get('text', '')) > 80 else sentence.get('text', '')
                    print(f"   {i}. {speaker}: {text}")
            
            return True
        else:
            print("❌ No content found for this transcript")
            return False
            
    except Exception as e:
        print(f"❌ Error getting transcript content: {str(e)}")
        return False


def test_search_transcripts():
    """Test searching transcripts"""
    print_separator("TESTING: Search Transcripts")
    
    try:
        manager = TranscriptManager()
        search_query = "planning"  # Search for transcripts containing "planning"
        results = manager.search_transcripts(search_query, limit=5)
        
        if results:
            print(f"✅ Found {len(results)} transcript(s) matching '{search_query}':")
            
            for i, transcript in enumerate(results, 1):
                print(f"\n{i}. {transcript.get('title', 'Untitled')}")
                print(f"   ID: {transcript.get('id')}")
                print(f"   Date: {format_timestamp(transcript.get('date', 0))}")
                print(f"   Participants: {', '.join(transcript.get('participants', []))}")
        else:
            print(f"❌ No transcripts found matching '{search_query}'")
            
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Error searching transcripts: {str(e)}")
        return False


def main():
    """Main test function"""
    print("🔥 FIREFLIES TRANSCRIPT TESTING SUITE")
    print("Testing transcript functionality...")
    
    # Test 1: Get transcripts list
    transcript_id = test_get_transcripts()
    
    # Test 2: Get transcript content (if we have a transcript ID)
    content_success = False
    if transcript_id:
        content_success = test_get_transcript_content(transcript_id)
    else:
        print("\n⚠️  Skipping content test - no transcript ID available")
    
    # Test 3: Search transcripts
    search_success = test_search_transcripts()
    
    # Summary
    print_separator("TEST SUMMARY")
    print(f"✅ Get Transcripts: {'PASSED' if transcript_id else 'FAILED'}")
    print(f"✅ Get Content: {'PASSED' if content_success else 'FAILED' if transcript_id else 'SKIPPED'}")
    print(f"✅ Search Transcripts: {'PASSED' if search_success else 'FAILED'}")
    
    if transcript_id:
        print(f"\n🎉 Transcript functionality is working!")
        print(f"\n💡 To view full transcript content, run:")
        print(f"   python transcript_viewer.py --id {transcript_id}")
        print(f"\n💡 To search transcripts, run:")
        print(f"   python transcript_viewer.py --search 'your query'")
    else:
        print("\n⚠️  Could not retrieve transcripts. Check your API key and permissions.")


if __name__ == "__main__":
    main()