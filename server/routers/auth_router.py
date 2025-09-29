# En backend/routers/auth_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pymongo.database import Database
from datetime import datetime, timedelta, timezone
import secrets
from bson import ObjectId

from schemas import user_schemas
from utils import security
from database.database import get_db_nosql
from services import auth_services as auth_service
from services import email_service

router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"]
)

# En backend/routers/auth_router.py

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=user_schemas.UserOut)
async def register_user(user: user_schemas.UserCreate, db: Database = Depends(get_db_nosql)):
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado."
        )

    # --- ¡ACÁ METEMOS LA VALIDACIÓN! ---
    if len(user.password) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña es demasiado larga. El máximo es 72 caracteres."
        )
    # ------------------------------------

    # Si pasa el control, recién ahí la hasheamos
    hashed_password = security.get_password_hash(user.password)

    user_document = user.model_dump()
    user_document["hashed_password"] = hashed_password
    del user_document["password"]

    user_document["role"] = "user"
    user_document["created_at"] = datetime.now()

    result = await db.users.insert_one(user_document)
    created_user = await db.users.find_one({"_id": result.inserted_id})

    return created_user

@router.post("/login", response_model=user_schemas.Token)
async def login_for_access_token(db: Database = Depends(get_db_nosql), form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.users.find_one({"email": form_data.username})

    if not user or not security.verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = {
        "sub": user["email"],
        "user_id": str(user["_id"]),
        "role": user.get("role", "user")
    }

    access_token = security.create_access_token(data=token_data)

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: user_schemas.ForgotPasswordRequest,
    db: Database = Depends(get_db_nosql)
):
    user = await db.users.find_one({"email": request.email})
    if user:
        reset_token = secrets.token_urlsafe(32)
        hashed_token = security.get_password_hash(reset_token)
        expire_date = datetime.now(timezone.utc) + timedelta(hours=1)

        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "reset_password_token": hashed_token,
                "reset_password_token_expires": expire_date
            }}
        )

        try:
            await email_service.send_password_reset_email(user["email"], reset_token)
        except Exception as e:
            print(f"Error al enviar email: {e}")
            pass

    return {"message": "Si tu email está en nuestra base de datos, recibirás un link para resetear tu contraseña."}


@router.post("/reset-password/{token}", status_code=status.HTTP_200_OK)
async def reset_password(
    token: str,
    request: user_schemas.ResetPasswordRequest,
    db: Database = Depends(get_db_nosql)
):
    users_cursor = db.users.find({"reset_password_token": {"$exists": True}})

    user_to_update = None
    async for user in users_cursor:
        # --- ¡ESTA ES LA LÍNEA DEL ARREGLO posta posta! ---
        # Usamos el 'token' de la URL, no el 'request.token' que no existe.
        if security.verify_password(token, user["reset_password_token"]):
        # --- FIN DEL ARREGLO ---
            user_to_update = user
            break

    if not user_to_update:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido.")

    # La corrección de la fecha que te pasé antes la dejamos, porque está bien y previene futuros bardos.
    expire_time = user_to_update["reset_password_token_expires"].replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expire_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El token ha expirado.")

    new_hashed_password = security.get_password_hash(request.new_password)

    await db.users.update_one(
        {"_id": user_to_update["_id"]},
        {"$set": {
            "hashed_password": new_hashed_password
         },
         "$unset": {
            "reset_password_token": "",
            "reset_password_token_expires": ""
         }}
    )

    return {"message": "Contraseña actualizada con éxito."}

@router.get("/me", response_model=user_schemas.UserOut, summary="Obtener datos del usuario actual")
async def read_users_me(current_user: user_schemas.UserOut = Depends(auth_service.get_current_user)):
    return current_user

@router.post("/merge-cart", status_code=status.HTTP_200_OK, summary="Merge guest cart with user cart")
async def merge_guest_cart(
    request: user_schemas.MergeCartRequest,
    db: Database = Depends(get_db_nosql),
    current_user: user_schemas.UserOut = Depends(auth_service.get_current_user)
):
    guest_session_id = request.guest_session_id
    user_id = ObjectId(current_user.id)

    # Find the guest cart
    guest_cart = await db.carts.find_one({"guest_session_id": guest_session_id})
    if not guest_cart or not guest_cart.get("items"):
        # No guest cart to merge, so we're done.
        return {"message": "No guest cart to merge."}

    # Find the user's cart
    user_cart = await db.carts.find_one({"user_id": user_id})

    if not user_cart:
        # User has no cart, so we can just assign the guest cart to them.
        await db.carts.update_one(
            {"_id": guest_cart["_id"]},
            {
                "$set": {"user_id": user_id},
                "$unset": {"guest_session_id": ""}
            }
        )
        return {"message": "Guest cart assigned to user."}
    else:
        # Both user and guest have carts, merge them.
        guest_items = guest_cart.get("items", [])
        user_items = user_cart.get("items", [])
        
        user_items_map = {str(item["variante_id"]): item for item in user_items}

        for guest_item in guest_items:
            guest_variant_id = str(guest_item["variante_id"])
            if guest_variant_id in user_items_map:
                # Item exists, update quantity
                user_items_map[guest_variant_id]["quantity"] += guest_item["quantity"]
            else:
                # New item, add it to the user's cart
                user_items.append(guest_item)
        
        await db.carts.update_one(
            {"_id": user_cart["_id"]},
            {"$set": {"items": user_items}}
        )
        
        # Delete the guest cart
        await db.carts.delete_one({"_id": guest_cart["_id"]})
        
        return {"message": "Carts merged successfully."}
