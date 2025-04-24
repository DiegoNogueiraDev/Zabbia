"use client";

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Bell, Clock, Server, AlertCircle, CheckCircle, Ban, Search, Filter, ArrowUpDown, ChevronDown, ChevronRight } from 'lucide-react';
import MainLayout from '@/components/layout/MainLayout';

// Tipos e dados simulados
type AlertSeverity = 'critical' | 'warning' | 'info' | 'resolved';
type AlertStatus = 'active' | 'acknowledged' | 'resolved';

interface Alert {
  id: string;
  title: string;
  description: string;
  host: string;
  severity: AlertSeverity;
  status: AlertStatus;
  timestamp: string;
  duration: string;
}

const mockAlerts: Alert[] = [
  {
    id: '1',
    title: 'Disco cheio',
    description: '/var/log está com 92% de uso',
    host: 'storage01',
    severity: 'critical',
    status: 'active',
    timestamp: '2023-11-15 14:32:12',
    duration: '2h 15m'
  },
  {
    id: '2',
    title: 'Falha HTTP',
    description: 'Serviço HTTP não está respondendo na porta 80',
    host: 'web03',
    severity: 'critical',
    status: 'acknowledged',
    timestamp: '2023-11-15 15:02:45',
    duration: '1h 45m'
  },
  {
    id: '3',
    title: 'CPU elevada',
    description: 'Uso de CPU acima de 80% por mais de 15 minutos',
    host: 'db01',
    severity: 'warning',
    status: 'active',
    timestamp: '2023-11-15 16:10:33',
    duration: '37m'
  },
  {
    id: '4',
    title: 'Ping timeout',
    description: 'Host não responde a ping há 5 minutos',
    host: 'app02',
    severity: 'warning',
    status: 'acknowledged',
    timestamp: '2023-11-15 16:25:18',
    duration: '22m'
  },
  {
    id: '5',
    title: 'Swap em uso',
    description: 'Swap acima de 50% por mais de 30 minutos',
    host: 'web02',
    severity: 'info',
    status: 'active',
    timestamp: '2023-11-15 16:45:02',
    duration: '3m'
  },
  {
    id: '6',
    title: 'Falha em processo',
    description: 'O processo nginx não está rodando',
    host: 'web01',
    severity: 'critical',
    status: 'resolved',
    timestamp: '2023-11-15 12:18:55',
    duration: '45m'
  },
];

