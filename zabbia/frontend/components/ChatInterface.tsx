"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import ReactMarkdown from "react-markdown";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export default function ChatInterface({ 
  messages, 
  onSendMessage, 
  isLoading 
}: ChatInterfaceProps) {
  const [input, setInput] = useState("");
  const endOfMessagesRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll para a última mensagem
  useEffect(() => {
    if (endOfMessagesRef.current) {
      endOfMessagesRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // Ajuste automático da altura do textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  }, [input]);

  const handleSendMessage = () => {
    if (input.trim() && !isLoading) {
      onSendMessage(input);
      setInput("");
      
      // Resetar a altura do textarea
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-[calc(80vh-160px)]">
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`rounded-lg px-4 py-2 max-w-[85%] ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground ml-4"
                    : "bg-muted mr-4"
                }`}
              >
                {msg.role === "assistant" ? (
                  <ReactMarkdown
                    className="prose dark:prose-invert prose-sm max-w-none"
                    components={{
                      pre: ({ node, ...props }) => (
                        <div className="bg-black/10 dark:bg-white/10 p-2 rounded-md my-2 overflow-auto">
                          <pre {...props} />
                        </div>
                      ),
                      code: ({ node, ...props }) => (
                        <code className="bg-black/10 dark:bg-white/10 p-1 rounded" {...props} />
                      ),
                      ul: ({ node, ...props }) => (
                        <ul className="list-disc pl-4 my-2" {...props} />
                      ),
                      ol: ({ node, ...props }) => (
                        <ol className="list-decimal pl-4 my-2" {...props} />
                      ),
                      table: ({ node, ...props }) => (
                        <div className="overflow-x-auto my-4">
                          <table className="border-collapse border border-gray-300 dark:border-gray-700" {...props} />
                        </div>
                      ),
                      th: ({ node, ...props }) => (
                        <th className="border border-gray-300 dark:border-gray-700 px-4 py-2 bg-gray-100 dark:bg-gray-800" {...props} />
                      ),
                      td: ({ node, ...props }) => (
                        <td className="border border-gray-300 dark:border-gray-700 px-4 py-2" {...props} />
                      ),
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                ) : (
                  <p>{msg.content}</p>
                )}
              </div>
            </div>
          ))}
          <div ref={endOfMessagesRef} />
        </div>
      </ScrollArea>

      <div className="border-t p-4">
        <div className="flex space-x-2">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Digite sua mensagem..."
            className="min-h-[40px] max-h-[150px] resize-none"
            disabled={isLoading}
          />
          <Button 
            onClick={handleSendMessage} 
            disabled={!input.trim() || isLoading}
            size="icon"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          Pressione Shift + Enter para nova linha.
        </p>
      </div>
    </div>
  );
} 