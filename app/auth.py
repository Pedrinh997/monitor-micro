from datetime import datetime, timedelta
from jose import JWTError, jwt
from pwdlib import PasswordHash
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from . import database, models, schemas

password_hash = PasswordHash.recommended()
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkeychange_this_in_production_123456789")

if SECRET_KEY == "supersecretkeychange_this_in_production_123456789":
    import warnings
    warnings.warn(
        "SECRET_KEY está com valor DEFAULT. Em produção, defina SECRET_KEY no .env",
        RuntimeWarning,
        stacklevel=2,
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def verify_password(plain, hashed):
    return password_hash.verify(plain, hashed)

def get_password_hash(password):
    return password_hash.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(db: Session = Depends(database.get_db_sync), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
