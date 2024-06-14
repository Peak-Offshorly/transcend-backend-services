from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.output_parsers import StrOutputParser
from app.ai.const import OPENAI_API_KEY
from app.ai.helpers.tokens import count_tokens

# GPT_MODEL = "gpt-4-1106-preview"
# GPT_MODEL = "gpt-3.5-turbo-0125"
GPT_MODEL = "gpt-4o-2024-05-13"

def generate_actions(trait_type, docs, initial_questions_with_answers, five_traits, chosen_trait, trait_practice, company_size, industry, employee_role, role_description):
  print("Generating answer")

  prompt = PromptTemplate(
  template="""
    <|begin_of_text|>
    <|start_header_id|>system<|end_header_id|>
    You are an expert at creating detailed step-by-step actionable improvement points for a Leadership Development Plan. 

    The employee will give you their personal and company details, their answers to a leadership questionnaire, their {type} as a leader, and the practice they want to focus on for their chosen {type}.
    
    Your task is to provide 5 detailed personal development actions that are feasible, measurable, and time-bound in order to guide the employee in leveraging and improving their {type}. Provide exactly 5 actions for the chosen {type}.

    Provide your answer in a JSON format with "actions" as the key. It should contain a list of 5 actions as values. Each action in the list should be an object that contains the name, details, importance, and measurement.
    The name pertains to the name or title of the action. 
    The details contain the thorough details or information for the action as instructed below The details for each action, which should be 2-3 sentences, must ALWAYS include the following:
    - Address the chosen {type} and the respective practice that the employee wants to focus on
    - Be as thorough and specific in terms of what the employee should do
    - Include a clear frequency or schedule (e.g., daily, weekly)
    - Be clear on the materials, tools, or resources required
    - Provide a step-by-step improvement strategy that is comprehensive and insightful
    - Be practical and reasonable given the employee's role and the company's context
    - Be measurable in terms of progress and impact on the employee's leadership skills
    
    The importance is the significance of the action in developing the employee's leadership skills.
    The measurement is how the action can be measured over time. Be as detailed and precise as possible in your response.

    Also use the following pieces of retrieved context to help GUIDE your answer. Your answer is not constrained to these pieces and you may use knowledge beyond the retrieved context, but take a deep breath and thoroughly make sure the details you generate are factual and reasonable.
    Context: {context}

    Make sure to understand the task you are given and provide a detailed, insightful, and correctly-formatted response that is relevant to the employee's details and needs.
    
    <|eot_id|><|start_header_id|>user<|end_header_id|>
    Use the given employee's details and answers to help finetune your answer. 

    Leadership Questionnaire Answers:
    {initial_questions}
    
    Employee Details:
    Industry: {industry}
    Role: {employee_role}
    Role Description: {role_description}
    Company Size: {company_size} employees

    It has been identified that their top 5 {type}s are: {five_traits}.

    They want to work on this {type}: "{chosen_trait}"
    Focused on their identified practice for that {type}: "{trait_practice}"

    Answer: <|eot_id|><|start_header_id|>assistant<|end_header_id|>
    """,
    input_variables=["type", "context", "initial_questions", "five_traits", "chosen_trait", "trait_practice", "company_size", "industry", "employee_role", "role_description"],
    )
  
  data_to_tokenize = [
    trait_type,
    prompt.template,
    docs,
    initial_questions_with_answers,
    five_traits,
    chosen_trait,
    trait_practice,
    company_size,
    industry,
    employee_role,
    role_description
  ]
  
  encoding_model = "o200k_base"
  tokens_total = sum(count_tokens(element, encoding_model) for element in data_to_tokenize)
  print(f"Tokens Used: {tokens_total}")
  
  llm = ChatOpenAI(model=GPT_MODEL,  openai_api_key=OPENAI_API_KEY, temperature=0)

  # chain = prompt | llm | StrOutputParser()
  chain = prompt | llm | JsonOutputParser()

  inputs = {
    "type": trait_type,
    "context": docs,
    "initial_questions": initial_questions_with_answers,
    "five_traits": five_traits,
    "chosen_trait": chosen_trait,
    "trait_practice": trait_practice,
    "company_size": company_size,
    "industry": industry,
    "employee_role": employee_role,
    "role_description": role_description
  }

  response = chain.invoke(inputs)
  # print(generation)
  return response


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