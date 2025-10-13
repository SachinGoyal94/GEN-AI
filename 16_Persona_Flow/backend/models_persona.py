from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from database_persona import Base
from datetime import datetime
from sqlalchemy.sql import func
class PersonaFlow(Base):
    __tablename__ = "persona_flow"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    character_name = Column(String(100), nullable=False)
    mode = Column(String(10), nullable=False)  # 'auto' or 'custom'
    tone = Column(String(50), default="neutral")
    summary = Column(Text, nullable=False)

    created_at = Column(DateTime, server_default=func.current_timestamp())
    messages = relationship("PersonaMessage", back_populates="persona", cascade="all, delete-orphan")

class PersonaMessage(Base):
    __tablename__ = "persona_messages"
    id = Column(Integer, primary_key=True, index=True)
    persona_id = Column(Integer, ForeignKey("persona_flow.id"), nullable=False)
    sender = Column(String(10), nullable=False)  # 'user' or 'agent'
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    persona = relationship("PersonaFlow", back_populates="messages")
