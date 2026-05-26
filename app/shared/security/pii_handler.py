import re
import logging

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_REGEX = re.compile(r"\b(\+?\d{1,3}[-.\s]?)?\d{10}\b")
URL_REGEX = re.compile(r"https?://\S+|www\.\S+")


def mask_pii(text: str) -> str:
    try:
        text = EMAIL_REGEX.sub("[EMAIL]", text)
        text = PHONE_REGEX.sub("[PHONE]", text)
        text = URL_REGEX.sub("[URL]", text)

        return text

    except Exception as e:
        logger.exception("pii_masking_failed")
        raise RuntimeError("PII masking failed")