#!/usr/bin/env python3
"""
Test script for AI leadership evaluation function
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.fireflies.helpers import evaluate_chunk_leadership


def test_ai_evaluation():
    """Test the AI evaluation function with sample transcript content"""
    print("🤖 Testing AI Leadership Evaluation Function")
    print("=" * 50)
    
    # Sample transcript content for testing
    sample_chunk = """
John [00:15]: Welcome everyone to today's meeting. Let's start with the project updates.
Sarah [00:25]: Thanks John. I've made significant progress on the user interface design.
Mike [00:35]: That's great Sarah. I think we should also discuss the timeline.
John [00:45]: Good point Mike. Sarah, can you walk us through your timeline?
Sarah [00:55]: Absolutely. I estimate we'll need two more weeks for the UI completion.
John [01:05]: That sounds reasonable. Mike, what's your take on the backend timeline?
Mike [01:15]: I can align with Sarah's timeline. Two weeks should work for integration too.
John [01:25]: Perfect. Let's schedule a follow-up meeting next week to check progress.
"""
    
    test_cases = [
        {
            "role": "Team Lead",
            "company": "Tech Startup",
            "name": "Laurent",
            "description": "Testing with leadership role and sample name"
        },
        {
            "role": "Product Manager", 
            "company": "SaaS Company",
            "name": "Sarah Johnson",
            "description": "Testing with product management role and real name"
        },
        {
            "role": "Team Member",
            "company": "General Business",
            "name": "John Smith",
            "description": "Testing with team member role and personalized name"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📊 Test Case {i}: {test_case['description']}")
        print(f"   Name: {test_case['name']}")
        print(f"   Role: {test_case['role']}")
        print(f"   Company: {test_case['company']}")
        print("-" * 30)
        
        try:
            # Call the AI evaluation function
            result = evaluate_chunk_leadership(
                chunk_content=sample_chunk,
                user_role=test_case['role'],
                company_context=test_case['company'],
                user_name=test_case['name']
            )
            
            # Display results
            print("✅ AI Evaluation Results:")
            
            if "error" in result:
                print(f"   ❌ Error: {result['error']}")
            else:
                print(f"   📈 Overall Score: {result.get('overall_score', 'N/A')}/10")
                
                strengths = result.get('strengths', [])
                print(f"   💪 Strengths ({len(strengths)}):")
                for strength in strengths:
                    print(f"      • {strength}")
                
                improvements = result.get('areas_for_improvement', [])
                print(f"   🔧 Areas for Improvement ({len(improvements)}):")
                for improvement in improvements:
                    print(f"      • {improvement}")
                
                action = result.get('specific_action', 'No action provided')
                print(f"   🎯 Specific Action: {action}")
            
        except Exception as e:
            print(f"   ❌ Test failed with error: {str(e)}")
            import traceback
            print(f"   Full traceback: {traceback.format_exc()}")
        
        print()  # Add spacing between test cases
    
    print("✅ AI Evaluation testing complete!")


if __name__ == "__main__":
    test_ai_evaluation()