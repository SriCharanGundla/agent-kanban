#!/bin/zsh
# Teardown agent-kanban backend container
# Usage: ./teardown.sh (from backend/ directory)

set -e  # Exit on error

# Container name
CONTAINER_NAME="agent-kanban-backend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "${BLUE}========================================${NC}"
echo "${BLUE}  Backend Teardown${NC}"
echo "${BLUE}========================================${NC}"
echo ""

echo "${YELLOW}Stopping backend container...${NC}"

# Stop and remove backend container
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "  Removing ${CONTAINER_NAME}..."
  docker rm -f $CONTAINER_NAME
  echo "${GREEN}✓ Backend container removed${NC}"
else
  echo "${YELLOW}⚠ ${CONTAINER_NAME} not found${NC}"
fi

echo ""
echo "${GREEN}========================================${NC}"
echo "${GREEN}  Backend Teardown Complete! ✓${NC}"
echo "${GREEN}========================================${NC}"
echo ""
