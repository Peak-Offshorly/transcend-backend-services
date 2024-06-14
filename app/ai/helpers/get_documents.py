from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser

# GPT_MODEL = "gpt-4-1106-preview"
# GPT_MODEL = "gpt-3.5-turbo-0125"
GPT_MODEL = "gpt-4o-2024-05-13"

from app.ai.const import OPENAI_API_KEY
def grade_docs(input_data, retrieved_docs, filename, model=GPT_MODEL):
  # print("Grading Retrieved Docs")
  llm_model = ChatOpenAI(model=model, openai_api_key=OPENAI_API_KEY, temperature=0)
  #todo improve prompt to be about the 
  prompt = PromptTemplate(
    template="""
      <|begin_of_text|>
      <|start_header_id|>system<|end_header_id|>
      You are a grader assessing relevance of a retrieved document to a user question. If the document contains keywords related to the user question, grade it as relevant. It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
      
      Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question. \n
      Provide the binary score as a JSON with a single key 'score' and no preamble or explanation.
      
      <|eot_id|>
      <|start_header_id|>user<|end_header_id|>
      Here are the retrieved document from the file {filename}:
        \n\n {documents} \n\n
      Here is the user data: {input} \n
      <|eot_id|>
    
      <|start_header_id|>assistant<|end_header_id|>
    """,
    input_variables=["input", "filename", "documents"],
  )

  retrieval_grader = prompt | llm_model | JsonOutputParser()

  # Expected Output: {'score': 'yes'}  or {'score': 'no'}
  output = retrieval_grader.invoke({"input": input_data, "filename": filename, "documents": retrieved_docs})
  # print("Output", output)
  return output

def format_docs(docs):
  return "\n\n".join(doc.page_content for doc in docs)

def get_docs(vectorstore, input_data):
  print("Retrieving relevant documents")
  retrieved_docs = vectorstore.similarity_search(query=input_data, k=5)
  filtered_docs = []
  for idx, doc in enumerate(retrieved_docs):
    # print(f"Doc {idx}")
    #filename is for more context on what document it came from
    filename = doc.metadata['filename']
    docs_grade = grade_docs(input_data, doc.page_content, filename)
    if docs_grade["score"] == "yes":
      filtered_docs.append(doc)

  #todo: ADD A FALLBACK FOR NO RELEVANT DOCS
  if len(filtered_docs) == 0:
    print("No relevant documents found")
    return retrieved_docs
  else:
    final_docs = format_docs(filtered_docs)
    return final_docs