from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time
import logging

logger = logging.getLogger("uvicorn.access")
logger.disabled = True

def register_all_middlewares(app: FastAPI):

    @app.middleware("http")
    async def custom_logging(request: Request, call_next):

        start_time = time.time()
    
        response = await call_next(request)
        processing_time = time.time() - start_time

        message = f"{request.client.host}:{request.client.port} - {request.method} - {request.url.path} - {response.status_code} - completed after: {processing_time}s"

        print(message)
        return response
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "https://queuemedix.vercel.app"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "localhost",
            "127.0.0.1",
            "*.onrender.com",
            "*.vercel.app"
        ]
    )
