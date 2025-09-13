from typing import  Literal
from sqlmodel import SQLModel, Field
from pydantic import EmailStr

# Request schema (no id, required for create)
class OrgCreate(SQLModel):
    userId: int
    email: EmailStr
    password: str
    provider: Literal["gmail", "outlook", "yahoo", "zoho"]

# Response schema (exclude password)
class OrgRead(SQLModel):
    id: int
    userId: int
    email: EmailStr
    provider: str
