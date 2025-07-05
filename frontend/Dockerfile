# Multi-stage build for Next.js application
# Stage 1: Build stage
FROM node:24-slim AS builder

# Set environment variables for building.
# Don't set NODE_ENV during build to avoid conflicts

# Install system-level dependencies that might be needed for building native modules.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container.
WORKDIR /app

# Copy package.json and package-lock.json to install dependencies before copying the rest of the code.
# This leverages Docker's layer caching for faster subsequent builds.
COPY package*.json ./

# Copy TypeScript configuration first
COPY tsconfig.json ./
COPY next.config.ts ./

# Install all dependencies (including dev dependencies needed for building).
RUN npm ci

# Copy the rest of the application's source code.
# The .dockerignore file will prevent copying unnecessary files and directories.
COPY . .

    # Build the Next.js application for production.
    RUN npm run build

# Stage 2: Production stage
FROM node:24-slim AS runner

# Set environment variables for production.
ENV NODE_ENV=production \
    PORT=3000

WORKDIR /app

# Create a non-root user to run the application for security.
RUN groupadd -g 1001 -r nodejs && useradd -r -g nodejs -u 1001 nextjs

# Copy package.json and package-lock.json for production dependencies.
COPY package*.json ./

# Install only production dependencies.
RUN npm ci --only=production && npm cache clean --force

# Copy the built application from the builder stage.
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

# Copy other necessary files.
COPY --from=builder /app/next.config.ts ./next.config.ts

# Change ownership of the app directory to the nextjs user.
RUN chown -R nextjs:nodejs /app

# Switch to the non-root user.
USER nextjs

# Expose the port the app runs on.
EXPOSE ${PORT}

# The command to run the application.
# Uses next start to run the production build.
# We use sh -c to allow the shell to expand the ${PORT} variable at runtime.
CMD ["/bin/sh", "-c", "npm start -- --port ${PORT}"] 