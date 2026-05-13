from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.models.schemas import (
    OrgCreate, OrgResponse, TeamCreate, TeamResponse,
    InviteCreate, MemberResponse,
)
from backend.services.teams import (
    create_org, get_user_orgs, get_org, get_org_members,
    create_team, get_org_teams, invite_member, accept_invitation,
    remove_member, is_org_owner_or_admin,
)
from backend.services.auth import get_current_user
from backend.models.user import User

router = APIRouter(prefix="/api/orgs", tags=["organizations"])


@router.post("", response_model=OrgResponse, status_code=201)
def create_organization(payload: OrgCreate, db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    return create_org(db, current_user.id, payload.name, payload.slug, payload.description)


@router.get("")
def list_organizations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_user_orgs(db, current_user.id)


@router.get("/{org_id}", response_model=OrgResponse)
def get_organization(org_id: int, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    org = get_org(db, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    org.member_count = len(get_org_members(db, org_id))
    return org


@router.get("/{org_id}/members")
def list_members(org_id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    return get_org_members(db, org_id)


@router.delete("/{org_id}/members/{user_id}")
def delete_member(org_id: int, user_id: int, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    if not is_org_owner_or_admin(db, org_id, current_user.id):
        raise HTTPException(status_code=403, detail="Only org owners can remove members")
    if not remove_member(db, org_id, user_id):
        raise HTTPException(status_code=400, detail="Cannot remove member")
    return {"detail": "Member removed"}


@router.post("/{org_id}/teams", response_model=TeamResponse, status_code=201)
def create_team_for_org(org_id: int, payload: TeamCreate, db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    if not is_org_owner_or_admin(db, org_id, current_user.id):
        raise HTTPException(status_code=403, detail="Only org owners can create teams")
    if payload.org_id != org_id:
        raise HTTPException(status_code=400, detail="Organization ID mismatch")
    return create_team(db, org_id, payload.name, payload.description)


@router.get("/{org_id}/teams")
def list_teams(org_id: int, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    return get_org_teams(db, org_id)


@router.post("/invitations", status_code=201)
def invite(payload: InviteCreate, db: Session = Depends(get_db),
           current_user: User = Depends(get_current_user)):
    if not is_org_owner_or_admin(db, payload.org_id, current_user.id):
        raise HTTPException(status_code=403, detail="Only org owners can invite members")
    invitation = invite_member(db, payload.org_id, payload.email, payload.role)
    return {"token": invitation.token, "email": payload.email, "expires_at": invitation.expires_at}


@router.post("/invitations/{token}/accept")
def accept_invite(token: str, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    if not accept_invitation(db, token, current_user.id):
        raise HTTPException(status_code=400, detail="Invalid or expired invitation")
    return {"detail": "Invitation accepted"}
