"""
Fireflies Helper Functions - Clean utility functions for transcript operations
"""

from typing import Dict, Any, List, Tuple
import tiktoken
import asyncio
import time
from .api_client import FirefliesAPIClient
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import PromptTemplate
from app.ai.const import OPENAI_API_KEY
from sqlalchemy.orm import Session
from app.utils.dev_plan_crud import dev_plan_get_current
from app.utils.traits_crud import chosen_traits_get


# Model pricing configurations (USD per 1M tokens)
MODEL_PRICING = {
    "gpt-4o-mini": {
        "input": 0.60,
        "cached_input": 0.30,
        "output": 2.40
    },
    "gpt-4.1-nano": {  # Future model - commented out for now
        "input": 0.100,
        "cached_input": 0.025,
        "output": 0.400
    },
    "gpt-4.1-mini": {  # Future model - commented out for now
        "input": 0.400,
        "cached_input": 0.100,
        "output": 1.600
    },
    "chatgpt-4o-latest": {  # Current model in use
        "input": 5.000,
        "cached_input": 0.000,
        "output": 15.000
    },
    "gpt-4.1": {
        "input": 2.000,
        "cached_input": 0.5,
        "output": 8.00
    },
}

# Current model in use - easy to switch when migrating to 4.1 nano
CURRENT_MODEL = "gpt-4.1"  # Switched from "gpt-4o-mini"


def get_model_pricing() -> Dict[str, float]:
    """
    Get pricing configuration for the current model

    Returns:
        Dict containing input and output token pricing
    """
    return MODEL_PRICING.get(CURRENT_MODEL, MODEL_PRICING["gpt-4o-mini"])


