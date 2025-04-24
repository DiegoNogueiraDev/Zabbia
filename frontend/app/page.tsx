"use client";

import React from 'react';
import MainLayout from '@/components/layout/MainLayout';
import ChatInterface from '@/components/dashboard/ChatInterface';
import StatusCard from '@/components/dashboard/StatusCard';
import { Activity, Server, AlertTriangle, Clock } from 'lucide-react';

export default function Home() {
  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-2">Dashboard Zabbia</h1>
          <p className="text-gray-500 dark:text-gray-400">
            Copiloto de Infraestrutura para Zabbix - Monitore e consulte sua infraestrutura com linguagem natural
          </p>
        </div>

        {/* Cards de status */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatusCard 
            title="Hosts Monitorados" 
            value="24" 
            description="Total de servidores ativos" 
            icon={Server}
            color="blue"
          />
          <StatusCard 
            title="Uptime Médio" 
            value="99.8%" 
            description="Últimas 24 horas" 
            icon={Clock}
            trend="up"
            trendValue="0.2%"
            color="green"
          />
          <StatusCard 
            title="Alertas Ativos" 
            value="3" 
            description="2 críticos, 1 warning" 
            icon={AlertTriangle}
            trend="down"
            trendValue="2"
            color="red"
          />
          <StatusCard 
            title="CPU Média" 
            value="42%" 
            description="Média de todos os hosts" 
            icon={Activity}
            color="purple"
          />
        </div>

        {/* Interface de chat */}
        <ChatInterface />
      </div>
    </MainLayout>
  );
} 