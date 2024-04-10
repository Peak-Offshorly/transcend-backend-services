import uuid
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.connection import Base, engine

class Traits(Base):
    __tablename__ = 'traits'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    trait = Column(String, index=True)
    questions = relationship("InitialQuestions", backref="traits")

class InitialQuestions(Base):
    __tablename__ = 'initial_questions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    question = Column(String, index=True)
    trait_id = Column(UUID(as_uuid=True), ForeignKey("traits.id"))

class InitialQuestionsChoices(Base):
    __tablename__ = 'initial_questions_choices'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("initial_questions.id"))
    choice = Column(String, index=True)

class Users(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True, index=True)
    email = Column(String, index=True)
    password = Column(String, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    initial_questions_response = relationship("UserInitialQuestionsResponse", backref="users")


class UserInitialQuestionsResponse(Base):
    __tablename__ = 'users_initial_questions_response'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    question_id = Column(UUID(as_uuid=True), ForeignKey("initial_questions.id"))
    choice_id = Column(UUID(as_uuid=True), ForeignKey("initial_questions_choices.id"))

Base.metadata.create_all(engine)
