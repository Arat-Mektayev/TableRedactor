from sqlalchemy.orm import Session
from sqlalchemy import Table, Column, MetaData, Text, Integer, Float, DateTime, String, select, insert, update, delete
from sqlalchemy.sql import quoted_name
from sqlalchemy.exc import NoSuchTableError, IntegrityError, SQLAlchemyError
from app.models.table import Table as TableModel
from app.schemas.table import TableCreate, ColumnSchema, RowDataRequest
import json
import datetime
from typing import Dict, Any, List

# Маппинг типов конструктора на типы SQLAlchemy
TYPE_MAP = {
    "text": Text,
    "number": Float,  # Используем Float для чисел
    "timestamp": DateTime,
    "select": String(255),
}


def get_dynamic_table_object(db: Session, table_name: str) -> Table:
    """Вспомогательная функция: динамически отражает (reflect) таблицу из БД."""
    # SQLAlchemy 2.x: don't bind MetaData; pass engine to autoload_with
    metadata = MetaData()
    dynamic_table_name = f"data_{table_name.lower()}"

    try:
        # Отражаем структуру таблицы, которая уже существует в БД
        dynamic_table = Table(quoted_name(dynamic_table_name, True), metadata, autoload_with=db.bind)
        return dynamic_table
    except NoSuchTableError:
        raise ValueError(f"Физическая таблица {dynamic_table_name} не найдена в БД.")


def create_table_model(db: Session, table_data: TableCreate):
    """
    Создает метаданные таблицы (TableModel) и саму физическую таблицу в БД.
    """

    # 1. Сохранение метаданных схемы
    db_table_meta = TableModel(
        name=table_data.name,
        description=table_data.description,
        columns_json=[col.model_dump() for col in table_data.columns]
    )
    db.add(db_table_meta)

    # 2. Динамическое создание физической таблицы в PostgreSQL
    metadata = MetaData()

    columns_list = [
        Column('id', Integer, primary_key=True, index=True),
        Column('created_at', DateTime, default=datetime.datetime.utcnow, nullable=False)
    ]

    # Добавление пользовательских столбцов
    for col in table_data.columns:
        sqlalchemy_type = TYPE_MAP.get(col.type)
        if sqlalchemy_type is None:
            raise ValueError(f"Неизвестный тип столбца: {col.type}")

        columns_list.append(Column(quoted_name(col.name, True), sqlalchemy_type, nullable=not col.is_required))

    dynamic_table_name = f"data_{table_data.name.lower()}"
    dynamic_table = Table(
        quoted_name(dynamic_table_name, True),  # Имя таблицы в БД (quoted)
        metadata,
        *columns_list
    )

    try:
        metadata.create_all(db.bind)
        db.commit()
        db.refresh(db_table_meta)
        return db_table_meta
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"Ошибка БД при создании таблицы: {e}")


def get_table_metadata(db: Session, table_id: int):
    """Получает метаданные (схему) таблицы по ID."""
    return db.query(TableModel).filter(TableModel.id == table_id).first()


# --- CRUD-операции над СТРОКАМИ ДАННЫХ ---

def create_row_data(db: Session, table_name: str, row_data: Dict[str, Any]) -> Dict[str, Any]:
    """Добавляет новую строку в динамическую таблицу."""
    dynamic_table = get_dynamic_table_object(db, table_name)

    # Добавляем created_at, чтобы вернуть его в ответе
    new_row = {**row_data, 'created_at': datetime.datetime.utcnow()}

    stmt = insert(dynamic_table).values(**new_row)

    try:
        # Выполняем вставку и получаем ID новой строки
        result = db.execute(stmt.returning(dynamic_table.c.id, dynamic_table.c.created_at))
        db.commit()

        # Получаем данные вставленной строки
        inserted_id, created_at = result.fetchone()

        return {
            'id': inserted_id,
            'created_at': created_at.isoformat(),
            'data': row_data
        }
    except IntegrityError:
        db.rollback()
        raise ValueError("Ошибка целостности данных (возможно, нарушено ограничение NOT NULL).")


def read_rows_data(db: Session, table_name: str) -> List[Dict[str, Any]]:
    """Получает все строки данных из динамической таблицы."""
    dynamic_table = get_dynamic_table_object(db, table_name)

    stmt = select(dynamic_table)
    # Use mappings() for SQLAlchemy 2.x to get dict-like rows
    result = db.execute(stmt).mappings().all()

    rows_as_dicts = []
    for row in result:
        row_dict = dict(row)
        row_data = {k: v for k, v in row_dict.items() if k not in ['id', 'created_at']}
        created_at_val = row_dict.get('created_at')
        try:
            created_at_str = created_at_val.isoformat() if created_at_val else None
        except AttributeError:
            created_at_str = str(created_at_val) if created_at_val is not None else None
        rows_as_dicts.append({
            'id': row_dict.get('id'),
            'created_at': created_at_str,
            'data': row_data
        })

    return rows_as_dicts


def update_row_data(db: Session, table_name: str, row_id: int, new_data: Dict[str, Any]) -> Dict[str, Any]:
    """Обновляет строку в динамической таблице."""
    dynamic_table = get_dynamic_table_object(db, table_name)

    stmt = update(dynamic_table).where(dynamic_table.c.id == row_id).values(**new_data)

    try:
        result = db.execute(stmt)
        if result.rowcount == 0:
            raise ValueError(f"Строка с ID {row_id} не найдена.")

        db.commit()

        # NOTE: Для получения обновленной строки требуется дополнительный SELECT-запрос,
        # но для простоты мы просто вернем переданные данные + ID.
        # В полноценном приложении здесь нужен SELECT по ID.

        # Заглушка для возврата, пока не реализован SELECT
        return {'id': row_id, 'data': new_data, 'status': 'updated'}
    except IntegrityError:
        db.rollback()
        raise ValueError("Ошибка целостности данных при обновлении.")


def delete_row_data(db: Session, table_name: str, row_id: int) -> int:
    """Удаляет строку из динамической таблицы."""
    dynamic_table = get_dynamic_table_object(db, table_name)

    stmt = delete(dynamic_table).where(dynamic_table.c.id == row_id)

    result = db.execute(stmt)
    db.commit()

    if result.rowcount == 0:
        raise ValueError(f"Строка с ID {row_id} не найдена.")

    return row_id
