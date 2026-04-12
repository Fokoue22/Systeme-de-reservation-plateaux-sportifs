from fastapi import FastAPI

from app.api.deps import init_schema
from app.api.m1_routes import router as m1_router
from app.api.m2_routes import router as m2_router

app = FastAPI(title="Systeme de reservation de plateaux sportifs")

app.include_router(m1_router)
app.include_router(m2_router)


@app.on_event("startup")
def startup() -> None:
    init_schema()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
