#!/bin/zsh
# Deploy agent-kanban backend with Docker
# Usage: ./deploy.sh (from backend/ directory)

set -e  # Exit on error

# Resolve paths relative to this script so it works from any cwd
SCRIPT_DIR="${0:A:h}"
ENV_FILE="$SCRIPT_DIR/../be-env/.env"

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
echo "${GREEN}[1/7] Pulling latest changes...${NC}"
git -C "$SCRIPT_DIR" pull
echo ""

# Step 2: Validate environment file
echo "${GREEN}[2/7] Validating environment file...${NC}"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "${RED}ERROR: $ENV_FILE not found${NC}"
  echo "Please create be-env/.env in the project root"
  exit 1
fi

# Step 3: Load and validate environment variables
echo "${GREEN}[3/7] Loading environment variables...${NC}"

# Source the .env file (without copying)
set -a
source "$ENV_FILE"
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
echo "${GREEN}[4/7] Stopping existing container...${NC}"
docker rm -f $CONTAINER_NAME 2>/dev/null || echo "No existing container to remove"
echo ""

# Step 5: Build Docker image
echo "${GREEN}[5/7] Building Docker image...${NC}"
docker build -t $IMAGE_NAME "$SCRIPT_DIR"
echo ""

# Step 6: Run container
echo "${GREEN}[6/7] Starting container on port $BACKEND_PORT...${NC}"

# If DATABASE_URL uses localhost, run with host networking so container can reach host Postgres
# without requiring pg_hba changes for Docker bridge subnets.
if [[ "$DATABASE_URL" == *"@localhost:"* || "$DATABASE_URL" == *"@127.0.0.1:"* || "$DATABASE_URL" == *"@::1:"* ]]; then
  echo "${YELLOW}Detected localhost DATABASE_URL; using host network mode${NC}"
  docker run -d \
    --name $CONTAINER_NAME \
    --restart unless-stopped \
    --network host \
    --env-file "$ENV_FILE" \
    $IMAGE_NAME \
    sh -c "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT"
else
  docker run -d \
    --name $CONTAINER_NAME \
    --restart unless-stopped \
    --add-host host.docker.internal:host-gateway \
    -p $BACKEND_PORT:8000 \
    --env-file "$ENV_FILE" \
    $IMAGE_NAME
fi
echo ""

# Step 7: Wait for backend to be ready
echo "${GREEN}[7/7] Waiting for backend to be ready...${NC}"
READY=false
for i in {1..30}; do
  # If container exited, fail immediately and show logs
  if ! docker ps --filter "name=$CONTAINER_NAME" --format "{{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
    echo "${RED}ERROR: Backend container exited during startup${NC}"
    echo "${YELLOW}Last container logs:${NC}"
    docker logs --tail 100 $CONTAINER_NAME || true
    exit 1
  fi

  if curl -fsS "http://localhost:$BACKEND_PORT/health" >/dev/null 2>&1; then
    READY=true
    break
  fi

  sleep 2
done

if [[ "$READY" != "true" ]]; then
  echo "${RED}ERROR: Backend did not become healthy in time${NC}"
  echo "${YELLOW}Last container logs:${NC}"
  docker logs --tail 100 $CONTAINER_NAME || true
  exit 1
fi
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
