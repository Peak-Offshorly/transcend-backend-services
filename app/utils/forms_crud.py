from uuid import UUID
from typing import Optional, List
from sqlalchemy import delete
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.future import select
from app.database.models import Forms, Questions, Options, Answers
from app.schemas.models import FormSchema, QuestionSchema, OptionSchema


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

def mind_body_form_questions_options_get_all(form_name: str, user_id: str, questions: List[str], categories: List[str], weights: List[int], sprint_number: Optional[int] = None,
                                    options: Optional[List[str]] = None, option_type: Optional[str] = None, trait_name: Optional[str] = None) -> FormSchema:
    
  question_schemas = []
  
  # The points for each choice would be put as the type field for the Option
  option_point = 1

  # for question, weight, category in zip(questions, weights, categories):
  for index, (question, weight, category) in enumerate(zip(questions, weights, categories)):
      # Initialize an empty list to hold OptionSchema instances for the current question
      option_schemas = []

      for option in options[index]:
        # Create an OptionSchema instance for the current option
        option_schema = OptionSchema(
            name=option,
            type=str(option_point),
            trait_name=trait_name
        )
        # Append the OptionSchema instance to the list of option schemas
        option_schemas.append(option_schema)
        option_point += 1

      # Create a QuestionSchema instance for the current question with its options
      question_schema = QuestionSchema(
          name=question,
          option_type=option_type,
          category=category,
          options=option_schemas,
          rank=weight
      )
      # Append the QuestionSchema instance to the list of question schemas
      question_schemas.append(question_schema)
      option_point = 1

  # Create a FormSchema instance with the fetched questions and options
  form_data = FormSchema(
      name=form_name,
      user_id=user_id,
      questions=question_schemas,
      sprint_number=sprint_number
  )
  return form_data

# Creating FormSchema for other set of questions/options
def form_questions_options_get_all(form_name: str, user_id: str, questions: List[str], category: str, ranks: List[int], sprint_number: Optional[int] = None,
                                    sprint_id: Optional[UUID] = None, options: Optional[List[str]] = None, option_type: Optional[str] = None, trait_name: Optional[str] = None) -> FormSchema:
    
  question_schemas = []
  
  for question, rank in zip(questions, ranks):
      # Initialize an empty list to hold OptionSchema instances for the current question
      option_schemas = []

      for option in options:
          # Create an OptionSchema instance for the current option
          option_schema = OptionSchema(
              name=option,
              type=option_type,
              trait_name=trait_name
          )
          # Append the OptionSchema instance to the list of option schemas
          option_schemas.append(option_schema)

      # Create a QuestionSchema instance for the current question with its options
      question_schema = QuestionSchema(
          name=question,
          option_type=option_type,
          category=category,
          options=option_schemas,
          rank=rank
      )
      # Append the QuestionSchema instance to the list of question schemas
      question_schemas.append(question_schema)

  # Create a FormSchema instance with the fetched questions and options
  form_data = FormSchema(
      name=form_name,
      user_id=user_id,
      questions=question_schemas,
      sprint_number=sprint_number,
      sprint_id = sprint_id
  )
  return form_data

# Creating Form for other set of questions/options
async def forms_create_one(db: Session, form: FormSchema):
  db_form = Forms(name=form.name, user_id=form.user_id, sprint_number=form.sprint_number, sprint_id=form.sprint_id)
  db.add(db_form)
  db.flush()

  for question in form.questions:
    db_question = Questions(name=question.name, form_id=db_form.id, option_type=question.option_type, category=question.category, rank=question.rank)
    db.add(db_question)
    db.flush()

    for option in question.options:
      db_option = Options(name=option.name, type=option.type, trait_name=option.trait_name, question_id=db_question.id)
      db.add(db_option)

  # Commit the transaction to save all changes to the database
  db.commit()

  # Return the created form with its questions and options
  return { "form": form, "form_id": db_form.id }

# 1 form, all questions, all options for that question
def forms_with_questions_options_get_all(db: Session, name: str, user_id: str):
  form = db.query(Forms).options(
    joinedload(Forms.questions).subqueryload(Questions.options)
    ).filter(Forms.name == name, Forms.user_id == user_id).first()

  return form

# 1 form, all questions, all options for that question with sprint_id
def forms_with_questions_options_sprint_id_get_all(db: Session, name: str, user_id: str, sprint_id: UUID):
  form = db.query(Forms).options(
    joinedload(Forms.questions).subqueryload(Questions.options)
    ).filter(Forms.name == name, Forms.user_id == user_id, Forms.sprint_id == sprint_id).first()

  return form

# 1 form all questions, options, and answers
def forms_with_questions_options_answers_get_all(db: Session, name: str, user_id: str):
  form = db.query(Forms).options(
      joinedload(Forms.questions).subqueryload(Questions.options),
      joinedload(Forms.questions).subqueryload(Questions.answers)
  ).filter(Forms.user_id == user_id, Forms.name == name).first()
  
  form_type = FormSchema.from_orm(form)

  return form_type

# Gets all Forms based on form name and user_id
def forms_get_all(db: Session, name: str, user_id: str):
  return db.query(Forms).filter(Forms.name == name, Forms.user_id == user_id).all()

def forms_get_one(db: Session, id: UUID):
  
  return db.query(Forms).filter_by(id=id).one()

def delete_form_and_associations(db: Session, form_id: UUID):
    # Find the form
    form = db.execute(select(Forms).where(Forms.id == form_id)).scalar_one_or_none()
    
    if not form:
        raise ValueError("Form not found")

    # Find all questions associated with the form
    questions = db.execute(
        select(Questions).where(Questions.form_id == form_id)
    ).scalars().all()

    # Collect question IDs
    question_ids = [question.id for question in questions]

    # Delete answers associated with the form and its questions
    db.execute(
        delete(Answers).where((Answers.form_id == form_id))
    )

    # Delete options associated with each question
    db.execute(
        delete(Options).where(Options.question_id.in_(question_ids))
    )

    # Delete questions associated with the form
    db.execute(
        delete(Questions).where(Questions.form_id == form_id)
    )

    # Finally, delete the form itself
    db.execute(
        delete(Forms).where(Forms.id == form_id)
    )

    db.commit()