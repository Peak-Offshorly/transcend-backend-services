from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from app.database.models import Forms, Questions, Options, Answers
from app.schemas.models import FormSchema, QuestionSchema, OptionSchema, AnswerSchema

from sqlalchemy.orm import Session
from fastapi import HTTPException


def forms_create_one(db: Session, form: FormSchema):
  db_form = Forms(name=form.name, user_id=form.user_id)
  db.add(db_form)
  db.flush()

  for question in form.questions:
    db_question = Questions(name=question.name, forms_id=db_form.id, option_type=question.option_type)
    db.add(db_question)
    db.flush()

    for option in question.options:
      db_option = Options(name=option.name, type=option.type, question_id=db_question.id)
      db.add(db_option)
  # Commit the transaction to save all changes to the database
  db.commit()

  # Return the created form with its questions and options
  return form

def forms_with_questions_get_one(db: Session, name: str, user_id: str):
  # Query the form with its associated questions, options, and answers
  form = db.query(Forms).options(
      joinedload(Forms.questions).subqueryload(Questions.options),
      joinedload(Forms.questions).subqueryload(Questions.answers)
  ).filter(Forms.user_id == user_id, Forms.name == name).one()
  
  form_type = FormSchema.from_orm(form)

  return form_type

def forms_with_questions_get_all(db: Session, name: str, user_id: str):
  # 1 form, all questions, all options for that question
  form = db.query(Forms).options(joinedload(Forms.questions).subqueryload(Questions.options)).filter(Forms.name == name, Forms.user_id == user_id).first()

  print(form)

  return form
  # return PydanticForm.from_orm(form)

def forms_with_questions_get_all(db: Session, id: UUID, user_id: UUID):
  db.query(Forms).filter_by(id=id).one()



  return db.query(Forms).all()

def forms_get_one(db: Session, id: UUID):
  
  return db.query(Forms).filter_by(id=id).one()
