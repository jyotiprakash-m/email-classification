from fastapi import FastAPI, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from contextlib import asynccontextmanager
from core.database import init_db
from api import desc
from api.v1 import classify_email_api
import secrets
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from api.v1.org_functionality_api import router as org_router
from api.v1.store_vectors_pdf_api import router as pdf_router
from api.v1.email_classification_graph_api import router as email_graph_router
from api.v1.reply_graph_api import router as reply_graph_router
from api.v1.rag_retrieval_api import router as rag_router
from dotenv import load_dotenv
load_dotenv()
from langsmith import Client

# ✅ Setup LangSmith client (optional, useful if you want to log manually too)
client = Client()

security = HTTPBasic()

def basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "password")
    if not (correct_username and correct_password):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Basic"})

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield 

app = FastAPI(title="Email Classification API", lifespan=lifespan, docs_url=None, redoc_url=None)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(desc.router, dependencies=[Depends(basic_auth)])
app.include_router(classify_email_api.router, dependencies=[Depends(basic_auth)])
app.include_router(org_router, dependencies=[Depends(basic_auth)])
app.include_router(pdf_router, dependencies=[Depends(basic_auth)])
app.include_router(email_graph_router, dependencies=[Depends(basic_auth)])
app.include_router(reply_graph_router, dependencies=[Depends(basic_auth)])
app.include_router(rag_router, dependencies=[Depends(basic_auth)])


# Update the Swagger UI documentation endpoint with basic authentication
@app.get("/docs", include_in_schema=False)
def custom_swagger_ui(credentials: HTTPBasicCredentials = Depends(security)):
    basic_auth(credentials)
    return get_swagger_ui_html(openapi_url="/openapi.json", title=app.title)

# Update the ReDoc documentation endpoint with basic authentication
@app.get("/redoc", include_in_schema=False)
def custom_redoc(credentials: HTTPBasicCredentials = Depends(security)):
    basic_auth(credentials)
    return get_redoc_html(openapi_url="/openapi.json", title=app.title)

# uv run uvicorn main:app --reload