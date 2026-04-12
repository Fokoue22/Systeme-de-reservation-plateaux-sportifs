from fastapi import FastAPI

from app.api.m1_routes import router as m1_router
from app.application import DisponibiliteService, PlateauService
from app.infrastructure import SQLiteDisponibiliteRepository, SQLiteManager, SQLitePlateauRepository

app = FastAPI(title="Systeme de reservation de plateaux sportifs")

db_manager = SQLiteManager()
plateau_repo = SQLitePlateauRepository(db_manager)
disponibilite_repo = SQLiteDisponibiliteRepository(db_manager)


def get_plateau_service() -> PlateauService:
    return PlateauService(plateau_repo)


def get_disponibilite_service() -> DisponibiliteService:
    return DisponibiliteService(plateau_repo=plateau_repo, disponibilite_repo=disponibilite_repo)


app.dependency_overrides[PlateauService] = get_plateau_service
app.dependency_overrides[DisponibiliteService] = get_disponibilite_service

app.include_router(m1_router)


@app.on_event("startup")
def startup() -> None:
    db_manager.initialize_schema()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
