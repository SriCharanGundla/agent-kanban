#!/bin/zsh
# Teardown agent-kanban frontend container
# Usage: ./teardown.sh (from frontend/ directory)

set -e  # Exit on error

# Container name
CONTAINER_NAME="agent-kanban-frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "${BLUE}========================================${NC}"
echo "${BLUE}  Frontend Teardown${NC}"
echo "${BLUE}========================================${NC}"
echo ""

echo "${YELLOW}Stopping frontend container...${NC}"

# Stop and remove frontend container
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "  Removing ${CONTAINER_NAME}..."
  docker rm -f $CONTAINER_NAME
  echo "${GREEN}✓ Frontend container removed${NC}"
else
  echo "${YELLOW}⚠ ${CONTAINER_NAME} not found${NC}"
fi

echo ""
echo "${GREEN}========================================${NC}"
echo "${GREEN}  Frontend Teardown Complete! ✓${NC}"
echo "${GREEN}========================================${NC}"
echo ""
