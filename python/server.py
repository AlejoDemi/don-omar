from fastapi import FastAPI
from .app.router import router  # modular router with endpoint(s)
from dotenv import load_dotenv

# Ensure .env is loaded for GOOGLE_API_KEY and other settings
load_dotenv()

app = FastAPI()
app.include_router(router)

 