// Componentes da interface
const AlertCard: React.FC<{ alert: Alert }> = ({ alert }) => {
  const [expanded, setExpanded] = useState(false);
  
  const severityClasses = {
    critical: 'bg-gradient-to-r from-red-900/20 to-red-800/10 border-l-4 border-red-500',
    warning: 'bg-gradient-to-r from-amber-900/20 to-amber-800/10 border-l-4 border-amber-500',
    info: 'bg-gradient-to-r from-blue-900/20 to-blue-800/10 border-l-4 border-blue-500',
    resolved: 'bg-gradient-to-r from-green-900/20 to-green-800/10 border-l-4 border-green-500'
  };
  
  const severityIcons = {
    critical: <AlertCircle className="h-5 w-5 text-red-500" />,
    warning: <AlertCircle className="h-5 w-5 text-amber-500" />,
    info: <AlertCircle className="h-5 w-5 text-blue-500" />,
    resolved: <CheckCircle className="h-5 w-5 text-green-500" />
  };
  
  const statusBadges = {
    active: <span className="px-2 py-1 text-xs rounded-full bg-red-900/40 text-red-400">Ativo</span>,
    acknowledged: <span className="px-2 py-1 text-xs rounded-full bg-blue-900/40 text-blue-400">Reconhecido</span>,
    resolved: <span className="px-2 py-1 text-xs rounded-full bg-green-900/40 text-green-400">Resolvido</span>
  };
  
  return (
    <motion.div 
      className={`mb-3 rounded-lg overflow-hidden ${severityClasses[alert.severity]}`}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div 
        className="p-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {severityIcons[alert.severity]}
            <div>
              <h3 className="text-md font-medium">{alert.title}</h3>
              <p className="text-sm text-gray-400 flex items-center gap-2">
                <Server className="h-3 w-3" />
                {alert.host}
                <span className="text-gray-500">•</span>
                <Clock className="h-3 w-3" />
                {alert.duration}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            {statusBadges[alert.status]}
            <div className="text-gray-400">
              {expanded ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
            </div>
          </div>
        </div>
      </div>
      
      {expanded && (
        <motion.div 
          className="p-4 pt-0 border-t border-gray-800"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          transition={{ duration: 0.2 }}
        >
          <p className="text-gray-300 mb-3">{alert.description}</p>
          <div className="flex justify-between text-xs text-gray-500">
            <span>Detectado: {alert.timestamp}</span>
            <div className="flex gap-2">
              <button className="px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded-md text-white">
                Reconhecer
              </button>
              <button className="px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded-md text-white">
                Resolver
              </button>
              <button className="px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded-md text-white">
                Silenciar
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

const AlertFilter: React.FC = () => (
  <div className="flex flex-wrap gap-3 mb-6">
    <div className="relative bg-gray-800/70 rounded-lg flex-1 min-w-[180px]">
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <Search className="h-4 w-4 text-gray-500" />
      </div>
      <input 
        type="text" 
        placeholder="Buscar alertas..." 
        className="bg-transparent w-full pl-10 pr-4 py-2 text-white rounded-lg focus:outline-none focus:ring-1 focus:ring-emerald-500 border border-gray-700"
      />
    </div>
    
    <div className="relative bg-gray-800/70 rounded-lg">
      <select className="appearance-none bg-transparent px-4 py-2 pr-8 text-white rounded-lg focus:outline-none focus:ring-1 focus:ring-emerald-500 border border-gray-700">
        <option>Todos os hosts</option>
        <option>Críticos</option>
        <option>Aplicação</option>
        <option>Banco de dados</option>
        <option>Storage</option>
      </select>
      <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
        <ChevronDown className="h-4 w-4 text-gray-500" />
      </div>
    </div>
    
    <div className="relative bg-gray-800/70 rounded-lg">
      <select className="appearance-none bg-transparent px-4 py-2 pr-8 text-white rounded-lg focus:outline-none focus:ring-1 focus:ring-emerald-500 border border-gray-700">
        <option>Todas severidades</option>
        <option>Crítico</option>
        <option>Alerta</option>
        <option>Informação</option>
      </select>
      <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
        <ChevronDown className="h-4 w-4 text-gray-500" />
      </div>
    </div>
    
    <button className="p-2 bg-gray-800/70 hover:bg-gray-700/70 rounded-lg text-gray-400 border border-gray-700">
      <Filter className="h-5 w-5" />
    </button>
    
    <button className="p-2 bg-gray-800/70 hover:bg-gray-700/70 rounded-lg text-gray-400 border border-gray-700">
      <ArrowUpDown className="h-5 w-5" />
    </button>
  </div>
);

const AlertStats: React.FC = () => (
  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
    <motion.div 
      className="bg-gradient-to-br from-red-900/40 to-red-900/10 rounded-lg p-4 backdrop-blur-sm border border-red-900/30"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.1 }}
    >
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-sm font-medium text-gray-400">Críticos</h3>
        <span className="bg-red-500/20 text-red-500 rounded-full w-8 h-8 flex items-center justify-center">
          <AlertCircle className="h-4 w-4" />
        </span>
      </div>
      <p className="text-2xl font-bold text-white">3</p>
      <p className="text-xs text-red-400 mt-1">+1 nas últimas 24h</p>
    </motion.div>
    
    <motion.div 
      className="bg-gradient-to-br from-amber-900/40 to-amber-900/10 rounded-lg p-4 backdrop-blur-sm border border-amber-900/30"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.2 }}
    >
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-sm font-medium text-gray-400">Alertas</h3>
        <span className="bg-amber-500/20 text-amber-500 rounded-full w-8 h-8 flex items-center justify-center">
          <Bell className="h-4 w-4" />
        </span>
      </div>
      <p className="text-2xl font-bold text-white">2</p>
      <p className="text-xs text-amber-400 mt-1">-1 nas últimas 24h</p>
    </motion.div>
    
    <motion.div 
      className="bg-gradient-to-br from-blue-900/40 to-blue-900/10 rounded-lg p-4 backdrop-blur-sm border border-blue-900/30"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.3 }}
    >
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-sm font-medium text-gray-400">Informações</h3>
        <span className="bg-blue-500/20 text-blue-500 rounded-full w-8 h-8 flex items-center justify-center">
          <AlertCircle className="h-4 w-4" />
        </span>
      </div>
      <p className="text-2xl font-bold text-white">1</p>
      <p className="text-xs text-blue-400 mt-1">0 nas últimas 24h</p>
    </motion.div>
    
    <motion.div 
      className="bg-gradient-to-br from-green-900/40 to-green-900/10 rounded-lg p-4 backdrop-blur-sm border border-green-900/30"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.4 }}
    >
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-sm font-medium text-gray-400">Resolvidos</h3>
        <span className="bg-green-500/20 text-green-500 rounded-full w-8 h-8 flex items-center justify-center">
          <CheckCircle className="h-4 w-4" />
        </span>
      </div>
      <p className="text-2xl font-bold text-white">12</p>
      <p className="text-xs text-green-400 mt-1">+3 nas últimas 24h</p>
    </motion.div>
  </div>
);

