from app.security.catalog import DEFAULT_SNMP_COMMUNITIES


def is_weak_snmp_community(community: str | None) -> bool:
    return bool(community) and community.strip().lower() in DEFAULT_SNMP_COMMUNITIES
