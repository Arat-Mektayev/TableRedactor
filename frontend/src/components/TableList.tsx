import React from "react";
import { Table } from "../api";
import { Box, Heading, List, ListItem, Text, Button, VStack } from "@chakra-ui/react";

interface Props {
  tables: Table[];
  onSelect: (table: Table) => void;
}

const TableList: React.FC<Props> = ({ tables, onSelect }) => {
  return (
    <Box borderWidth="1px" p={4} borderRadius="md" shadow="sm">
      <Heading size="md" mb={3}>Список таблиц</Heading>
      <VStack align="stretch" spacing={3}>
        {tables.map((table) => {
          const colsRaw: any = (table as any).columns_json;
          const cols = Array.isArray(colsRaw) ? colsRaw : (() => { try { return JSON.parse(colsRaw); } catch { return []; }})();
          return (
            <Box key={table.id} borderWidth="1px" p={3} borderRadius="md">
              <Text fontWeight="bold">{table.name}</Text>
              {cols?.length > 0 && (
                <Text fontSize="sm" color="gray.600">
                  Поля: {cols.map((c: any) => c?.name).filter(Boolean).join(", ")}
                </Text>
              )}
              <Button mt={2} size="sm" onClick={() => onSelect(table)} colorScheme="blue">Открыть</Button>
            </Box>
          );
        })}
      </VStack>
    </Box>
  );
};

export default TableList;
