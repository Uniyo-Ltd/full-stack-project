import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import EmailStr, BaseModel
from sqlmodel import Field, Relationship, SQLModel, Column, JSON
from sqlalchemy.ext.declarative import declarative_base
import requests
from sqlalchemy import Index

Base = declarative_base()


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)

class SetMenuCuisineLink(SQLModel, table=True):
    set_menu_id: Optional[int] = Field(default=None, foreign_key="setmenu.id", primary_key=True)
    cuisine_id: Optional[int] = Field(default=None, foreign_key="cuisine.id", primary_key=True)


class Cuisine(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    set_menus: List["SetMenu"] = Relationship(back_populates="cuisines", link_model=SetMenuCuisineLink)


class MenuGroupGroups(BaseModel):
    ungrouped: int
    Starters: Optional[int] = None
    Mains: Optional[int] = None
    Sides: Optional[int] = None
    Dessert: Optional[int] = None
    Sharing_Plates: Optional[int] = None
    Side_dish: Optional[int] = None
    Canape: Optional[int] = None
    Main: Optional[int] = None
    Main_Dish: Optional[int] = None
    Add_On: Optional[int] = None
    Desserts: Optional[int] = None
    To_Start: Optional[int] = None
    Main_Dish: Optional[int] = None
    Side_Dish: Optional[int] = None
    Sharing_Plates: Optional[int] = None
    Desserts: Optional[int] = None
    mains: Optional[int] = None
    starter: Optional[int] = None
    desserts: Optional[int] = None

class MenuGroups(BaseModel):
    dishes_count: int
    selectable_dishes_count: int
    groups: MenuGroupGroups


class SetMenu(SQLModel, table=True):
    __table_args__ = (
        # Index for price-based queries
        Index('idx_price_per_person', 'price_per_person'),
        
        # Composite index for dietary requirements (commonly filtered together)
        Index('idx_dietary', 'is_vegan', 'is_vegetarian', 'is_halal'),
        
        # Index for name searches
        Index('idx_name', 'name'),
        
        # Index for created_at (for sorting/filtering by date)
        Index('idx_created_at', 'created_at')
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime
    description: Optional[str] = None
    display_text: int
    image: str
    thumbnail: str
    is_vegan: bool
    is_vegetarian: bool
    name: str
    status: int
    price_per_person: float
    min_spend: float
    is_seated: bool
    is_standing: Optional[bool] = Field(default=False)
    is_canape: bool
    is_mixed_dietary: bool
    is_meal_prep: bool
    is_halal: bool
    is_kosher: bool
    available: bool
    number_of_orders: int
    cuisines: List[Cuisine] = Relationship(back_populates="set_menus", link_model=SetMenuCuisineLink)


class SetMenuData(SQLModel):
    data: List[SetMenu]
    links: Dict[str, Optional[str]]
    meta: Dict[str, any]

    class Config: # Add this Config inner class
        arbitrary_types_allowed = True # Set this to True