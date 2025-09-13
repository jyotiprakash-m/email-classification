from fastapi import FastAPI, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from contextlib import asynccontextmanager
from core.database import init_db
from api import desc
import secrets
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

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