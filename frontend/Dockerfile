# =============================================================================
# DesktopMaestro — Next.js Frontend
# =============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json .
RUN npm install

# Copy source
COPY . .

# Build
ARG API_URL=http://api:7899
ENV API_URL=$API_URL
RUN npm run build

# ─── Production image ───
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ARG API_URL=http://api:7899
ENV API_URL=$API_URL

# Copy standalone build output
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Expose frontend port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:3000/ || exit 1

CMD ["node", "server.js"]
