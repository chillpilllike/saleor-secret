FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

RUN corepack enable
RUN corepack prepare pnpm@9.6.0 --activate

FROM base AS builder
WORKDIR /app

# Install Python and pip
RUN apk add --no-cache python3 py3-pip
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Copy everything so we have the requirements file
COPY . .

# Install Python dependencies
# Adjust this command depending on Saleor’s actual requirements setup.
# If there is a `requirements.txt`:
RUN pip install --no-cache-dir -r requirements.txt

ENV NEXT_OUTPUT=standalone
ARG NEXT_PUBLIC_SALEOR_API_URL
ENV NEXT_PUBLIC_SALEOR_API_URL=${NEXT_PUBLIC_SALEOR_API_URL}
ARG NEXT_PUBLIC_STOREFRONT_URL
ENV NEXT_PUBLIC_STOREFRONT_URL=${NEXT_PUBLIC_STOREFRONT_URL}

RUN corepack enable
RUN corepack prepare pnpm@9.6.0 --activate

# Now that Python and dependencies are installed, build the schema
RUN pnpm build-schema

FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

ARG NEXT_PUBLIC_SALEOR_API_URL
ENV NEXT_PUBLIC_SALEOR_API_URL=${NEXT_PUBLIC_SALEOR_API_URL}
ARG NEXT_PUBLIC_STOREFRONT_URL
ENV NEXT_PUBLIC_STOREFRONT_URL=${NEXT_PUBLIC_STOREFRONT_URL}

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

RUN mkdir .next
RUN chown nextjs:nodejs .next

COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

CMD ["node", "server.js"]
