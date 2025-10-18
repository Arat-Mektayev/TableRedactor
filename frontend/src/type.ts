export type ColumnType = "text" | "number" | "timestamp" | "select";

export interface Column {
  name: string;
  type: ColumnType;
  is_required?: boolean;
  options?: string[];
}

// Note: This local type is kept only for legacy imports.
// Prefer importing Table, Column from src/api across components.
export interface TableLegacy {
  id: number;
  name: string;
  columns: Column[];
}

// Backward-compatible alias for old imports
export type Table = TableLegacy;
