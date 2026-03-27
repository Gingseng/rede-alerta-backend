from fastapi import APIRouter, HTTPException
from ..schemas import AdminLogin, TokenResponse
from ..auth import authenticate_admin, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(data: AdminLogin):
    if not authenticate_admin(data.username, data.password):
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")

    token = create_access_token({"sub": data.username})
    return {
        "access_token": token,
        "token_type": "bearer"
    }