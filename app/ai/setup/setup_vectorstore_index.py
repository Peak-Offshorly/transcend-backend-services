from app.ai.const import PINECONE_API_KEY, USE_SERVERLESS

#Creating an index
from pinecone import Pinecone, ServerlessSpec, PodSpec

def setup_vectorstore_index(index_name):
  # configure client
  print("Configuring client")
  pc = Pinecone(api_key=PINECONE_API_KEY)

  if USE_SERVERLESS:
    spec = ServerlessSpec(cloud='aws', region='us-west-2')
  else:
    # if not using a starter index, you should specify a pod_type too
    spec = PodSpec()

  print("Setting up index name", index_name) 

  #deletes if exists 
  if index_name in pc.list_indexes().names():
    user_input = input("Index name exists. Would you like to delete it? y/n: ")
    while user_input not in ['y', 'n']:
      user_input = input("Invalid input. Please enter y/n")

    if user_input == 'y':
      print("Deleting index")
      pc.delete_index(index_name)
    else:
      print("Exiting")
      return None

  import time

  print("Creating index")
  dimension = 1536 #768 or 1536
  pc.create_index(
    name=index_name,
    dimension=dimension,
    metric="cosine",
    spec=spec
  )

  while not pc.describe_index(index_name).status['ready']:
    print("Preparing index...")
    time.sleep(1)

  index = pc.Index(index_name)
  print("Index ready")
  print(index.describe_index_stats())

#todo: set index name here
index_name="peak-ai"
setup_vectorstore_index(index_name)