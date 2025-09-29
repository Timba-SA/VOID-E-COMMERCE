from pydantic import BaseModel

class ChatQuery(BaseModel):
    sesion_id: str
    pregunta: str

class ChatResponse(BaseModel):
    respuesta: str