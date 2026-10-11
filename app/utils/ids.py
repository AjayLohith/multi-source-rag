import uuid


def generate_uuid() -> str:
    """Generates a random v4 UUID string."""
    return str(uuid.uuid4())


def deterministic_uuid(namespace: str, name: str) -> str:
    """Generates a reproducible v5 UUID given a namespace and name."""
    ns = uuid.uuid5(uuid.NAMESPACE_DNS, namespace)
    return str(uuid.uuid5(ns, name))
