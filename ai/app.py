import os
from dotenv import load_dotenv
load_dotenv()
openai_api_key=os.environ["OPENAI_API_KEY"]

# "gpt-4-1106-preview"
# CRITIC_MODEL = "gpt-4-turbo"
GPT_MODEL = "gpt-3.5-turbo-0125"
EMBEDDING_MODEL = "text-embedding-ada-002"


from langchain_community.document_loaders import Docx2txtLoader
# loader = Docx2txtLoader("example_data/fake.docx")
# data = loader.load()
# data

# Specify the directory path where your.docx files are located
directory_path = "training_data"

# Iterate over all files in the directory
for filename in os.listdir(directory_path):
    # Check if the file is a.docx file
    if filename.endswith(".docx"):
        # Construct the full file path
        file_path = os.path.join(directory_path, filename)

        # Create a Docx2txtLoader instance for the current file
        loader = Docx2txtLoader(file_path)
        
        # Load the data from the.docx file
        data = loader.load()
        
        # Do something with the loaded data (e.g., print it)
        print(f"Loaded data from {file_path}:")
        print(data)
        print("\n")  # Add a newline for better readability between files