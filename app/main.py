from fastapi import FastAPI

app = FastAPI(title="Systeme de reservation de plateaux sportifs")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
