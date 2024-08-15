import logging
from dotenv import load_dotenv
from typing import Dict, List, Tuple, Any
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
from langgraph.graph import StateGraph, END
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

fast_app = FastAPI()

# Add CORS middleware
fast_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ChatOpenAI
llm = ChatOpenAI(temperature=0.7, model="gpt-4o-mini")

# Set up RAG
vectorstore = PineconeVectorStore(embedding=OpenAIEmbeddings(), index_name="chatbot-peak")
retriever = vectorstore.as_retriever()
rag = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=True)

# Define the state
class State:
    def __init__(self):frontend
        self.question = ""
        self.answer = ""
        self.chat_history = []
        self.is_relevant = False
        self.goal_clear = False
        self.reality_clear = False
        self.options_clear = False
        self.is_scenario = False

# Global WebSocket variable
websocket_connection = None

async def send_message(message: str):
    if websocket_connection:
        await websocket_connection.send_text(message)

async def receive_input() -> str:
    if websocket_connection:
        return await websocket_connection.receive_text()
    return ""

async def start_and_check_relevance(state: State):
    logger.debug("Entering start_and_check_relevance")
    if not state.chat_history:  # If this is the first run
        logger.debug("First run, introducing PeakBot")
        message = llm.invoke("You are PeakBot, a bot designed to be an expert in coaching leaders through specific situations. Introduce yourself.").content
        logger.debug(f"PeakBot introduction: {message}")
        await send_message(message)
        state.chat_history.append({"role": "assistant", "content": message})
        logger.debug(f"Chat history: {state.chat_history}")
        
        # Wait for user input
        state.question = await receive_input()
        logger.debug(f"Received user input: {state.question}")
        state.chat_history.append({"role": "user", "content": state.question})

    response = llm.invoke(f"User input: {state.question}\nIs this a question or a scenario that is relevant to coaching or leadership? Answer with 'Yes' only if the question is relevant to coaching or leadership. For example, your answer for math or geography questions should be 'No'.").content
    logger.debug(f"Relevance check response: {response}")
    state.is_relevant = response.lower().strip() == "yes"
    logger.debug(f"Is relevant: {state.is_relevant}")

    yield state

# CHECK IF RELEVANT
async def reprompt_for_relevance(state: State):

    message = llm.invoke(f"The user has just asked something irrelevant to coaching or leadership: {state.question}\nReiterate that you are here to help with scenario or question-based coaching and leadership.").content
    await send_message(message)
    state.chat_history.append({"role": "assistant", "content": message})

    state.question = await receive_input()
    state.chat_history.append({"role": "user", "content": state.question})

    response = llm.invoke(f"User input: {state.question}\nIs this a question or a scenario that is relevant to coaching or leadership? Answer with 'Yes' only if the question is relevant to coaching or leadership. For example, your answer for math or geography questions should be 'No'.").content

    state.is_relevant = response.lower().strip() == "yes"

    yield state

# CHECK IF GOAL IS CLEAR
async def check_goal(state: State):

    response = llm.invoke(f"Chat history: {state.chat_history}\nYou are evaluating 'G' in the GROW method. Is the user's goal clear? Answer with 'Yes' or 'No' only. Answer with 'No' if it is vague.").content

    state.goal_clear = response.lower().strip() == "yes"

    yield state

# PROMPT FOR GOAL
async def prompt_for_goal(state: State):
    message = llm.invoke(f"You are a leadership coach. Ask the user what they want to achieve given their scenario. If it is vague, ask them to make sure it is specific, measurable, achievable, and time-based. MAXIMUM OF THREE SENTENCES ONLY.").content
    await send_message(message)
    state.chat_history.append({"role": "assistant", "content": message})

    # Wait for user input
    state.question = await receive_input()
    state.chat_history.append({"role": "user", "content": state.question})

    print("Goal checkpoint:")
    print(state.chat_history)

    response = llm.invoke(f"Chat history: {state.chat_history}\nYou are evaluating 'G' in the GROW method. Is the user's goal clear? Answer with 'Yes' or 'No' only.").content
    state.goal_clear = response.lower().strip() == "yes"

    yield state

# CHECK IF REALITY IS CLEAR
async def check_reality(state: State):
    response = llm.invoke(f"Chat history: {state.chat_history}\nYou are evaluating 'R' in the GROW method. Is the reality in the user's problem clear? For example, has the user explained what makes it challenging to achieve their goal? Answer with 'Yes' or 'No' only.").content

    state.reality_clear = response.lower().strip() == "yes"

    yield state

# PROMPT FOR REALITY
async def prompt_for_reality(state: State):
    message = llm.invoke(f"Chat history: {state.chat_history}\nIf the user's last input is about their situation, then make a quick comment about it. MAXIMUM OF TWO SENTENCES ONLY. Then, ask the user to clarify the reality of their problem. For example: what makes it challenging for the user to achieve their goal (repeat the goal they gave)? do they have a problem with their team? do they lack certain resources? and so on. MAXIMUM OF THREE SENTENCES ONLY.").content
    await send_message(message)
    state.chat_history.append({"role": "assistant", "content": message})

    state.question = await receive_input()
    state.chat_history.append({"role": "user", "content": state.question})

    response = llm.invoke(f"Chat history: {state.chat_history}\nYou are evaluating 'R' in the GROW method. Is the reality in the user's problem clear? For example, has the user explained what makes it challenging to achieve their goal? Answer with 'Yes' or 'No' only.").content

    state.reality_clear = response.lower().strip() == "yes"

    yield state

