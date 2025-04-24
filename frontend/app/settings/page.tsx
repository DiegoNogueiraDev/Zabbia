"use client";

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Settings, Moon, Sun, Globe, Shield, Zap, Bell, Save } from 'lucide-react';
import MainLayout from '@/components/layout/MainLayout';

export default function SettingsPage() {
  const [verifySSL, setVerifySSL] = useState(false);
  const [useCache, setUseCache] = useState(true);
  const [browserAlerts, setBrowserAlerts] = useState(true);
  const [soundAlerts, setSoundAlerts] = useState(false);
  const [dailySummary, setDailySummary] = useState(true);

  const fadeIn = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.4 }
  };

  return (
    <MainLayout>
      <div className="space-y-8">
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
            <Settings className="h-8 w-8 text-emerald-500" />
            <span>Configurações</span>
          </h1>
          <p className="text-gray-400">
            Personalize sua experiência no Zabbia
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Aparência */}
          <motion.div 
            className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50 overflow-hidden"
            {...fadeIn}
            transition={{ delay: 0.1, duration: 0.4 }}
          >
            <div className="p-5 border-b border-gray-700/50">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <Moon className="h-5 w-5 text-blue-400" />
                Aparência
              </h2>
            </div>
            <div className="p-5 space-y-6">
              <div>
                <label className="flex items-center justify-between mb-2">
                  <span className="text-gray-300">Tema</span>
                  <select className="bg-gray-700 text-white rounded-md px-3 py-1.5 border border-gray-600">
                    <option>Escuro</option>
                    <option>Claro</option>
                    <option>Sistema</option>
                  </select>
                </label>
              </div>
              
              <div>
                <label className="flex items-center justify-between mb-2">
                  <span className="text-gray-300">Cor de destaque</span>
                  <div className="flex gap-2">
                    <button className="w-6 h-6 rounded-full bg-emerald-500 ring-2 ring-emerald-500/30"></button>
                    <button className="w-6 h-6 rounded-full bg-blue-500"></button>
                    <button className="w-6 h-6 rounded-full bg-purple-500"></button>
                    <button className="w-6 h-6 rounded-full bg-rose-500"></button>
                  </div>
                </label>
              </div>
            </div>
          </motion.div>

          {/* Conexão */}
          <motion.div 
            className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50 overflow-hidden"
            {...fadeIn}
            transition={{ delay: 0.2, duration: 0.4 }}
          >
            <div className="p-5 border-b border-gray-700/50">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <Globe className="h-5 w-5 text-emerald-400" />
                Conexão
              </h2>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block mb-2">
                  <span className="text-gray-300 block mb-1">URL do Servidor Zabbix</span>
                  <input type="text" 
                    className="w-full bg-gray-700 text-white rounded-md px-3 py-2 border border-gray-600" 
                    placeholder="https://zabbix.exemplo.com/"
                  />
                </label>
              </div>
              
              <div className="flex items-center text-gray-300 space-x-4">
                <div className="flex items-center">
                  <input 
                    type="checkbox" 
                    id="ssl" 
                    className="mr-2" 
                    checked={verifySSL}
                    onChange={e => setVerifySSL(e.target.checked)}
                  />
                  <label htmlFor="ssl">Verificar SSL</label>
                </div>
                <div className="flex items-center">
                  <input 
                    type="checkbox" 
                    id="cache" 
                    className="mr-2"
                    checked={useCache}
                    onChange={e => setUseCache(e.target.checked)}
                  />
                  <label htmlFor="cache">Cache local</label>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Notificações */}
          <motion.div 
            className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50 overflow-hidden"
            {...fadeIn}
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
                    checked={browserAlerts}
                    onChange={e => setBrowserAlerts(e.target.checked)}
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
                    checked={soundAlerts}
                    onChange={e => setSoundAlerts(e.target.checked)}
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
                    checked={dailySummary}
                    onChange={e => setDailySummary(e.target.checked)}
                  />
                  <div className="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
                </label>
              </div>
            </div>
          </motion.div>

          {/* API */}
          <motion.div 
            className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50 overflow-hidden"
            {...fadeIn}
            transition={{ delay: 0.4, duration: 0.4 }}
          >
            <div className="p-5 border-b border-gray-700/50">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <Shield className="h-5 w-5 text-purple-400" />
                API
              </h2>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block mb-2">
                  <span className="text-gray-300 block mb-1">Chave da API</span>
                  <input type="password" 
                    className="w-full bg-gray-700 text-white rounded-md px-3 py-2 border border-gray-600" 
                    value="••••••••••••••••••••••••"
                  />
                </label>
              </div>
              
              <div>
                <span className="text-amber-400 text-sm">Esta chave expira em 45 dias</span>
              </div>
              
              <div>
                <button className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-md flex items-center gap-2 text-sm">
                  <Zap className="h-4 w-4" />
                  Gerar nova chave
                </button>
              </div>
            </div>
          </motion.div>
        </div>

        <motion.div 
          className="flex justify-end"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6, duration: 0.4 }}
        >
          <button className="px-6 py-2.5 bg-gradient-to-r from-emerald-600 to-cyan-600 text-white rounded-md font-medium flex items-center gap-2 hover:from-emerald-500 hover:to-cyan-500 transition-all">
            <Save className="h-4 w-4" />
            Salvar alterações
          </button>
        </motion.div>
      </div>
    </MainLayout>
  );
} 