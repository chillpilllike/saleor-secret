# Base image with Node.js 20
FROM node:20-alpine AS base

# Install dependencies for building the application
RUN apk add --no-cache git bash libc6-compat python3 py3-pip

# Set working directory
WORKDIR /app

# Clone the repository
RUN git clone https://github.com/saleor/storefront.git /app


# Install pnpm globally
RUN corepack enable
RUN corepack prepare pnpm@9.6.0 --activate

# Install dependencies
RUN pnpm install

# Expose the default port for the app
EXPOSE 3000

# Set environment variables for Saleor
ARG NEXT_PUBLIC_SALEOR_API_URL
ENV NEXT_PUBLIC_SALEOR_API_URL=${NEXT_PUBLIC_SALEOR_API_URL}

# Build the application
RUN pnpm run build

# Start the production server
CMD ["pnpm", "start"]

# Development stage (Optional)
# Uncomment the following if you want to use the development server
# CMD ["pnpm", "dev"]
