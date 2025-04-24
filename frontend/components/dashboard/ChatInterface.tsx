"use client";

import React, { useState } from 'react';
import { Send, Bot, User } from 'lucide-react';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Olá! Sou o Zabbia, seu assistente de infraestrutura para Zabbix. Como posso ajudar você hoje?',
      sender: 'bot',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      text: input,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // Simulate API call - in real app, replace with actual API call
    setTimeout(() => {
      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: getSimulatedResponse(input),
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botResponse]);
      setIsLoading(false);
    }, 1000);
  };

  const getSimulatedResponse = (query: string): string => {
    if (query.toLowerCase().includes('cpu')) {
      return 'Encontrei 3 hosts com CPU acima de 80%: web01 (92%), web02 (88%), db01 (85%).';
    } else if (query.toLowerCase().includes('memória') || query.toLowerCase().includes('memoria')) {
      return 'O uso de memória nos servidores está estável. Nenhum alerta de memória no momento.';
    } else if (query.toLowerCase().includes('alerta') || query.toLowerCase().includes('problema')) {
      return 'Temos 2 alertas ativos: Disco cheio no servidor db02 (95%) e Serviço HTTP indisponível no web03.';
    } else {
      return 'Para consultar informações do Zabbix, tente perguntar sobre CPU, memória, disco, alertas ou status de hosts específicos.';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-[80vh] border border-gray-200 rounded-lg shadow-sm bg-white dark:bg-gray-800 dark:border-gray-700">
      <div className="p-4 border-b dark:border-gray-700">
        <h2 className="text-lg font-semibold">Chat com Zabbia</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Pergunte sobre hosts, serviços, métricas ou problemas
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`
                max-w-[80%] rounded-lg p-3 
                ${
                  message.sender === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 dark:text-white'
                }
              `}
            >
              <div className="flex items-center space-x-2 mb-1">
                {message.sender === 'bot' ? (
                  <Bot className="h-4 w-4" />
                ) : (
                  <User className="h-4 w-4" />
                )}
                <p className="text-xs opacity-70">
                  {message.sender === 'user' ? 'Você' : 'Zabbia'} • {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
              <p>{message.text}</p>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-3 max-w-[80%]">
              <div className="flex items-center space-x-2">
                <Bot className="h-4 w-4" />
                <p className="text-xs opacity-70">Zabbia está digitando...</p>
              </div>
              <div className="flex space-x-1 mt-2">
                <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="p-4 border-t dark:border-gray-700">
        <div className="flex items-center space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Pergunte sobre seus hosts Zabbix..."
            className="flex-1 p-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          />
          <button
            onClick={handleSendMessage}
            disabled={!input.trim() || isLoading}
            className="p-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          Experimente: "Quais hosts estão com CPU acima de 80%?" ou "Mostre os alertas ativos"
        </p>
      </div>
    </div>
  );
} 