import uuid
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float 
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database.connection import Base, engine

class Users(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True, index=True)
    email = Column(String, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    role = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    form_id = Column(UUID(as_uuid=True), ForeignKey("forms.id"))

class Sprints(Base):
    __tablename__ = 'sprints'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(Integer, index=True)

class DevelopmentPlan(Base):
    __tablename__ = 'development_plan'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)

class UserDevelopmentPlan(Base):
    __tablename__ = 'user_development_plan'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    development_plan_id = Column(UUID(as_uuid=True), ForeignKey("development_plan.id"))

class Forms(Base):
    __tablename__ = 'forms'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    sprint_id = Column(String, ForeignKey("sprints.id"))

class UserTraits(Base):
    __tablename__ = 'user_traits'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    trait_id = Column(UUID(as_uuid=True), ForeignKey("traits.id"))
    form_id = Column(UUID(as_uuid=True), ForeignKey("forms.id"))
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"))
    t_score = Column(Integer, index=True)

class Questions(Base):
    __tablename__ = 'questions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    forms_id = Column(UUID(as_uuid=True), ForeignKey("forms.id"))
    option_type = Column(String, index=True)

class Traits(Base):
    __tablename__ = 'traits'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    average = Column(Float, index=True)
    standard_deviation = Column(Float, index=True)
    total_raw_score = Column(Integer, index=True)
    t_score = Column(Integer, index=True)
    option_id = Column(UUID(as_uuid=True), ForeignKey('options.id'))

class Options(Base):
    __tablename__ = 'options'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    type = Column(String, index=True)
    raw_score = Column(Integer, index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey('questions.id'))
    traits_id = Column(UUID(as_uuid=True), ForeignKey('traits.id'))

class Answers(Base):
    __tablename__ = 'answers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, ForeignKey('users.id'))
    question_id = Column(UUID(as_uuid=True), ForeignKey('questions.id'))
    option_id = Column(UUID(as_uuid=True), ForeignKey('options.id'))
    answer = Column(String, index=True)

class Practices(Base):
    __tablename__ = 'practices'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    score = Column(Integer, index=True)


Base.metadata.create_all(engine)
