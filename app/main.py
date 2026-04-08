from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import Base, engine
from .routes import cases, admin, auth, tips
import os
from app.routes import news
from app.routes import share



Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rede Alerta API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(admin.router)
app.include_router(tips.router)
app.include_router(news.router)
app.include_router(share.router)
@app.get("/")
def root():
    return {"message": "API Rede Alerta funcionando"}

