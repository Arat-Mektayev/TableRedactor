// frontend/src/components/RowForm.tsx

import React, { useState } from 'react';
import { Box, Button, FormControl, FormLabel, Input, Stack } from '@chakra-ui/react';

interface Column {
  name: string;
  type: string;
  // Добавьте другие поля при необходимости
}

interface Props {
  columns: Column[];
  onSubmit: (data: Record<string, any>) => void;
  initialData?: Record<string, any>; // Новый пропс
}

const RowForm: React.FC<Props> = ({ columns, onSubmit, initialData = {} }) => {
  const [formData, setFormData] = useState<Record<string, any>>(
    Object.fromEntries(
      columns.map((col) => [col.name, initialData[col.name] || ''])
    )
  );

  const handleChange = (name: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
    // Сброс формы после отправки
    setFormData(
      Object.fromEntries(
        columns.map((col) => [col.name, ''])
      )
    );
  };

  return (
    <Box as="form" onSubmit={handleSubmit}>
      <Stack spacing={3}>
        {columns.map((col) => (
          <FormControl key={col.name}>
            <FormLabel>{col.name}</FormLabel>
            <Input
              type="text"
              value={formData[col.name] || ''}
              onChange={(e) => handleChange(col.name, e.target.value)}
            />
          </FormControl>
        ))}
        <Button type="submit" colorScheme="blue">
          {initialData && Object.keys(initialData).length > 0 ? 'Сохранить изменения' : 'Добавить строку'}
        </Button>
      </Stack>
    </Box>
  );
};

export default RowForm;