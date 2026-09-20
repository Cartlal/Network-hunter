from app.security.catalog import find_service
from app.security.scoring import compute_score
from app.security.snmp_audit import is_weak_snmp_community


def test_score_with_no_findings_is_perfect():
    assert compute_score([]) == 100


def test_score_deducts_per_severity():
    assert compute_score(["low"]) == 95
    assert compute_score(["medium"]) == 90
    assert compute_score(["high"]) == 75
    assert compute_score(["critical"]) == 60


def test_score_floors_at_zero_and_never_goes_negative():
    assert compute_score(["critical"] * 10) == 0


def test_score_stacks_multiple_findings():
    assert compute_score(["high", "medium", "low"]) == 100 - 25 - 10 - 5


def test_find_service_returns_catalog_entry_by_port():
    telnet = find_service(23)
    assert telnet is not None
    assert telnet.service_name == "Telnet"
    assert telnet.severity == "critical"


def test_find_service_returns_none_for_unknown_port():
    assert find_service(22) is None  # SSH is deliberately not in the catalog
    assert find_service(65000) is None


def test_weak_snmp_community_matches_known_defaults_case_insensitively():
    assert is_weak_snmp_community("public")
    assert is_weak_snmp_community("PUBLIC")
    assert is_weak_snmp_community(" private ")


def test_weak_snmp_community_rejects_custom_strings_and_empty_values():
    assert not is_weak_snmp_community("a-custom-secret")
    assert not is_weak_snmp_community(None)
    assert not is_weak_snmp_community("")
