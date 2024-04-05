from typing import Optional
from uuid import UUID
from pydantic import BaseModel

### sample
class HealthResponse(BaseModel):
    status: str

class SignUpSchema(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str

class LoginSchema(BaseModel):
    email: str
    password: str


