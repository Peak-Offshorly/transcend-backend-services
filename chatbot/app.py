import logging
import json
from dotenv import load_dotenv
from typing import Dict, List, Tuple, Any
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import tiktoken
from langchain_anthropic import ChatAnthropic
from langchain.globals import set_llm_cache
from langchain.cache import InMemoryCache
from starlette.websockets import WebSocketState
from asyncio import Lock

# Start debug logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

# FastAPI and WS app
fast_app = FastAPI()
fast_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a class to hold session-specific data
class ClientSession:
    def __init__(self):
        self.websocket = None
        self.token_count = 0
        self.token_cost = 0
        self.ai_message = ""
        self.chat_history = []
        self.num_of_followups = 1
        self.stage = "intro"
        self.lock = Lock()

# Create a dictionary to store client sessions
client_sessions = {}

# Initialize ChatOpenAI
llm = ChatAnthropic(model='claude-3-opus-20240229')
set_llm_cache(InMemoryCache())
# Set up for RAG
vectorstore = PineconeVectorStore(embedding=OpenAIEmbeddings(), index_name="peak-ai")
retriever = vectorstore.as_retriever()
rag = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=True)

# Abstracted prompts for Jeremy to tweak
identity = "You are PeakBot, a bot designed to be an expert in coaching leaders through specific situations."
custom_prompts = {
    "intro_prompt": "Introduce yourself with three sentences at most.", 
    "goal_prompt": "Make an insightful observation about the user's situation in two sentences. Do not jump to negative conclusions about the user. Be empathetic about their complaint. Then in one sentence ask the user what they want to achieve given their scenario.",
    "reality_prompt": "Make a useful observation about the user's goal in two sentences. Then in another paragraph and in two sentences only, ask the user to clarify the reality of their problem. For example: what makes it challenging for the user to achieve their goal (repeat the goal they gave)? do they have a problem with their team? do they personally have a certain behavior they'd like to correct? and so on. Tailor-fit these leading questions to the user's scenario.", 
    "options_prompt": "Make a useful observation about the user's reality in one sentence. Then in one sentence, ask the user what options they have considered to solve their challenge. In two sentences, give the user some suggestions specific to their challenge using the user's profile and the retrieved context.", 
    "will_prompt": "Give constructive feedback on the options the user has considered in two sentences. Then, in one sentence, ask the user for an action plan moving forward.",
    "goodbye_prompt": "Summarize the user's situation and the action plan they have decided on. Offer encouragement and support. End the conversation with a positive note. Maximum of three sentences only.",
    "followup_prompt": "Make an empathetic comment about the user's answer in one sentence. If the user is complaining, make sure that they feel validated. Then, in another sentence, ask an insightful follow-up question."
}
for key, value in custom_prompts.items():
    custom_prompts[key] = identity + "\n" + value

relevancy_prompts = {
    "intro": """Is the user's question relevant to coaching or leadership? Answer 'Yes' or 'No' only. Examples of relevant responses:
    - "I am the head of a small sales team and I need help."
    - "I need help with my leadership skills."
    - "I need a way to motivate my team."
    - "I'm struggling with delegating tasks to my team and it feels like I do everything myself."
    - "As a software developer, how do I become a better team lead?"
    - "I'm not really sure what I want. I just feel overwhelmed with work lately."
    
    Examples of non-relevant responses:
    - "I'm a student and I need help with my homework."
    - "What is the capital of Paris?"
    - "What is 2 * 2?"
    - "What is the weather today?"
    """,
    "goal": """Has the user provided a goal? Answer 'Yes' or 'No' only.
    
    Examples of goals:
    - "I'd like my dev team to launch a beta version by the end of this month."
    - "My sales team needs to launch a new marketing campaign by the end of the quarter."
    - "I want my team to be more productive."
    - "I want to improve my leadership skills."

    Examples of answers that are not goals:
    - "I'm a student and I need help with my homework."
    - "What is the capital of Paris?"
    - "My car crashed and I don't know how to fix it."
    """,
    "reality": """Does the user explain their reality or situation? Answer 'Yes' or 'No' only.
    
    Examples of relevant responses:
    - "My team is not motivated enough to meet our sales targets."
    - "Whenever there is a deadline my team keeps beating around the bush."
    - "I can never get my team to agree on a single idea."
    - "I always end up doing everything."

    Examples of non-relevant responses:
    - "I'm a student and I need help with my homework."
    - "What is the capital of Paris?"
    - "What is 2 * 2?"
    """,
    "options": """Does the user provide options they have considered? Answer 'Yes' or 'No' only.
    
    Examples of relevant responses:
    - "I've tried giving them incentives but it doesn't work."
    - "I've tried talking to them but they don't listen."
    - "I've tried setting stricter deadlines but they still miss them."

    Examples of non-relevant responses:
    - "Find the square root of pi."
    - "What is the capital of Paris?"
    """,
    "will": """Does the user provide a plan or action they will take? Answer 'Yes' or 'No' only.

    Examples of plans:
    - "I will try to motivate my team by giving them more structured incentives."
    - "I will be a better listener and try to understand my team's perspective."
    - "I could start by delegating smaller tasks and gradually increase the complexity as my trust grows." 
    - "I could also set clearer expectations and check-in points instead of constant oversight."
    """
}

