"""Service to load and validate role configuration files."""

import json
import os
from typing import Dict, List, Optional
from app.config import ROLES_DIR


def list_roles() -> List[Dict]:
    """List all available roles from the roles directory."""
    roles = []
    if not os.path.exists(ROLES_DIR):
        return roles
    for filename in os.listdir(ROLES_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(ROLES_DIR, filename)
            with open(filepath, "r") as f:
                role = json.load(f)
                roles.append(role)
    return roles


def get_role_config(role_id: str) -> Optional[Dict]:
    """Load a specific role configuration by role_id."""
    filepath = os.path.join(ROLES_DIR, f"{role_id}.json")
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r") as f:
        return json.load(f)


def validate_role_config(config: Dict) -> bool:
    """Validate that a role config has all required fields."""
    required_fields = ["role_id", "title", "required_skills", "min_experience_years",
                       "location_constraints", "evaluation_criteria"]
    return all(field in config for field in required_fields)
