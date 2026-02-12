from fastapi import FastAPI
from src.api import main_router as APIRouter
from src.sse.router import router as SSERouter
from src.middlewares.logger import LoggingMiddleware
from fastapi.middleware.cors import CORSMiddleware
import os
from src.events import startup, shutdown
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup(app)
    try:
        yield
    finally:
        await shutdown(app)


app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(APIRouter)
app.include_router(SSERouter)

if __name__ == "__main__":
    import uvicorn

    DEFAULT_PORT = "3030"
    try:
        port = int(os.environ.get("PORT", DEFAULT_PORT))
    except Exception:
        port = int(DEFAULT_PORT)

    uvicorn.run(
        "main:app",
        port=port,
        host=os.environ.get("HOST", "0.0.0.0"),
        reload=os.environ.get("ENV", "DEV") == "DEV",
    )