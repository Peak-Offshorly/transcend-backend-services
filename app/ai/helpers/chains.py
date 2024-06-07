from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.output_parsers import StrOutputParser
from app.ai.const import OPENAI_API_KEY

# GPT_MODEL = "gpt-4-1106-preview"
# GPT_MODEL = "gpt-3.5-turbo-0125"
GPT_MODEL = "gpt-4o-2024-05-13"

def generate_actions(docs, strengths, weaknesses, chosen_strength, chosen_weakness):
  print("Generating answer")

  prompt = PromptTemplate(
  # todo: add a format -- should be JSON ? One for strength and One for weakness. Have 5 for each.
  template="""
    <|begin_of_text|>
    <|start_header_id|>system<|end_header_id|>
    You are an expert at creating Leadership Development Plans. Employees are assessed on their strengths and weaknesses as a leader and your task is to suggest improvement strategies in the form of a comprehensive and insightful development plan. The employee has answered a set of questions to identify their top 5 strengths and weaknesses.

    It has been identified that their top 5 strengths are: {strengths} and their top 5 weaknesses are: {weaknesses}.

    The employee will give you their chosen strength and weakness. Your task is to provide 10 detailed development actions that are feasible, measurable, and time-bound in order to guide the employee in strengthening and leveraging their strengths and in order to address and improve their weaknesses. You should provide exactly 5 actions for the chosen strength and exactly 5 actions for the chosen weakness. Each action should be specific, actionable, and relevant to the employee's chosen strength and weakness.

    Provide your answer in a JSON format with "strength" and "weakness" as keys. Each should have a list of 5 actions as values. Each action in the list should be an object that contains the name, details, importance, and measurement. The name pertains to the name or title of the action, the details are the description and specifics of the action, the importance is the significance of the action in developing the employee's leadership skills, and the measurement is how the action can be measured over time. Be as detailed and precise as possible in your response.

    Use the following pieces of retrieved context to help GUIDE your answer. Your answer is not constrained to these pieces and you may use knowledge beyond the retrieved context, but take a deep breath and thoroughly make sure the details you generate are factual and reasonable.
    Context: {context}

    Make sure to understand the task you are given and provide a detailed, insightful, and correctly-formatted response that is relevant to the employee's chosen strength and weakness.
    
    <|eot_id|><|start_header_id|>user<|end_header_id|>
    Chosen strength: {chosen_strength} and chosen weakness: {chosen_weakness} to work on.

    Answer: <|eot_id|><|start_header_id|>assistant<|end_header_id|>
    """,
    input_variables=["strengths", "weaknesses", "context", "chosen_strength", "chosen_weakness"],
    )
  
  llm = ChatOpenAI(model=GPT_MODEL,  openai_api_key=OPENAI_API_KEY, temperature=0)

  # chain = prompt | llm | StrOutputParser()
  chain = prompt | llm | JsonOutputParser()

  generation = chain.invoke({"strengths": strengths, "weaknesses": weaknesses, "context": docs, "chosen_strength": chosen_strength, "chosen_weakness": chosen_weakness})
  # print(generation)
  return generation


#add hallucination checker and formatting grader function
def check_answer():
  llm_model = ChatOpenAI(model=GPT_MODEL, openai_api_key=OPENAI_API_KEY, temperature=0)

  #todo improve prompt so that it gives 3 answers for the json object. 1 for checking if the answer is grounded by the docs, 1 for checking if the answer is relevant, 1 for correct format
  #todo: add formatting prompt
  prompt = PromptTemplate(
    template="""
      <|begin_of_text|>
        <|start_header_id|>system<|end_header_id|> You are a grader assessing two things. The first one is to assess whether an answer is grounded in / supported by a set of facts given by the user. Give a binary score 'yes' or 'no' score to indicate whether the answer is grounded in / supported by a set of facts. Provide the binary score as a field in a JSON object with the key 'facts' and no preamble or explanation. The second one is to assess whether the answer is relevant to the user's strength and weakness. Give a binary score 'yes' or 'no' score to indicate whether the answer is relevant. Provide the binary score as a field in the same JSON object with the key 'answer' and no preamble or explanation.
        
      <|eot_id|>
        <|start_header_id|>user<|end_header_id|>
        Here are the facts:
        \n ------- \n
        {documents} 
        \n ------- \n
        Here is the answer: {generation}
      <|eot_id|>
      
      <|start_header_id|>assistant<|end_header_id|>""",
      input_variables=["generation", "documents"],
    )

  hallucination_grader = prompt | llm_model | JsonOutputParser()
  # hallucination_grader.invoke({"documents": docs, "generation": generation})

#add answer grader here