# Update helper functions to use ClientSession
async def send_message(session: ClientSession, message: str, fromUser: str, currentPrompt: str):
    if session.websocket and session.websocket.client_state == WebSocketState.CONNECTED:
        session.token_count += len(tiktoken.get_encoding("cl100k_base").encode(message))
        session.token_cost += 30 * session.token_count / 1000000
        await session.websocket.send_json({
            "message": message,
            "fromUser": fromUser,
            "currentPrompt": currentPrompt,
            "tokenCount": session.token_count,
            "tokenCost": session.token_cost
        })

async def receive_input(session: ClientSession) -> Dict[str, str]:
    if session.websocket and session.websocket.client_state == WebSocketState.CONNECTED:
        while True:
            response = await session.websocket.receive_text()
            if response!= "ping":
                return json.loads(response)
            else:
                print("Received ping!")
                await session.websocket.send_json({"action": "pong"})
                return None

# Handle response type (either regenerate, for the prompt playground or receive message)
async def handle_response_type(session: ClientSession, response: Dict[str, str]):
    # For abstracted prompts
    while response["action"] == "regenerate":
        if session.chat_history:
            session.chat_history.pop()
        custom_prompts.intro_prompt = response['message']
        message = llm.invoke(custom_prompts.intro_prompt).content

        await send_message(session, message, False, custom_prompts.intro_prompt)
        session.chat_history.append({"role": "assistant", "content": message})

        response = await receive_input(session)
        print(f"Receiving response: {response['action']}")

    if response["action"] == "message":
        session.chat_history.append({"role": "user", "content": response["message"]})

# Check relevance to the last question
async def check_relevance(session: ClientSession, user_message: str, stage: str):
    relevancy_query = relevancy_prompts[stage]
    ai_checkpoint = llm.invoke(f"Chat history: {session.chat_history}\n{relevancy_query}").content
    print("**")
    print(relevancy_query)
    print(ai_checkpoint)
    print("**")

    while ai_checkpoint.lower().strip() == "no":
        if llm.invoke(f"User message: {user_message}\nAnswer 'yes' or 'no' only. Is the user message a simple greeting like 'hi there' or 'hello'?").content.lower() == "yes":
            await send_message(session, llm.invoke(f"User message: {user_message}\nAI question: {session.ai_message}\nGreet the user back and restate your question in one sentence.").content, False, None)
        else:
            await send_message(session, llm.invoke(f"User message: {user_message}\nAI question: {session.ai_message}\nNudge the user to stick to responses relevant to coaching and restate your question. Do this in one or two sentences.").content, False, None)
        
        user_response = None
        while not user_response:
            user_response = await receive_input(session)

        user_message = user_response["message"]

        ai_checkpoint = llm.invoke(f"Last user message: {user_response}\n{relevancy_query}").content
    
    session.chat_history.append({"role": "user", "content": user_message})

