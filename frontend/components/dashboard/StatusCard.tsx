"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';

interface StatusCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: LucideIcon;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple' | 'cyan' | 'emerald' | 'amber' | 'fuchsia';
}

export default function StatusCard({ 
  title, 
  value, 
  description, 
  icon: Icon, 
  trend, 
  trendValue,
  color = 'blue'
}: StatusCardProps) {
  // Gradientes modernos para fundos e bordas dos cards
  const gradients = {
    blue: 'bg-gradient-to-br from-blue-900/20 to-blue-800/5 border-blue-700/30',
    green: 'bg-gradient-to-br from-green-900/20 to-green-800/5 border-green-700/30',
    yellow: 'bg-gradient-to-br from-yellow-900/20 to-yellow-800/5 border-yellow-700/30',
    red: 'bg-gradient-to-br from-red-900/20 to-red-800/5 border-red-700/30',
    purple: 'bg-gradient-to-br from-purple-900/20 to-purple-800/5 border-purple-700/30',
    cyan: 'bg-gradient-to-br from-cyan-900/20 to-cyan-800/5 border-cyan-700/30',
    emerald: 'bg-gradient-to-br from-emerald-900/20 to-emerald-800/5 border-emerald-700/30',
    amber: 'bg-gradient-to-br from-amber-900/20 to-amber-800/5 border-amber-700/30',
    fuchsia: 'bg-gradient-to-br from-fuchsia-900/20 to-fuchsia-800/5 border-fuchsia-700/30',
  };

  // Cores para ícones
  const iconColors = {
    blue: 'text-blue-500',
    green: 'text-green-500',
    yellow: 'text-yellow-500',
    red: 'text-red-500',
    purple: 'text-purple-500',
    cyan: 'text-cyan-500',
    emerald: 'text-emerald-500',
    amber: 'text-amber-500',
    fuchsia: 'text-fuchsia-500',
  };

  // Cores para valores de tendência
  const trendColors = {
    up: 'text-green-500',
    down: 'text-red-500',
    neutral: 'text-gray-500',
  };

  // Ícones de tendência
  const trendIcons = {
    up: '↑',
    down: '↓',
    neutral: '→'
  };

  // Gradientes de texto
  const textGradients = {
    blue: 'bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent',
    green: 'bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent',
    yellow: 'bg-gradient-to-r from-yellow-400 to-amber-400 bg-clip-text text-transparent',
    red: 'bg-gradient-to-r from-red-400 to-rose-400 bg-clip-text text-transparent',
    purple: 'bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent',
    cyan: 'bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent',
    emerald: 'bg-gradient-to-r from-emerald-400 to-green-400 bg-clip-text text-transparent',
    amber: 'bg-gradient-to-r from-amber-400 to-yellow-400 bg-clip-text text-transparent',
    fuchsia: 'bg-gradient-to-r from-fuchsia-400 to-pink-400 bg-clip-text text-transparent',
  };

  return (
    <motion.div 
      className={`backdrop-blur-sm rounded-xl border overflow-hidden ${gradients[color]}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      whileHover={{ translateY: -5 }}
    >
      <div className="p-6">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-sm font-medium text-gray-400">{title}</h3>
            <div className="mt-2 flex items-baseline">
              <p className={`text-2xl font-bold ${textGradients[color]}`}>
                {value}
              </p>
              {trendValue && trend && (
                <p className={`ml-2 text-sm font-medium ${trendColors[trend]}`}>
                  {trendIcons[trend]} {trendValue}
                </p>
              )}
            </div>
            {description && (
              <p className="mt-1 text-xs text-gray-500">{description}</p>
            )}
          </div>
          {Icon && (
            <div className={`p-3 rounded-xl ${iconColors[color]} bg-gray-800/50`}>
              <Icon className="h-5 w-5" />
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
} 