from typing import Optional
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