# CHECK IF OPTIONS ARE CLEAR
async def check_options(state: State):
    response = llm.invoke(f"Chat history: {state.chat_history}\nYou are evaluating 'O' in the GROW method. Has the user mentioned what action they have attempted to address the problem? Answer 'Yes' or 'No' only.").content

    state.options_clear = response.lower().strip() == "yes"

    yield state

# PROPMT FOR OPTIONS
async def prompt_for_options(state: State):

    message = llm.invoke(f"Chat history: {state.chat_history}\nIf the user's last input is about their situation, then make a quick comment about it. MAXIMUM OF TWO SENTENCES ONLY. You are evaluating 'O' in the GROW method. Ask the user to explain what options or alternatives they have considered to approach their problem. MAXIMUM OF THREE SENTENCES ONLY.").content
    await send_message(message)
    state.chat_history.append({"role": "assistant", "content": message})

    state.question = await receive_input()
    state.chat_history.append({"role": "user", "content": state.question})

    response = llm.invoke(f"Chat history: {state.chat_history}\nYou are evaluating 'O' in the GROW method. Has the user mentioned what action they have attempted to address the problem? Answer 'Yes' or 'No' only.").content

    state.options_clear = response.lower().strip() == "yes"

    yield state

async def get_rag_advice(state: State):
    # GET ADDITIONAL INFORMATION, IF ANY
    message = llm.invoke(f"Chat history: {state.chat_history}\nGive the user a summary of what they just said in three sentences. Then ask if there are any more details that they might want to include").content
    await send_message(message)

    state.chat_history.append({"role": "assistant", "content": message})

    state.question = await receive_input()
    state.chat_history.append({"role": "user", "content": state.question})

    # FORMULATE ACTION PLAN VIA RAG
    message =rag.invoke(f"Chat history: {state.chat_history}\nAnalyze the user's scenario and goals as revealed in the conversation history above. Remember, you are a leadership coach. Provide an action plan based on the retrieved information in the context.")['result']

    await send_message(message)

    return state

# Create the graph
workflow = StateGraph(State)

# Add nodes
workflow.add_node("start_and_check_relevance", start_and_check_relevance)

# Create the graph
workflow = StateGraph(State)

# Add nodes
workflow.add_node("start_and_check_relevance", start_and_check_relevance)
workflow.add_node("reprompt_for_relevance", reprompt_for_relevance)

workflow.add_node("check_goal", check_goal)
workflow.add_node("prompt_for_goal", prompt_for_goal)
workflow.add_node("check_reality", check_reality)
workflow.add_node("prompt_for_reality", prompt_for_reality)

workflow.add_node("check_options", check_options)
workflow.add_node("prompt_for_options", prompt_for_options)

workflow.add_node("get_rag_advice", get_rag_advice)

# Relevance
workflow.add_conditional_edges("start_and_check_relevance", lambda x: "check_goal" if x.is_relevant else "reprompt_for_relevance")
workflow.add_conditional_edges("reprompt_for_relevance", lambda x: "check_goal" if x.is_relevant else "reprompt_for_relevance")

# Goal
workflow.add_conditional_edges("check_goal", lambda x: "check_reality" if x.goal_clear else "prompt_for_goal")
workflow.add_conditional_edges("prompt_for_goal", lambda x: "check_reality" if x.goal_clear else "prompt_for_goal")

# Reality
workflow.add_conditional_edges("check_reality", lambda x: "check_options" if x.reality_clear else "prompt_for_reality")
workflow.add_conditional_edges("prompt_for_reality", lambda x: "check_options" if x.reality_clear else "prompt_for_reality")

# Options
workflow.add_conditional_edges("check_options", lambda x: "get_rag_advice" if x.options_clear else "prompt_for_options")
workflow.add_conditional_edges("prompt_for_options", lambda x: "get_rag_advice" if x.options_clear else "prompt_for_options")

# Will + RAG
workflow.add_edge("get_rag_advice", END)

# Set the entry point
workflow.set_entry_point("start_and_check_relevance")

# After creating the workflow
logger.debug(f"Workflow nodes: {workflow.nodes}")
logger.debug(f"Workflow edges: {workflow.edges}")

# Before compiling the graph
logger.debug("Compiling the graph")
try:
    lang_app = workflow.compile()
except Exception as e:
    logger.error(f"Error compiling graph: {e}", exc_info=True)
    raise

logger.debug("Graph compiled successfully")

# Compile the graph
lang_app = workflow.compile()

@fast_app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    logger.debug("WebSocket connection attempt")
    await websocket.accept()
    logger.debug("WebSocket connection accepted")
    global websocket_connection
    websocket_connection = websocket
    
    state = State()
    logger.debug(f"Initial state: {state}")
    
    try:
        logger.debug("Starting LangGraph app")
        async for step in lang_app.astream(state):
            logger.debug(f"Step: {step}")
            if isinstance(step, tuple):
                node, state = step
                if node == END:
                    await send_message("End of conversation.")
                    break
            elif step is None:
                user_input = await receive_input()
                if user_input:
                    await lang_app.astep(state, user_input)
                else:
                    break
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket handler: {e}", exc_info=True)
        await websocket.send_text(f"An unexpected error occurred: {str(e)}")
    finally:
        logger.debug("WebSocket connection closed")
        websocket_connection = None
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(fast_app, host="0.0.0.0", port=8000)