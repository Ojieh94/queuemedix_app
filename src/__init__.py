from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.app.database.main import init_db
from src.app.router import auth

version = "v1"

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server is starting..................")
    await init_db()
    yield
    print("Server is stopping................")
    print("Server has been stopped.")

app = FastAPI(
    title="Medical Queueing System",
    description="A system designed for hospitals and individual practitioners to eliminate the inefficiencies of uncoordinated patient queues by streamlining and managing appointments effectively.",
    version=version,
    lifespan=lifespan,
    docs_url=f"/api/{version}/docs",
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/mit"
    },
    contact={
        "name": "Queuemedix Team",
        "email": "queuemedix@gmail.com",
        "url": "https://queuemedix.com"
    }
)


app.include_router(auth.auth_router, prefix=f"/api/{version}")


@app.get('/')
async def root():
    return{"Medical Queueing System designed by: Queuemedix Team"}