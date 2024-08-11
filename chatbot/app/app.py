from dotenv import load_dotenv
from typing import Dict, List, Tuple
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

load_dotenv()

# Initialize ChatOpenAI
llm = ChatOpenAI(temperature=0.7, model="gpt-4o-mini")

# Set up RAG
vectorstore = PineconeVectorStore(embedding=OpenAIEmbeddings(), index_name="chatbot-peak")
retriever = vectorstore.as_retriever()
rag = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=True)

# Define the state
class State(BaseModel):
    # QA STATES
    question: str = "" # User input
    answer: str = "" # AI response
    chat_history: List[Dict[str, str]] = []

    # NODE STATES - determines flow
    is_relevant: bool = False # Is the initial prompt relevant?
    goal_clear: bool = False # Is the goal clear? (G in GROW)
    reality_clear: bool = False # Is the situation / reality clear? (R in GROW)
    options_clear: bool = False # Are the user's options clear? (O in GROW)
    is_scenario: bool = False # Is the question scenario-based or is it more technical?

# START NODE - INTRO AND CHECK RELEVANCE OF ANSWER
def start_and_check_relevance(state: State) -> State:
    message = llm.invoke("You are PeakBot, a bot designed to be an expert in coaching leaders through specific situations. Introduce yourself.").content
    print(message)
    state.chat_history.append({"role": "assistant", "content": message})

    state.question = input("User: ")
    state.chat_history.append({"role": "user", "content": state.question})

    response = llm.invoke(f"User input: {state.question}\nIs this a question or a scenario that is relevant to coaching or leadership? Answer with 'Yes' only if the question is relevant to coaching or leadership. For example, your answer for math or geography questions should be 'No'.").content
    print(f"##Relevance: {response}##")
    state.is_relevant = response.lower().strip() == "yes"

    return state

# CHECK IF RELEVANT
def reprompt_for_relevance(state: State) -> State:
    message = llm.invoke(f"The user has just asked something irrelevant to coaching or leadership: {state.question}\nReiterate that you are here to help with scenario or question-based coaching and leadership.").content
    print(message)
    state.chat_history.append({"role": "assistant", "content": message})

    state.question = input("User: ")
    state.chat_history.append({"role": "user", "content": state.question})

    response = llm.invoke(f"User input: {state.question}\nIs this a question or a scenario that is relevant to coaching or leadership? Answer with 'Yes' only if the question is relevant to coaching or leadership. For example, your answer for math or geography questions should be 'No'.").content
    print(f"##Relevance: {response}##")

    state.is_relevant = response.lower().strip() == "yes"

    return state

# CHECK IF GOAL IS CLEAR
def check_goal(state: State) -> State:
    response = llm.invoke(f"Chat history: {state.chat_history}\nYou are evaluating 'G' in the GROW method. Is the user's goal clear? Answer with 'Yes' or 'No' only. Answer with 'No' if it is vague.").content

    print(f"##Goal: {response}##")

    state.goal_clear = response.lower().strip() == "yes"

    return state

# PROMPT FOR GOAL
def prompt_for_goal(state: State) -> State:
    message = llm.invoke(f"You are a leadership coach. Ask the user what they want to achieve given their scenario. If it is vague, ask them to make sure it is specific, measurable, achievable, and time-based. MAXIMUM OF THREE SENTENCES ONLY.").content
    print(message)
    state.chat_history.append({"role": "assistant", "content": message})

    state.question = input("User: ")
    state.chat_history.append({"role": "user", "content": state.question})

    response = llm.invoke(f"Chat history: {state.chat_history}\nYou are evaluating 'G' in the GROW method. Is the user's goal clear? Answer with 'Yes' or 'No' only.").content
    print(f"##Goal: {response}##")

    state.goal_clear = response.lower().strip() == "yes"

    return state

# CHECK IF REALITY IS CLEAR
def check_reality(state: State) -> Dict:
    response = llm.invoke(f"Chat history: {state.chat_history}\nYou are evaluating 'R' in the GROW method. Is the reality in the user's problem clear? For example, has the user explained what makes it challenging to achieve their goal? Answer with 'Yes' or 'No' only.").content

    print(f"##Reality: {response}##")

    state.reality_clear = response.lower().strip() == "yes"

    return state

# PROMPT FOR REALITY
def prompt_for_reality(state: State) -> Dict:
    message = llm.invoke(f"Chat history: {state.chat_history}\nIf the user's last input is about their situation, then make a quick comment about it. MAXIMUM OF TWO SENTENCES ONLY. Then, ask the user to clarify the reality of their problem. For example: what makes it challenging for the user to achieve their goal (repeat the goal they gave)? do they have a problem with their team? do they lack certain resources? and so on. MAXIMUM OF THREE SENTENCES ONLY.").content
    print(message)
    state.chat_history.append({"role": "assistant", "content": message})

    state.question = input("User: ")
    state.chat_history.append({"role": "user", "content": state.question})

    response = llm.invoke(f"Chat history: {state.chat_history}\nYou are evaluating 'R' in the GROW method. Is the reality in the user's problem clear? For example, has the user explained what makes it challenging to achieve their goal? Answer with 'Yes' or 'No' only.").content
    print(f"##Reality: {response}##")

    state.reality_clear = response.lower().strip() == "yes"

    return state

# CHECK IF OPTIONS ARE CLEAR
def check_options(state: State) -> Dict:
    response = llm.invoke(f"Chat history: {state.chat_history}\nYou are evaluating 'O' in the GROW method. Has the user mentioned what action they have attempted to address the problem? Answer 'Yes' or 'No' only.").content

    print(f"##Options: {response}##")

    state.options_clear = response.lower().strip() == "yes"

    return state

# PROPMT FOR OPTIONS
def prompt_for_options(state: State) -> Dict:
    print("Prompting for options...")

    message = llm.invoke(f"Chat history: {state.chat_history}\nIf the user's last input is about their situation, then make a quick comment about it. MAXIMUM OF TWO SENTENCES ONLY. You are evaluating 'O' in the GROW method. Ask the user to explain what options or alternatives they have considered to approach their problem. MAXIMUM OF THREE SENTENCES ONLY.").content
    print(message)
    state.chat_history.append({"role": "assistant", "content": message})

    state.question = input("User: ")
    state.chat_history.append({"role": "user", "content": state.question})

    response = llm.invoke(f"Chat history: {state.chat_history}\nYou are evaluating 'O' in the GROW method. Has the user mentioned what action they have attempted to address the problem? Answer 'Yes' or 'No' only.").content
    print(f"##Options: {response}##")

    state.options_clear = response.lower().strip() == "yes"

    return state

def get_rag_advice(state: State) -> Dict:
    # GET ADDITIONAL INFORMATION, IF ANY
    message = llm.invoke(f"Chat history: {state.chat_history}\nSummarize the user's problem in three to five sentences. Then ask if there are any more details that they might want to include").content
    print(message)
    state.chat_history.append({"role": "assistant", "content": message})

    state.question = input("User: ")
    state.chat_history.append({"role": "user", "content": state.question})

    # FORMULATE ACTION PLAN VIA RAG
    message = rag.invoke(f"Chat history: {state.chat_history}\nAnalyze the user's scenario and goals as revealed in the conversation history above. Remember, you are a leadership coach. Provide an action plan based on the retrieved information in the context.")
    print(message) 

    return state

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

# Compile the graph
app = workflow.compile()

def main():
    while True:
        state = State()
        
        for output in app.stream(state):
            if isinstance(output, Tuple):
                node, state = output
                if node == END:
                    print("Assistant:", state.answer)

if __name__ == "__main__":
    main()