from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from database_persona import Base
from datetime import datetime
from sqlalchemy.sql import func


class PersonaFlow(Base):
    __tablename__ = "persona_flow"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, index=True, nullable=False)
    character_name = Column(String(100), nullable=False)
    mode = Column(String(10), nullable=False)  # 'auto' or 'custom'
    tone = Column(String(50), default="neutral", nullable=False)
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)

    # Relationship to messages (cascade delete)
    messages = relationship(
        "PersonaMessage",
        back_populates="persona",
        cascade="all, delete-orphan",
        lazy="dynamic"  # Better performance for counting
    )

    # Composite index for faster user queries
    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
    )

    def __repr__(self):
        return f"<PersonaFlow(id={self.id}, user_id={self.user_id}, character='{self.character_name}')>"


class PersonaMessage(Base):
    __tablename__ = "persona_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    persona_id = Column(Integer, ForeignKey("persona_flow.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String(10), nullable=False)  # 'user' or 'agent'
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)

    # Relationship back to persona
    persona = relationship("PersonaFlow", back_populates="messages")

    # Composite index for faster history queries
    __table_args__ = (
        Index('idx_persona_created', 'persona_id', 'created_at'),
    )

    def __repr__(self):
        return f"<PersonaMessage(id={self.id}, persona_id={self.persona_id}, sender='{self.sender}')>"