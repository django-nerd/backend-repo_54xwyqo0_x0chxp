import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Service, Booking, Video

app = FastAPI(title="El Patron API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "El Patron API a bombar"}


# Utilidades
LOCATIONS = ["Faro", "Olhão", "Tavira"]


# Seed inicial de serviços (se colecção estiver vazia)
@app.on_event("startup")
async def seed_services():
    try:
        existing = list(db["service"].find().limit(1)) if db else []
        if not existing and db:
            base_services = [
                Service(name="Corte", description="Corte clássico ou moderno, ao teu estilo.", price=15.0, duration_min=30, featured=True),
                Service(name="Barba", description="Desenho e acabamento de barba com navalha.", price=12.0, duration_min=20),
                Service(name="Corte + Barba", description="Combo completo para sair afiado.", price=25.0, duration_min=45, featured=True),
                Service(name="Camuflagem Cabelo", description="Cobertura discreta para brancos.", price=18.0, duration_min=30),
                Service(name="Camuflagem Barba", description="Tom uniforme e natural na barba.", price=14.0, duration_min=20),
            ]
            for s in base_services:
                create_document("service", s)
    except Exception:
        # Em ambientes sem DB configurada, ignorar
        pass


# Modelos auxiliares
class SlotResponse(BaseModel):
    datetime: str
    available: bool


# Endpoints públicos
@app.get("/locations", response_model=List[str])
def get_locations():
    return LOCATIONS


@app.get("/services")
def list_services():
    try:
        services = get_documents("service")
        # Converter ObjectId e formatar
        def norm(s):
            s["id"] = str(s.pop("_id")) if "_id" in s else None
            return s
        return [norm(s) for s in services]
    except Exception:
        # fallback sem DB
        return [
            {"id": "1", "name": "Corte", "description": "Corte clássico ou moderno, ao teu estilo.", "price": 15.0, "duration_min": 30, "featured": True},
            {"id": "2", "name": "Barba", "description": "Desenho e acabamento de barba com navalha.", "price": 12.0, "duration_min": 20, "featured": False},
            {"id": "3", "name": "Corte + Barba", "description": "Combo completo para sair afiado.", "price": 25.0, "duration_min": 45, "featured": True},
            {"id": "4", "name": "Camuflagem Cabelo", "description": "Cobertura discreta para brancos.", "price": 18.0, "duration_min": 30, "featured": False},
            {"id": "5", "name": "Camuflagem Barba", "description": "Tom uniforme e natural na barba.", "price": 14.0, "duration_min": 20, "featured": False},
        ]


@app.get("/slots")
def get_slots(location: str, date: str):
    # Gera slots a cada 30 min entre 10:00 e 19:00
    if location not in LOCATIONS:
        raise HTTPException(status_code=400, detail="Localização inválida")

    try:
        # Buscar marcações existentes para bloquear slots
        bookings = get_documents("booking", {"location": location, "date": date})
        taken = {(b["date"], b["time"]) for b in bookings}
    except Exception:
        taken = set()

    base = datetime.fromisoformat(f"{date}T10:00:00")
    end = datetime.fromisoformat(f"{date}T19:00:00")
    out: List[SlotResponse] = []
    cur = base
    while cur <= end:
        key = (date, cur.strftime("%H:%M"))
        out.append(SlotResponse(datetime=cur.strftime("%Y-%m-%dT%H:%M"), available=(key not in taken)))
        cur += timedelta(minutes=30)
    return [s.model_dump() for s in out]


@app.post("/book")
def create_booking(payload: Booking):
    if payload.location not in LOCATIONS:
        raise HTTPException(status_code=400, detail="Localização inválida")

    # Verificar conflito do slot
    try:
        conflict = get_documents("booking", {"location": payload.location, "date": payload.date, "time": payload.time})
        if conflict:
            raise HTTPException(status_code=409, detail="Esse horário já não está disponível")
    except Exception:
        # Se não houver DB, permitemos a marcação mas sem persistência
        pass

    # Guardar na BD se disponível
    try:
        create_document("booking", payload)
    except Exception:
        # Ignorar se sem BD
        pass

    return {"status": "ok", "message": "Marcação confirmada. Vais receber uma confirmação em breve."}


@app.get("/gallery")
def get_gallery():
    try:
        vids = get_documents("video")
        def norm(v):
            v["id"] = str(v.pop("_id")) if "_id" in v else None
            return v
        return [norm(v) for v in vids]
    except Exception:
        # Conteúdo exemplo
        return [
            {"id": "v1", "title": "Fade limpo em 30s", "platform": "youtube", "url": "https://www.youtube.com/embed/dQw4w9WgXcQ", "tags": ["corte","fade"]},
            {"id": "v2", "title": "Barba afiada", "platform": "youtube", "url": "https://www.youtube.com/embed/ysz5S6PUM-U", "tags": ["barba"]},
            {"id": "v3", "title": "Ritual El Patron", "platform": "mp4", "url": "https://www.w3schools.com/html/mov_bbb.mp4", "tags": ["ritual"]},
        ]


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = getattr(db, 'name', '✅ Connected')
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
