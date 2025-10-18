FROM node:20-alpine

WORKDIR /app

# Install serve for production static file serving
RUN npm install -g serve

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Build frontend
RUN npm run build

EXPOSE 3000

# Serve static files
CMD ["serve", "-s", "build", "-l", "3000"]