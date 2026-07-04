"""Central config loader for Shundo backend."""
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_SECRETS_FILE = os.getenv("GOOGLE_CLIENT_SECRETS_FILE", "credentials.json")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]
TOKEN_STORE_FILE = os.getenv("TOKEN_STORE_FILE", "token_store.json")

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3.1:free")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

HF_API_KEY = os.getenv("HF_API_KEY", "")
HF_MODEL = os.getenv("HF_MODEL", "meta-llama/Llama-3.3-70B-Instruct")
HF_BASE_URL = "https://router.huggingface.co/v1"

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "huggingface")  # "openrouter", "nvidia", or "huggingface"

TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")

SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
