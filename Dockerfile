FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat python3 py3-pip jq
RUN ln -sf python3 /usr/bin/python
WORKDIR /app

# Get PNPM version from package.json
RUN export PNPM_VERSION=$(cat package.json | jq '.engines.pnpm' | sed -E 's/[^0-9.]//g')

# Install pnpm globally
RUN yarn global add pnpm@$PNPM_VERSION

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY . .

# Install Node.js dependencies
RUN pnpm install --frozen-lockfile

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Run schema build
RUN pnpm build-schema

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

ARG NEXT_PUBLIC_SALEOR_API_URL
ENV NEXT_PUBLIC_SALEOR_API_URL=${NEXT_PUBLIC_SALEOR_API_URL}
ARG NEXT_PUBLIC_STOREFRONT_URL
ENV NEXT_PUBLIC_STOREFRONT_URL=${NEXT_PUBLIC_STOREFRONT_URL}

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built files
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Set permissions for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

USER nextjs

CMD ["node", "server.js"]
