from fastapi import APIRouter, HTTPException
from typing import List
from models.schema import Org, ProviderEnum
from services.org_service import create_org, get_orgs_by_user, get_org_by_id

router = APIRouter(prefix="/v1/orgs", tags=["Org Functionality"])

# 1. Create Org
@router.post("/create", response_model=Org)
async def api_create_org(org: Org):
	try:
		created_org = create_org(org)
		return created_org
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))

# 2. Get all orgs of a user
@router.get("/user/{user_id}", response_model=List[Org])
async def api_get_orgs_by_user(user_id: int):
	orgs = get_orgs_by_user(user_id)
	return orgs

# 3. Get org by orgid
@router.get("/{org_id}", response_model=Org)
async def api_get_org_by_id(org_id: int):
	org = get_org_by_id(org_id)
	if not org:
		raise HTTPException(status_code=404, detail="Org not found")
	return org
