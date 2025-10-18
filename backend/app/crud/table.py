from sqlalchemy.orm import Session
from sqlalchemy import Table, Column, MetaData, Text, Integer, Float, DateTime, String, select, insert, update, delete
from sqlalchemy.exc import NoSuchTableError, IntegrityError, SQLAlchemyError
from app.models.table import TableModel
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


def get_dynamic_table_object(db: Session, table_db_name: str) -> Table:
    metadata = MetaData()
    try:
        dynamic_table = Table(table_db_name, metadata, autoload_with=db.bind)
        return dynamic_table
    except Exception as e:
        raise ValueError(f"Физическая таблица {table_db_name} не найдена в БД: {e}")


def create_table_model(db: Session, table_data: TableCreate):
    """Создает метаданные таблицы (TableModel) и саму физическую таблицу в БД."""
    
    # Генерируем имя физической таблицы, например: dynamic_table_123
    table_db_name = f"dynamic_table_{int(datetime.datetime.now().timestamp())}_{db.query(TableModel).count() + 1}"

    # 1. Создаём метаданные
    db_table_meta = TableModel(
        name=table_data.name,
        description=table_data.description,
        columns_json=[col.model_dump() for col in table_data.columns],
        table_db_name=table_db_name  # ← важно: поле должно быть в модели!
    )
    db.add(db_table_meta)
    db.commit()
    db.refresh(db_table_meta)

    # 2. Строим структуру таблицы через SQLAlchemy
    metadata = MetaData()
    columns = [
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("created_at", DateTime, default=datetime.datetime.utcnow),
    ]

    type_map = {
        "text": Text,
        "number": Float,
        "timestamp": DateTime,
        "select": String(255)
    }

    for col in table_data.columns:
        col_type = type_map.get(col.type)
        if not col_type:
            raise ValueError(f"Неподдерживаемый тип столбца: {col.type}")

        nullable = not col.is_required if col.is_required is not None else True
        columns.append(Column(col.name, col_type, nullable=nullable))

    # 3. Создаём таблицу в БД
    dynamic_table = Table(table_db_name, metadata, *columns)
    try:
        dynamic_table.create(bind=db.bind)
    except Exception as e:
        db.rollback()
        raise ValueError(f"Не удалось создать таблицу в БД: {e}")

    return db_table_meta


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
    result = db.execute(stmt).fetchall()

    rows_as_dicts = []
    for row in result:
        row_dict = row._asdict()
        row_data = {k: v for k, v in row_dict.items() if k not in ['id', 'created_at']}
        rows_as_dicts.append({
            'id': row_dict['id'],
            'created_at': row_dict['created_at'].isoformat() if row_dict['created_at'] else None,
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