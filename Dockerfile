FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
# libc6-compat may be needed for certain Node.js dependencies on Alpine
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Enable and prepare PNPM
RUN corepack enable
RUN corepack prepare pnpm@9.6.0 --activate

FROM base AS builder
WORKDIR /app

# Install Python and virtualenv
RUN apk add --no-cache python3 py3-pip py3-virtualenv

# Create and activate a virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy all project files including requirements.txt
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Re-enable PNPM in this stage, as environment differs between stages
RUN corepack enable
RUN corepack prepare pnpm@9.6.0 --activate

# Run the schema build command which uses `python manage.py get_graphql_schema`
RUN pnpm build-schema

# Production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

ARG NEXT_PUBLIC_SALEOR_API_URL
ENV NEXT_PUBLIC_SALEOR_API_URL=${NEXT_PUBLIC_SALEOR_API_URL}
ARG NEXT_PUBLIC_STOREFRONT_URL
ENV NEXT_PUBLIC_STOREFRONT_URL=${NEXT_PUBLIC_STOREFRONT_URL}

# Create a non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Create a .next directory and set permissions
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Copy the built standalone output from the builder stage
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

# Start the application
CMD ["node", "server.js"]
