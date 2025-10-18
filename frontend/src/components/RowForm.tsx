import React, { useEffect, useState } from "react";
import {
  Box,
  Button,
  Input,
  VStack,
  FormControl,
  FormLabel,
  NumberInput,
  NumberInputField,
  Select,
  useToast,
} from "@chakra-ui/react";
import { Column } from "../api";

interface Props {
  columns: Column[];
  onSubmit: (row: Record<string, any>) => Promise<void>;
}

const RowForm: React.FC<Props> = ({ columns, onSubmit }) => {
  const [rowData, setRowData] = useState<Record<string, any>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const toast = useToast();

  useEffect(() => {
    const initialData = Object.fromEntries(
      columns.map(c => [c.name, c.type === 'number' ? 0 : ''])
    );
    setRowData(initialData);
  }, [columns]);

  const handleChange = (col: Column, value: any) => {
    let processedValue = value;
    if (col.type === 'number') {
      processedValue = value === '' ? undefined : Number(value);
    } else if (col.type === 'timestamp' && value) {
      processedValue = new Date(value).toISOString();
    }
    setRowData(prev => ({ ...prev, [col.name]: processedValue }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await onSubmit(rowData);
      const initialData = Object.fromEntries(
        columns.map(c => [c.name, c.type === 'number' ? 0 : ''])
      );
      setRowData(initialData);
      toast({
        title: "Строка успешно добавлена",
        status: "success",
        duration: 2000,
      });
    } catch (error: any) {
      const detail = error?.response?.data?.detail || error.message;
      toast({
        title: "Ошибка добавления строки",
        description: detail,
        status: "error",
        duration: 5000,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderInput = (column: Column) => {
    switch (column.type) {
      case 'number':
        return (
          <NumberInput
            value={rowData[column.name] || 0}
            onChange={(value) => handleChange(column, value)}
          >
            <NumberInputField />
          </NumberInput>
        );
      case 'timestamp':
        return (
          <Input
            type="datetime-local"
            value={rowData[column.name] || ''}
            onChange={(e) => handleChange(column, e.target.value)}
          />
        );
      case 'select':
        return (
          <Select
            value={rowData[column.name] || ''}
            onChange={(e) => handleChange(column, e.target.value)}
          >
            <option value="">Выберите...</option>
            {(column.options || []).map((opt) => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </Select>
        );
      default:
        return (
          <Input
            type="text"
            value={rowData[column.name] || ''}
            onChange={(e) => handleChange(column, e.target.value)}
          />
        );
    }
  };

  return (
    <Box as="form" onSubmit={handleSubmit} borderWidth="1px" p={4} borderRadius="md" shadow="sm">
      <VStack spacing={4}>
        {columns.map((column) => (
          <FormControl key={column.name} isRequired={column.is_required}>
            <FormLabel>{column.name}</FormLabel>
            {renderInput(column)}
          </FormControl>
        ))}
        <Button
          type="submit"
          colorScheme="blue"
          isLoading={isSubmitting}
          loadingText="Добавление..."
          width="full"
        >
          Добавить строку
        </Button>
      </VStack>
    </Box>
  );
}

export default RowForm;