export default function AlertsPage() {
  const [alertsEnabled, setAlertsEnabled] = useState(true);
  const [soundsEnabled, setSoundsEnabled] = useState(false);
  const [summaryEnabled, setSummaryEnabled] = useState(true);

  return (
    <MainLayout>
      <div className="space-y-6">
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
            <Bell className="h-8 w-8 text-amber-500" />
            <span>Alertas</span>
          </h1>
          <p className="text-gray-400">
            Visualize e gerencie alertas da sua infraestrutura
          </p>
        </motion.div>
        
        <AlertStats />
        <AlertFilter />
        
        <div className="space-y-3">
          {mockAlerts.map(alert => (
            <AlertCard key={alert.id} alert={alert} />
          ))}
        </div>

        <div className="flex justify-between items-center text-sm text-gray-500 mt-6">
          <div>Mostrando 1-6 de 18 alertas</div>
          <div className="flex gap-2">
            <button className="px-4 py-2 bg-gray-800/70 hover:bg-gray-700/70 rounded-md disabled:opacity-50 disabled:cursor-not-allowed" disabled>
              Anterior
            </button>
            <button className="px-4 py-2 bg-gray-800/70 hover:bg-gray-700/70 rounded-md">
              Próximo
            </button>
          </div>
        </div>

        {/* Notificações */}
        <motion.div 
          className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50 overflow-hidden"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.4 }}
        >
          <div className="p-5 border-b border-gray-700/50">
            <h2 className="text-xl font-semibold text-white flex items-center gap-2">
              <Bell className="h-5 w-5 text-amber-400" />
              Notificações
            </h2>
          </div>
          <div className="p-5 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Alertas no navegador</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input 
                  type="checkbox" 
                  className="sr-only peer" 
                  checked={alertsEnabled}
                  onChange={e => setAlertsEnabled(e.target.checked)}
                />
                <div className="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
              </label>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Sons</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input 
                  type="checkbox" 
                  className="sr-only peer"
                  checked={soundsEnabled}
                  onChange={e => setSoundsEnabled(e.target.checked)}
                />
                <div className="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
              </label>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Resumo diário</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input 
                  type="checkbox" 
                  className="sr-only peer" 
                  checked={summaryEnabled}
                  onChange={e => setSummaryEnabled(e.target.checked)}
                />
                <div className="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
              </label>
            </div>
          </div>
        </motion.div>
      </div>
    </MainLayout>
  );
} 