"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import ChatInterface from "@/components/ChatInterface";
import { sendChatMessage } from "@/lib/api";

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<any[]>([]);
  const [mounted, setMounted] = useState(false);

  // Inicializar com mensagem de boas-vindas
  useEffect(() => {
    setMounted(true);
    setMessages([
      {
        role: "assistant",
        content: "Olá, sou o Zabbia, seu copiloto de infraestrutura. Como posso ajudar você hoje? Você pode me perguntar sobre hosts, métricas, alertas, ou usar comandos especiais como `/generate-sql`, `/call-api`, `/graph`, ou `/recommend`."
      }
    ]);
  }, []);

  const chatMutation = useMutation({
    mutationFn: (newMessage: string) => {
      const allMessages = [
        ...messages,
        { role: "user", content: newMessage }
      ];
      return sendChatMessage(allMessages);
    },
    onSuccess: (data) => {
      // Adicionar resposta do assistente
      setMessages(prevMessages => [
        ...prevMessages,
        { role: "assistant", content: data.response }
      ]);
    },
  });

  // Função para enviar mensagem
  const handleSendMessage = (message: string) => {
    // Adicionar mensagem do usuário
    setMessages(prevMessages => [
      ...prevMessages,
      { role: "user", content: message }
    ]);

    // Enviar para API
    chatMutation.mutate(message);
  };

  // Mostrar estado de carregamento inicial
  if (!mounted) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="flex flex-col space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="heading-responsive font-bold">Chat</h1>
      </div>

      <Card className="flex-1 overflow-hidden">
        <CardHeader>
          <CardTitle>Zabbia - Copiloto de Infraestrutura</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ChatInterface 
            messages={messages} 
            onSendMessage={handleSendMessage} 
            isLoading={chatMutation.isPending}
          />
        </CardContent>
      </Card>
    </div>
  );
} 