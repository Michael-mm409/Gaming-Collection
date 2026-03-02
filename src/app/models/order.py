# SQLAlchemy models moved from models.py
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional

class Base(DeclarativeBase):
	pass

class Category(Base):
	__tablename__ = 'category'
	id: Mapped[int] = mapped_column(primary_key=True)
	name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
	type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'platform', 'status', 'ownership', 'digital_physical'

class Game(Base):
	__tablename__ = 'game'
	id: Mapped[int] = mapped_column(primary_key=True)
	title: Mapped[str] = mapped_column(String(100), nullable=False)
	platform_id: Mapped[int] = mapped_column(ForeignKey('platform.id'), nullable=False)
	cost: Mapped[Optional[float]] = mapped_column(nullable=True)
	grade: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Boxed, Boxed/Digital, Digital, New, Preowned, Want
	status_id: Mapped[Optional[int]] = mapped_column(ForeignKey('category.id'), nullable=True)
	ownership_id: Mapped[Optional[int]] = mapped_column(ForeignKey('category.id'), nullable=True)
	digital_physical_id: Mapped[Optional[int]] = mapped_column(ForeignKey('category.id'), nullable=True)
	notes: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
	image_url: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
	type: Mapped[str] = mapped_column(String(20), default="game")

	platform: Mapped['Platform'] = relationship('Platform', foreign_keys=[platform_id])
	status: Mapped[Optional[Category]] = relationship('Category', foreign_keys=[status_id])
	ownership: Mapped[Optional[Category]] = relationship('Category', foreign_keys=[ownership_id])
	digital_physical: Mapped[Optional[Category]] = relationship('Category', foreign_keys=[digital_physical_id])

class Peripheral(Base):
	__tablename__ = 'peripheral'
	id: Mapped[int] = mapped_column(primary_key=True)
	name: Mapped[str] = mapped_column(String(100), nullable=False)
	platform_id: Mapped[int] = mapped_column(ForeignKey('platform.id'), nullable=False)
	peripheral_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
	platform_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
	cost: Mapped[Optional[float]] = mapped_column(nullable=True)
	quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
	purchased_from: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
	ownership_id: Mapped[Optional[int]] = mapped_column(ForeignKey('category.id'), nullable=True)
	notes: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

	platform: Mapped['Platform'] = relationship('Platform', foreign_keys=[platform_id])
	ownership: Mapped[Optional[Category]] = relationship('Category', foreign_keys=[ownership_id])

class Platform(Base):
	__tablename__ = 'platform'
	id: Mapped[int] = mapped_column(primary_key=True)
	name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
	manufacturer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
	release_year: Mapped[Optional[int]] = mapped_column(nullable=True)
	generation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
	description: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
	cost: Mapped[Optional[float]] = mapped_column(nullable=True)
	quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
	purchased_from: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
	ownership_id: Mapped[Optional[int]] = mapped_column(ForeignKey('category.id'), nullable=True)
	notes: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

	ownership: Mapped[Optional[Category]] = relationship('Category', foreign_keys=[ownership_id])
# Placeholder for order model
