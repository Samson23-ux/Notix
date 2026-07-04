from uuid import UUID
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


from app.api.models.user import UserType


class UserBase(BaseModel):
    type: UserType
    is_active: bool = False
    is_verified: bool = False

    model_config = ConfigDict(from_attributes=True)


class GoogleUser(UserBase):
    google_id: Optional[str] = None
    google_email: Optional[EmailStr] = None


class GithubUser(UserBase):
    github_id: Optional[str] = None
    github_email: Optional[EmailStr] = None


class EmailUser(UserBase):
    email: Optional[EmailStr] = None


class UserInDB(GoogleUser, GithubUser, EmailUser):
    hashed_password: Optional[str] = None


class GoogleUserResponse(GoogleUser):
    id: UUID


class GithubUserResponse(GithubUser):
    id: UUID


class EmailUserResponse(EmailUser):
    id: UUID
