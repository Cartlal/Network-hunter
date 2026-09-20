from dataclasses import dataclass


@dataclass(frozen=True)
class RiskyService:
    port: int
    service_name: str
    severity: str  # low | medium | high | critical
    detail: str
    remediation: str


# Deliberately excludes 22/80/443/8080 - SSH/HTTP(S) aren't inherently risky
# and flagging them would just be noise. Every entry here is either
# unencrypted by design or has a track record of critical exploits when
# left reachable on an ordinary LAN. See SECURITY_METHODOLOGY.md for the
# full rationale and known false-positive cases.
RISKY_SERVICES: tuple[RiskyService, ...] = (
    RiskyService(
        21, "FTP", "high",
        "FTP transmits credentials and file contents in plaintext.",
        "Disable FTP, or replace it with SFTP/FTPS.",
    ),
    RiskyService(
        23, "Telnet", "critical",
        "Telnet transmits everything, including login credentials, completely unencrypted.",
        "Disable Telnet and use SSH for remote administration instead.",
    ),
    RiskyService(
        139, "NetBIOS", "medium",
        "Legacy SMB transport; can leak hostnames, shares, and session information.",
        "Disable NetBIOS over TCP/IP if direct-hosted SMB (445) isn't required.",
    ),
    RiskyService(
        445, "SMB", "high",
        "SMB has a history of critical remote-code-execution worms (EternalBlue/WannaCry).",
        "Ensure the device is fully patched, and block 445 from untrusted network segments.",
    ),
    RiskyService(
        512, "rexec", "critical",
        "Unauthenticated, plaintext remote command execution.",
        "Disable rexec; use SSH instead.",
    ),
    RiskyService(
        513, "rlogin", "critical",
        "Plaintext remote login protocol relying on weak host-based trust.",
        "Disable rlogin; use SSH instead.",
    ),
    RiskyService(
        514, "rsh", "critical",
        "Unauthenticated, plaintext remote shell.",
        "Disable rsh; use SSH instead.",
    ),
    RiskyService(
        1433, "MSSQL", "medium",
        "A database server is reachable from the LAN.",
        "Restrict access with a firewall rule and confirm strong authentication is enforced.",
    ),
    RiskyService(
        3306, "MySQL", "medium",
        "A database server is reachable from the LAN.",
        "Restrict access with a firewall rule and confirm strong authentication is enforced.",
    ),
    RiskyService(
        3389, "RDP", "high",
        "RDP is one of the most common ransomware and brute-force entry points.",
        "Restrict RDP to a VPN, require MFA/NLA, and never expose it directly to the internet.",
    ),
    RiskyService(
        5900, "VNC", "high",
        "VNC implementations frequently ship with weak or no authentication.",
        "Set a strong VNC password or tunnel it over SSH/VPN instead of exposing it directly.",
    ),
    RiskyService(
        6379, "Redis", "high",
        "Redis is very commonly deployed with no authentication at all.",
        "Enable requirepass/ACLs and bind Redis to localhost or a trusted interface only.",
    ),
)

DEFAULT_SNMP_COMMUNITIES = frozenset({"public", "private", "community", "cisco"})


def find_service(port: int) -> RiskyService | None:
    return next((s for s in RISKY_SERVICES if s.port == port), None)
