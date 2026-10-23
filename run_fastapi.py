"""Run the FastAPI LedgerBud backend with Uvicorn."""

import os
import uvicorn
from dotenv import load_dotenv

# Load .env into os.environ before anything else starts
load_dotenv()


def run():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    env = os.environ.get("ENVIRONMENT", "development").lower()

    # Reload only in development mode unless explicitly set by RELOAD env var
    reload_env = os.environ.get("RELOAD")
    if reload_env is not None:
        reload_enabled = reload_env.lower() in ("true", "1", "yes")
    else:
        reload_enabled = (env == "development")

    uvicorn.run(
        "app.fastapi_app.main:app",
        host=host,
        port=port,
        reload=reload_enabled,
    )


if __name__ == "__main__":
    run()
