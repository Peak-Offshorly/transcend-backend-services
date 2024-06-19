from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

EMBEDDING_MODEL = "text-embedding-ada-002"

def get_vectorstore(index_name: str, embedding_model: str = EMBEDDING_MODEL):
  print("Retrieving Pinecone Vectorstore")
  embeddings = OpenAIEmbeddings(model=embedding_model)
  pinecone_vectorstore = PineconeVectorStore.from_existing_index(index_name=index_name, embedding=embeddings)
  
  return pinecone_vectorstore