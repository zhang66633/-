FROM node:22-alpine AS build

WORKDIR /app

# 构建期环境变量（docker-compose build args 注入；缺省同 dev 模式走同源代理）
ARG VITE_API_BASE_URL=/api
ARG VITE_WS_URL=ws://localhost:8002/api/ws
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_WS_URL=$VITE_WS_URL

# Install pnpm
RUN npm install -g pnpm

# Copy dependencies
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Copy source
COPY . .

# Build
RUN pnpm build

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