def calculate_token_cost(input_tokens: int, output_tokens: int, model: str = None) -> Dict[str, float]:
    """
    Calculate cost for given token usage

    Args:
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens generated
        model: Model name (defaults to CURRENT_MODEL)

    Returns:
        Dict with cost breakdown
    """
    model_name = model or CURRENT_MODEL
    pricing = MODEL_PRICING.get(model_name, MODEL_PRICING["gpt-4o-mini"])

    input_cost = (input_tokens * pricing["input"]) / 1_000_000
    output_cost = (output_tokens * pricing["output"]) / 1_000_000
    total_cost = input_cost + output_cost

    return {
        "input_cost_usd": round(input_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "total_cost_usd": round(total_cost, 6)
    }


def estimate_tokens_with_tiktoken(text: str) -> int:
    """
    Estimate token count using tiktoken as fallback

    Args:
        text: Text to count tokens for

    Returns:
        Estimated token count
    """
    try:
        tokenizer = tiktoken.get_encoding("cl100k_base")
        return len(tokenizer.encode(text))
    except Exception:
        # Rough fallback: ~4 characters per token
        return len(text) // 4


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
            chunk_speakers = list(
                set([sent.split(' [')[0] for sent in current_chunk_content]))

            # Get time range for chunk
            first_sentence_time = float(current_chunk_content[0].split('[')[1].split(']:')[
                                        0].replace(':', '')) if current_chunk_content else 0
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
                    sentence_token_count = len(
                        tokenizer.encode(sentence_content))

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
        chunk_speakers = list(set([sent.split(' [')[0]
                              for sent in current_chunk_content]))

        # Get time range for final chunk
        first_sentence_time = 0
        last_sentence_time = sentences[-1].get(
            'start_time', 0) if sentences else 0

        try:
            if current_chunk_content:
                time_str = current_chunk_content[0].split(
                    '[')[1].split(']:')[0]
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


def count_transcript_sentences(transcript_data: Dict[str, Any]) -> int:
    """
    Count the number of sentences in a transcript

    Args:
        transcript_data: The full transcript data from get_transcript_content()

    Returns:
        Number of sentences in the transcript
    """
    if not transcript_data:
        return 0

    sentences = transcript_data.get('sentences')
    if sentences is None:
        return 0

    return len(sentences)


# def evaluate_chunk_leadership(
#     chunk_content: str,
#     user_role: str = "Team Member",
#     company_context: str = "General Business",
#     user_name: str = "Laurent"
# ) -> Dict[str, Any]:
#     """
#     Evaluate a transcript chunk for leadership behaviors using GPT-4o mini

#     Args:
#         chunk_content: The transcript content to evaluate
#         user_role: The user's role in the organization
#         company_context: Company/industry context for relevant advice
#         user_name: The user's name for personalized feedback (default: "Laurent")

#     Returns:
#         Dict containing leadership assessment and coaching advice

#     Example:
#         {
#             "strengths": ["Laurent showed clear communication", "Active listening"],
#             "areas_for_improvement": ["Laurent could improve decision-making speed"],
#             "specific_action": "Laurent should schedule 1:1s with team members weekly",
#             "overall_score": 7.5
#         }
#     """
#     # Use GPT-4o mini for cost efficiency
#     llm = ChatOpenAI(
#         model="gpt-4o-mini",
#         openai_api_key=OPENAI_API_KEY,
#         temperature=0.3
#     )

#     prompt_template = PromptTemplate(
#         template="""
#         You are an expert leadership coach analyzing {user_name}'s meeting performance. 

#         **IMPORTANT: First, check if {user_name} speaks or participates in this transcript chunk.**

#         If {user_name} does NOT appear in the transcript:
#         - Clearly state that {user_name} did not speak during this portion of the meeting
#         - Analyze whether this silence was appropriate or problematic based on:
#         * The meeting content and context
#         * {user_name}'s role and expected participation level
#         * Whether this was a moment requiring their input, decision-making, or leadership
#         * The flow of conversation and natural speaking opportunities

#         If {user_name} DOES appear in the transcript:
#         - Evaluate their leadership behaviors and provide specific improvement advice
#         - Focus on: communication style, decision-making, team engagement, and meeting facilitation

#         Consider {user_name}'s role: {user_role}
#         Company context: {company_context}

#         Transcript content:
#         {chunk_content}

#         Provide your assessment in JSON format with:

#         **If {user_name} did not speak:**
#         - "participation_status": "silent"
#         - "silence_analysis": Brief explanation of why {user_name} didn't participate in this segment
#         - "silence_assessment": "appropriate" or "missed_opportunity" with reasoning
#         - "recommended_action": One specific suggestion for how {user_name} could have engaged (if silence was problematic) or affirmation of good judgment (if silence was appropriate)
#         - "overall_score": Numeric score from 1-10 for {user_name}'s participation decision in this interaction

#         **If {user_name} did speak:**
#         - "participation_status": "active"
#         - "strengths": Array of 2-3 observed leadership strengths with brief explanations (reference {user_name} by name)
#         - "areas_for_improvement": Array of 2-3 specific areas for {user_name} to develop with context
#         - "specific_action": One concrete, actionable next step {user_name} can take (address them directly by name)
#         - "overall_score": Numeric score from 1-10 for {user_name}'s overall leadership effectiveness in this interaction

#         Keep feedback constructive, specific, and actionable. Address {user_name} directly in your recommendations. Base your assessment only on observable behaviors and participation patterns in the transcript. Remember that strategic silence can be as important as active participation in leadership.
#         """,
#         input_variables=["chunk_content", "user_role",
#                          "company_context", "user_name"]
#     )

#     try:
#         chain = prompt_template | llm | JsonOutputParser()

#         response = chain.invoke({
#             "chunk_content": chunk_content,
#             "user_role": user_role,
#             "company_context": company_context,
#             "user_name": user_name
#         })

#         return response

#     except Exception as e:
#         # Return error response if AI evaluation fails
#         return {
#             "error": f"AI evaluation failed: {str(e)}",
#             "strengths": [],
#             "areas_for_improvement": [],
#             "specific_action": "Unable to provide recommendation due to evaluation error",
#             "overall_score": 0
        # }


async def evaluate_chunk_leadership_async(
    chunk_content: str,
    user_role: str = "Team Member",
    company_context: str = "General Business",
    user_name: str = "",
    db: Session = None,
    user_id: str = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Async version of evaluate_chunk_leadership for concurrent processing with token usage tracking

    Args:
        chunk_content: The transcript content to evaluate
        user_role: The user's role in the organization
        company_context: Company/industry context for relevant advice
        user_name: The user's name for personalized feedback (default: "Laurent")
        db: Database session for fetching user traits (optional)
        user_id: User ID for fetching chosen traits (optional)

    Returns:
        Tuple of (evaluation_result, token_usage_info)
    """
    # Initialize chosen traits variables
    strength_name = None
    weakness_name = None

    # Get user's chosen traits if database access is available
    if db and user_id:
        try:
            # Get user's current development plan
            current_dev_plan = await dev_plan_get_current(db=db, user_id=user_id)
            if current_dev_plan:
                dev_plan_id = str(current_dev_plan["dev_plan_id"])

                # Get user's chosen traits (strength and weakness)
                chosen_traits = chosen_traits_get(
                    db=db, user_id=user_id, dev_plan_id=dev_plan_id)
                if chosen_traits:
                    strength_name = chosen_traits["chosen_strength"]["name"]
                    weakness_name = chosen_traits["chosen_weakness"]["name"]
        except Exception as e:
            # If traits fetching fails, continue without them
            print(f"Warning: Could not fetch user traits: {str(e)}")
    
    # Use GPT-4o mini for cost efficiency
    llm = ChatOpenAI(
        model="gpt-4.1-nano",
        openai_api_key=OPENAI_API_KEY,
        temperature=0.3
    )

    prompt_template = PromptTemplate(
        template="""
        You are an expert leadership coach specializing in real-time communication analysis. Your role is to provide specific, actionable feedback on {user_name}'s actual dialogue and leadership behavior during this meeting segment.

        **Leadership Context:**
        - Name: {user_name}
        - Role: {user_role}
        - Company: {company_context}
        {development_focus_context}

        **Meeting Transcript Segment:**
        {chunk_content}

        **ANALYSIS INSTRUCTIONS:**

        1. **First, determine {user_name}'s participation level in this segment**
        
        2. **Focus on leadership communication, NOT task management**
        - Analyze HOW they communicated, not WHAT tasks were discussed
        - Ignore action items like "finish report," "send to Bill," etc.
        - Focus on influence, persuasion, team dynamics, decision-making style

        3. **Provide evidence-based coaching tied to their development goals**

        **OUTPUT FORMAT (JSON):**

        **If {user_name} was SILENT in this segment:**
        {{
            "participation_status": "silent",
            "segment_context": "Brief description of what was being discussed during their silence",
            "silence_evaluation": {{
                "assessment": "strategic_listening" | "missed_leadership_opportunity" | "appropriate_restraint",
                "reasoning": "Specific explanation based on meeting content and their role"
            }},
            "development_insights": {{
                "strength_application": "How their {strength_name} could have been leveraged in this moment",
                "growth_opportunity": "Specific way their {weakness_name} manifested or could be addressed",
                "recommended_intervention": "Exact words or approach they could have used"
            }},
            "coaching_feedback": "Direct, specific guidance on when and how to engage in similar future scenarios"
        }}

        **If {user_name} was ACTIVE in this segment:**
        {{
            "participation_status": "active",
            "dialogue_analysis": {{
                "effective_moments": [
                    {{
                        "quote": "Exact words they said",
                        "leadership_technique": "Specific technique demonstrated (e.g., 'active listening,' 'stakeholder alignment,' 'decisive communication')",
                        "why_effective": "How this advanced their leadership goals"
                    }}
                ],
                "improvement_opportunities": [
                    {{
                        "what_they_said": "Exact quote",
                        "missed_technique": "Leadership technique they could have applied",
                        "alternative_approach": "Specific words/phrases they could have used instead",
                        "potential_impact": "How this change would have improved the outcome"
                    }}
                ]
            }},
            "development_progress": {{
                "strength_demonstration": "Specific examples of how they leveraged their {strength_name} in their actual words",
                "growth_area_progress": "Evidence of improvement or continued challenge with {weakness_name}",
                "development_recommendation": "Specific communication techniques to practice for next meeting"
            }},
            "communication_patterns": {{
                "positive_patterns": "Recurring effective communication behaviors observed",
                "limiting_patterns": "Communication habits that may be hindering their leadership effectiveness"
            }},
            "coaching_feedback": "Specific, actionable advice for improving their communication approach in similar future situations"
        }}

        **COACHING STANDARDS:**
        - Ground ALL feedback in actual transcript evidence
        - Focus on communication style, influence techniques, and team dynamics
        - Tie insights directly to their stated development goals ({strength_name} and {weakness_name})
        - Provide specific alternative phrasings when suggesting improvements
        - Avoid generic leadership advice - make it specific to their actual behavior
        - Remember: Leadership development is about HOW they communicate, not WHAT tasks they manage
        """,
        input_variables=["chunk_content", "user_role", "company_context", "user_name", "development_focus_context", "strength_name", "weakness_name"]
    )
    try:
        # Create chain without JsonOutputParser to access raw response
        chain = prompt_template | llm

        # Create development focus context if traits are available
        development_focus_context = ""
        if strength_name and weakness_name:
            development_focus_context = f"""

                {user_name}'s Current Development Focus:
                - Strength to leverage: {strength_name}
                - Area to improve: {weakness_name}

                Please provide specific feedback on how {user_name} demonstrated progress or opportunities in these areas during this segment.
            """

       
        # Use ainvoke for async execution and get raw response
        raw_response = await chain.ainvoke({
            "chunk_content": chunk_content,
            "user_role": user_role,
            "development_focus_context": development_focus_context,
            "company_context": company_context,
            "user_name": user_name,
            "strength_name": strength_name,
            "weakness_name": weakness_name
        })

        # Extract token usage from response metadata
        token_usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0
        }

        # Try to get token usage from response metadata
        if hasattr(raw_response, 'usage_metadata') and raw_response.usage_metadata:
            token_usage = {
                "input_tokens": raw_response.usage_metadata.get('input_tokens', 0),
                "output_tokens": raw_response.usage_metadata.get('output_tokens', 0),
                "total_tokens": raw_response.usage_metadata.get('total_tokens', 0)
            }
        elif hasattr(raw_response, 'response_metadata') and raw_response.response_metadata:
            # Fallback to response_metadata
            usage_info = raw_response.response_metadata.get('token_usage', {})
            token_usage = {
                "input_tokens": usage_info.get('prompt_tokens', 0),
                "output_tokens": usage_info.get('completion_tokens', 0),
                "total_tokens": usage_info.get('total_tokens', 0)
            }
        else:
            # Fallback: estimate input tokens using tiktoken
            estimated_input = estimate_tokens_with_tiktoken(chunk_content)
            token_usage["input_tokens"] = estimated_input

        # Parse the JSON response
        parser = JsonOutputParser()
        evaluation_result = parser.parse(raw_response.content)

        # Calculate cost for this evaluation
        cost_info = calculate_token_cost(
            token_usage["input_tokens"],
            token_usage["output_tokens"],
            CURRENT_MODEL
        )

        # Combine token usage with cost info
        usage_info = {
            **token_usage,
            **cost_info,
            "model_used": CURRENT_MODEL
        }

        return evaluation_result, usage_info

    except Exception as e:
        # Return error response if AI evaluation fails
        error_result = {
            "error": f"AI evaluation failed: {str(e)}",
            "strengths": [],
            "areas_for_improvement": [],
            "specific_action": "Unable to provide recommendation due to evaluation error",
            "overall_score": 0
        }

        # Estimate token usage for error case
        estimated_input = estimate_tokens_with_tiktoken(chunk_content)
        error_usage = {
            "input_tokens": estimated_input,
            "output_tokens": 0,
            "total_tokens": estimated_input,
            "input_cost_usd": 0.0,
            "output_cost_usd": 0.0,
            "total_cost_usd": 0.0,
            "model_used": CURRENT_MODEL
        }

        return error_result, error_usage


async def evaluate_chunks_concurrently(
    chunks: List[Dict[str, Any]],
    user_role: str = "Team Member",
    company_context: str = "General Business",
    user_name: str = "Laurent",
    concurrency_limit: int = 5,
    timeout_seconds: int = 30,
    db: Session = None,
    user_id: str = None
) -> Dict[str, Any]:
    """
    Evaluate multiple transcript chunks concurrently with comprehensive usage tracking

    Args:
        chunks: List of transcript chunks from chunk_transcript_by_tokens()
        user_role: The user's role in the organization
        company_context: Company/industry context for relevant advice
        user_name: The user's name for personalized feedback
        concurrency_limit: Maximum number of concurrent evaluations (default: 5)
        timeout_seconds: Timeout for each evaluation task (default: 30)
        db: Database session for fetching user traits (optional)
        user_id: User ID for fetching chosen traits (optional)

    Returns:
        Dict containing AI evaluations and comprehensive usage analytics

    Example:
        {
            "ai_evaluations": [...],
            "usage_analytics": {
                "model_used": "gpt-4o-mini",
                "total_chunks_processed": 5,
                "token_usage": {...},
                "cost_breakdown": {...},
                "per_chunk_details": [...],
                "performance_metrics": {...}
            }
        }
    """
    if not chunks:
        return {
            "ai_evaluations": [],
            "usage_analytics": {
                "model_used": CURRENT_MODEL,
                "total_chunks_processed": 0,
                "token_usage": {"total_input_tokens": 0, "total_output_tokens": 0, "total_tokens": 0},
                "cost_breakdown": {"input_cost_usd": 0.0, "output_cost_usd": 0.0, "total_cost_usd": 0.0},
                "per_chunk_details": [],
                "performance_metrics": {"total_processing_time_seconds": 0.0, "average_time_per_chunk": 0.0}
            }
        }

    # Start timing
    start_time = time.time()

    # Pre-allocate results arrays (pigeonhole method)
    ai_evaluations = [None] * len(chunks)
    usage_details = [None] * len(chunks)

    # Create semaphore to limit concurrent evaluations
    semaphore = asyncio.Semaphore(concurrency_limit)

    async def evaluate_single_chunk(chunk: Dict[str, Any]) -> None:
        """Evaluate a single chunk with usage tracking and place result in correct pigeonhole"""
        chunk_start_time = time.time()
        async with semaphore:
            try:
                # Add timeout to prevent hanging
                evaluation_result, usage_info = await asyncio.wait_for(
                    evaluate_chunk_leadership_async(
                        chunk_content=chunk['content'],
                        user_role=user_role,
                        company_context=company_context,
                        user_name=user_name,
                        db=db,
                        user_id=user_id
                    ),
                    timeout=timeout_seconds
                )

                chunk_processing_time = time.time() - chunk_start_time

                # Place results in correct pigeonhole (chunk_id - 1 because chunk_id starts from 1)
                chunk_index = chunk['chunk_id'] - 1
                ai_evaluations[chunk_index] = {
                    "chunk_id": chunk['chunk_id'],
                    "leadership_assessment": evaluation_result
                }

                # Store usage details with processing time
                usage_details[chunk_index] = {
                    "chunk_id": chunk['chunk_id'],
                    "processing_time_seconds": round(chunk_processing_time, 2),
                    **usage_info
                }

                print(f"✅ Completed evaluation for chunk {chunk['chunk_id']} - "
                      f"Tokens: {usage_info.get('total_tokens', 0)}, "
                      f"Cost: ${usage_info.get('total_cost_usd', 0):.6f}, "
                      f"Time: {chunk_processing_time:.1f}s")

            except asyncio.TimeoutError:
                chunk_processing_time = time.time() - chunk_start_time
                print(
                    f"⚠️ Timeout evaluating chunk {chunk['chunk_id']} after {chunk_processing_time:.1f}s")
                chunk_index = chunk['chunk_id'] - 1

                ai_evaluations[chunk_index] = {
                    "chunk_id": chunk['chunk_id'],
                    "leadership_assessment": {
                        "error": f"Evaluation timed out after {timeout_seconds} seconds",
                        "strengths": [],
                        "areas_for_improvement": [],
                        "specific_action": "Unable to provide recommendation due to timeout",
                        "overall_score": 0
                    }
                }

                # Estimate token usage for timeout case
                estimated_input = estimate_tokens_with_tiktoken(
                    chunk['content'])
                usage_details[chunk_index] = {
                    "chunk_id": chunk['chunk_id'],
                    "processing_time_seconds": round(chunk_processing_time, 2),
                    "input_tokens": estimated_input,
                    "output_tokens": 0,
                    "total_tokens": estimated_input,
                    "input_cost_usd": 0.0,
                    "output_cost_usd": 0.0,
                    "total_cost_usd": 0.0,
                    "model_used": CURRENT_MODEL,
                    "error": "timeout"
                }

            except Exception as e:
                chunk_processing_time = time.time() - chunk_start_time
                print(
                    f"⚠️ Failed to evaluate chunk {chunk['chunk_id']}: {str(e)} (after {chunk_processing_time:.1f}s)")
                chunk_index = chunk['chunk_id'] - 1

                ai_evaluations[chunk_index] = {
                    "chunk_id": chunk['chunk_id'],
                    "leadership_assessment": {
                        "error": f"Evaluation failed: {str(e)}",
                        "strengths": [],
                        "areas_for_improvement": [],
                        "specific_action": "Unable to provide recommendation",
                        "overall_score": 0
                    }
                }

                # Estimate token usage for error case
                estimated_input = estimate_tokens_with_tiktoken(
                    chunk['content'])
                usage_details[chunk_index] = {
                    "chunk_id": chunk['chunk_id'],
                    "processing_time_seconds": round(chunk_processing_time, 2),
                    "input_tokens": estimated_input,
                    "output_tokens": 0,
                    "total_tokens": estimated_input,
                    "input_cost_usd": 0.0,
                    "output_cost_usd": 0.0,
                    "total_cost_usd": 0.0,
                    "model_used": CURRENT_MODEL,
                    "error": str(e)
                }

    # Create tasks for all chunks
    tasks = [evaluate_single_chunk(chunk) for chunk in chunks]

    # Execute all evaluations concurrently
    print(
        f"🚀 Starting concurrent evaluation of {len(chunks)} chunks (max {concurrency_limit} at a time)")
    print(f"   Model: {CURRENT_MODEL}")
    print(
        f"   Current pricing: ${get_model_pricing()['input']:.2f}/1M input, ${get_model_pricing()['output']:.2f}/1M output")

    await asyncio.gather(*tasks, return_exceptions=True)

    # Calculate total processing time
    total_processing_time = time.time() - start_time

    # Filter out any None values and aggregate usage statistics
    completed_evaluations = [
        eval for eval in ai_evaluations if eval is not None]
    completed_usage = [usage for usage in usage_details if usage is not None]

    # Aggregate token usage and costs
    total_input_tokens = sum(usage.get('input_tokens', 0)
                             for usage in completed_usage)
    total_output_tokens = sum(usage.get('output_tokens', 0)
                              for usage in completed_usage)
    total_tokens = total_input_tokens + total_output_tokens
    total_cost = sum(usage.get('total_cost_usd', 0)
                     for usage in completed_usage)

    # Calculate aggregated cost breakdown
    aggregated_cost = calculate_token_cost(
        total_input_tokens, total_output_tokens, CURRENT_MODEL)

    # Create comprehensive usage analytics
    usage_analytics = {
        "model_used": CURRENT_MODEL,
        "total_chunks_processed": len(completed_evaluations),
        "chunks_requested": len(chunks),
        "success_rate": len(completed_evaluations) / len(chunks) if chunks else 0,
        "token_usage": {
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_tokens": total_tokens,
            "average_tokens_per_chunk": total_tokens / len(completed_evaluations) if completed_evaluations else 0
        },
        "cost_breakdown": {
            "input_cost_usd": aggregated_cost['input_cost_usd'],
            "output_cost_usd": aggregated_cost['output_cost_usd'],
            "total_cost_usd": aggregated_cost['total_cost_usd'],
            "average_cost_per_chunk": aggregated_cost['total_cost_usd'] / len(completed_evaluations) if completed_evaluations else 0
        },
        "per_chunk_details": completed_usage,
        "performance_metrics": {
            "total_processing_time_seconds": round(total_processing_time, 2),
            "average_time_per_chunk": round(total_processing_time / len(chunks), 2) if chunks else 0,
            "chunks_per_second": round(len(completed_evaluations) / total_processing_time, 2) if total_processing_time > 0 else 0
        }
    }

    print(
        f"✅ Completed {len(completed_evaluations)}/{len(chunks)} evaluations")
    print(
        f"   Total tokens: {total_tokens:,} (input: {total_input_tokens:,}, output: {total_output_tokens:,})")
    print(f"   Total cost: ${aggregated_cost['total_cost_usd']:.6f}")
    print(
        f"   Processing time: {total_processing_time:.2f}s ({total_processing_time/len(chunks):.2f}s/chunk)")

    return {
        "ai_evaluations": completed_evaluations,
        "usage_analytics": usage_analytics
    }


async def summarize_evaluated_chunks(
    evaluated_chunks_data: Dict[str, Any],
    user_name: str = "Laurent",
    user_role: str = "Team Member",
    company_context: str = "General Business",
    transcript_metadata: Dict[str, Any] = None,
    db: Session = None,
    user_id: str = None
) -> Dict[str, Any]:
    """
    Summarize evaluated transcript chunks into an overall leadership assessment

    Args:
        evaluated_chunks_data: Output from evaluate_chunks_concurrently() containing ai_evaluations
        user_name: The user's name for personalized feedback
        user_role: The user's role in the organization
        company_context: Company/industry context for relevant advice
        transcript_metadata: Optional metadata about the transcript (title, date, participants, etc.)

    Returns:
        Dict containing overall leadership assessment and usage analytics

    Example:
        {
            "overall_leadership_assessment": "Hi Laurent, based on your meeting participation, I observed some strong leadership qualities...",
            "usage_analytics": {...}
        }
    """
    # Initialize chosen traits variables
    strength_name = None
    weakness_name = None

    # Get user's chosen traits if database access is available
    if db and user_id:
        try:
            # Get user's current development plan
            current_dev_plan = await dev_plan_get_current(db=db, user_id=user_id)
            if current_dev_plan:
                dev_plan_id = str(current_dev_plan["dev_plan_id"])

                # Get user's chosen traits (strength and weakness)
                chosen_traits = chosen_traits_get(
                    db=db, user_id=user_id, dev_plan_id=dev_plan_id)
                if chosen_traits:
                    strength_name = chosen_traits["chosen_strength"]["name"]
                    weakness_name = chosen_traits["chosen_weakness"]["name"]
        except Exception as e:
            # If traits fetching fails, continue without them
            print(f"Warning: Could not fetch user traits: {str(e)}")

    # Extract AI evaluations from the input data
    ai_evaluations = evaluated_chunks_data.get('ai_evaluations', [])

    if not ai_evaluations:
        return {
            "overall_leadership_assessment": "I don't have any meeting data to analyze at the moment. Please ensure your meeting transcript was processed successfully and try again.",
            "usage_analytics": {
                "model_used": CURRENT_MODEL
            }
        }

    # Prepare the summary content from all evaluated chunks
    chunks_summary = []
    participation_count = 0
    total_scores = []
    all_strengths = []
    all_improvements = []
    all_actions = []

    for eval_data in ai_evaluations:
        chunk_id = eval_data.get('chunk_id', 'Unknown')
        assessment = eval_data.get('leadership_assessment', {})

        # Skip chunks with errors
        if 'error' in assessment:
            continue

        # Collect data for summary
        participation_status = assessment.get(
            'participation_status', 'unknown')
        if participation_status == 'active':
            participation_count += 1

        score = assessment.get('overall_score', 0)
        if score > 0:
            total_scores.append(score)

        # Collect qualitative feedback
        strengths = assessment.get('strengths', [])
        improvements = assessment.get('areas_for_improvement', [])
        action = assessment.get('specific_action', '')

        if isinstance(strengths, list):
            all_strengths.extend(strengths)
        if isinstance(improvements, list):
            all_improvements.extend(improvements)
        if action:
            all_actions.append(action)

        # Create chunk summary for context
        chunk_summary = f"Chunk {chunk_id}: {participation_status}"
        if participation_status == 'active':
            chunk_summary += f" (Score: {score}/10)"
        chunks_summary.append(chunk_summary)

    # Create the prompt content
    chunks_context = "\n".join(chunks_summary)
    # Limit for token efficiency
    strengths_context = "\n".join(
        f"- {strength}" for strength in all_strengths[:10])
    improvements_context = "\n".join(
        f"- {improvement}" for improvement in all_improvements[:10])
    actions_context = "\n".join(f"- {action}" for action in all_actions[:5])

    # Add transcript metadata context if available
    metadata_context = ""
    if transcript_metadata:
        title = transcript_metadata.get('title', 'Untitled Meeting')
        duration = transcript_metadata.get('duration', 0)
        participants = transcript_metadata.get('participants', [])
        metadata_context = f"""
Meeting Context:
- Title: {title}
- Duration: {duration} seconds
- Participants: {len(participants)} people
        """

    # Add development focus context if traits are available
    development_focus_context = ""
    if strength_name and weakness_name:
        development_focus_context = f"""

{user_name}'s Current Development Focus:
- Strength to leverage: {strength_name}
- Area to improve: {weakness_name}

Please provide specific feedback on how {user_name} demonstrated progress or opportunities in these areas during the meeting.
        """

    # Use the current model for summarization
    llm = ChatOpenAI(
        model=CURRENT_MODEL,
        openai_api_key=OPENAI_API_KEY,
        temperature=0.3
    )

    prompt_template = PromptTemplate(
        template="""
        You are {user_name}'s personal leadership coach providing specific feedback on their actual contributions during this meeting.

        {user_name} is a {user_role} in a {company_context} context.
        {metadata_context}
        {development_focus_context}

        I have analyzed your participation across multiple segments of the meeting. Here's the segment-by-segment data:

        PARTICIPATION SUMMARY:
        {chunks_context}

        OBSERVED STRENGTHS ACROSS SEGMENTS:
        {strengths_context}

        AREAS FOR IMPROVEMENT IDENTIFIED:
        {improvements_context}

        SPECIFIC ACTIONS RECOMMENDED:
        {actions_context}

        Provide specific coaching feedback on their actual meeting performance, speaking directly to them as their coach. Focus on what they said and how they said it.

        Structure your response as:

        **What You Did Well:**
        - Quote specific phrases or approaches you used that were effective
        - Explain why these particular words/approaches worked well for your leadership goals
        - Connect your actual dialogue to leadership best practices you demonstrated

        **Missed Opportunities in Your Dialogue:**
        - Identify specific moments where you could have used more effective language
        - Quote what you actually said, then suggest how you could have phrased it differently
        - Point to leadership techniques you could have applied in those specific exchanges

        **Your Language Patterns:**
        - Highlight recurring phrases or communication patterns that serve you well
        - Note any blind spots in your communication style based on the actual transcript

        Write as their personal coach speaking directly to them. Use "you" throughout and ground all feedback in their actual words and contributions.
        """,
        input_variables=["user_name", "user_role", "company_context", "metadata_context", "development_focus_context",
                        "chunks_context", "strengths_context", "improvements_context", "actions_context"]
    )

    try:
        # Create chain and invoke
        chain = prompt_template | llm

        # Get the response
        raw_response = chain.invoke({
            "user_name": user_name,
            "user_role": user_role,
            "company_context": company_context,
            "metadata_context": metadata_context,
            "development_focus_context": development_focus_context,
            "chunks_context": chunks_context,
            "strengths_context": strengths_context,
            "improvements_context": improvements_context,
            "actions_context": actions_context
        })

        # Get the plain text response (no JSON parsing needed)
        summary_text = raw_response.content.strip()

        # Simple usage analytics without detailed token tracking
        usage_analytics = {
            "model_used": CURRENT_MODEL,
            "chunks_summarized": len(ai_evaluations),
            "active_participation_segments": participation_count,
            "average_chunk_score": sum(total_scores) / len(total_scores) if total_scores else 0
        }

        return {
            "overall_leadership_assessment": summary_text,
            "usage_analytics": usage_analytics
        }

    except Exception as e:
        # Return error response if summarization fails
        error_usage = {
            "model_used": CURRENT_MODEL,
            "error": str(e)
        }

        return {
            "overall_leadership_assessment": f"I apologize, but I encountered an error while analyzing your meeting performance: {str(e)}. Please try again later.",
            "usage_analytics": error_usage
        }
