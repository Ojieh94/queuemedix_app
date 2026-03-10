from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time


def register_all_middlewares(app: FastAPI):

    # Logging middleware
    @app.middleware("http")
    async def custom_logging(request: Request, call_next):

        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time

        print(
            f"{request.client.host}:{request.client.port} "
            f"{request.method} {request.url.path} "
            f"{response.status_code} "
            f"{process_time}s"
        )

        return response

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "https://queuemedix.vercel.app",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "localhost",
            "127.0.0.1",
            "queuemedix-app.onrender.com",
        ],
    )
