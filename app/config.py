import os
from dotenv import load_dotenv


class ConfigError(Exception):
    pass


def load_config():
    load_dotenv()

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ConfigError("OPENAI_API_KEY is missing. Add it to .env")

    llm_model = os.getenv("LLM_MODEL", "gpt-4.1-mini")
    vision_model = os.getenv("VISION_MODEL", llm_model)

    return {
        "OPENAI_API_KEY": openai_key,
        "LLM_MODEL": llm_model,
        "VISION_MODEL": vision_model,
        "OCR_DPI": int(os.getenv("OCR_DPI", "200")),
        "OCR_MAX_PAGES": int(os.getenv("OCR_MAX_PAGES", "10")),
    }
