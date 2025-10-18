# backend/app/models/table.py
from sqlalchemy import Column, Integer, String, JSON
from app.core.database import Base

class TableModel(Base):
    __tablename__ = "tables_metadata"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    columns_json = Column(JSON, nullable=False)
    table_db_name = Column(String, nullable=False)  # ← новое поле