import re
import structlog
from typing import Any, Dict

# Regex for common PII
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
AUTH_HEADER_REGEX = re.compile(r'(Authorization:\s*)(Bearer\s+|Basic\s+)([a-zA-Z0-9._-]+)', re.IGNORECASE)
GENERIC_SECRET_REGEX = re.compile(r'(password|secret|token|key|api_key|access_token)["\s:]+["\']?([^"\'\s,]+)["\']?', re.IGNORECASE)

def mask_pii_processor(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    structlog processor to mask PII in log events.
    """
    def mask_text(text: str) -> str:
        if not isinstance(text, str):
            return text
        
        # Mask emails
        text = EMAIL_REGEX.sub("[EMAIL_MASKED]", text)
        
        # Mask Auth headers
        text = AUTH_HEADER_REGEX.sub(r"\1\2[TOKEN_MASKED]", text)
        
        return text

    # Apply to event message
    if "event" in event_dict:
        event_dict["event"] = mask_text(event_dict["event"])

    # Apply to other fields recursively
    for key, value in event_dict.items():
        if key == "event":
            continue
        
        # Mask specific sensitive keys
        if any(secret in key.lower() for secret in ["password", "secret", "token", "key", "api_key"]):
            event_dict[key] = "[SENSITIVE_MASKED]"
        elif isinstance(value, str):
            event_dict[key] = mask_text(value)
            
    return event_dict

def configure_logging(log_level="INFO"):
    """Configure structured logging with PII masking"""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            mask_pii_processor,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(log_level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
