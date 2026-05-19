ARG NODE_IMAGE=node:20-bookworm-slim
ARG NGINX_IMAGE=nginx:1.27-alpine
ARG HTTP_PROXY=
ARG HTTPS_PROXY=
ARG NO_PROXY=

FROM ${NODE_IMAGE} AS builder

WORKDIR /app

RUN corepack enable

ENV HTTP_PROXY=${HTTP_PROXY} \
    HTTPS_PROXY=${HTTPS_PROXY} \
    http_proxy=${HTTP_PROXY} \
    https_proxy=${HTTPS_PROXY} \
    npm_config_proxy=${HTTP_PROXY} \
    npm_config_https_proxy=${HTTPS_PROXY} \
    NPM_CONFIG_PROXY=${HTTP_PROXY} \
    NPM_CONFIG_HTTPS_PROXY=${HTTPS_PROXY} \
    NO_PROXY=${NO_PROXY} \
    no_proxy=${NO_PROXY}

COPY pnpm-lock.yaml pnpm-workspace.yaml ./
COPY web/package.json web/package.json

RUN corepack prepare pnpm@9.1.0 --activate \
    && pnpm install --filter ./web --frozen-lockfile

COPY web web

ARG VITE_API_BASE=/api/v1
ENV VITE_API_BASE=${VITE_API_BASE}

RUN pnpm -C web build

FROM ${NGINX_IMAGE}

COPY --from=builder /app/web/dist /usr/share/nginx/html

EXPOSE 80
