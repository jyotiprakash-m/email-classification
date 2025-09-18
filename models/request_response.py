from typing import  Literal,Dict, Optional
from fastapi import UploadFile
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
    password: str
    provider: str

# Email content schema
class EmailClassificationRequest(BaseModel):
    email_content: str
    
# Response model for email classification
class EmailClassificationResponse(BaseModel):
    predicted_department: str
    confidence: float
    all_probabilities: Dict[str, float]
    
    
# Store PDF file
class StorePDFRequest(BaseModel):
    file: UploadFile  # or use str if storing file path, or UploadFile if using FastAPI

# Classification request for graph
class ClassifyEmailRequest(BaseModel):
    userId: str
    orgId: str
    offset: Optional[str]
    limit: Optional[int]

# Reply email request
class ReplyEmailRequest(BaseModel):
    userId: str
    tone: str
    email_body: str
    tool_instructions: Optional[str]