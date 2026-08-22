import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # "groq" (ücretsiz) veya "anthropic" (ücretli, daha güçlü model)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")

    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")

    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "small")
    WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "cpu")
    WHISPER_COMPUTE_TYPE: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

    BURN_SUBTITLES: bool = os.getenv("BURN_SUBTITLES", "true").lower() == "true"

    DOWNLOADS_DIR: str = os.getenv("DOWNLOADS_DIR", "downloads")
    OUTPUTS_DIR: str = os.getenv("OUTPUTS_DIR", "outputs")


settings = Settings()
