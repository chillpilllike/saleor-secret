FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
# libc6-compat may be needed for certain Node.js dependencies on Alpine
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Enable PNPM
RUN corepack enable
RUN corepack prepare pnpm@9.6.0 --activate

FROM base AS builder
WORKDIR /app

# Install Python, pip, and virtualenv
RUN apk add --no-cache python3 py3-pip py3-virtualenv

# Create and activate a virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# First copy only the requirements file to install dependencies
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the application
COPY . .

# Set environment variables for Next.js
ENV NEXT_OUTPUT=standalone
ARG NEXT_PUBLIC_SALEOR_API_URL
ENV NEXT_PUBLIC_SALEOR_API_URL=${NEXT_PUBLIC_SALEOR_API_URL}
ARG NEXT_PUBLIC_STOREFRONT_URL
ENV NEXT_PUBLIC_STOREFRONT_URL=${NEXT_PUBLIC_STOREFRONT_URL}

# Re-enable PNPM for this stage
RUN corepack enable
RUN corepack prepare pnpm@9.6.0 --activate

# Build the GraphQL schema using the Django manage.py command
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

# Switch to non-root user
USER nextjs

# Start the application
CMD ["node", "server.js"]
