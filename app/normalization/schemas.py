import hashlib
import json
from typing import Any, Dict, Tuple


# Known field aliases mapping to canonical standard names
CANONICAL_ALIASES: Dict[str, str] = {
    # Identifiers
    "employee_id": "id",
    "user_id": "id",
    "emp_id": "id",
    "record_id": "id",
    "id": "id",

    # Names
    "full_name": "name",
    "emp_name": "name",
    "user_name": "name",
    "username": "name",
    "name": "name",

    # Organization / Roles
    "dept": "department",
    "division": "department",
    "department": "department",
    "job_title": "role",
    "designation": "role",
    "position": "role",
    "role": "role",

    # Contact
    "email_address": "email",
    "work_email": "email",
    "email": "email",

    # Compensation
    "comp": "salary",
    "compensation": "salary",
    "annual_salary": "salary",
    "salary": "salary",
}

CANONICAL_FIELDS = {"id", "name", "role", "department", "email", "salary"}


def normalize_record_schema(raw_dict: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
    """
    Maps known field aliases to canonical names.
    Any unknown or unexpected fields are isolated into extra_metadata without crashing.
    Generates a deterministic schema fingerprint (hash) to identify changes over time.

    Returns:
        (canonical_fields, extra_metadata, schema_hash)
    """
    canonical: Dict[str, Any] = {}
    extra: Dict[str, Any] = {}

    for raw_key, val in raw_dict.items():
        clean_key = str(raw_key).lower().strip()
        target_field = CANONICAL_ALIASES.get(clean_key)
        if target_field:
            canonical[target_field] = val
        else:
            extra[raw_key] = val

    # Deterministic fingerprint of raw schema keys
    sorted_keys = sorted(str(k) for k in raw_dict.keys())
    schema_str = json.dumps(sorted_keys)
    schema_hash = hashlib.sha256(schema_str.encode("utf-8")).hexdigest()[:12]

    return canonical, extra, schema_hash
