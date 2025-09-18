from sqlmodel import Session, select
from models.schema import Org
from typing import List, Optional
from core.database import engine

# 1. Create Org
def create_org(org: Org) -> Org:
    with Session(engine) as session:
        session.add(org)
        session.commit()
        session.refresh(org)
        return org

# 2. Get all orgs of a user
def get_orgs_by_user(user_id: int) -> List[Org]:
    with Session(engine) as session:
        orgs = session.exec(select(Org).where(Org.userId == user_id)).all()
        return list(orgs)

# 3. Get org by orgid
def get_org_by_id(org_id: int) -> Optional[Org]:
    with Session(engine) as session:
        org = session.get(Org, org_id)
        return org
