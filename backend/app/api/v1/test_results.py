from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import datetime
from sqlalchemy.orm import Session
from typing import List
from io import BytesIO
import pandas as pd

from app.schemas.table import TableCreate, TableInDB, DynamicTableData, RowDataRequest, RowDataResponse
from app.crud import table as crud_table
from app.core.database import get_db

router = APIRouter(
    prefix="/tables",
    tags=["Tables"]
)

@router.get("/", response_model=List[TableInDB])
def list_tables(db: Session = Depends(get_db)):
    """
    [LIST Таблиц] Возвращает список всех таблиц (метаданных).
    """
    return db.query(crud_table.TableModel).all()


# --- 1. CRUD для Схемы (Метаданных) Таблицы ---

@router.post("/", response_model=TableInDB, status_code=201)
def create_table(table_data: TableCreate, db: Session = Depends(get_db)):
    """
    [CREATE Таблицы] Создает новую таблицу (метаданные + физическая таблица в БД).
    """
    try:
        # Проверяем, существует ли таблица с таким именем
        if db.query(crud_table.TableModel).filter(crud_table.TableModel.name == table_data.name).first():
            raise HTTPException(status_code=400, detail="Таблица с таким именем уже существует.")

        db_table = crud_table.create_table_model(db, table_data)
        return db_table
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{table_id}", response_model=TableInDB)
def get_table_schema(table_id: int, db: Session = Depends(get_db)):
    """
    [READ Схемы] Получает структуру (схему) таблицы по ID.
    """
    db_table = crud_table.get_table_metadata(db, table_id)
    if db_table is None:
        raise HTTPException(status_code=404, detail="Таблица не найдена")

    return db_table


# NOTE: CRUD для полей (добавление/удаление/изменение столбцов в существующей
# таблице) требует сложной логики ALTER TABLE и обычно делается через миграции.
# В рамках этого MVP мы ограничимся созданием таблицы с заданным набором полей.


# --- 2. CRUD для Строк Данных в Динамической Таблице ---

@router.post("/{table_id}/rows", response_model=RowDataResponse, status_code=201)
def create_row(table_id: int, row_data: RowDataRequest, db: Session = Depends(get_db)):
    """
    [CREATE Строки] Добавляет новую строку в динамическую таблицу.
    """
    db_table_meta = crud_table.get_table_metadata(db, table_id)
    if db_table_meta is None:
        raise HTTPException(status_code=404, detail="Таблица не найдена")

    try:
        new_row = crud_table.create_row_data(db, db_table_meta.name, row_data.data)
        return new_row
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервера при вставке строки: {e}")


@router.get("/{table_id}/data", response_model=DynamicTableData)
def get_table_data(table_id: int, db: Session = Depends(get_db)):
    """
    [READ Все Строки] Получает схему таблицы и все её данные.
    """
    db_table_meta = crud_table.get_table_metadata(db, table_id)
    if db_table_meta is None:
        raise HTTPException(status_code=404, detail="Таблица не найдена")

    try:
        table_rows = crud_table.read_rows_data(db, db_table_meta.name)
    except ValueError as e:
        # Ошибка, если физическая таблица не существует
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сервера при получении данных: {e}")

    return DynamicTableData(
        table_schema=db_table_meta,
        rows=table_rows
    )


@router.put("/{table_id}/rows/{row_id}", response_model=RowDataResponse)
def update_row(table_id: int, row_id: int, new_data: RowDataRequest, db: Session = Depends(get_db)):
    """
    [UPDATE Строки] Обновляет существующую строку в динамической таблице.
    """
    db_table_meta = crud_table.get_table_metadata(db, table_id)
    if db_table_meta is None:
        raise HTTPException(status_code=404, detail="Таблица не найдена")

    try:
        updated_row = crud_table.update_row_data(db, db_table_meta.name, row_id, new_data.data)
        # В реальном приложении: вернуть полную обновленную строку
        return RowDataResponse(id=row_id, data=new_data.data, created_at=datetime.datetime.utcnow().isoformat())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при обновлении строки: {e}")


@router.delete("/{table_id}/rows/{row_id}", status_code=204)
def delete_row(table_id: int, row_id: int, db: Session = Depends(get_db)):
    """
    [DELETE Строки] Удаляет строку из динамической таблицы.
    """
    db_table_meta = crud_table.get_table_metadata(db, table_id)
    if db_table_meta is None:
        raise HTTPException(status_code=404, detail="Таблица не найдена")

    try:
        crud_table.delete_row_data(db, db_table_meta.name, row_id)
        return {"detail": "Строка успешно удалена"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении строки: {e}")


@router.post("/{table_id}/import")
async def import_excel(table_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    [IMPORT Excel] Загружает данные из Excel-файла и добавляет строки в динамическую таблицу.
    Ожидается, что названия столбцов в Excel совпадают с именами столбцов схемы таблицы.
    """
    db_table_meta = crud_table.get_table_metadata(db, table_id)
    if db_table_meta is None:
        raise HTTPException(status_code=404, detail="Таблица не найдена")

    try:
        content = await file.read()
        df = pd.read_excel(BytesIO(content))
        # Приводим имена столбцов к строкам (важно для числовых заголовков '1','2','3','4')
        try:
            df.columns = [str(c).strip() for c in df.columns]
        except Exception:
            pass

        # Получаем список допустимых столбцов из схемы
        columns = db_table_meta.columns_json
        if isinstance(columns, str):
            import json
            columns = json.loads(columns)
        allowed_cols = [c.get("name") for c in columns if isinstance(c, dict) and c.get("name")]

        inserted_rows = []
        for _, r in df.iterrows():
            data = {}
            for col in allowed_cols:
                # В pandas заголовки могли быть числами; после преобразования — строки
                value = r.get(col, None)
                # Обработка NaN
                try:
                    import math
                    if value is None or (isinstance(value, float) and math.isnan(value)):
                        value = None
                except Exception:
                    pass
                # Даты -> ISO
                if hasattr(value, "isoformat"):
                    try:
                        value = value.isoformat()
                    except Exception:
                        pass
                data[col] = value

            try:
                new_row = crud_table.create_row_data(db, db_table_meta.name, data)
                inserted_rows.append(new_row)
            except ValueError:
                # Пропускаем строки, не подходящие под ограничения
                continue

        return {"rows": inserted_rows}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка импорта: {e}")
