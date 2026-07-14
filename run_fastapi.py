"""Run the FastAPI LedgerBud backend with Uvicorn."""

import uvicorn
from dotenv import load_dotenv

# Load .env into os.environ before anything else starts
load_dotenv()


if __name__ == "__main__":
    uvicorn.run("app.fastapi_app.main:app", host="0.0.0.0", port=8000, reload=True)
