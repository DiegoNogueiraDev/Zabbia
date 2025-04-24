"use client";

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, ArrowDownRight, ArrowUpRight, Cpu, HardDrive, Clock, RefreshCw, ListFilter } from 'lucide-react';
import { MemoryStick as Memory } from 'lucide-react';
import MainLayout from '@/components/layout/MainLayout';

export default function MetricsPage() {
  const [showFilters, setShowFilters] = useState(false);
  const [selectedHosts, setSelectedHosts] = useState<string[]>(["web01", "web02", "db01"]);

  const toggleHost = (hostname: string) => {
    if (selectedHosts.includes(hostname)) {
      setSelectedHosts(selectedHosts.filter(h => h !== hostname));
    } else {
      setSelectedHosts([...selectedHosts, hostname]);
    }
  };

  const fadeIn = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.4 }
  };

  return (
    <MainLayout>
      <div className="space-y-8">
        {/* Cabeçalho com animação */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="flex justify-between items-center flex-wrap gap-4 mb-2">
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <BarChart3 className="h-8 w-8 text-blue-500" />
              <span>Métricas</span>
            </h1>
            
            <div className="flex items-center gap-4">
              <motion.button 
                className="px-3.5 py-2 bg-gray-800/60 hover:bg-gray-700/80 text-white rounded-md flex items-center gap-2 text-sm border border-gray-700/50"
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => setShowFilters(!showFilters)}
              >
                <ListFilter className="h-4 w-4" />
                Filtros
              </motion.button>
              
              <motion.button 
                className="px-3.5 py-2 bg-gray-800/60 hover:bg-gray-700/80 text-white rounded-md flex items-center gap-2 text-sm border border-gray-700/50"
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
              >
                <RefreshCw className="h-4 w-4" />
                Atualizar
              </motion.button>
            </div>
          </div>
          
          <p className="text-gray-400">
            Visualize e analise o desempenho da sua infraestrutura em tempo real
          </p>
        </motion.div>
        
        {/* Filtros */}
        {showFilters && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50 p-4"
          >
            <div className="mb-3">
              <h3 className="text-white font-medium mb-2">Servidores</h3>
              <div className="flex flex-wrap gap-3">
                {["web01", "web02", "db01", "app01", "cache01"].map(host => (
                  <label key={host} className="flex items-center bg-gray-700/60 rounded-lg px-3 py-1.5">
                    <input 
                      type="checkbox" 
                      className="mr-2" 
                      checked={selectedHosts.includes(host)}
                      onChange={() => toggleHost(host)}
                    />
                    <span className="text-gray-200">{host}</span>
                  </label>
                ))}
              </div>
            </div>
            
            <div className="flex flex-wrap gap-4">
              <div>
                <h3 className="text-white font-medium mb-2">Período</h3>
                <select className="bg-gray-700 text-white rounded-md px-3 py-1.5 border border-gray-600">
                  <option>Última hora</option>
                  <option>Último dia</option>
                  <option>Última semana</option>
                  <option>Personalizado</option>
                </select>
              </div>
              
              <div>
                <h3 className="text-white font-medium mb-2">Métricas</h3>
                <select className="bg-gray-700 text-white rounded-md px-3 py-1.5 border border-gray-600">
                  <option>Todas</option>
                  <option>CPU</option>
                  <option>Memória</option>
                  <option>Disco</option>
                  <option>Rede</option>
                </select>
              </div>
            </div>
          </motion.div>
        )}

        {/* Painéis de Gráficos */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* CPU Utilization */}
          <motion.div 
            className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50 overflow-hidden"
            {...fadeIn}
            transition={{ delay: 0.1, duration: 0.4 }}
          >
            <div className="p-5 border-b border-gray-700/50 flex justify-between items-center">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <Cpu className="h-5 w-5 text-rose-400" />
                CPU
              </h2>
              <div className="text-gray-300 text-sm flex items-center gap-1.5">
                <Clock className="h-4 w-4" />
                Atualizado há 2 min
              </div>
            </div>
            
            <div className="p-5">
              {/* Placeholder para gráfico */}
              <div className="h-60 flex items-center justify-center bg-gray-700/20 rounded-lg border border-gray-700/30">
                <div className="text-center">
                  <p className="text-gray-400 mb-2">Gráfico de utilização de CPU</p>
                  <div className="flex space-x-3 justify-center text-sm">
                    <div className="flex items-center gap-1">
                      <span className="h-3 w-3 rounded-full bg-blue-500"></span>
                      <span className="text-gray-300">web01</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="h-3 w-3 rounded-full bg-green-500"></span>
                      <span className="text-gray-300">web02</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="h-3 w-3 rounded-full bg-purple-500"></span>
                      <span className="text-gray-300">db01</span>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Métricas */}
              <div className="grid grid-cols-3 gap-4 mt-4">
                <div className="bg-gray-700/30 p-3 rounded-lg">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-400 text-sm">web01</span>
                    <div className="flex items-center text-green-400 text-xs">
                      <ArrowDownRight className="h-3.5 w-3.5" />
                      <span>3%</span>
                    </div>
                  </div>
                  <div className="text-white text-xl font-semibold">23%</div>
                </div>
                
                <div className="bg-gray-700/30 p-3 rounded-lg">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-400 text-sm">web02</span>
                    <div className="flex items-center text-red-400 text-xs">
                      <ArrowUpRight className="h-3.5 w-3.5" />
                      <span>8%</span>
                    </div>
                  </div>
                  <div className="text-white text-xl font-semibold">67%</div>
                </div>
                
                <div className="bg-gray-700/30 p-3 rounded-lg">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-400 text-sm">db01</span>
                    <div className="flex items-center text-green-400 text-xs">
                      <ArrowDownRight className="h-3.5 w-3.5" />
                      <span>5%</span>
                    </div>
                  </div>
                  <div className="text-white text-xl font-semibold">42%</div>
                </div>
              </div>
            </div>
          </motion.div>
          
          {/* Memory */}
          <motion.div 
            className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50 overflow-hidden"
            {...fadeIn}
            transition={{ delay: 0.2, duration: 0.4 }}
          >
            <div className="p-5 border-b border-gray-700/50 flex justify-between items-center">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <Memory className="h-5 w-5 text-blue-400" />
                Memória
              </h2>
              <div className="text-gray-300 text-sm flex items-center gap-1.5">
                <Clock className="h-4 w-4" />
                Atualizado há 2 min
              </div>
            </div>
            
            <div className="p-5">
              {/* Placeholder para gráfico */}
              <div className="h-60 flex items-center justify-center bg-gray-700/20 rounded-lg border border-gray-700/30">
                <div className="text-center">
                  <p className="text-gray-400 mb-2">Gráfico de utilização de memória</p>
                  <div className="flex space-x-3 justify-center text-sm">
                    <div className="flex items-center gap-1">
                      <span className="h-3 w-3 rounded-full bg-blue-500"></span>
                      <span className="text-gray-300">web01</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="h-3 w-3 rounded-full bg-green-500"></span>
                      <span className="text-gray-300">web02</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="h-3 w-3 rounded-full bg-purple-500"></span>
                      <span className="text-gray-300">db01</span>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Métricas */}
              <div className="grid grid-cols-3 gap-4 mt-4">
                <div className="bg-gray-700/30 p-3 rounded-lg">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-400 text-sm">web01</span>
                    <div className="flex items-center text-red-400 text-xs">
                      <ArrowUpRight className="h-3.5 w-3.5" />
                      <span>2%</span>
                    </div>
                  </div>
                  <div className="text-white text-xl font-semibold">3.4 GB</div>
                </div>
                
                <div className="bg-gray-700/30 p-3 rounded-lg">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-400 text-sm">web02</span>
                    <div className="flex items-center text-red-400 text-xs">
                      <ArrowUpRight className="h-3.5 w-3.5" />
                      <span>5%</span>
                    </div>
                  </div>
                  <div className="text-white text-xl font-semibold">5.2 GB</div>
                </div>
                
                <div className="bg-gray-700/30 p-3 rounded-lg">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-400 text-sm">db01</span>
                    <div className="flex items-center text-green-400 text-xs">
                      <ArrowDownRight className="h-3.5 w-3.5" />
                      <span>1%</span>
                    </div>
                  </div>
                  <div className="text-white text-xl font-semibold">14.8 GB</div>
                </div>
              </div>
            </div>
          </motion.div>
          
          {/* Disk */}
          <motion.div 
            className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50 overflow-hidden"
            {...fadeIn}
            transition={{ delay: 0.3, duration: 0.4 }}
          >
            <div className="p-5 border-b border-gray-700/50 flex justify-between items-center">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <HardDrive className="h-5 w-5 text-amber-400" />
                Disco
              </h2>
              <div className="text-gray-300 text-sm flex items-center gap-1.5">
                <Clock className="h-4 w-4" />
                Atualizado há 3 min
              </div>
            </div>
            
            <div className="p-5">
              {/* Placeholder para gráfico */}
              <div className="h-60 flex items-center justify-center bg-gray-700/20 rounded-lg border border-gray-700/30">
                <div className="text-center">
                  <p className="text-gray-400 mb-2">Gráfico de utilização de disco</p>
                  <div className="flex space-x-3 justify-center text-sm">
                    <div className="flex items-center gap-1">
                      <span className="h-3 w-3 rounded-full bg-blue-500"></span>
                      <span className="text-gray-300">web01</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="h-3 w-3 rounded-full bg-green-500"></span>
                      <span className="text-gray-300">web02</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="h-3 w-3 rounded-full bg-purple-500"></span>
                      <span className="text-gray-300">db01</span>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Métricas */}
              <div className="grid grid-cols-3 gap-4 mt-4">
                <div className="bg-gray-700/30 p-3 rounded-lg">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-400 text-sm">web01</span>
                    <span className="text-gray-300 text-xs">100GB</span>
                  </div>
                  <div className="text-white text-xl font-semibold">48%</div>
                  <div className="w-full bg-gray-600 rounded-full h-2 mt-2">
                    <div className="bg-blue-500 h-2 rounded-full" style={{ width: '48%' }}></div>
                  </div>
                </div>
                
                <div className="bg-gray-700/30 p-3 rounded-lg">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-400 text-sm">web02</span>
                    <span className="text-gray-300 text-xs">100GB</span>
                  </div>
                  <div className="text-white text-xl font-semibold">53%</div>
                  <div className="w-full bg-gray-600 rounded-full h-2 mt-2">
                    <div className="bg-green-500 h-2 rounded-full" style={{ width: '53%' }}></div>
                  </div>
                </div>
                
                <div className="bg-gray-700/30 p-3 rounded-lg">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-400 text-sm">db01</span>
                    <span className="text-gray-300 text-xs">2TB</span>
                  </div>
                  <div className="text-white text-xl font-semibold">72%</div>
                  <div className="w-full bg-gray-600 rounded-full h-2 mt-2">
                    <div className="bg-amber-500 h-2 rounded-full" style={{ width: '72%' }}></div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
          
          {/* Network */}
          <motion.div 
            className="bg-gray-800/50 backdrop-blur-sm rounded-xl border border-gray-700/50 overflow-hidden"
            {...fadeIn}
            transition={{ delay: 0.4, duration: 0.4 }}
          >
            <div className="p-5 border-b border-gray-700/50 flex justify-between items-center">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-purple-400">
                  <path d="M6 12H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
                  <path d="M6 8h12"></path>
                  <path d="M18.3 17.7 12 11.4l-6.3 6.3a2 2 0 0 0 0 2.8 2 2 0 0 0 2.8 0l3.5-3.5 3.5 3.5a2 2 0 0 0 2.8 0 2 2 0 0 0 0-2.8Z"></path>
                </svg>
                Rede
              </h2>
              <div className="text-gray-300 text-sm flex items-center gap-1.5">
                <Clock className="h-4 w-4" />
                Atualizado há 1 min
              </div>
            </div>
            
            <div className="p-5">
              {/* Placeholder para gráfico */}
              <div className="h-60 flex items-center justify-center bg-gray-700/20 rounded-lg border border-gray-700/30">
                <div className="text-center">
                  <p className="text-gray-400 mb-2">Gráfico de utilização de rede</p>
                  <div className="flex space-x-3 justify-center text-sm">
                    <div className="flex items-center gap-1">
                      <span className="h-3 w-3 rounded-full bg-blue-500"></span>
                      <span className="text-gray-300">web01</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="h-3 w-3 rounded-full bg-green-500"></span>
                      <span className="text-gray-300">web02</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="h-3 w-3 rounded-full bg-purple-500"></span>
                      <span className="text-gray-300">db01</span>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Métricas */}
              <div className="grid grid-cols-3 gap-4 mt-4">
                <div className="bg-gray-700/30 p-3 rounded-lg">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-400 text-sm">web01</span>
                  </div>
                  <div className="text-white flex justify-between mt-1">
                    <div>
                      <span className="text-xs text-gray-400">▼</span>
                      <span>2.4 MB/s</span>
                    </div>
                    <div>
                      <span className="text-xs text-gray-400">▲</span>
                      <span>0.8 MB/s</span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-700/30 p-3 rounded-lg">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-400 text-sm">web02</span>
                  </div>
                  <div className="text-white flex justify-between mt-1">
                    <div>
                      <span className="text-xs text-gray-400">▼</span>
                      <span>3.6 MB/s</span>
                    </div>
                    <div>
                      <span className="text-xs text-gray-400">▲</span>
                      <span>1.2 MB/s</span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-700/30 p-3 rounded-lg">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-gray-400 text-sm">db01</span>
                  </div>
                  <div className="text-white flex justify-between mt-1">
                    <div>
                      <span className="text-xs text-gray-400">▼</span>
                      <span>0.5 MB/s</span>
                    </div>
                    <div>
                      <span className="text-xs text-gray-400">▲</span>
                      <span>0.3 MB/s</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </MainLayout>
  );
} 