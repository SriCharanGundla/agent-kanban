#!/bin/zsh
# Deploy agent-kanban backend with Docker
# Usage: ./deploy.sh (from backend/ directory)

set -e  # Exit on error

# Configuration
BACKEND_PORT=${BACKEND_PORT:-7655}
CONTAINER_NAME="agent-kanban-backend"
IMAGE_NAME="agent-kanban-backend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "${BLUE}========================================${NC}"
echo "${BLUE}  Backend Deployment${NC}"
echo "${BLUE}========================================${NC}"
echo ""

# Step 1: Git pull
echo "${GREEN}[1/8] Pulling latest changes...${NC}"
git pull
echo ""

# Step 2: Validate environment file
echo "${GREEN}[2/8] Validating environment file...${NC}"
if [[ ! -f "../be-env/.env" ]]; then
  echo "${RED}ERROR: ../be-env/.env not found${NC}"
  echo "Please create be-env/.env in the project root"
  exit 1
fi

# Step 3: Load and validate environment variables
echo "${GREEN}[3/8] Loading environment variables...${NC}"

# Source the .env file (without copying)
set -a
source ../be-env/.env
set +a

# Validate required variables
if [[ -z "$DATABASE_URL" ]]; then
  echo "${RED}ERROR: DATABASE_URL is not set in .env${NC}"
  exit 1
fi

if [[ -z "$JWT_SECRET_KEY" ]]; then
  echo "${RED}ERROR: JWT_SECRET_KEY is not set in .env${NC}"
  exit 1
fi

echo "✓ DATABASE_URL is set"
echo "✓ JWT_SECRET_KEY is set"
echo ""

# Step 4: Stop and remove existing container
echo "${GREEN}[4/8] Stopping existing container...${NC}"
docker rm -f $CONTAINER_NAME 2>/dev/null || echo "No existing container to remove"
echo ""

# Step 5: Build Docker image
echo "${GREEN}[5/8] Building Docker image...${NC}"
docker build -t $IMAGE_NAME .
echo ""

# Step 6: Run container
echo "${GREEN}[6/8] Starting container on port $BACKEND_PORT...${NC}"
docker run -d \
  --name $CONTAINER_NAME \
  --restart unless-stopped \
  -p $BACKEND_PORT:8000 \
  --env-file ../be-env/.env \
  $IMAGE_NAME
echo ""

# Step 7: Wait for backend to be ready
echo "${GREEN}[7/8] Waiting for backend to be ready...${NC}"
sleep 5
echo ""

# Step 8: Run database migrations
echo "${GREEN}[8/8] Running database migrations...${NC}"
docker exec $CONTAINER_NAME uv run alembic upgrade head
echo ""

# Check container status
echo "${GREEN}Container Status:${NC}"
docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "${GREEN}========================================${NC}"
echo "${GREEN}  Backend Deployment Complete! ✓${NC}"
echo "${GREEN}========================================${NC}"
echo ""
echo "Backend API:  ${GREEN}http://localhost:$BACKEND_PORT${NC}"
echo "Swagger UI:   ${GREEN}http://localhost:$BACKEND_PORT/docs${NC}"
echo ""
echo "To view logs: docker logs -f $CONTAINER_NAME"
echo ""
