from langchain.prompts import PromptTemplate
class DevelopmentActionsPrompts:
  def initial_generation_prompt():
    prompt = PromptTemplate(
    template="""
      <|begin_of_text|>
      <|start_header_id|>system<|end_header_id|>
      You are an expert at creating detailed step-by-step actionable improvement points for a Leadership Development Plan. 

      The employee will give you their personal and company details, their answers to a leadership questionnaire, their {type} as a leader, and the practice they want to focus on for their chosen {type}.
      
      Your task is to provide 3 detailed personal development actions that are feasible, measurable, and time-bound in order to guide the employee in leveraging and improving their {type}. Provide exactly 3 personalized actions for the chosen {type} that can be done within a span of 2 weeks on an individual level or a team level, depending on the chosen practice.

      Provide your answer in a JSON format with "actions" as the key. It should contain a list of 3 actions as values. Each action in the list should be an object that contains the name and details.
      
      The name pertains to the name or title of the action. 
      The details contain the thorough details or information for the action as instructed below. The details for each action, which should be AT MOST 20 words and must ALWAYS include the following:
      - Address the chosen {type} and the respective chosen practice that the employee wants to focus on
      - Should be primarily focused on the employee's personal development, but it can include the team if necessary
      - Be as thorough and specific in terms of what the employee should do
      - Include a clear frequency or schedule (e.g., daily, every other day, weekly, at the start or end of the week)
      - Provide a step-by-step improvement strategy that is comprehensive and insightful
      - Be practical and reasonable given the employee's role, the company's context, and the time frame
      - Be measurable in terms of progress and impact on the employee's leadership skills
      - Be time-bound within a span of 2 weeks

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

    return prompt

  def regeneration_prompt():
    prompt = PromptTemplate(
    template="""
      <|begin_of_text|>
      <|start_header_id|>system<|end_header_id|>
      You are an expert at creating detailed step-by-step actionable improvement points for a Leadership Development Plan. The employee would like a different set of actions from the ones you have provided before. You should regenerate new ones based on the employee's details and needs.

      The employee will give you their personal and company details, their answers to a leadership questionnaire, their {type} as a leader, and the practice they want to focus on for their chosen {type}. They will also provide the actions you have previously given them that they do not want.
      
      Your task is to regenerate and provide 3 new detailed personal development actions that are feasible, measurable, and time-bound in order to guide the employee in leveraging and improving their {type}. Provide exactly 3 new personalized actions for the chosen {type} that can be done within a span of 2 weeks on an individual level or a team level, depending on the chosen practice.

      Provide your new answer in a JSON format with "actions" as the key. It should contain a list of 3 actions as values. Each new action in the list should be an object that contains the name and details.
      
      The name pertains to the name or title of the action. 
      The details contain the thorough details or information for the action as instructed below. The details for each action, which should be AT MOST 20 words and must ALWAYS include the following:
      - Address the chosen {type} and the respective chosen practice that the employee wants to focus on
      - Should be primarily focused on the employee's personal development, but it can include the team if necessary
      - Be as thorough and specific in terms of what the employee should do
      - Include a clear frequency or schedule (e.g., daily, every other day, weekly, at the start or end of the week)
      - Provide a step-by-step improvement strategy that is comprehensive and insightful
      - Be practical and reasonable given the employee's role, the company's context, and the time frame
      - Be measurable in terms of progress and impact on the employee's leadership skills
      - Be time-bound within a span of 2 weeks

      Also use the following pieces of retrieved context to help GUIDE your new answer. Your answer is not constrained to these pieces and you may use knowledge beyond the retrieved context, but take a deep breath and thoroughly make sure the details you generate are factual and reasonable.
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

      The following are your previous actions that the employee does not want:
      {previous_actions}

      Answer: <|eot_id|><|start_header_id|>assistant<|end_header_id|>
      """,
      input_variables=["type", "context", "initial_questions", "five_traits", "chosen_trait", "trait_practice", "company_size", "industry", "employee_role", "role_description", "previous_actions"],
      )

    return prompt