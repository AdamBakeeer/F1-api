from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    favorite_drivers = relationship(
        "FavoriteDriver",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    favorite_constructors = relationship(
        "FavoriteConstructor",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    favorite_circuits = relationship(
        "FavoriteCircuit",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class FavoriteDriver(Base):
    __tablename__ = "favorite_drivers"

    favorite_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    driver_id = Column(Integer, nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("user_id", "driver_id", name="unique_user_driver"),
    )

    user = relationship(
        "User",
        back_populates="favorite_drivers",
        primaryjoin="User.user_id == foreign(FavoriteDriver.user_id)",
    )


class FavoriteConstructor(Base):
    __tablename__ = "favorite_constructors"

    favorite_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    constructor_id = Column(Integer, nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("user_id", "constructor_id", name="unique_user_constructor"),
    )

    user = relationship(
        "User",
        back_populates="favorite_constructors",
        primaryjoin="User.user_id == foreign(FavoriteConstructor.user_id)",
    )


class FavoriteCircuit(Base):
    __tablename__ = "favorite_circuits"

    favorite_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    circuit_id = Column(Integer, nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("user_id", "circuit_id", name="unique_user_circuit"),
    )

    user = relationship(
        "User",
        back_populates="favorite_circuits",
        primaryjoin="User.user_id == foreign(FavoriteCircuit.user_id)",
    )