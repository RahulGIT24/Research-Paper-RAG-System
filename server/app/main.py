from fastapi import FastAPI
from app.api.v1 import api
from fastapi.responses import JSONResponse
from app.core.exceptions import BaseAPIException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from shared_lib.infra.redis import redis_instance
from app.core.constants import UPLOAD_DIR
from contextlib import asynccontextmanager

load_dotenv()

UPLOAD_DIR.mkdir(exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_instance.create_consumer_groups()
    print("Redis consumer groups ready")

    yield

    await redis_instance.client.close()


app = FastAPI(title="DataVaultServer",lifespan=lifespan)
origins = [
    "http://localhost:5173",   
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            
    allow_credentials=True,           
    allow_methods=["*"],              
    allow_headers=["*"],              
)

@app.exception_handler(BaseAPIException)
async def http_exception_handling(request,exc:BaseAPIException):
    return JSONResponse(
        status_code=exc.statuscode,
        content={"success":False,"error":exc.message}
    )

app.include_router(api.api_router,prefix="/api/v1")

@app.get('/api/health')
def root():
    return {"status":"Server is Healthy"}

# uvicorn app.main:app