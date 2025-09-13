from typing import  Literal,Dict, Optional
from sqlmodel import SQLModel, Field
from pydantic import BaseModel, EmailStr

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

# Email content schema
class EmailClassificationRequest(BaseModel):
    email_content: str
    
# Response model for email classification
class EmailClassificationResponse(BaseModel):
    predicted_department: str
    confidence: float
    all_probabilities: Dict[str, float]