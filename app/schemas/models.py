from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class SignUpSchema(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str

### sample
class HealthResponse(BaseModel):
    status: str


class Post(BaseModel):
    id: Optional[UUID]
    title: str
    description: str

    class Config:
        orm_mode = True


class DeletePostResponse(BaseModel):
    detail: str


class UpdatePost(BaseModel):
    id: UUID
    title: str
    description: str

    class Config:
        orm_mode = True