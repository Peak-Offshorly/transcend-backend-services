from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str

class SignUpSchema(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str

class UpdateUserSchema(BaseModel):
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]

class LoginSchema(BaseModel):
    email: str
    password: str

class OptionSchema(BaseModel):
    id: Optional[UUID] = None
    name: str
    type: str
    question_id: Optional[UUID] = None

    class Config:
        orm_mode = True
        from_attributes = True

class AnswerSchema(BaseModel):
    id: Optional[UUID] = None
    answer: List[str]
    user_id: Optional[UUID] = None
    question_id: Optional[UUID] = None
    option_id: Optional[UUID] = None

    class Config:
        orm_mode = True
        from_attributes = True
        
class QuestionSchema(BaseModel):
    id: Optional[UUID] = None
    name: str
    form_id: Optional[UUID] = None
    option_type: str
    options: List[OptionSchema]
    answer: Optional[AnswerSchema] = None
    class Config:
        orm_mode = True
        from_attributes = True

class FormSchema(BaseModel):
    id: Optional[UUID] = None
    name: str
    user_id: Optional[str] = None
    questions: List[QuestionSchema]
    class Config:
        orm_mode = True
        from_attributes = True

class DataFormSchema(BaseModel):
    form_name: str
    user_id: str
