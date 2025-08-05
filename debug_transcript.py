#!/usr/bin/env python3
"""
Debug script to check what's actually in the transcript data
"""

import sys
import os
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.fireflies.helpers import get_transcripts_list, get_transcript_content


def debug_transcript():
    """Debug the transcript to see what data we're getting"""
    print("🔍 Debugging Transcript Data")
    print("=" * 50)
    
    try:
        # Get transcript list
        print("📋 Getting transcript list...")
        transcripts = get_transcripts_list()
        
        if not transcripts:
            print("❌ No transcripts found")
            return
            
        print(f"✅ Found {len(transcripts)} transcripts")
        
        # Check first transcript
        first_transcript = transcripts[0]
        transcript_id = first_transcript['id']
        
        print(f"\n📝 First transcript details:")
        print(f"   ID: {transcript_id}")
        print(f"   Title: {first_transcript.get('title', 'No title')}")
        print(f"   Duration: {first_transcript.get('duration', 0)} seconds")
        print(f"   Date: {first_transcript.get('date', 'No date')}")
        print(f"   Participants: {first_transcript.get('participants', [])}")
        
        # Get full transcript content
        print(f"\n🔍 Getting full content for transcript: {transcript_id}")
        transcript_content = get_transcript_content(transcript_id)
        
        print(f"\n📊 Transcript content structure:")
        for key, value in transcript_content.items():
            if key == 'sentences':
                sentences = value or []
                print(f"   {key}: {len(sentences)} sentences")
                if sentences:
                    print(f"      First sentence: {sentences[0]}")
                else:
                    print(f"      ❌ No sentences found!")
            elif isinstance(value, (list, dict)):
                print(f"   {key}: {type(value).__name__} with {len(value) if value else 0} items")
            else:
                print(f"   {key}: {value}")
        
        # Check if sentences exist and show sample
        sentences = transcript_content.get('sentences', [])
        if sentences:
            print(f"\n✅ Found {len(sentences)} sentences")
            print(f"Sample sentences:")
            for i, sentence in enumerate(sentences[:3]):
                speaker = sentence.get('speaker_name', 'Unknown')
                text = sentence.get('text', 'No text')[:100]
                time = sentence.get('start_time', 0)
                print(f"   {i+1}. {speaker} [{time}s]: {text}...")
        else:
            print(f"\n❌ NO SENTENCES FOUND!")
            print("This is why chunking returns 0 chunks.")
            print("\nPossible reasons:")
            print("- Transcript is still being processed by Fireflies")
            print("- Meeting was too short to generate sentences")
            print("- GraphQL query is missing sentence data")
            print("- Audio quality was too poor to transcribe")
        
        # Check summary
        summary = transcript_content.get('summary', {})
        if summary:
            print(f"\n📄 Summary data available:")
            for key, value in summary.items():
                if value:
                    print(f"   {key}: {str(value)[:100]}...")
        else:
            print(f"\n❌ No summary data either")
            
    except Exception as e:
        print(f"❌ Error during debugging: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    debug_transcript()