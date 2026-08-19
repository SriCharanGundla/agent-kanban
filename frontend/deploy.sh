#!/bin/zsh
# Deploy agent-kanban frontend with Docker
# Usage: ./deploy.sh (from frontend/ directory)

set -e  # Exit on error

# Resolve paths relative to this script so it works from any cwd
SCRIPT_DIR="${0:A:h}"
ENV_FILE="$SCRIPT_DIR/../fe-env/.env"

# Configuration
FRONTEND_PORT=${FRONTEND_PORT:-7654}
CONTAINER_NAME="agent-kanban-frontend"
IMAGE_NAME="agent-kanban-frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "${BLUE}========================================${NC}"
echo "${BLUE}  Frontend Deployment${NC}"
echo "${BLUE}========================================${NC}"
echo ""

# Step 1: Git pull
echo "${GREEN}[1/6] Pulling latest changes...${NC}"
git -C "$SCRIPT_DIR" pull
echo ""

# Step 2: Validate environment file
echo "${GREEN}[2/6] Validating environment file...${NC}"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "${RED}ERROR: $ENV_FILE not found${NC}"
  echo "Please create fe-env/.env in the project root"
  exit 1
fi

# Step 3: Load and validate environment variables
echo "${GREEN}[3/6] Loading environment variables...${NC}"

# Source the .env file (without copying)
set -a
source "$ENV_FILE"
set +a

# Validate required variables
if [[ -z "$VITE_API_BASE_URL" ]]; then
  echo "${RED}ERROR: VITE_API_BASE_URL is not set in .env${NC}"
  exit 1
fi

echo "✓ VITE_API_BASE_URL is set: $VITE_API_BASE_URL"
echo ""

# Step 4: Stop and remove existing container
echo "${GREEN}[4/6] Stopping existing container...${NC}"
docker rm -f $CONTAINER_NAME 2>/dev/null || echo "No existing container to remove"
echo ""

# Step 5: Build Docker image
echo "${GREEN}[5/6] Building Docker image...${NC}"
docker build -t $IMAGE_NAME \
  --build-arg VITE_API_BASE_URL="$VITE_API_BASE_URL" \
  "$SCRIPT_DIR"
echo ""

# Step 6: Run container
echo "${GREEN}[6/6] Starting container on port $FRONTEND_PORT...${NC}"
docker run -d \
  --name $CONTAINER_NAME \
  --restart unless-stopped \
  -p $FRONTEND_PORT:80 \
  $IMAGE_NAME
echo ""

# Check container status
echo "${GREEN}Container Status:${NC}"
docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "${GREEN}========================================${NC}"
echo "${GREEN}  Frontend Deployment Complete! ✓${NC}"
echo "${GREEN}========================================${NC}"
echo ""
echo "Frontend:     ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
echo ""
echo "To view logs: docker logs -f $CONTAINER_NAME"
echo ""
