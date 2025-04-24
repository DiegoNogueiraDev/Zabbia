import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ChatInterface from '@/components/ChatInterface';
import * as api from '@/lib/api';

// Mock do módulo api
jest.mock('@/lib/api', () => ({
  sendChatMessage: jest.fn(),
  getChatHistory: jest.fn(),
}));

describe('ChatInterface Component', () => {
  beforeEach(() => {
    // Configurar mocks antes de cada teste
    (api.sendChatMessage as jest.Mock).mockResolvedValue({
      id: '123',
      response: 'Resposta de teste',
      success: true
    });
    
    (api.getChatHistory as jest.Mock).mockResolvedValue([
      { id: '1', message: 'Mensagem do usuário', timestamp: '2023-10-10T10:00:00', role: 'user' },
      { id: '2', message: 'Resposta do assistente', timestamp: '2023-10-10T10:01:00', role: 'assistant' }
    ]);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renderiza a interface de chat corretamente', async () => {
    render(<ChatInterface />);
    
    // Verificar se o input de texto está presente
    expect(screen.getByPlaceholderText('Digite sua mensagem aqui...')).toBeInTheDocument();
    
    // Verificar se o botão de enviar está presente
    expect(screen.getByRole('button', { name: /enviar/i })).toBeInTheDocument();
    
    // Esperar pelo histórico de chat carregado
    await waitFor(() => {
      expect(api.getChatHistory).toHaveBeenCalledTimes(1);
      expect(screen.getByText('Mensagem do usuário')).toBeInTheDocument();
      expect(screen.getByText('Resposta do assistente')).toBeInTheDocument();
    });
  });

  test('envia uma mensagem quando o usuário clica em enviar', async () => {
    render(<ChatInterface />);
    
    // Digitar uma mensagem no input
    const input = screen.getByPlaceholderText('Digite sua mensagem aqui...');
    fireEvent.change(input, { target: { value: 'Nova mensagem de teste' } });
    
    // Clicar no botão de enviar
    const sendButton = screen.getByRole('button', { name: /enviar/i });
    fireEvent.click(sendButton);
    
    // Verificar se a API foi chamada com os parâmetros corretos
    await waitFor(() => {
      expect(api.sendChatMessage).toHaveBeenCalledWith('Nova mensagem de teste');
      expect(input).toHaveValue(''); // Input deve ser limpo após envio
    });
  });

  test('envia uma mensagem quando o usuário pressiona Enter', async () => {
    render(<ChatInterface />);
    
    // Digitar uma mensagem no input
    const input = screen.getByPlaceholderText('Digite sua mensagem aqui...');
    fireEvent.change(input, { target: { value: 'Mensagem via Enter' } });
    
    // Pressionar Enter
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter', charCode: 13 });
    
    // Verificar se a API foi chamada com os parâmetros corretos
    await waitFor(() => {
      expect(api.sendChatMessage).toHaveBeenCalledWith('Mensagem via Enter');
      expect(input).toHaveValue(''); // Input deve ser limpo após envio
    });
  });

  test('não envia mensagens vazias', async () => {
    render(<ChatInterface />);
    
    // Clicar no botão de enviar sem digitar nada
    const sendButton = screen.getByRole('button', { name: /enviar/i });
    fireEvent.click(sendButton);
    
    // A API não deve ser chamada
    await waitFor(() => {
      expect(api.sendChatMessage).not.toHaveBeenCalled();
    });
  });

  test('exibe mensagem de carregamento enquanto aguarda resposta', async () => {
    // Atrasar a resposta da API
    (api.sendChatMessage as jest.Mock).mockImplementation(() => {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            id: '123',
            response: 'Resposta demorada',
            success: true
          });
        }, 100);
      });
    });
    
    render(<ChatInterface />);
    
    // Digitar e enviar uma mensagem
    const input = screen.getByPlaceholderText('Digite sua mensagem aqui...');
    fireEvent.change(input, { target: { value: 'Mensagem de teste' } });
    
    const sendButton = screen.getByRole('button', { name: /enviar/i });
    fireEvent.click(sendButton);
    
    // Verificar se a mensagem de carregamento é exibida
    await waitFor(() => {
      expect(screen.getByText('Digitando...')).toBeInTheDocument();
    });
    
    // Verificar se a resposta é exibida após o término do carregamento
    await waitFor(() => {
      expect(screen.getByText('Resposta demorada')).toBeInTheDocument();
      expect(screen.queryByText('Digitando...')).not.toBeInTheDocument();
    });
  });
}); 