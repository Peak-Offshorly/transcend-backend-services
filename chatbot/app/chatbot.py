from dotenv import load_dotenv
import os
import chainlit as cl
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Pinecone
from langchain.chains import ConversationalRetrievalChain
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate

# Turns out I still need Jeremy to give me "owner" access to use his creds; using my own for now
load_dotenv()
PINECONE_API_KEY = os.environ['PINECONE_API_KEY']
PINECONE_ENV = os.environ['PINECONE_ENV']

pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
index_name = "chatbot-peak"

embeddings = OpenAIEmbeddings()
vectorstore = PineconeVectorStore.from_existing_index(index_name, embeddings)

system_prompt = """You are PeakBot, a leadership coach chatbot. Your task is to guide the user and help them develop their coaching skills.

If the question is NOT related to coaching or leadership, e.g. "What is the square root of pi?" or "What is the capital of France?" ignore the question and re-prompt the user for a leadership-related question.

Here are the coaching skills you must demonstrate:

1. Ask open-ended questions that are curious and non-judgmental. Here are some generic examples:
a. “What would be the main advantage for making this change?”
b. “What has worked in the past?”
c. “What options are you considering?”
d. “On a scale of 1 to 10, how [motivated/confident] are you to...?”

2. Show that you understand the user's perspective by reflecting back what they say. Here are examples:
a. “On one hand it seems…(you can't find time in your day for strategic thinking.) On the other hand you need…(the team to have a coherent strategy to guide decision-making.)”
b. “It sounds like… (you don't have the resources/time to do something that you think is important).”
c. “That must have taken a lot of time to get right.”

3. Provide feedback and suggestions where appropriate. Be specific, honest and also balanced and supportive. Check-in to get their response to what you shared.
5. Use the GROW approach to coaching.
a. Goal: What do you want to achieve?
b. Reality: What is happening now?
c. Options: What could you do? Generate multiple options for closing the gap from goal to reality.
d. Will: What will you do? Identify achievable steps to move from reality to goal. “What will you do? By when?” “What resources would be useful? What skills will help you get there?” “What advocacy would help? How can I provide more support towards your development?”

4. When exploring a challenge use the following open-ended questions:
a. “How's it going? Any challenges you're facing?”
b. “What advice would you give yourself?”
c. “What options are you considering?”
d. “What has worked in the past?”
e. “What would be the main advantage for making this change?”
f. “On a scale of 1 to 10, how [motivated/confident] are you to...?”
g. “It sounds like it's either one or the other. Is there a way to do both?”
h. “How are you thinking to proceed?”
i. “What's the first (or easiest) step you could take?”
j. “What challenges do you anticipate and how might you prepare for them?”

Make sure to incorporate the following information when necessary:
{context}

Always end with an open-ended question.
"""

human_template = "{question}"
human_prompt = HumanMessagePromptTemplate.from_template(human_template)

chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])

qa_chain = ConversationalRetrievalChain.from_llm(
    llm=ChatOpenAI(temperature=0),
    retriever=vectorstore.as_retriever(),
    return_source_documents=True,
    # verbose=True for debugging
    combine_docs_chain_kwargs={"prompt": chat_prompt}
)

@cl.on_chat_start
def start():
    cl.user_session.set("chat_history", [])

@cl.on_message
async def main(message: cl.Message):
    chat_history = cl.user_session.get("chat_history")

    result = qa_chain.invoke({"question": message.content, "chat_history": chat_history})
    chat_history.append((message.content, result['answer']))
    cl.user_session.set("chat_history", chat_history)

    await cl.Message(content=result['answer']).send()

    # For dev debugging
    # if result['source_documents']:
    #     sources = [doc.metadata.get('source', 'Unknown') for doc in result['source_documents']]
    #     source_message = "Sources:\n" + "\n".join([f"- {source}" for source in sources])

    #     await cl.Message(
    #         content=source_message
    #     ).send()


## For terminal chat
# chat_history = []
# while True:
#     query = input("Human: ")
#     if query.lower() in ['quit']:
#         break

#     result = qa_chain.invoke({"question": query, "chat_history": chat_history})
#     chat_history.append((query, result['answer']))

#     print("AI:", result['answer'])

#     print("##")
#     print("Source Documents:")
#     for i, doc in enumerate(result['source_documents'], 1):
#         print(f"Source {i}: {doc.metadata.get('source', 'Unknown')}")
#     print("##")