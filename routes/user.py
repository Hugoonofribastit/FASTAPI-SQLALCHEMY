
from config.db import conn
from models.user import users
from schemas.user import User, UserCount
from typing import List
from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_204_NO_CONTENT
from sqlalchemy import func, select
import bcrypt



from cryptography.fernet import Fernet

user = APIRouter()
key = Fernet.generate_key()
f = Fernet(key)


@user.get(
    "/users",
    tags=["users"],
    response_model=List[User],
    description="Get a list of all users",
)
def get_users():
    return conn.execute(users.select()).fetchall()


@user.get("/users/count", tags=["users"], response_model=UserCount)
def get_users_count():
    result = conn.execute(select([func.count()]).select_from(users))
    return {"total": tuple(result)[0][0]}


@user.get(
    "/users/{id}",
    tags=["users"],
    response_model=User,
    description="Get a single user by Id",
)
def get_user(id: str):
    return conn.execute(users.select().where(users.c.id == id)).first()


@user.post("/", tags=["users"], response_model=User, description="Create a new user")
def create_user(user: User):
    new_user = {"name": user.name, "email": user.email}
    new_user["password"] = f.encrypt(user.password.encode("utf-8"))
    result = conn.execute(users.insert().values(new_user))
    return conn.execute(users.select().where(users.c.id == result.lastrowid)).first()


""" @user.put(
    "users/{id}", tags=["users"], response_model=User, description="Update a User by Id"
)
def update_user(user: User, id: int):
    conn.execute(
        users.update().values(name=user.name, email=user.email, password=user.password).where(users.c.id == id)
    )
    return conn.execute(users.select().where(users.c.id == id)).first() """


@user.delete("/{id}", tags=["users"], status_code=HTTP_204_NO_CONTENT)
def delete_user(id: int):
    conn.execute(users.delete().where(users.c.id == id))
    return conn.execute(users.select().where(users.c.id == id)).first()

@user.put("/users/{id}", response_model=User, description="Update a User by Id")
def update_user(id: int, user: User):
    # Comprueba si el usuario con el ID proporcionado existe
    user_query = users.select().where(users.c.id == id)
    existing_user = conn.execute(user_query).first()

    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Hashea la nueva contraseña antes de actualizarla en la base de datos
    hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())

    # Actualiza el usuario con los nuevos datos
    conn.execute(
        users.update()
        .values(name=user.name, email=user.email, password=hashed_password)
        .where(users.c.id == id)
    )
    # Recupera y devuelve el usuario actualizado
    updated_user = conn.execute(user_query).first()
    return updated_user