"use client";

import React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { useState, useEffect } from "react";

interface Column {
  header: string;
  accessorKey: string;
  cell?: ({ row }: { row: any }) => React.ReactNode;
}

interface DataTableProps {
  data: any[];
  columns: Column[];
  defaultSort?: string;
  defaultSortDir?: "asc" | "desc";
  searchable?: boolean;
}

export function DataTable({
  data,
  columns,
  defaultSort,
  defaultSortDir = "asc",
  searchable = false,
}: DataTableProps) {
  const [sortColumn, setSortColumn] = useState<string | undefined>(defaultSort);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">(defaultSortDir);
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredData, setFilteredData] = useState(data);

  // Atualizar dados filtrados quando os dados mudam
  useEffect(() => {
    setFilteredData(data);
  }, [data]);

  // Filtrar e ordenar dados
  useEffect(() => {
    let result = [...data];

    // Filtragem
    if (searchTerm) {
      result = result.filter((item) => {
        return columns.some((column) => {
          const value = item[column.accessorKey];
          return value
            ? String(value).toLowerCase().includes(searchTerm.toLowerCase())
            : false;
        });
      });
    }

    // Ordenação
    if (sortColumn) {
      result.sort((a, b) => {
        const valueA = a[sortColumn];
        const valueB = b[sortColumn];

        if (valueA === undefined || valueA === null) return sortDirection === "asc" ? -1 : 1;
        if (valueB === undefined || valueB === null) return sortDirection === "asc" ? 1 : -1;

        // Comparação strings vs números
        if (typeof valueA === "string" && typeof valueB === "string") {
          return sortDirection === "asc"
            ? valueA.localeCompare(valueB)
            : valueB.localeCompare(valueA);
        } else {
          return sortDirection === "asc" ? valueA - valueB : valueB - valueA;
        }
      });
    }

    setFilteredData(result);
  }, [searchTerm, sortColumn, sortDirection, data, columns]);

  // Alternar ordenação
  const toggleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortColumn(column);
      setSortDirection("asc");
    }
  };

  return (
    <div className="space-y-4">
      {searchable && (
        <Input
          placeholder="Buscar..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-xs"
        />
      )}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((column) => (
                <TableHead
                  key={column.accessorKey}
                  className={sortColumn === column.accessorKey ? "bg-muted/50" : ""}
                  onClick={() => toggleSort(column.accessorKey)}
                >
                  <div className="flex items-center cursor-pointer">
                    {column.header}
                    {sortColumn === column.accessorKey && (
                      <span className="ml-2">
                        {sortDirection === "asc" ? "↑" : "↓"}
                      </span>
                    )}
                  </div>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredData.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  Nenhum resultado encontrado.
                </TableCell>
              </TableRow>
            ) : (
              filteredData.map((row, rowIndex) => (
                <TableRow key={rowIndex}>
                  {columns.map((column) => (
                    <TableCell key={column.accessorKey}>
                      {column.cell
                        ? column.cell({ row })
                        : row[column.accessorKey]}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
      <div className="text-xs text-muted-foreground">
        {filteredData.length} {filteredData.length === 1 ? "registro" : "registros"}
      </div>
    </div>
  );
} 