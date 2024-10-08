from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str

class SignUpSchema(BaseModel):
    email: str
    first_name: str
    last_name: str
    mobile_number: str
    password: str

class UpdateUserSchema(BaseModel):
    id: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile_number: Optional[str] = None

class UserCompanyDetailsSchema(BaseModel):
    id: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    role: Optional[str] = None
    role_description: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True

class LoginSchema(BaseModel):
    email: str
    password: str

class TraitsSchema(BaseModel):
    id: Optional[UUID] = None
    user_id: Optional[str] = None
    name: str
    average: Optional[float] = None
    standard_deviation: Optional[float] = None
    total_raw_score: Optional[int] = None
    t_score: Optional[int] = None

class OptionSchema(BaseModel):
    id: Optional[UUID] = None
    name: str
    type: str
    trait_name: Optional[str] = None
    question_id: Optional[UUID] = None

    class Config:
        orm_mode = True
        from_attributes = True

class AnswerSchema(BaseModel):
    id: Optional[UUID] = None
    answer: str
    form_id: Optional[UUID] = None
    question_id: Optional[UUID] = None
    question_rank: Optional[int] = None
    question_category: Optional[str] = None
    option_id: Optional[UUID] = None
    option_type: Optional[str] = None
    trait_name: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True
        
class QuestionSchema(BaseModel):
    id: Optional[UUID] = None
    name: str
    category: Optional[str] = None
    form_id: Optional[UUID] = None
    option_type: str
    options: List[OptionSchema]
    rank: Optional[int] = None
    answer: Optional[AnswerSchema] = None
    class Config:
        orm_mode = True
        from_attributes = True

class FormSchema(BaseModel):
    id: Optional[UUID] = None
    name: str
    user_id: Optional[str] = None
    sprint_number: Optional[int] = None
    sprint_id: Optional[UUID] = None
    questions: Optional[List[QuestionSchema]] = None
    development_plan_id: Optional[UUID] = None
    class Config:
        orm_mode = True
        from_attributes = True

class FormAnswerSchema(BaseModel):
    form_id: UUID
    form_name: str
    user_id: str
    answers: List[AnswerSchema]
    class Config:
        orm_mode = True
        from_attributes = True

class ChosenTraitsSchema(BaseModel):
    user_id: str
    strength: TraitsSchema
    weakness: TraitsSchema
    class Config:
        orm_mode = True
        from_attributes = True

class PracticeSchema(BaseModel):
    id: Optional[UUID] = None
    name: Optional[str] = None
    user_id: Optional[str] = None
    question_id: Optional[UUID] = None
    chosen_trait_id: Optional[UUID] = None
    development_plan_id: Optional[UUID] = None
    class Config:
        orm_mode = True
        from_attributes = True

class ChosenPracticesSchema(BaseModel):
    user_id: str
    strength_practice: Optional[PracticeSchema] = None
    weakness_practice: Optional[PracticeSchema] = None
    class Config:
        orm_mode = True
        from_attributes = True

class PersonalPracticeSchema(BaseModel):
    name: Optional[str] = None
    class Config:
        orm_mode = True
        from_attributes = True

class ChosenPersonalPracticesSchema(BaseModel):
    user_id: str
    recommended_mind_body_category_id: UUID
    chosen_practices: Optional[List[PersonalPracticeSchema]] = None
    class Config:
        orm_mode = True
        from_attributes = True

class UserColleagueEmailsSchema(BaseModel):
    user_id: str
    emails: List[str]

class UserColleagueSurveyAnswersSchema(BaseModel):
    user_colleague_id: str
    q1_answer: int
    q2_answer: int
    q3_answer: int
    q4_answer: Optional[str]
    q5_answer: Optional[str]

class UserColleaguesStatusSchema(BaseModel):
    email: str
    survey_completed: bool

    class Config:
        orm_mode = True
        from_attributes = True

class DataFormSchema(BaseModel):
    form_name: Optional[str] = None
    user_id: str

class DevelopmentActionsSchema(BaseModel):
    user_id: str
    trait_type: str
class CompanyDataSchema(BaseModel):
    id: Optional[str] = None
    name: str
    company_photo_url: Optional[str] = None
    

    class Config:
        orm_mode = True
        from_attributes = True

class CustomTokenRequestSchema(BaseModel):
    user_id: str    

class AddUserToCompanySchema(BaseModel):
    user_id: str

class AddUserToCompanyDashboardSchema(BaseModel):
    user_email: str
    user_role: str


class CreateCompanyRequest(BaseModel):
    data: CompanyDataSchema
    users: Optional[List[AddUserToCompanyDashboardSchema]] = None
    
class PasswordChangeRequest(BaseModel):
    new_password: str
    old_password: str

class UpdatePersonalDetailsSchema(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile_number: Optional[str] = None
    job_title: Optional[str] = None
    password: str

class ResetPasswordRequest(BaseModel):
    email: str
    user_type: Optional[str] = None

class UpdateFirstAndLastNameSchema(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class ResendLinkSchema(BaseModel):
    email: str