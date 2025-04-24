"use client";

import React from 'react';
import { motion } from 'framer-motion';
import Sidebar from './Sidebar';

type MainLayoutProps = {
  children: React.ReactNode;
}

export default function MainLayout({ children }: MainLayoutProps) {
  const variants = {
    hidden: { opacity: 0 },
    enter: { opacity: 1 },
    exit: { opacity: 0 },
  };

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 overflow-hidden">
      {/* Noise texture overlay */}
      <div 
        className="absolute inset-0 opacity-25 mix-blend-overlay"
        style={{ 
          backgroundImage: "url('/noise.png')",
          backgroundRepeat: 'repeat',
        }}
      />
      
      {/* Gradient accents */}
      <div className="absolute -top-64 -left-64 w-96 h-96 bg-emerald-900/30 rounded-full blur-3xl"/>
      <div className="absolute -bottom-64 -right-64 w-96 h-96 bg-cyan-900/20 rounded-full blur-3xl"/>
      <div className="absolute top-1/4 right-0 w-64 h-64 bg-rose-900/10 rounded-full blur-3xl"/>
      
      <Sidebar />
      
      <motion.main
        variants={variants}
        initial="hidden"
        animate="enter"
        exit="exit"
        transition={{ duration: 0.4 }}
        className="ml-64 p-8 min-h-screen relative"
      >
        {children}
      </motion.main>
    </div>
  );
} 