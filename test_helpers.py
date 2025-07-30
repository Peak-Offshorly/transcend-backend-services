#!/usr/bin/env python3
"""
Simple test script for Fireflies helper functions
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.fireflies.helpers import get_transcripts_list, get_transcript_content


def test_get_transcripts_list():
    """Test getting list of transcripts"""
    print("Testing get_transcripts_list()...")
    try:
        transcripts = get_transcripts_list()
        print(f"✅ Success: Retrieved {len(transcripts)} transcripts")
        
        if transcripts:
            # Show first transcript details
            first = transcripts[0]
            print(f"   First transcript: {first.get('title', 'No title')}")
            print(f"   ID: {first.get('id', 'No ID')}")
            print(f"   Date: {first.get('date', 'No date')}")
            return first.get('id')  # Return ID for content test
        else:
            print("   No transcripts found")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def test_get_transcript_content(transcript_id):
    """Test getting transcript content"""
    if not transcript_id:
        print("⏭️  Skipping content test - no transcript ID available")
        return
        
    print(f"\nTesting get_transcript_content('{transcript_id}')...")
    try:
        content = get_transcript_content(transcript_id)
        print(f"✅ Success: Retrieved transcript content")
        print(f"   Title: {content.get('title', 'No title')}")
        print(f"   Duration: {content.get('duration', 0)} seconds")
        
        sentences = content.get('sentences', [])
        print(f"   Sentences: {len(sentences)}")
        
        if sentences:
            print(f"   First sentence: {sentences[0].get('text', '')[:100]}...")
            
        summary = content.get('summary', {})
        if summary:
            print(f"   Has summary: {bool(summary.get('overview'))}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    print("🔧 Testing Fireflies Helper Functions")
    print("=" * 50)
    
    # Test getting transcripts list
    transcript_id = test_get_transcripts_list()
    
    # Test getting transcript content if we have an ID
    test_get_transcript_content(transcript_id)
    
    print("\n✅ Testing complete!")