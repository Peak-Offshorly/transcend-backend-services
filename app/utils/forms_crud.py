from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from app.database.models import Forms, Questions, Options, Answers
from app.schemas.models import FormSchema, QuestionSchema, OptionSchema, AnswerSchema

from sqlalchemy.orm import Session
from fastapi import HTTPException

def form_initial_questions_with_options_get_all(db: Session, form_name: str, user_id: str, form_id: Optional[str]) -> FormSchema:
    questions = db.query(Questions).filter(Questions.category == 'INITIAL_QS').all()
    question_schemas = []

    for question in questions:
        # Initialize an empty list to hold OptionSchema instances for the current question
        option_schemas = []
        # Fetch options for the current question
        options = db.query(Options).filter(Options.question_id == question.id).all()

        for option in options:
            # Create an OptionSchema instance for the current option
            option_schema = OptionSchema(
                id=option.id,
                name=option.name,
                type=option.type,
                trait_name=option.trait_name,
                question_id=option.question_id
            )
            # Append the OptionSchema instance to the list of option schemas
            option_schemas.append(option_schema)

        # Create a QuestionSchema instance for the current question with its options
        question_schema = QuestionSchema(
            id=question.id,
            form_id=form_id,
            name=question.name,
            option_type=question.option_type,
            options=option_schemas
        )
        # Append the QuestionSchema instance to the list of question schemas
        question_schemas.append(question_schema)

    # Create a FormSchema instance with the fetched questions and options
    form_data = FormSchema(
        id=form_id,
        name=form_name,
        user_id=user_id,
        questions=question_schemas
    )

    return form_data

# Creating Form for initial questions, since initial questions/options are shared they are not added back to the DB
def forms_create_one_initial_questions_form(db: Session, form: FormSchema):
  db_form = Forms(name=form.name, user_id=form.user_id)
  db.add(db_form)
  db.flush()
  
  # Commit to database
  db.commit()

  form_data = form_initial_questions_with_options_get_all(db=db, form_id=db_form.id, form_name=form.name, user_id=form.user_id)

  # Return Form data with form_id
  return form_data

# 1 form all questions, options, and answers for initial questions
def forms_with_initial_questions_options_answers_get_all(db: Session, name: str, user_id: str):
  form = db.query(Forms).options(
      joinedload(Forms.answers)
  ).filter(Forms.user_id == user_id, Forms.name == name).first()
  
  form_type = FormSchema.model_validate(form)

  return form_type

# Creating Form for other set of questions/options
def forms_create_one(db: Session, form: FormSchema):
  db_form = Forms(name=form.name, user_id=form.user_id)
  db.add(db_form)
  db.flush()

  for question in form.questions:
    db_question = Questions(name=question.name, form_id=db_form.id, option_type=question.option_type)
    db.add(db_question)
    db.flush()

    for option in question.options:
      db_option = Options(name=option.name, type=option.type, question_id=db_question.id)
      db.add(db_option)
  # Commit the transaction to save all changes to the database
  db.commit()

  # Return the created form with its questions and options
  return form

# 1 form, all questions, all options for that question
def forms_with_questions_options_get_all(db: Session, name: str, user_id: str):
  form = db.query(Forms).options(
    joinedload(Forms.questions).subqueryload(Questions.options)
    ).filter(Forms.name == name, Forms.user_id == user_id).first()

  return form

# 1 form all questions, options, and answers
def forms_with_questions_options_answers_get_all(db: Session, name: str, user_id: str):
  form = db.query(Forms).options(
      joinedload(Forms.questions).subqueryload(Questions.options),
      joinedload(Forms.questions).subqueryload(Questions.answers)
  ).filter(Forms.user_id == user_id, Forms.name == name).first()
  
  form_type = FormSchema.from_orm(form)

  return form_type

def forms_get_all(db: Session, id: UUID, user_id: UUID):
  #db.query(Forms).filter_by(id=id).one()
  return db.query(Forms).all()

def forms_get_one(db: Session, id: UUID):
  
  return db.query(Forms).filter_by(id=id).one()
