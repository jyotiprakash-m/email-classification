from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import EmailStr

class ProviderEnum(str, Enum):
    gmail = "gmail"
    outlook = "outlook"
    yahoo = "yahoo"
    zoho = "zoho"

class Org(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    userId: int = Field(index=True)
    email: EmailStr
    password: str
    provider: ProviderEnum