"use client";

import React from 'react';
import MainLayout from '@/components/layout/MainLayout';
import ChatInterface from '@/components/dashboard/ChatInterface';

export default function ChatPage() {
  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-2">Chat com Zabbia</h1>
          <p className="text-gray-500 dark:text-gray-400">
            Consulte informações do Zabbix através de conversas em linguagem natural
          </p>
        </div>

        <div className="max-w-4xl mx-auto">
          <ChatInterface />
        </div>
      </div>
    </MainLayout>
  );
} 