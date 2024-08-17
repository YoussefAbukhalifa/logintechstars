import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from passlib.context import CryptContext
from pydantic import BaseModel, Field, field_validator
import jwt
from datetime import datetime, timedelta
import random
import string
import re
from email_utils import send_email_async, send_email_background
import pytz

# Load environment variables
load_dotenv()

app = FastAPI()

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///./techstars.db')
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
import secrets
SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone = Column(String)
    national_id = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    reset_token = Column(String)
    reset_token_expiry = Column(DateTime)

# Database initialization function
def init_db():
    Base.metadata.create_all(bind=engine)

# Pydantic models
class UserCreate(BaseModel):
    name: str
    phone: str
    national_id: str
    email: str
    password: str

    @field_validator('national_id')
    def validate_national_id(cls, v):
        if not v.isdigit() or len(v) != 14:
            raise ValueError('National ID must be a 14-digit number')
        return v

    @field_validator('phone')
    def validate_phone(cls, v):
        if not re.match(r'^\d{11}$', v):
            raise ValueError('Phone number must be 11 digits')
        return v

class UserLogin(BaseModel):
    national_id: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Helper functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

# API endpoints
@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.national_id == user.national_id).first()
    if db_user:
        raise HTTPException(status_code=400, detail="National ID already registered")
    
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(name=user.name, phone=user.phone, national_id=user.national_id, 
                    email=user.email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}

@app.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.national_id == user.national_id).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Incorrect national ID or password")
    
    access_token = create_access_token(data={"sub": db_user.national_id})
    return {"access_token": access_token, "token_type": "bearer"}

# Define the time zone
TIME_ZONE = 'Africa/Cairo'  

@app.post("/reset-password")
async def reset_password(national_id: str, method: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.national_id == national_id).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="User not found")
    
    token = generate_token()

    # Get the current time in the specified time zone
    local_tz = pytz.timezone(TIME_ZONE)
    current_time = datetime.now(local_tz)

    # Set the expiration time (60 seconds from now)
    expiry = current_time + timedelta(seconds=60)
    
    db_user.reset_token = token
    db_user.reset_token_expiry = expiry
    db.commit()
    
    if method == "email":
        await send_email_async(
            subject="Password Reset",
            email_to=db_user.email,
            body={
                "title": "Password Reset",
                "name": db_user.name,
                "token": token
            }
        )
        return {"message": f"Password reset token sent to email: {db_user.email}"}
    else:
        raise HTTPException(status_code=400, detail="Invalid method")
    
@app.post("/confirm-reset")
def confirm_reset(national_id: str, token: str, new_password: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.national_id == national_id).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="User not found")
    
    if db_user.reset_token != token or db_user.reset_token_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    db_user.password = get_password_hash(new_password)
    db_user.reset_token = None
    db_user.reset_token_expiry = None
    db.commit()
    
    return {"message": "Password reset successfully"}

# Startup event to initialize the database
@app.on_event("startup")
async def startup_event():
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)