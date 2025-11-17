from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import secrets

from . import models
from . import schemas
from .database import engine, SessionLocal


# Створюємо таблиці БД
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SpySignal E2EE Backend")

# CORS (для WebApp / GitHub Pages / Render фронтенду)
origins = ["*"]  # у продакшені обмежити доменами фронтенду

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- DB session dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Simple token auth ---
def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = authorization.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid auth header")

    token = parts[1]

    user = db.query(models.User).filter(models.User.token == token).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user


# --- Register / login ---
@app.post("/api/register")
def register(req: schemas.RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == req.username).first()

    if existing:
        return {
            "id": existing.id,
            "username": existing.username,
            "token": existing.token,
        }

    token = secrets.token_hex(32)

    user = models.User(
        username=req.username,
        telegram_id=req.telegram_id,
        token=token,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"id": user.id, "username": user.username, "token": user.token}


# --- User search ---
@app.get("/api/users/search")
def search_users(
    query: str = Query(..., alias="query"),
    db: Session = Depends(get_db)
):
    q = query.strip()
    if not q:
        return {"results": []}

    results = []

    # Search by numeric id
    if q.isdigit():
        u = db.query(models.User).filter(models.User.id == int(q)).first()
        if u:
            results.append(u)

    # Search by username (partial, case-insensitive)
    by_name = (
        db.query(models.User)
        .filter(models.User.username.ilike(f"%{q}%"))
        .all()
    )

    for u in by_name:
        if u not in results:
            results.append(u)

    # Для pydantic v2:
    return {"results": [schemas.UserOut.model_validate(u) for u in results]}


# --- Зберегти публічний E2EE ключ поточного користувача ---
@app.post("/api/pubkey")
def save_pubkey(
    req: schemas.PubKeyUpdate,
    current = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current.pubkey = req.pubkey
    db.commit()
    return {"ok": True}


# --- Отримати публічний ключ іншого користувача ---
@app.get("/api/pubkey/{user_id}", response_model=schemas.PubKeyOut)
def get_pubkey(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.pubkey:
        raise HTTPException(status_code=404, detail="No pubkey")
    return {"pubkey": user.pubkey}


# --- Create encrypted message ---
@app.post("/api/messages")
def create_message(
    msg: schemas.MessageCreate,
    current = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    peer = db.query(models.User).filter(models.User.id == msg.to).first()

    if not peer:
        raise HTTPException(status_code=404, detail="Recipient not found")

    db_msg = models.Message(
        from_id=current.id,
        to_id=peer.id,
        iv=msg.iv,
        ciphertext=msg.ciphertext,
        msg_type=msg.msg_type,
        ttl_sec=msg.ttl_sec,
    )

    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)

    return {"ok": True, "id": db_msg.id}


# --- Get encrypted messages for dialog ---
@app.get("/api/messages", response_model=schemas.MessagesResponse)
def get_messages(
    peer_id: int = Query(...),
    current = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()

    msgs = (
        db.query(models.Message)
        .filter(
            ((models.Message.from_id == current.id) & (models.Message.to_id == peer_id))
            | ((models.Message.from_id == peer_id) & (models.Message.to_id == current.id))
        )
        .order_by(models.Message.created_at.asc())
        .all()
    )

    visible = []

    for m in msgs:
        if m.ttl_sec is not None:
            if m.created_at + timedelta(seconds=m.ttl_sec) < now:
                continue
        visible.append(m)

    return {"messages": visible}


@app.get("/health")
def health():
    return {"status": "ok"}
