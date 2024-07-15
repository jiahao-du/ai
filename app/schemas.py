from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

from typing import Any, List, Optional


class KindsBase(BaseModel):
    id: Optional[int] = Field(0, description='')
    fname: Optional[str] = Field('', description='')
    fdescription: Optional[str] = Field('', description='')
    sname: Optional[str] = Field('', description='')
    sdescription: Optional[str] = Field('', description='')
    tname: Optional[str] = Field('', description='')
    tdescription: Optional[str] = Field('', description='')
    tdata_level: Optional[str] = Field('', description='')
    tregex: Optional[str] = Field('', description='')
    tsen_word: Optional[list] = Field([], description='')
    tif_sen: Optional[int] = Field(0, description='')


class ModelCostBase(BaseModel):
    manufacturer: Optional[str] = Field(..., description='')
    model_name: Optional[str] = Field(..., description='')
    input_price: Optional[str] = Field(..., description='')
    output_price: Optional[str] = Field(..., description='')
    train_price: Optional[str] = Field(..., description='')
    date: Optional[str] = Field(..., description='')
    unit: Optional[str] = Field(..., description='')


class PaginationRequest(BaseModel):
    page: int = 1
    page_size: int = 10


class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    display_name: str = None
    status: int
    is_superuser: bool


# class ContentSchema(BaseModel):
#     content: str = Field(..., description="内容")
#     role: str = Field(..., description="角色")


class PromptRequest(BaseModel):
    prompt: list = Field(..., description="prompt")
    uid: str = Field(..., description="uid")


class UserBase(BaseModel):
    username: str
    email: EmailStr
    is_superuser: Optional[bool] = False
    status: Optional[str] = 'active'
    display_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserOut(UserBase):
    id: int
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
