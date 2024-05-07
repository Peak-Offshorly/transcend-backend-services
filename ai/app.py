import os
from dotenv import load_dotenv
load_dotenv()
openai_api_key=os.environ["OPENAI_API_KEY"]

# "gpt-4-1106-preview"
# CRITIC_MODEL = "gpt-4-turbo"
GPT_MODEL = "gpt-3.5-turbo-0125"
EMBEDDING_MODEL = "text-embedding-ada-002"


from langchain_community.document_loaders import Docx2txtLoader

# Specify the directory path where your.docx files are located
directory_path = "training_data"

for filename in os.listdir(directory_path):
    if filename.endswith(".docx"):
        file_path = os.path.join(directory_path, filename)
        loader = Docx2txtLoader(file_path)
        data = loader.load()git add