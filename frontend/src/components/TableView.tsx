import React, { useState, useEffect } from 'react';
import {
  Box,
  Heading,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Button,
  useToast,
  Spinner,
} from '@chakra-ui/react';
import { Table as TableType, Row, getTableData, addRow, deleteRow, updateRow } from '../api';
import RowForm from './RowForm';

interface Props {
  selectedTable: TableType | null;
}

const TableView: React.FC<Props> = ({ selectedTable }) => {
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingRow, setEditingRow] = useState<Row | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  const toast = useToast();

  useEffect(() => {
    loadData();
  }, [selectedTable]);

  const loadData = async () => {
    if (!selectedTable) return;

    try {
      setLoading(true);
      const { rows } = await getTableData(selectedTable.id);
      setRows(rows);
    } catch (error: any) {
      toast({
        title: 'Ошибка загрузки данных',
        description: error?.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAddRow = async (data: Record<string, any>) => {
    if (!selectedTable) return;

    try {
      await addRow(selectedTable.id, data);
      toast({ title: 'Строка добавлена', status: 'success', duration: 3000 });
      loadData();
    } catch (error: any) {
      toast({
        title: 'Ошибка добавления строки',
        description: error?.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };

  const handleDeleteRow = async (rowId: number) => {
    if (!selectedTable) return;

    try {
      await deleteRow(selectedTable.id, rowId);
      toast({ title: 'Строка удалена', status: 'success', duration: 3000 });
      loadData();
    } catch (error: any) {
      toast({
        title: 'Ошибка удаления строки',
        description: error?.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };

  const handleEdit = (row: Row) => {
    setEditingRow(row);
    setIsEditing(true);
  };

  const handleSubmitEdit = async (data: Record<string, any>) => {
    if (!selectedTable || !editingRow) return;

    try {
      await updateRow(selectedTable.id, editingRow.id, data);
      toast({ title: 'Строка обновлена', status: 'success', duration: 3000 });
      loadData();
      setIsEditing(false);
      setEditingRow(null);
    } catch (error: any) {
      toast({
        title: 'Ошибка обновления строки',
        description: error?.response?.data?.detail || error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditingRow(null);
  };

  if (!selectedTable) {
    return <Box p={4}>Выберите таблицу</Box>;
  }

  const columns = selectedTable.columns_json;

  return (
    <Box p={4}>
      <Heading size="lg" mb={4}>
        {selectedTable.name}
      </Heading>

      {isEditing && editingRow && (
        <Box mt={4} p={4} bg="gray.50" borderRadius="md">
          <Heading size="sm" mb={4}>
            Редактирование строки
          </Heading>
          <RowForm
            columns={columns}
            onSubmit={handleSubmitEdit}
            initialData={editingRow.data}
          />
          <Button mt={2} onClick={handleCancelEdit} variant="outline">
            Отмена
          </Button>
        </Box>
      )}

      {!isEditing && (
        <RowForm columns={columns} onSubmit={handleAddRow} />
      )}

      {loading ? (
        <Spinner />
      ) : (
        <Table variant="simple" mt={4}>
          <Thead>
            <Tr>
              {columns.map((col: any) => (
                <Th key={col.name}>{col.name}</Th>
              ))}
              <Th>Действия</Th>
            </Tr>
          </Thead>
          <Tbody>
            {rows.map((row) => (
              <Tr key={row.id}>
                {columns.map((col: any) => (
                  <Td key={col.name}>{row.data[col.name]}</Td>
                ))}
                <Td>
                  <Button
                    size="sm"
                    colorScheme="yellow"
                    mr={2}
                    onClick={() => handleEdit(row)}
                  >
                    Редактировать
                  </Button>
                  <Button
                    size="sm"
                    colorScheme="red"
                    onClick={() => handleDeleteRow(row.id)}
                  >
                    Удалить
                  </Button>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      )}
    </Box>
  );
};

export default TableView;