"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2, CheckCircle, XCircle } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { 
  saveZabbixSettings, 
  getZabbixSettings, 
  saveOpenRouterKey,
  checkOpenRouterSettings,
  validateLicense,
  saveLicense
} from "@/lib/api";

// Esquema Zabbix
const zabbixSchema = z.object({
  url: z.string().url("URL inválida").min(1, "URL é obrigatória"),
  username: z.string().min(1, "Nome de usuário é obrigatório"),
  password: z.string().min(1, "Senha é obrigatória"),
  api_token: z.string().optional(),
});

// Esquema OpenRouter
const openRouterSchema = z.object({
  api_key: z.string().min(1, "Chave de API é obrigatória"),
});

// Esquema de Licença
const licenseSchema = z.object({
  license_key: z.string().min(1, "Chave de licença é obrigatória"),
});

type ZabbixFormData = z.infer<typeof zabbixSchema>;
type OpenRouterFormData = z.infer<typeof openRouterSchema>;
type LicenseFormData = z.infer<typeof licenseSchema>;

export default function SettingsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [mounted, setMounted] = useState(false);

  // Forms
  const zabbixForm = useForm<ZabbixFormData>({
    resolver: zodResolver(zabbixSchema),
    defaultValues: {
      url: "",
      username: "",
      password: "",
      api_token: "",
    },
  });

  const openRouterForm = useForm<OpenRouterFormData>({
    resolver: zodResolver(openRouterSchema),
    defaultValues: {
      api_key: "",
    },
  });

  const licenseForm = useForm<LicenseFormData>({
    resolver: zodResolver(licenseSchema),
    defaultValues: {
      license_key: localStorage?.getItem("zabbia_license") || "",
    },
  });

  // Consultas e mutações
  const zabbixQuery = useQuery({
    queryKey: ["zabbix-settings"],
    queryFn: getZabbixSettings,
    enabled: mounted,
  });

  const openRouterQuery = useQuery({
    queryKey: ["openrouter-settings"],
    queryFn: checkOpenRouterSettings,
    enabled: mounted,
  });

  const zabbixMutation = useMutation({
    mutationFn: saveZabbixSettings,
    onSuccess: () => {
      toast({
        title: "Configurações salvas",
        description: "As configurações do Zabbix foram salvas com sucesso.",
      });
      zabbixQuery.refetch();
    },
    onError: (error) => {
      toast({
        title: "Erro",
        description: `Falha ao salvar configurações: ${error instanceof Error ? error.message : "Erro desconhecido"}`,
        variant: "destructive",
      });
    },
  });

  const openRouterMutation = useMutation({
    mutationFn: saveOpenRouterKey,
    onSuccess: () => {
      toast({
        title: "Chave API salva",
        description: "A chave de API do OpenRouter foi salva com sucesso.",
      });
      openRouterQuery.refetch();
    },
    onError: (error) => {
      toast({
        title: "Erro",
        description: `Falha ao salvar chave API: ${error instanceof Error ? error.message : "Erro desconhecido"}`,
        variant: "destructive",
      });
    },
  });

  const licenseMutation = useMutation({
    mutationFn: (data: LicenseFormData) => {
      // Primeiro validar a licença
      return validateLicense(data.license_key).then(result => {
        if (result.valid) {
          // Salvar localmente
          localStorage.setItem("zabbia_license", data.license_key);
          // Salvar no backend
          return saveLicense(data.license_key);
        } else {
          throw new Error(`Licença inválida: ${result.message || "verificação falhou"}`);
        }
      });
    },
    onSuccess: (data) => {
      toast({
        title: "Licença ativada",
        description: `Licença válida para ${data.customer} até ${new Date(data.expires).toLocaleDateString('pt-BR')}`,
      });
    },
    onError: (error) => {
      toast({
        title: "Erro de licença",
        description: `${error instanceof Error ? error.message : "Erro desconhecido"}`,
        variant: "destructive",
      });
    },
  });

  // Inicialização
  useEffect(() => {
    setMounted(true);
  }, []);

  // Preencher o formulário quando os dados estiverem disponíveis
  useEffect(() => {
    if (zabbixQuery.data) {
      zabbixForm.reset({
        url: zabbixQuery.data.url || "",
        username: zabbixQuery.data.username || "",
        password: "", // Não preencher senha por segurança
        api_token: "", // Não preencher token por segurança
      });
    }
  }, [zabbixQuery.data, zabbixForm]);

  // Handlers de formulário
  const onZabbixSubmit = (data: ZabbixFormData) => {
    zabbixMutation.mutate(data);
  };

  const onOpenRouterSubmit = (data: OpenRouterFormData) => {
    openRouterMutation.mutate(data);
  };

  const onLicenseSubmit = (data: LicenseFormData) => {
    licenseMutation.mutate(data);
  };

  // Mostrar estado de carregamento
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
        <h1 className="heading-responsive font-bold">Configurações</h1>
      </div>

      <Tabs defaultValue="zabbix" className="w-full">
        <TabsList className="grid w-full grid-cols-3 mb-4">
          <TabsTrigger value="zabbix">Zabbix</TabsTrigger>
          <TabsTrigger value="openrouter">OpenRouter</TabsTrigger>
          <TabsTrigger value="license">Licenciamento</TabsTrigger>
        </TabsList>
        
        <TabsContent value="zabbix">
          <Card>
            <CardHeader>
              <CardTitle>Configurações do Zabbix</CardTitle>
              <CardDescription>
                Configure a conexão com o servidor Zabbix.
              </CardDescription>
            </CardHeader>
            <form onSubmit={zabbixForm.handleSubmit(onZabbixSubmit)}>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-4">
                  <div className="font-semibold">Status:</div>
                  {zabbixQuery.isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  ) : zabbixQuery.data?.connected ? (
                    <div className="flex items-center text-green-600">
                      <CheckCircle className="h-5 w-5 mr-1" />
                      <span>Conectado</span>
                    </div>
                  ) : (
                    <div className="flex items-center text-red-600">
                      <XCircle className="h-5 w-5 mr-1" />
                      <span>Desconectado</span>
                    </div>
                  )}
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="url">URL do Zabbix</Label>
                  <Input 
                    id="url" 
                    placeholder="https://seu-zabbix.exemplo.com" 
                    {...zabbixForm.register("url")} 
                  />
                  {zabbixForm.formState.errors.url && (
                    <p className="text-red-500 text-sm">{zabbixForm.formState.errors.url.message}</p>
                  )}
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="username">Usuário</Label>
                  <Input 
                    id="username" 
                    placeholder="Nome de usuário" 
                    {...zabbixForm.register("username")} 
                  />
                  {zabbixForm.formState.errors.username && (
                    <p className="text-red-500 text-sm">{zabbixForm.formState.errors.username.message}</p>
                  )}
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="password">Senha</Label>
                  <Input 
                    id="password" 
                    type="password" 
                    placeholder="Senha" 
                    {...zabbixForm.register("password")} 
                  />
                  {zabbixForm.formState.errors.password && (
                    <p className="text-red-500 text-sm">{zabbixForm.formState.errors.password.message}</p>
                  )}
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="api_token">Token API (opcional)</Label>
                  <Input 
                    id="api_token" 
                    placeholder="Token API" 
                    {...zabbixForm.register("api_token")} 
                  />
                </div>
              </CardContent>
              <CardFooter>
                <Button 
                  type="submit" 
                  disabled={zabbixMutation.isPending}
                >
                  {zabbixMutation.isPending && (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  )}
                  Salvar configurações
                </Button>
              </CardFooter>
            </form>
          </Card>
        </TabsContent>
        
        <TabsContent value="openrouter">
          <Card>
            <CardHeader>
              <CardTitle>Configurações do OpenRouter</CardTitle>
              <CardDescription>
                Configure a chave de API do OpenRouter para ativar as funcionalidades de IA.
              </CardDescription>
            </CardHeader>
            <form onSubmit={openRouterForm.handleSubmit(onOpenRouterSubmit)}>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-4 mb-4">
                  <div className="font-semibold">Status:</div>
                  {openRouterQuery.isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  ) : openRouterQuery.data?.configured ? (
                    <div className="flex items-center text-green-600">
                      <CheckCircle className="h-5 w-5 mr-1" />
                      <span>Configurado</span>
                    </div>
                  ) : (
                    <div className="flex items-center text-red-600">
                      <XCircle className="h-5 w-5 mr-1" />
                      <span>Não configurado</span>
                    </div>
                  )}
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="api_key">Chave API</Label>
                  <Input 
                    id="api_key" 
                    placeholder="sk-or-..." 
                    {...openRouterForm.register("api_key")} 
                  />
                  {openRouterForm.formState.errors.api_key && (
                    <p className="text-red-500 text-sm">{openRouterForm.formState.errors.api_key.message}</p>
                  )}
                  <p className="text-sm text-muted-foreground">
                    Obtenha sua chave em <a href="https://openrouter.ai/keys" className="text-blue-600 hover:underline" target="_blank" rel="noreferrer">openrouter.ai/keys</a>
                  </p>
                </div>
              </CardContent>
              <CardFooter>
                <Button 
                  type="submit" 
                  disabled={openRouterMutation.isPending}
                >
                  {openRouterMutation.isPending && (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  )}
                  Salvar chave API
                </Button>
              </CardFooter>
            </form>
          </Card>
        </TabsContent>
        
        <TabsContent value="license">
          <Card>
            <CardHeader>
              <CardTitle>Licenciamento</CardTitle>
              <CardDescription>
                Ative sua licença do Zabbia.
              </CardDescription>
            </CardHeader>
            <form onSubmit={licenseForm.handleSubmit(onLicenseSubmit)}>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="license_key">Chave de Licença</Label>
                  <Input 
                    id="license_key" 
                    placeholder="Insira sua chave de licença" 
                    {...licenseForm.register("license_key")} 
                  />
                  {licenseForm.formState.errors.license_key && (
                    <p className="text-red-500 text-sm">{licenseForm.formState.errors.license_key.message}</p>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">
                  Para adquirir uma licença, entre em contato com nossa equipe de vendas.
                </p>
              </CardContent>
              <CardFooter>
                <Button 
                  type="submit" 
                  disabled={licenseMutation.isPending}
                >
                  {licenseMutation.isPending && (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  )}
                  Ativar Licença
                </Button>
              </CardFooter>
            </form>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
} 