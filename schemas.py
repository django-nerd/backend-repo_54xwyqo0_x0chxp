"""
Database Schemas for El Patron Barber Shop

Each Pydantic model represents a collection in MongoDB.
Collection name is the lowercase of the class name.
"""
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr

# Serviços oferecidos
class Service(BaseModel):
    name: str = Field(..., description="Nome do serviço")
    description: Optional[str] = Field(None, description="Descrição do serviço")
    price: float = Field(..., ge=0, description="Preço em euros")
    duration_min: int = Field(30, ge=10, le=240, description="Duração do serviço em minutos")
    featured: bool = Field(False, description="Se o serviço é destaque")

# Marcação/Reserva
class Booking(BaseModel):
    location: str = Field(..., description="Localização: Faro, Olhão, Tavira")
    service_id: Optional[str] = Field(None, description="ID do serviço (opcional)")
    service_name: str = Field(..., description="Nome do serviço escolhido")
    date: str = Field(..., description="Data no formato YYYY-MM-DD")
    time: str = Field(..., description="Hora no formato HH:MM")
    name: str = Field(..., description="Nome do cliente")
    phone: str = Field(..., description="Telefone do cliente")
    email: Optional[EmailStr] = Field(None, description="Email do cliente (opcional)")

# Vídeos da galeria
class Video(BaseModel):
    title: str = Field(..., description="Título do vídeo")
    platform: str = Field("youtube", description="Plataforma: youtube, vimeo, mp4")
    url: str = Field(..., description="URL do vídeo ou ID de embed")
    thumbnail: Optional[str] = Field(None, description="Thumbnail opcional")
    tags: Optional[List[str]] = Field(default_factory=list, description="Etiquetas")
