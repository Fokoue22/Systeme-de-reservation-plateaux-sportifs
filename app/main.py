from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.deps import init_schema
from app.api.m1_routes import router as m1_router
from app.api.m2_routes import router as m2_router
from app.api.m4_routes import router as m4_router
from app.api.m5_auth_routes import router as m5_router
from app.api.ui_routes import router as ui_router

app = FastAPI(title="Systeme de reservation de plateaux sportifs")

app.include_router(m1_router)
app.include_router(m2_router)
app.include_router(m4_router)
app.include_router(m5_router)
app.include_router(ui_router)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/Images", StaticFiles(directory="Images"), name="images")


@app.on_event("startup")
def startup() -> None:
    init_schema()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
