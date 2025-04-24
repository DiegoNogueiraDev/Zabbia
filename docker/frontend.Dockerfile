FROM node:18-alpine

WORKDIR /app

# Copiar arquivos de projeto
COPY frontend/package.json ./
COPY frontend/next.config.js ./
COPY frontend/postcss.config.js ./
COPY frontend/tailwind.config.js ./
COPY frontend/tsconfig.json ./

# Instalar dependências
RUN npm install
RUN npm install framer-motion

# Copiar código-fonte
COPY frontend/app ./app
COPY frontend/components ./components
COPY frontend/styles ./styles
COPY frontend/public ./public

# Construir aplicação
RUN npm run build

# Expor porta
EXPOSE 3000

# Comando para iniciar o servidor
CMD ["npm", "start"] 