async def handle_response(session: ClientSession, stage: str):
    response = await receive_input(session)
    if response:
        # Ping or not ping
        await handle_response_type(session, response)
        # Relevant or not relevant
        await check_relevance(session, user_message=response["message"], stage=stage)
        # Follow-ups based on user time
        if stage != "intro":
            for _ in range(session.num_of_followups):
                session.ai_message = llm.invoke(f"Chat history: {session.chat_history}\n" + custom_prompts["followup_prompt"]).content
                await send_message(session, session.ai_message, fromUser=False, currentPrompt=custom_prompts["followup_prompt"])

                response = await receive_input(session)
                if response:
                    await handle_response_type(session, response)
                    await check_relevance(session, user_message=response["message"], stage=stage)
                else:
                    return None
        return response

# Main conversation loop, WS endpoint
@fast_app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = id(websocket)
    session = ClientSession()
    session.websocket = websocket
    client_sessions[session_id] = session

    try:
        logger.debug(f"WebSocket connection accepted for session {session_id}")

        # [0] Bot receives user input time
        response = await receive_input(session)
        if response["action"] == "time":
            print("Following " + response["message"])
            if response["message"] == "5 minutes":
                session.num_of_followups = 1
            elif response["message"] == "10 minutes":
                session.num_of_followups = 2
            else:
                session.num_of_followups = 4
            print(response["profile"])
            for prompt in custom_prompts:
                custom_prompts[prompt] = "Incorporate the user's role, role description, and industry in your answer when appropriate. Refer to them by their first name.\n" + response["profile"] + "\n" + custom_prompts[prompt]
        
        # [1] Bot introduces itself
        session.ai_message = "Awesome, let's get started. How can I help you achieve your coaching goals?"
        session.chat_history.append({"role": "assistant", "content": session.ai_message})
        await send_message(session, session.ai_message, fromUser=False, currentPrompt=custom_prompts["intro_prompt"])

        response = None
        while not response:
            response = await handle_response(session, stage="intro")
        
        # [2] Bot asks for the user's goal
        session.ai_message = llm.invoke(f"Chat history: {session.chat_history}\n" + custom_prompts["goal_prompt"]).content
        await send_message(session, session.ai_message, fromUser=False, currentPrompt=custom_prompts["goal_prompt"])
        session.chat_history.append({"role": "assistant", "content": session.ai_message})

        response = None
        while not response:
            response = await handle_response(session, stage="goal")

        # [3] Bot asks for the user's reality
        session.ai_message = llm.invoke(f"Chat history: {session.chat_history}\n" + custom_prompts["reality_prompt"]).content
        await send_message(session, session.ai_message, fromUser=False, currentPrompt=custom_prompts["reality_prompt"])
        session.chat_history.append({"role": "assistant", "content": session.ai_message})

        response = None
        while not response:
            response = await handle_response(session, stage="reality")

        # [4] Bot asks for options the user has tried
        session.ai_message = rag.invoke(f"Chat history: {session.chat_history}\n" + custom_prompts["options_prompt"])['result']
        await send_message(session, session.ai_message, fromUser=False, currentPrompt=custom_prompts["options_prompt"])
        session.chat_history.append({"role": "assistant", "content": session.ai_message})

        response = None
        while not response:
            response = await handle_response(session, stage="options")

        # [5] Bot asks for a plan: what *will* the user do?
        session.ai_message = llm.invoke(f"Chat history: {session.chat_history}\n" + custom_prompts["will_prompt"]).content
        await send_message(session, session.ai_message, fromUser=False, currentPrompt=custom_prompts["will_prompt"])
        session.chat_history.append({"role": "assistant", "content": session.ai_message})

        response = None
        while not response:
            response = await handle_response(session, stage="will")

        # [6] Recap and farewell
        session.ai_message = llm.invoke(f"Chat history: {session.chat_history}\n" + custom_prompts["goodbye_prompt"]).content
        await send_message(session, session.ai_message, fromUser=False, currentPrompt=custom_prompts["goodbye_prompt"])
        session.chat_history.append({"role": "assistant", "content": session.ai_message})

    finally:
        # Clean up the session when the WebSocket closes
        if session_id in client_sessions:
            del client_sessions[session_id]
        logger.debug(f"WebSocket connection closed for session {session_id}")

