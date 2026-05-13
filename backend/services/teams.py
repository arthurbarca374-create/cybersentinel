from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from backend.models.team import Organization, Team, Membership, TeamMember, Invitation
from backend.models.user import User
import secrets
from datetime import datetime, timedelta


def create_org(db: Session, user_id: int, name: str, slug: str, description: Optional[str] = None) -> Organization:
    org = Organization(name=name, slug=slug, description=description, owner_id=user_id)
    db.add(org)
    db.commit()
    db.refresh(org)
    membership = Membership(user_id=user_id, org_id=org.id, role="owner")
    db.add(membership)
    db.commit()
    return org


def is_org_owner_or_admin(db: Session, org_id: int, user_id: int) -> bool:
    membership = db.query(Membership).filter(
        Membership.org_id == org_id,
        Membership.user_id == user_id,
        Membership.role.in_(["owner", "admin"]),
    ).first()
    return membership is not None


def get_user_orgs(db: Session, user_id: int) -> list[Organization]:
    membership_ids = db.query(Membership.org_id).filter(Membership.user_id == user_id)
    orgs = db.query(Organization).filter(Organization.id.in_(membership_ids)).all()
    if orgs:
        counts = dict(
            db.query(Membership.org_id, func.count(Membership.id))
            .filter(Membership.org_id.in_([o.id for o in orgs]))
            .group_by(Membership.org_id)
            .all()
        )
        for org in orgs:
            org.member_count = counts.get(org.id, 0)
    return orgs


def get_org(db: Session, org_id: int) -> Optional[Organization]:
    return db.query(Organization).filter(Organization.id == org_id).first()


def get_org_members(db: Session, org_id: int) -> list[dict]:
    memberships = db.query(Membership).filter(Membership.org_id == org_id).all()
    result = []
    for m in memberships:
        user = db.query(User).filter(User.id == m.user_id).first()
        if user:
            result.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "avatar_url": user.avatar_url,
                "role": m.role,
                "joined_at": m.joined_at,
            })
    return result


def create_team(db: Session, org_id: int, name: str, description: Optional[str] = None) -> Team:
    team = Team(org_id=org_id, name=name, description=description)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


def get_org_teams(db: Session, org_id: int) -> list[Team]:
    teams = db.query(Team).filter(Team.org_id == org_id).all()
    if teams:
        counts = dict(
            db.query(TeamMember.team_id, func.count(TeamMember.id))
            .filter(TeamMember.team_id.in_([t.id for t in teams]))
            .group_by(TeamMember.team_id)
            .all()
        )
        for team in teams:
            team.member_count = counts.get(team.id, 0)
    return teams


def invite_member(db: Session, org_id: int, email: str, role: str = "member") -> Invitation:
    token = secrets.token_urlsafe(32)
    invitation = Invitation(
        org_id=org_id,
        email=email,
        token=token,
        role=role,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


def accept_invitation(db: Session, token: str, user_id: int) -> bool:
    invitation = db.query(Invitation).filter(
        Invitation.token == token,
        Invitation.status == "pending",
    ).first()
    if not invitation or invitation.expires_at < datetime.utcnow():
        return False
    membership = Membership(user_id=user_id, org_id=invitation.org_id, role=invitation.role)
    db.add(membership)
    invitation.status = "accepted"
    db.commit()
    return True


def add_team_member(db: Session, team_id: int, user_id: int, role: str = "member") -> TeamMember:
    tm = TeamMember(team_id=team_id, user_id=user_id, role=role)
    db.add(tm)
    db.commit()
    db.refresh(tm)
    return tm


def remove_member(db: Session, org_id: int, user_id: int) -> bool:
    membership = db.query(Membership).filter(
        Membership.org_id == org_id,
        Membership.user_id == user_id,
    ).first()
    if not membership:
        return False
    if membership.role == "owner":
        return False
    db.delete(membership)
    db.commit()
    return True
