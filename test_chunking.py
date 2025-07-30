#!/usr/bin/env python3
"""
Test script for transcript chunking function
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.fireflies.helpers import get_transcript_content, chunk_transcript_by_tokens


def create_sample_transcript_data():
    """Create sample transcript data for testing"""
    sample_sentences = []
    
    # Create sample sentences (simulating a 10-minute meeting)
    speakers = ["John", "Sarah", "Mike", "Lisa"]
    sample_texts = [
        "Welcome everyone to today's meeting. Let's start with the project updates.",
        "Thanks John. I've made significant progress on the user interface design.",
        "The new dashboard layout is much more intuitive and user-friendly.",
        "I've also completed the integration with the payment gateway.",
        "That's great Sarah. Mike, how are we doing with the backend development?",
        "We've implemented all the core APIs and they're working perfectly.",
        "The database optimization has improved query performance by 40%.",
        "We should be ready for testing by the end of this week.",
        "Excellent work team. Lisa, what's the status on the marketing campaign?",
        "We've launched the social media campaign and initial response is positive.",
        "The email marketing has a 25% open rate which is above industry average.",
        "We're on track to meet our user acquisition goals for this quarter.",
        "Perfect. Let's discuss the challenges we're facing.",
        "One issue is the mobile responsiveness on older devices.",
        "We might need to spend extra time optimizing for legacy browsers.",
        "Also, the third-party API we're using has some rate limiting issues.",
        "I suggest we implement caching to reduce API calls.",
        "That's a good solution. Let's prioritize these fixes.",
        "We should also consider adding more error handling.",
        "Agreed. Let's schedule a follow-up meeting next week to review progress."
    ]
    
    # Generate sentences with timestamps
    time_counter = 15  # Start at 15 seconds
    for i, text in enumerate(sample_texts):
        speaker = speakers[i % len(speakers)]
        sample_sentences.append({
            "speaker_name": speaker,
            "text": text,
            "start_time": time_counter,
            "end_time": time_counter + 10
        })
        time_counter += 25  # Add 25 seconds between sentences
    
    return {
        "id": "sample_transcript_123",
        "title": "Weekly Team Meeting",
        "sentences": sample_sentences
    }


def test_chunking_function():
    """Test the chunking function with sample data"""
    print("🔧 Testing Transcript Chunking Function")
    print("=" * 50)
    
    # Create sample data
    print("📝 Creating sample transcript data...")
    sample_data = create_sample_transcript_data()
    print(f"   Created transcript with {len(sample_data['sentences'])} sentences")
    
    # Test chunking with different parameters
    test_cases = [
        {"max_tokens": 500, "overlap_tokens": 50, "description": "Small chunks (500 tokens)"},
        {"max_tokens": 1500, "overlap_tokens": 150, "description": "Medium chunks (1500 tokens)"},
        {"max_tokens": 3500, "overlap_tokens": 300, "description": "Large chunks (3500 tokens - default)"}
    ]
    
    for test_case in test_cases:
        print(f"\n📊 Testing: {test_case['description']}")
        try:
            chunks = chunk_transcript_by_tokens(
                sample_data, 
                max_tokens=test_case['max_tokens'],
                overlap_tokens=test_case['overlap_tokens']
            )
            
            print(f"   ✅ Created {len(chunks)} chunks")
            
            for i, chunk in enumerate(chunks):
                print(f"   Chunk {chunk['chunk_id']}:")
                print(f"      - Tokens: {chunk['token_count']}")
                print(f"      - Sentences: {chunk['sentence_count']}")
                print(f"      - Speakers: {chunk['speakers']}")
                print(f"      - Time range: {chunk['time_range']['start_seconds']:.1f}s - {chunk['time_range']['end_seconds']:.1f}s")
                print(f"      - Has overlap: {chunk['has_overlap']}")
                
                # Show first few lines of content
                content_lines = chunk['content'].split('\n')
                first_line = content_lines[0] if content_lines else "No content"
                print(f"      - Content preview: {first_line[:100]}...")
                print()
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("✅ Chunking function testing complete!")


def test_with_real_transcript():
    """Test with real transcript if available"""
    print("\n🌐 Testing with Real Transcript (if available)")
    print("=" * 50)
    
    try:
        # Try to get a real transcript (this will only work if API is configured)
        from app.fireflies.helpers import get_transcripts_list
        
        transcripts = get_transcripts_list()
        if transcripts:
            transcript_id = transcripts[0]['id']
            print(f"📋 Using real transcript: {transcript_id}")
            
            real_transcript = get_transcript_content(transcript_id)
            if real_transcript and real_transcript.get('sentences'):
                chunks = chunk_transcript_by_tokens(real_transcript)
                print(f"   ✅ Successfully chunked real transcript into {len(chunks)} chunks")
                
                # Show summary of first chunk
                if chunks:
                    first_chunk = chunks[0]
                    print(f"   First chunk preview:")
                    print(f"      - Tokens: {first_chunk['token_count']}")
                    print(f"      - Speakers: {first_chunk['speakers']}")
                    print(f"      - Duration: {first_chunk['time_range']['end_seconds'] - first_chunk['time_range']['start_seconds']:.1f}s")
            else:
                print("   ⚠️  Real transcript has no sentences")
        else:
            print("   ⚠️  No real transcripts available")
            
    except Exception as e:
        print(f"   ⚠️  Could not test with real transcript: {str(e)}")
        print("   (This is normal if Fireflies API is not configured)")


if __name__ == "__main__":
    test_chunking_function()
    test_with_real_transcript()