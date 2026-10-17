import re

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"reveal|show|print\s+(your\s+)?(system|developer)\s+prompt",
    r"\bact\s+as\s+(dan|jailbreak|an?\s+unrestricted)",
    r"(print|show|dump|leak).*(api[_ -]?key|environment|secret|password|token)",
    r"(override|replace|forget).*(system|developer|safety)\s+(prompt|instruction)",
]

def is_prompt_injection(text: str) -> bool:
    """Return true for common instruction-hijacking or secret-exfiltration attempts."""
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in INJECTION_PATTERNS)

