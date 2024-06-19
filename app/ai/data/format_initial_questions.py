import json

def get_initial_questions():
  with open('app/ai/data/initial_questions.json') as json_file:
    data = json.load(json_file)

  return data

def get_initial_questions_with_answers(answers):
  initial_questions = get_initial_questions()["initial_questions"]

  data = ""

  for idx, question in enumerate(initial_questions):
    # question["answer"] = answers[idx].answer

    #todo: see if adding options is necessary
    options = ""
    for option in question["options_w_traits"]:
      options += f"""
        - {option['name']} ({option['trait']})\n
      """

    data += f"""
      [Question {idx+1}]
      Options:
      {options}
      Answer: {answers[idx].answer}\n\n
    """

  return data

# FORM_ANSWERS = {
#     "forms_and_answers": [
#         {
#             "id": "f9be02f6-d4de-4d36-b3ce-b3fc74775789",
#             "sprint_number": None,
#             "development_plan_id": None,
#             "name": "1_INITIAL_QUESTIONS",
#             "user_id": "jhqF9ocJn4fkWzQ2ztLTUZHvDp32",
#             "sprint_id": None,
#             "answers": [
#                 {
#                     "id": "1f2e0f9c-bda0-4d2a-85aa-35b55cbff647",
#                     "option_id": "375ace0f-32f9-4153-b957-efdae4d5fad3",
#                     "form_id": "f9be02f6-d4de-4d36-b3ce-b3fc74775789",
#                     "question_id": "909edff9-58e0-424d-b181-964c83538d68",
#                     "answer": "I prioritize long-term goals over short-term gains."
#                 },
#                 {
#                     "id": "712a52ce-7a61-4e1b-8c38-0d190f953db6",
#                     "option_id": "77a10218-642a-4bc6-b44f-cbf055e08d4b",
#                     "form_id": "f9be02f6-d4de-4d36-b3ce-b3fc74775789",
#                     "question_id": "c0242556-e3f6-432e-9435-1661d944bc92",
#                     "answer": "I provide a safe space for team members to express grievances."
#                 },
#                 {
#                     "id": "40e4d5c3-72ee-47d8-bb07-72f291f04c85",
#                     "option_id": "9535a086-f7d1-411f-8299-323eded687d7",
#                     "form_id": "f9be02f6-d4de-4d36-b3ce-b3fc74775789",
#                     "question_id": "9b98f17d-f831-4190-a447-c14900405cff",
#                     "answer": "I delegate tasks effectively, empowering my team."
#                 },
#                 {
#                     "id": "808da024-b829-4964-8eb0-73757aede12a",
#                     "option_id": "f6ca5947-9e53-4d5a-82be-f9481854e8b3",
#                     "form_id": "f9be02f6-d4de-4d36-b3ce-b3fc74775789",
#                     "question_id": "2f5712ac-dc1a-4e9d-b900-8934d4292d07",
#                     "answer": "I limit the number of active projects to maintain focus on what's most important."
#                 },
#                 {
#                     "id": "10dfc922-668d-481c-aa60-dbdb07283a5b",
#                     "option_id": "7f6c58e1-7341-4a2b-87c6-2b7b4bdd657b",
#                     "form_id": "f9be02f6-d4de-4d36-b3ce-b3fc74775789",
#                     "question_id": "58421fd1-2fd6-48aa-88d5-ba61e97f8288",
#                     "answer": "I proactively advocate for well-considered changes that propel our team forward."
#                 },
#                 {
#                     "id": "a7f44314-13fe-4e29-89b2-921ba9fa4db9",
#                     "option_id": "ecad3a3b-8c7a-43aa-bc09-9dadaf103e65",
#                     "form_id": "f9be02f6-d4de-4d36-b3ce-b3fc74775789",
#                     "question_id": "e38136a4-fbc7-487f-b859-d042e2f33b91",
#                     "answer": "I engage others in the decision-making process to foster commitment and support."
#                 },
#                 {
#                     "id": "b77fcf9a-6eeb-497b-b0dc-cb617e6f40cd",
#                     "option_id": "5d85519e-31ca-45ba-8994-e74f4b83c95c",
#                     "form_id": "f9be02f6-d4de-4d36-b3ce-b3fc74775789",
#                     "question_id": "b56ed5c7-a0cd-44e0-94d7-626873f571f2",
#                     "answer": "I make informed decisions even in complex situations."
#                 },
#                 {
#                     "id": "4b856495-ccec-4473-a97f-45da303f19f8",
#                     "option_id": "0b6be9a9-efa6-439c-9852-4562992a8a3e",
#                     "form_id": "f9be02f6-d4de-4d36-b3ce-b3fc74775789",
#                     "question_id": "ded949eb-442a-409a-96b0-389076ef2942",
#                     "answer": "I attract diverse and skilled talent to the organization."
#                 },
#                 {
#                     "id": "37cbe902-c3dc-4713-b65f-2f2db2edfb75",
#                     "option_id": "fda58ee9-7542-4332-9719-ec68f4523173",
#                     "form_id": "f9be02f6-d4de-4d36-b3ce-b3fc74775789",
#                     "question_id": "5b728898-331b-4d71-a9e4-e5b72c75049d",
#                     "answer": "I regularly share praise that is specific and genuine."
#                 },
#                 {
#                     "id": "4e267fcf-ff69-4d3e-b662-33ad132154fc",
#                     "option_id": "27e38bd9-6d43-49ee-9561-07a5ba9f6d73",
#                     "form_id": "f9be02f6-d4de-4d36-b3ce-b3fc74775789",
#                     "question_id": "bb9b8f15-ee06-4e86-bf9d-62323ccdd55c",
#                     "answer": "I ensure goals are specific and measurable with clear owners."
#                 },
#                 {
#                     "id": "f1bf5f8f-d6de-4731-b18e-da74219154a7",
#                     "option_id": "e831b56b-da22-445b-94cc-42457813f798",
#                     "form_id": "f9be02f6-d4de-4d36-b3ce-b3fc74775789",
#                     "question_id": "bde1511f-f7ff-4bf5-a653-4b52e3d5f41e",
#                     "answer": "I streamline processes for better efficiency and effectiveness."
#                 },
#                 {
#                     "id": "86691a52-eadf-4533-9ad5-957852acd688",
#                     "option_id": "b5d1cfdc-5ba3-43a9-8ad9-b1efdd22c79b",
#                     "form_id": "f9be02f6-d4de-4d36-b3ce-b3fc74775789",
#                     "question_id": "ee5b8817-3393-4d73-8a33-ca1485671b37",
#                     "answer": "I promote a healthy work-life balance for the team."
#                 },
#                 {
#                     "id": "05e436f2-f59c-4690-a093-ab352b74691c",
#                     "option_id": "31af8e70-a063-4cd9-941a-af1ba4141b01",
#                     "form_id": "f9be02f6-d4de-4d36-b3ce-b3fc74775789",
#                     "question_id": "1e81b17a-808f-48e8-9c61-b4a7fc31bfed",
#                     "answer": "I mentor and develop individuals to reach their potential."
#                 },
#                 {
#                     "id": "8211ead9-c122-494f-8b0c-b969f4b60b7c",
#                     "option_id": "f2f0f404-9874-40a7-a8a5-493a306edb3b",
#                     "form_id": "f9be02f6-d4de-4d36-b3ce-b3fc74775789",
#                     "question_id": "339acf96-6b9f-4f92-bb1b-6f45b8959080",
#                     "answer": "I match tasks with team members' strengths and interests."
#                 },
#                 {
#                     "id": "8f3a607c-4c9d-4fac-bb34-5a81bea1881f",
#                     "option_id": "479a8edd-65ab-4eb1-a4ee-441418c31d78",
#                     "form_id": "f9be02f6-d4de-4d36-b3ce-b3fc74775789",
#                     "question_id": "7bbf48d0-ceca-4646-9aa9-fe034ad1d0fa",
#                     "answer": "I proactively anticipate changes in my work or industry."
#                 },
#                 {
#                     "id": "a5d2d9c3-0e79-4b4e-8f60-4f7373d06d44",
#                     "option_id": "323e7459-1760-42b7-9eba-ed2573db9389",
#                     "form_id": "f9be02f6-d4de-4d36-b3ce-b3fc74775789",
#                     "question_id": "77649a5a-6dee-47e9-a035-ad74f1a9c343",
#                     "answer": "I effectively communicate the rationale for changes we want to make."
#                 },
#                 {
#                     "id": "f7977982-c02a-42c6-aa89-ba9001faac55",
#                     "option_id": "f73adab5-ca9f-473b-b980-91a0250f1651",
#                     "form_id": "f9be02f6-d4de-4d36-b3ce-b3fc74775789",
#                     "question_id": "65009ef4-4b5d-4df0-8797-115764b76e4f",
#                     "answer": "I advocate for and achieve exceptional standards in our work."
#                 },
#                 {
#                     "id": "a1184133-781a-40d7-9ab3-f103889ea135",
#                     "option_id": "2b9516e9-37b1-48c2-9a30-d4bbc477cfd1",
#                     "form_id": "f9be02f6-d4de-4d36-b3ce-b3fc74775789",
#                     "question_id": "a12ab86f-6302-4d7b-a547-96d1c9c87f38",
#                     "answer": "I excel in empathetic listening, ensuring team members feel heard and valued."
#                 }
#             ]
#         }
#     ]
# }
# print(get_initial_questions_with_answers(FORM_ANSWERS))