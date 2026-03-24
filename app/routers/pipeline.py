"""Role configuration API endpoints."""

from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas import RoleConfigResponse
from app.services.role_config import list_roles, get_role_config

router = APIRouter(prefix="/api/roles", tags=["Roles"])


@router.get("", response_model=List[RoleConfigResponse])
def get_all_roles():
    """List all available roles."""
    roles = list_roles()
    return [
        RoleConfigResponse(
            role_id=r["role_id"],
            title=r["title"],
            required_skills=r["required_skills"],
            min_experience_years=r["min_experience_years"],
            location_constraints=r["location_constraints"],
            evaluation_criteria=r["evaluation_criteria"]
        )
        for r in roles
    ]


@router.get("/{role_id}", response_model=RoleConfigResponse)
def get_role(role_id: str):
    """Get details for a specific role."""
    config = get_role_config(role_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Role '{role_id}' not found")
    return RoleConfigResponse(
        role_id=config["role_id"],
        title=config["title"],
        required_skills=config["required_skills"],
        min_experience_years=config["min_experience_years"],
        location_constraints=config["location_constraints"],
        evaluation_criteria=config["evaluation_criteria"]
    )
