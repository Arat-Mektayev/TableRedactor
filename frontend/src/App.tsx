// frontend/src/App.tsx

import React, { useEffect, useState } from "react";
import { ChakraProvider, Box, Heading, SimpleGrid, Button } from "@chakra-ui/react";
import CreateTableForm from "./components/CreateTableForm";
import TableView from "./components/TableView";
import TableList from "./components/TableList";
import { getTables, Table } from "./api";

const App: React.FC = () => {
  const [tableId, setTableId] = useState<number | null>(null);
  const [tables, setTables] = useState<Table[]>([]);

  const loadTables = async () => {
    try {
      const list = await getTables();
      setTables(list);
    } catch (e) {
      // ignore for initial load
    }
  };

  useEffect(() => {
    if (tableId === null) {
      loadTables();
    }
  }, [tableId]);

  // Найдём выбранную таблицу по ID
  const selectedTable = tableId ? tables.find(t => t.id === tableId) || null : null;

  return (
    <ChakraProvider>
      <Box p={4}>
        <Heading mb={4}>Динамические Таблицы</Heading>
        {!tableId ? (
          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
            <CreateTableForm onCreated={(id) => setTableId(id)} />
            <TableList tables={tables} onSelect={(t) => setTableId(t.id)} />
          </SimpleGrid>
        ) : (
          <Box>
            <Button mb={4} onClick={() => setTableId(null)}>← Назад</Button>
            {/* Передаём selectedTable вместо tableId */}
            {selectedTable ? (
              <TableView selectedTable={selectedTable} />
            ) : (
              <Box>Таблица не найдена</Box>
            )}
          </Box>
        )}
      </Box>
    </ChakraProvider>
  );
};

export default App;