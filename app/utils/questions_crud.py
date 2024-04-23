from typing import Optional
from sqlalchemy.orm import Session
from app.database.models import Forms, Questions, Options
from app.schemas.models import FormSchema, QuestionSchema, OptionSchema

# COULD BE BASIS FOR GETTING QUESTIONS FROM EXTERNAL FILE AND RETURNING A FORM SCHEMA
# ------------------------------
# def initial_questions_with_options_get_all(db: Session, form_name: str, user_id: str, form_id: Optional[str]) -> FormSchema:
#     questions = db.query(Questions).filter(Questions.category == 'INITIAL_QS').all()
#     question_schemas = []

#     for question in questions:
#         # Initialize an empty list to hold OptionSchema instances for the current question
#         option_schemas = []
#         # Fetch options for the current question
#         options = db.query(Options).filter(Options.question_id == question.id).all()

#         for option in options:
#             # Create an OptionSchema instance for the current option
#             option_schema = OptionSchema(
#                 id=option.id,
#                 name=option.name,
#                 type=option.type,
#                 trait_name=option.trait_name,
#                 question_id=option.question_id
#             )
#             # Append the OptionSchema instance to the list of option schemas
#             option_schemas.append(option_schema)

#         # Create a QuestionSchema instance for the current question with its options
#         question_schema = QuestionSchema(
#             id=question.id,
#             form_id=form_id,
#             name=question.name,
#             option_type=question.option_type,
#             options=option_schemas
#         )
#         # Append the QuestionSchema instance to the list of question schemas
#         question_schemas.append(question_schema)

#     # Create a FormSchema instance with the fetched questions and options
#     form_data = FormSchema(
#         id=form_id,
#         name=form_name,
#         user_id=user_id,
#         questions=question_schemas
#     )

#     return form_data
