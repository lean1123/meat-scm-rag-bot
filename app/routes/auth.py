from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app import auth

router = APIRouter()

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username == "nhanvienA" and auth.verify_password("123456",
        "$2y$10$26N//aTcQr9ZjY7mcmNKXOCJOJS.V13hS34oP0UbPMIF0SvTzu6by"):
        user_farm_id = "farmA"
        access_token = auth.create_access_token(
            data={"sub": form_data.username, "facilityID": user_farm_id}
        )
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(
        status_code=401,
        detail="Incorrect username or password",
    )