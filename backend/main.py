from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.pipeline import ask

app = FastAPI(
    title="ERP AI Assistant",
    description="Assistant IA pour ERP Textile",
    version="1.0.0"
)

class QuestionRequest(BaseModel):
    question: str

class QuestionResponse(BaseModel):
    success: bool
    question: str
    view: str | None = None
    sql: str | None = None
    nombre_reele:int | None = None
    response: str

@app.get("/")
def root():
    return {"status": "ERP AI Assistant is running 🚀"}

@app.post("/ask", response_model=QuestionResponse)
def ask_question(request: QuestionRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question vide")
    
    result = ask(request.question)
    return QuestionResponse(**result)

@app.get("/health")
def health():
    return {"status": "ok"}