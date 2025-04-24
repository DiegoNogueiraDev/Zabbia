"use client";

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Home, 
  MessageSquare, 
  BarChart3, 
  Bell, 
  Settings, 
  Zap
} from 'lucide-react';

type NavItemProps = {
  href: string;
  icon: React.ReactNode;
  label: string;
  isActive?: boolean;
}

const NavItem = ({ href, icon, label, isActive }: NavItemProps) => {
  return (
    <Link href={href} className="block">
      <motion.div
        className={`
          flex items-center gap-3 px-4 py-3 rounded-xl mb-1
          transition-all duration-200 relative overflow-hidden group
          ${isActive 
            ? 'text-white font-medium' 
            : 'text-gray-400 hover:text-gray-200'}
        `}
        whileHover={{ x: 4 }}
        whileTap={{ scale: 0.98 }}
      >
        {/* Gradient background for active item */}
        {isActive && (
          <motion.div 
            className="absolute inset-0 bg-gradient-to-r from-emerald-600/80 to-cyan-600/80 rounded-xl -z-10"
            layoutId="activeNavBackground"
            transition={{ type: "spring", duration: 0.6 }}
          />
        )}
        
        {/* Hover effect for inactive items */}
        {!isActive && (
          <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 rounded-xl -z-10 transition-opacity duration-200" />
        )}
        
        <div className={`${isActive ? 'text-white' : 'text-gray-400 group-hover:text-gray-200'}`}>
          {icon}
        </div>
        <span>{label}</span>
      </motion.div>
    </Link>
  );
};

export default function Sidebar() {
  const pathname = usePathname();
  const [isOnline, setIsOnline] = useState(true);
  
  const mainNavItems = [
    { href: '/', icon: <Home size={20} />, label: 'Início' },
    { href: '/chat', icon: <MessageSquare size={20} />, label: 'Chat' },
  ];
  
  const monitoringNavItems = [
    { href: '/dashboard', icon: <BarChart3 size={20} />, label: 'Dashboard' },
    { href: '/alerts', icon: <Bell size={20} />, label: 'Alertas' },
    { href: '/settings', icon: <Settings size={20} />, label: 'Configurações' },
  ];

  return (
    <div className="fixed inset-y-0 left-0 w-64 bg-gray-900/70 backdrop-blur-xl border-r border-gray-800/50 z-30">
      <div className="flex flex-col h-full">
        {/* Logo and header */}
        <div className="p-6 border-b border-gray-800/50">
          <div className="flex items-center gap-3">
            <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500 text-white overflow-hidden">
              <Zap size={20} className="relative z-10 text-white" />
              <div className="absolute inset-0 opacity-20 bg-[url('/noise.png')]" />
            </div>
            
            <div>
              <h1 className="text-xl font-semibold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                Zabbia
              </h1>
              <p className="text-xs text-gray-500">v1.0.0</p>
            </div>
          </div>
        </div>
        
        {/* Navigation menu */}
        <div className="flex-1 px-4 py-6 space-y-8 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-800 scrollbar-track-transparent">
          {/* Principal section */}
          <div>
            <h2 className="px-4 mb-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
              Principal
            </h2>
            <nav>
              {mainNavItems.map((item) => (
                <NavItem
                  key={item.href}
                  href={item.href}
                  icon={item.icon}
                  label={item.label}
                  isActive={pathname === item.href}
                />
              ))}
            </nav>
          </div>
          
          {/* Monitoring section */}
          <div>
            <h2 className="px-4 mb-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
              Monitoramento
            </h2>
            <nav>
              {monitoringNavItems.map((item) => (
                <NavItem
                  key={item.href}
                  href={item.href}
                  icon={item.icon}
                  label={item.label}
                  isActive={pathname === item.href}
                />
              ))}
            </nav>
          </div>
        </div>
        
        {/* Status section */}
        <div className="p-4 border-t border-gray-800/50">
          <div className="flex items-center px-4 py-3 rounded-xl bg-gray-800/50">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-300">Status</p>
              <p className="text-xs text-gray-500">Sistema {isOnline ? 'online' : 'offline'}</p>
            </div>
            <div className="relative">
              {isOnline ? (
                <div className="relative">
                  <div className="w-3 h-3 bg-emerald-500 rounded-full" />
                  <AnimatePresence>
                    <motion.div
                      key="pulse"
                      initial={{ scale: 1, opacity: 0.8 }}
                      animate={{ 
                        scale: [1, 1.8, 1], 
                        opacity: [0.8, 0, 0.8] 
                      }}
                      transition={{ 
                        duration: 2,
                        repeat: Infinity,
                        repeatType: "loop"
                      }}
                      className="absolute inset-0 bg-emerald-500 rounded-full"
                    />
                  </AnimatePresence>
                </div>
              ) : (
                <div className="w-3 h-3 bg-gray-500 rounded-full" />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 