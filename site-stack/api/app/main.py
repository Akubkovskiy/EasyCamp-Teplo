from fastapi import FastAPI

app = FastAPI(title="Teplo API", version="0.1.0")


@app.get("/health")
async def health():
    return {"ok": True}
