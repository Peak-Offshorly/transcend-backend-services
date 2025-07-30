"""
Fireflies Helper Functions - Clean utility functions for transcript operations
"""

from typing import Dict, Any, List
import tiktoken
from .api_client import FirefliesAPIClient
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import PromptTemplate
from app.ai.const import OPENAI_API_KEY


def get_transcripts_list() -> List[Dict[str, Any]]:
    """
    Get list of 10 most recent transcripts with metadata
    
    Returns:
        List of transcript dictionaries with metadata
        
    Raises:
        Exception: If API request fails
    """
    client = FirefliesAPIClient()
    
    query = """
    query Transcripts {
        transcripts(limit: 10) {
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
        }
    }
    """
    
    result = client._make_request(query)
    return result.get("data", {}).get("transcripts", [])


def get_transcript_content(transcript_id: str) -> Dict[str, Any]:
    """
    Get the full transcript content including sentences and speakers
    
    Args:
        transcript_id: The ID of the transcript to fetch
        
    Returns:
        Dict containing transcript content with sentences
        
    Raises:
        Exception: If API request fails
    """
    client = FirefliesAPIClient()
    
    query = f"""
    query GetTranscriptContent {{
        transcript(id: "{transcript_id}") {{
            id
            title
            date
            duration
            participants
            summary {{
                overview
                action_items
                keywords
                bullet_gist
                gist
                outline
            }}
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
    
    result = client._make_request(query)
    return result.get("data", {}).get("transcript", {})


def chunk_transcript_by_tokens(
    transcript_data: Dict[str, Any], 
    max_tokens: int = 4000,
    overlap_tokens: int = 300
) -> List[Dict[str, Any]]:
    """
    Chunk transcript content by token count for AI processing
    
    Args:
        transcript_data: The full transcript data from get_transcript_content()
        max_tokens: Maximum tokens per chunk (default: 3500)
        overlap_tokens: Overlap tokens between chunks (default: 300)
        
    Returns:
        List of transcript chunks with metadata
        
    Example:
        [
            {
                "chunk_id": 1,
                "content": "Speaker A [00:15]: Hello everyone...",
                "token_count": 3420,
                "speakers": ["Speaker A", "Speaker B"],
                "time_range": {"start_seconds": 15.2, "end_seconds": 425.8},
                "sentence_count": 45,
                "has_overlap": False
            }
        ]
    """
    # Initialize tokenizer (using GPT-4 encoding for consistency)
    tokenizer = tiktoken.get_encoding("cl100k_base")
    
    # Extract sentences from transcript
    sentences = transcript_data.get('sentences', [])
    if not sentences:
        return []
    
    chunks = []
    current_chunk_content = []
    current_chunk_tokens = 0
    chunk_id = 0
    overlap_content = []
    overlap_token_count = 0
    
    for sentence in sentences:
        speaker_name = sentence.get('speaker_name', 'Unknown')
        text = sentence.get('text', '').strip()
        start_time = sentence.get('start_time', 0)
        
        if not text:
            continue
            
        # Format sentence with speaker and timestamp
        time_formatted = f"{int(start_time // 60):02d}:{int(start_time % 60):02d}"
        formatted_sentence = f"{speaker_name} [{time_formatted}]: {text}"
        
        # Count tokens for this sentence
        sentence_tokens = len(tokenizer.encode(formatted_sentence))
        
        # Check if adding this sentence would exceed max tokens
        if current_chunk_tokens + sentence_tokens > max_tokens and current_chunk_content:
            # Create chunk from current content
            chunk_content = "\n".join(current_chunk_content)
            chunk_speakers = list(set([sent.split(' [')[0] for sent in current_chunk_content]))
            
            # Get time range for chunk
            first_sentence_time = float(current_chunk_content[0].split('[')[1].split(']:')[0].replace(':', '')) if current_chunk_content else 0
            last_sentence_time = start_time
            
            chunk_id += 1
            chunks.append({
                "chunk_id": chunk_id,
                "content": chunk_content,
                "token_count": current_chunk_tokens,
                "speakers": chunk_speakers,
                "time_range": {
                    "start_seconds": first_sentence_time,
                    "end_seconds": last_sentence_time
                },
                "sentence_count": len(current_chunk_content),
                "has_overlap": len(overlap_content) > 0
            })
            
            # Prepare overlap for next chunk
            overlap_content = []
            overlap_token_count = 0
            
            # Take last few sentences as overlap for next chunk if needed
            if overlap_tokens > 0:
                for i in range(len(current_chunk_content) - 1, -1, -1):
                    sentence_content = current_chunk_content[i]
                    sentence_token_count = len(tokenizer.encode(sentence_content))
                    
                    if overlap_token_count + sentence_token_count <= overlap_tokens:
                        overlap_content.insert(0, sentence_content)
                        overlap_token_count += sentence_token_count
                    else:
                        break
            
            # Start new chunk with overlap
            current_chunk_content = overlap_content.copy()
            current_chunk_tokens = overlap_token_count
        
        # Add current sentence to chunk
        current_chunk_content.append(formatted_sentence)
        current_chunk_tokens += sentence_tokens
    
    # Add final chunk if there's remaining content
    if current_chunk_content:
        chunk_content = "\n".join(current_chunk_content)
        chunk_speakers = list(set([sent.split(' [')[0] for sent in current_chunk_content]))
        
        # Get time range for final chunk
        first_sentence_time = 0
        last_sentence_time = sentences[-1].get('start_time', 0) if sentences else 0
        
        try:
            if current_chunk_content:
                time_str = current_chunk_content[0].split('[')[1].split(']:')[0]
                if ':' in time_str:
                    parts = time_str.split(':')
                    first_sentence_time = int(parts[0]) * 60 + int(parts[1])
        except:
            first_sentence_time = 0
        
        chunk_id += 1
        chunks.append({
            "chunk_id": chunk_id,
            "content": chunk_content,
            "token_count": current_chunk_tokens,
            "speakers": chunk_speakers,
            "time_range": {
                "start_seconds": first_sentence_time,
                "end_seconds": last_sentence_time
            },
            "sentence_count": len(current_chunk_content),
            "has_overlap": len(overlap_content) > 0
        })
    
    return chunks


def evaluate_chunk_leadership(
    chunk_content: str,
    user_role: str = "Team Member",
    company_context: str = "General Business",
    user_name: str = "Laurent"
) -> Dict[str, Any]:
    """
    Evaluate a transcript chunk for leadership behaviors using GPT-4o mini
    
    Args:
        chunk_content: The transcript content to evaluate
        user_role: The user's role in the organization
        company_context: Company/industry context for relevant advice
        user_name: The user's name for personalized feedback (default: "Laurent")
        
    Returns:
        Dict containing leadership assessment and coaching advice
        
    Example:
        {
            "strengths": ["Laurent showed clear communication", "Active listening"],
            "areas_for_improvement": ["Laurent could improve decision-making speed"],
            "specific_action": "Laurent should schedule 1:1s with team members weekly",
            "overall_score": 7.5
        }
    """
    # Use GPT-4o mini for cost efficiency
    llm = ChatOpenAI(
        model="gpt-4o-mini", 
        openai_api_key=OPENAI_API_KEY, 
        temperature=0.3
    )
    
    prompt_template = PromptTemplate(
        template="""
        You are an expert leadership coach analyzing {user_name}'s meeting performance. 
        
        Evaluate this transcript chunk for {user_name}'s leadership behaviors and provide specific improvement advice.
        Focus on: communication style, decision-making, team engagement, and meeting facilitation.
        
        Consider {user_name}'s role: {user_role}
        Company context: {company_context}
        
        Transcript content:
        {chunk_content}
        
        Provide your assessment in JSON format with:
        - "strengths": Array of 2-3 observed leadership strengths with brief explanations (reference {user_name} by name)
        - "areas_for_improvement": Array of 2-3 specific areas for {user_name} to develop with context
        - "specific_action": One concrete, actionable next step {user_name} can take (address them directly by name)
        - "overall_score": Numeric score from 1-10 for {user_name}'s overall leadership effectiveness in this interaction
        
        Keep feedback constructive, specific, and actionable. Address {user_name} directly in your recommendations. Base your assessment only on observable behaviors in the transcript.
        """,
        input_variables=["chunk_content", "user_role", "company_context", "user_name"]
    )
    
    try:
        chain = prompt_template | llm | JsonOutputParser()
        
        response = chain.invoke({
            "chunk_content": chunk_content,
            "user_role": user_role,
            "company_context": company_context,
            "user_name": user_name
        })
        
        return response
        
    except Exception as e:
        # Return error response if AI evaluation fails
        return {
            "error": f"AI evaluation failed: {str(e)}",
            "strengths": [],
            "areas_for_improvement": [],
            "specific_action": "Unable to provide recommendation due to evaluation error",
            "overall_score": 0
        }