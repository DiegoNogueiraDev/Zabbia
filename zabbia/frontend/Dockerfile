FROM node:18-alpine AS base

# Dependências para sharp (processamento de imagens)
RUN apk add --no-cache libc6-compat

# Diretório de trabalho
WORKDIR /app

# Camada de dependências
FROM base AS deps
COPY package.json package-lock.json* ./
RUN npm ci

# Camada de build
FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Variáveis de ambiente para build
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Build da aplicação
RUN npm run build

# Camada de execução
FROM base AS runner
ENV NODE_ENV production

# Criar usuário não-root
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
USER nextjs

# Copiar arquivos de build e pacotes
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Expor porta
EXPOSE 3000

# Variáveis de ambiente para execução
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# Comando para iniciar a aplicação
CMD ["node", "server.js"] 