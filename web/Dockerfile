# Select base image
FROM node:alpine

# Set working directory
WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Copy node packages
COPY package*.json ./

# Install dependencies
RUN pnpm install

# Copy the remaining app components
COPY . .

# Expose port for app development server
EXPOSE 3000

# Run the Next.js app upon container start
CMD ["npm", "run", "dev"]