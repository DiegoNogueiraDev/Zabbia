"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LineChart, BarChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Loader2 } from "lucide-react";
import { DataTable } from "@/components/DataTable";
import { fetchMetricsOverview } from "@/lib/api";

export default function Dashboard() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const { data: metricsData, isLoading, error } = useQuery({
    queryKey: ["metrics-overview"],
    queryFn: fetchMetricsOverview,
  });

  // Mostrar estado de carregamento
  if (!mounted || isLoading) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-2">Carregando dados...</span>
      </div>
    );
  }

  // Mostrar estado de erro
  if (error) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <div className="rounded-lg bg-destructive/10 p-6 text-destructive">
          <h3 className="text-lg font-semibold">Erro ao carregar dados</h3>
          <p className="mt-2">{error instanceof Error ? error.message : "Ocorreu um erro desconhecido"}</p>
        </div>
      </div>
    );
  }

  // Dados dos gráficos
  const cpuData = metricsData?.metrics?.cpu || [];
  const memoryData = metricsData?.metrics?.memory || [];
  const availabilityData = metricsData?.metrics?.availability || [];
  const hostsInAlert = metricsData?.hosts_in_alert || [];

  // Calcular uptime médio
  const avgUptime = metricsData?.avg_uptime || 0;

  return (
    <div className="flex flex-col space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="heading-responsive font-bold">Dashboard</h1>
        <span className="text-sm text-muted-foreground">Atualizado em: {new Date().toLocaleString('pt-BR')}</span>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="card-hover">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Uptime Médio</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{avgUptime.toFixed(2)}%</div>
            <p className="text-xs text-muted-foreground">Últimas 24 horas</p>
          </CardContent>
        </Card>

        <Card className="card-hover">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Hosts Monitorados</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metricsData?.hosts?.length || 0}</div>
            <p className="text-xs text-muted-foreground">Total de hosts ativos</p>
          </CardContent>
        </Card>

        <Card className="card-hover">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Hosts em Alerta</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{hostsInAlert.length}</div>
            <p className="text-xs text-muted-foreground">Com problemas ativos</p>
          </CardContent>
        </Card>

        <Card className="card-hover">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Alertas Ativos</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {hostsInAlert.reduce((total, host) => total + host.alerts.length, 0)}
            </div>
            <p className="text-xs text-muted-foreground">Total de alertas</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="cpu" className="w-full">
        <TabsList className="grid w-full grid-cols-3 mb-4">
          <TabsTrigger value="cpu">CPU</TabsTrigger>
          <TabsTrigger value="memory">Memória</TabsTrigger>
          <TabsTrigger value="availability">Disponibilidade</TabsTrigger>
        </TabsList>
        
        <TabsContent value="cpu" className="w-full">
          <Card>
            <CardHeader>
              <CardTitle>Utilização de CPU</CardTitle>
            </CardHeader>
            <CardContent className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={cpuData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis label={{ value: '%', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="value" stroke="#8884d8" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="memory" className="w-full">
          <Card>
            <CardHeader>
              <CardTitle>Utilização de Memória</CardTitle>
            </CardHeader>
            <CardContent className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={memoryData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis label={{ value: '%', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="value" stroke="#82ca9d" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="availability" className="w-full">
          <Card>
            <CardHeader>
              <CardTitle>Disponibilidade do Sistema</CardTitle>
            </CardHeader>
            <CardContent className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={availabilityData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="host_name" />
                  <YAxis label={{ value: '%', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="availability_percent" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Card>
        <CardHeader>
          <CardTitle>Hosts em Alerta</CardTitle>
        </CardHeader>
        <CardContent>
          {hostsInAlert.length > 0 ? (
            <DataTable 
              data={hostsInAlert}
              columns={[
                { header: "Host", accessorKey: "name" },
                { header: "Alertas", accessorKey: "alerts", cell: ({ row }) => row.original.alerts.length },
                { header: "Severidade", accessorKey: "maxPriority", cell: ({ row }) => {
                  const priorities = row.original.alerts.map(a => a.priority);
                  const maxPriority = Math.max(...priorities);
                  return (
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      maxPriority >= 4 ? 'bg-red-100 text-red-800' : 
                      maxPriority >= 3 ? 'bg-orange-100 text-orange-800' : 
                      maxPriority >= 2 ? 'bg-yellow-100 text-yellow-800' : 
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {maxPriority >= 4 ? 'Crítico' : 
                       maxPriority >= 3 ? 'Alto' : 
                       maxPriority >= 2 ? 'Médio' : 
                       'Baixo'}
                    </span>
                  );
                }},
                { header: "Desde", accessorKey: "since", cell: ({ row }) => {
                  // Pegar a data mais antiga dos alertas
                  const dates = row.original.alerts.map(a => new Date(a.since));
                  const oldestDate = new Date(Math.min(...dates));
                  return oldestDate.toLocaleString('pt-BR');
                }}
              ]}
            />
          ) : (
            <div className="flex h-40 w-full items-center justify-center text-muted-foreground">
              Nenhum host em alerta no momento.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
} 