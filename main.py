from fastapi import FastAPI
import uvicorn
from app.settings import init_db
from app.routers import kinds, users, model_cost, session
from app.settings import redis_client

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    await init_db()


app.include_router(kinds.router, prefix="/v1", tags=["kinds"])
app.include_router(model_cost.router, prefix="/v1", tags=["model_cost"])
app.include_router(session.router, prefix="/v1", tags=["session"])

app.include_router(users.router, prefix="/v1", tags=["users"])


@app.on_event("startup")
async def startup_event():
    await redis_client.connect()


@app.on_event("shutdown")
async def shutdown_event():
    await redis_client.close()


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8003, log_level="debug", reload=True)
