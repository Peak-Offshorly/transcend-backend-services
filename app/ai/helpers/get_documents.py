from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser

# GPT_MODEL = "gpt-4-1106-preview"
# GPT_MODEL = "gpt-3.5-turbo-0125"
GPT_MODEL = "gpt-4o-2024-05-13"

from app.ai.const import OPENAI_API_KEY
def grade_docs(trait, practice, retrieved_docs, filename, model=GPT_MODEL):
  # print("Grading Retrieved Docs")
  llm_model = ChatOpenAI(model=model, openai_api_key=OPENAI_API_KEY, temperature=0)
  prompt = PromptTemplate(
    template="""
      <|begin_of_text|>
      <|start_header_id|>system<|end_header_id|>
      You are a grader assessing relevance of multiple retrieved documents to a user question. If the document contains keywords or related words to the user question, grade it as relevant. It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
      
      Give a binary score 'yes' or 'no' score for each document to indicate whether the document is relevant to the question with no preamble or explanation. \n
      Provide the scores as a JSON with the index of the documents as the keys according to the order of the given documents.
      
      <|eot_id|>
      <|start_header_id|>user<|end_header_id|>
      Documents:

        \n\n {documents} \n\n
      Here is the user data:
        - {trait}
        - {practice}
        \n
      <|eot_id|>
    
      <|start_header_id|>assistant<|end_header_id|>
    """,
    input_variables=["documents", "trait", "practice"],
  )

  retrieval_grader = prompt | llm_model | JsonOutputParser()

  output = retrieval_grader.invoke({"documents": retrieved_docs, "trait": trait, "practice": practice})
  # print("Output", output)
  return output

def format_docs(docs):
  return "\n\n".join(doc.page_content for doc in docs)

def get_docs(vectorstore, trait, practice):
  
  # print("Retrieving relevant documents")
  query = f"{trait} - {practice}"
  retrieved_docs = vectorstore.similarity_search(query=query, k=5)
  retrieved_docs_string = ""
  for idx, doc in enumerate(retrieved_docs):
    # print(f"Doc {doc.page_content}")  
    #filename is for more context on what document it came from
    filename = doc.metadata['filename']
    retrieved_docs_string += f"""
      Document {idx} with filename '{filename}':
        \n {doc.page_content} \n
      \n
    """

  filtered_docs = []
  graded_docs = grade_docs(trait, practice, retrieved_docs_string, filename)

  for key, val in graded_docs.items():
    if val == "yes":
      filtered_docs.append(retrieved_docs[int(key)])

  # print("filtered docs", filtered_docs)

  #todo: ADD A FALLBACK FOR NO RELEVANT DOCS
  if len(filtered_docs) == 0:
    # print("No relevant documents found")
    # return retrieved_docs
    return ""
  else:
    final_docs = format_docs(filtered_docs)
    return final_docs