import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME")
KAGGLE_KEY = os.getenv("KAGGLE_KEY")
PROXYCURL_API_KEY = os.getenv("PROXYCURL_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Preferred model override from env
LLM_MODEL = os.getenv("LLM_MODEL")

# Output directory for data and visualizations
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Kaggle credentials config
if KAGGLE_USERNAME and KAGGLE_KEY:
    os.environ["KAGGLE_USERNAME"] = KAGGLE_USERNAME
    os.environ["KAGGLE_KEY"] = KAGGLE_KEY

def get_llm(temperature=0.0):
    """
    Returns the Chat LLM client based on environment configuration.
    Defaults to Gemini ChatGoogleGenerativeAI (gemini-1.5-flash) or ChatOpenAI.
    """
    if OPENAI_API_KEY:
        from langchain_openai import ChatOpenAI
        model_name = LLM_MODEL or "gpt-4o-mini"
        return ChatOpenAI(model=model_name, temperature=temperature, api_key=OPENAI_API_KEY)
    elif GROQ_API_KEY:
        from langchain_groq import ChatGroq
        model_name = LLM_MODEL or "llama-3.3-70b-versatile"
        return ChatGroq(model_name=model_name, temperature=temperature, api_key=GROQ_API_KEY)
    elif GEMINI_API_KEY:
        from langchain_google_genai import ChatGoogleGenerativeAI
        model_name = LLM_MODEL or "gemini-1.5-flash"
        return ChatGoogleGenerativeAI(model=model_name, temperature=temperature, google_api_key=GEMINI_API_KEY)
    else:
        raise ValueError("No valid LLM API key configured")
