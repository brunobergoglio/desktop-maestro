# syntax=docker/dockerfile:1
# =============================================================================
# 🧹 DesktopMaestro — Next.js Frontend (Alpine, multi-stage)
# =============================================================================
# Best practices: multi-stage, non-root, pnpm, cache mounts, minimal size
# =============================================================================

# ── Stage 1: Dependencies ────────────────────────────────────────────────────
FROM node:22-alpine AS deps

WORKDIR /app

# Copy only dependency manifests (leverage Docker layer caching)
COPY package.json pnpm-lock.yaml ./

# Install with frozen lockfile for reproducibility + cache mount for speed
RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
    corepack enable && \
    pnpm install --frozen-lockfile

# ── Stage 2: Build ────────────────────────────────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

# Copy node_modules from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source code
COPY . .

# Build the Next.js app
ARG API_URL=http://api:7899
ENV API_URL=$API_URL
RUN pnpm run build

# ── Stage 3: Production runtime ───────────────────────────────────────────────
FROM node:22-alpine AS runner

# Security: non-root user
RUN addgroup -S maestro && adduser -S -G maestro maestro

WORKDIR /app

ENV NODE_ENV=production
ARG API_URL=http://api:7899
ENV API_URL=$API_URL

# Copy only the absolute minimum for production
COPY --from=builder --chown=maestro:maestro /app/.next/standalone ./
COPY --from=builder --chown=maestro:maestro /app/.next/static ./.next/static
COPY --from=builder --chown=maestro:maestro /app/public ./public

# Hygiene
RUN rm -rf /root/.cache /tmp/*

# Drop privileges
USER maestro

EXPOSE 3000

# Health check
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s \
  CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:3000/ || exit 1

CMD ["node", "server.js"]
