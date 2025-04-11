from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MINIAPP_URL = os.getenv("MINIAPP_URL")
EMPLOYEE_CHAT_ID = int(os.getenv("EMPLOYEE_CHAT_ID", 0))
OPENAI_PROXY = os.getenv("OPENAI_PROXY")