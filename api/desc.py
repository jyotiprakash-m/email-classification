from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def greeting():
 
    return {"message": "Hello, welcome to the Email Classification API!"}