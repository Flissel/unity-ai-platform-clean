#!/bin/bash
# Test each service in the n8n stack individually
# This script tests PostgreSQL, Redis, n8n, Traefik, Prometheus, and Grafana as standalone services

echo "=== N8N Services Individual Testing Script ==="
echo "This script will test each service individually to verify they work correctly."
echo ""

# Change to the n8n directory
cd "$(dirname "$0")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Function to test if a port is available
test_port() {
    local host=${1:-localhost}
    local port=$2
    local timeout=${3:-5}
    
    if timeout $timeout bash -c "</dev/tcp/$host/$port"; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local service_name=$1
    local host=${2:-localhost}
    local port=$3
    local max_wait=${4:-60}
    
    echo -e "${YELLOW}Waiting for $service_name to be ready on port $port...${NC}"
    local elapsed=0
    while [ $elapsed -lt $max_wait ]; do
        if test_port $host $port; then
            echo -e "${GREEN}✓ $service_name is ready!${NC}"
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
        echo -e "${GRAY}  Waiting... ($elapsed/$max_wait seconds)${NC}"
    done
    echo -e "${RED}✗ $service_name failed to start within $max_wait seconds${NC}"
    return 1
}

# Test 1: PostgreSQL Database
echo -e "\n${CYAN}=== Test 1: PostgreSQL Database ===${NC}"
echo -e "${YELLOW}Starting PostgreSQL container...${NC}"

# Stop any existing postgres container
docker stop n8n_postgres_test 2>/dev/null
docker rm n8n_postgres_test 2>/dev/null

# Start PostgreSQL with test configuration
docker run -d \
    --name n8n_postgres_test \
    -e POSTGRES_DB=n8n_test \
    -e POSTGRES_USER=n8n_user \
    -e POSTGRES_PASSWORD=test_password \
    -p 5433:5432 \
    postgres:15-alpine

if wait_for_service "PostgreSQL" "localhost" 5433; then
    # Test database connection
    echo -e "${YELLOW}Testing database connection...${NC}"
    if docker exec n8n_postgres_test psql -U n8n_user -d n8n_test -c "SELECT version();" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL test PASSED - Database is working correctly${NC}"
    else
        echo -e "${RED}✗ PostgreSQL test FAILED - Database connection failed${NC}"
    fi
fi

# Cleanup
echo -e "${GRAY}Cleaning up PostgreSQL test container...${NC}"
docker stop n8n_postgres_test >/dev/null 2>&1
docker rm n8n_postgres_test >/dev/null 2>&1

# Test 2: Redis Cache
echo -e "\n${CYAN}=== Test 2: Redis Cache ===${NC}"
echo -e "${YELLOW}Starting Redis container...${NC}"

# Stop any existing redis container
docker stop n8n_redis_test 2>/dev/null
docker rm n8n_redis_test 2>/dev/null

# Start Redis with test configuration
docker run -d \
    --name n8n_redis_test \
    -p 6380:6379 \
    redis:7-alpine \
    redis-server --requirepass test_password

if wait_for_service "Redis" "localhost" 6380; then
    # Test Redis connection
    echo -e "${YELLOW}Testing Redis connection...${NC}"
    if [ "$(docker exec n8n_redis_test redis-cli -a test_password ping 2>/dev/null)" = "PONG" ]; then
        echo -e "${GREEN}✓ Redis test PASSED - Cache is working correctly${NC}"
        
        # Test basic operations
        docker exec n8n_redis_test redis-cli -a test_password set test_key "test_value" >/dev/null 2>&1
        if [ "$(docker exec n8n_redis_test redis-cli -a test_password get test_key 2>/dev/null)" = "test_value" ]; then
            echo -e "${GREEN}✓ Redis operations test PASSED${NC}"
        else
            echo -e "${RED}✗ Redis operations test FAILED${NC}"
        fi
    else
        echo -e "${RED}✗ Redis test FAILED - Connection failed${NC}"
    fi
fi

# Cleanup
echo -e "${GRAY}Cleaning up Redis test container...${NC}"
docker stop n8n_redis_test >/dev/null 2>&1
docker rm n8n_redis_test >/dev/null 2>&1

# Test 3: N8N Application (with dependencies)
echo -e "\n${CYAN}=== Test 3: N8N Application ===${NC}"
echo -e "${YELLOW}Starting N8N with dependencies...${NC}"

# Create a temporary docker-compose for testing
cat > docker-compose.test.yml << 'EOF'
version: '3.8'
services:
  postgres_test:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: n8n_test
      POSTGRES_USER: n8n_user
      POSTGRES_PASSWORD: test_password
    ports:
      - "5434:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U n8n_user -d n8n_test"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis_test:
    image: redis:7-alpine
    command: redis-server --requirepass test_password
    ports:
      - "6381:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "test_password", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  n8n_test:
    image: n8nio/n8n:latest
    ports:
      - "5679:5678"
    environment:
      - NODE_ENV=development
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=test_password
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres_test
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=n8n_test
      - DB_POSTGRESDB_USER=n8n_user
      - DB_POSTGRESDB_PASSWORD=test_password
      - QUEUE_BULL_REDIS_HOST=redis_test
      - QUEUE_BULL_REDIS_PORT=6379
      - QUEUE_BULL_REDIS_PASSWORD=test_password
    depends_on:
      postgres_test:
        condition: service_healthy
      redis_test:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:5678/healthz || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
EOF

# Start the test stack
docker-compose -f docker-compose.test.yml up -d

# Wait for N8N to be ready
if wait_for_service "N8N" "localhost" 5679 120; then
    # Test N8N health endpoint
    echo -e "${YELLOW}Testing N8N health endpoint...${NC}"
    if curl -s -f http://localhost:5679/healthz >/dev/null 2>&1; then
        echo -e "${GREEN}✓ N8N test PASSED - Application is healthy${NC}"
        
        # Test N8N login page
        echo -e "${YELLOW}Testing N8N login page...${NC}"
        if curl -s -f http://localhost:5679 >/dev/null 2>&1; then
            echo -e "${GREEN}✓ N8N UI test PASSED - Login page accessible${NC}"
        else
            echo -e "${RED}✗ N8N UI test FAILED - Login page not accessible${NC}"
        fi
    else
        echo -e "${RED}✗ N8N test FAILED - Health check failed${NC}"
    fi
fi

# Cleanup
echo -e "${GRAY}Cleaning up N8N test stack...${NC}"
docker-compose -f docker-compose.test.yml down -v >/dev/null 2>&1
rm -f docker-compose.test.yml

# Test 4: Traefik Reverse Proxy
echo -e "\n${CYAN}=== Test 4: Traefik Reverse Proxy ===${NC}"
echo -e "${YELLOW}Starting Traefik container...${NC}"

# Stop any existing traefik container
docker stop traefik_test 2>/dev/null
docker rm traefik_test 2>/dev/null

# Start Traefik with test configuration
docker run -d \
    --name traefik_test \
    -p 8081:8080 \
    -p 8082:80 \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    traefik:v3.0 \
    --api.dashboard=true \
    --api.insecure=true \
    --providers.docker=true \
    --providers.docker.exposedbydefault=false \
    --entrypoints.web.address=:80

if wait_for_service "Traefik" "localhost" 8081; then
    # Test Traefik dashboard
    echo -e "${YELLOW}Testing Traefik dashboard...${NC}"
    if curl -s -f http://localhost:8081/dashboard/ >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Traefik test PASSED - Dashboard is accessible${NC}"
    else
        echo -e "${RED}✗ Traefik test FAILED - Dashboard not accessible${NC}"
    fi
fi

# Cleanup
echo -e "${GRAY}Cleaning up Traefik test container...${NC}"
docker stop traefik_test >/dev/null 2>&1
docker rm traefik_test >/dev/null 2>&1

# Test 5: Prometheus Monitoring
echo -e "\n${CYAN}=== Test 5: Prometheus Monitoring ===${NC}"
echo -e "${YELLOW}Starting Prometheus container...${NC}"

# Stop any existing prometheus container
docker stop prometheus_test 2>/dev/null
docker rm prometheus_test 2>/dev/null

# Create a minimal prometheus config
cat > prometheus.test.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF

# Start Prometheus with test configuration
docker run -d \
    --name prometheus_test \
    -p 9091:9090 \
    -v "$(pwd)/prometheus.test.yml:/etc/prometheus/prometheus.yml" \
    prom/prometheus:latest

if wait_for_service "Prometheus" "localhost" 9091; then
    # Test Prometheus web interface
    echo -e "${YELLOW}Testing Prometheus web interface...${NC}"
    if curl -s -f http://localhost:9091 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Prometheus test PASSED - Web interface is accessible${NC}"
        
        # Test Prometheus API
        if curl -s -f "http://localhost:9091/api/v1/query?query=up" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Prometheus API test PASSED${NC}"
        else
            echo -e "${RED}✗ Prometheus API test FAILED${NC}"
        fi
    else
        echo -e "${RED}✗ Prometheus test FAILED - Web interface not accessible${NC}"
    fi
fi

# Cleanup
echo -e "${GRAY}Cleaning up Prometheus test container...${NC}"
docker stop prometheus_test >/dev/null 2>&1
docker rm prometheus_test >/dev/null 2>&1
rm -f prometheus.test.yml

# Test 6: Grafana Visualization
echo -e "\n${CYAN}=== Test 6: Grafana Visualization ===${NC}"
echo -e "${YELLOW}Starting Grafana container...${NC}"

# Stop any existing grafana container
docker stop grafana_test 2>/dev/null
docker rm grafana_test 2>/dev/null

# Start Grafana with test configuration
docker run -d \
    --name grafana_test \
    -p 3001:3000 \
    -e GF_SECURITY_ADMIN_PASSWORD=test_password \
    grafana/grafana:latest

if wait_for_service "Grafana" "localhost" 3001 90; then
    # Test Grafana login page
    echo -e "${YELLOW}Testing Grafana login page...${NC}"
    if curl -s -f http://localhost:3001/login >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Grafana test PASSED - Login page is accessible${NC}"
    else
        echo -e "${RED}✗ Grafana test FAILED - Login page not accessible${NC}"
    fi
fi

# Cleanup
echo -e "${GRAY}Cleaning up Grafana test container...${NC}"
docker stop grafana_test >/dev/null 2>&1
docker rm grafana_test >/dev/null 2>&1

# Summary
echo -e "\n${GREEN}=== Test Summary ===${NC}"
echo -e "${YELLOW}Individual service testing completed.${NC}"
echo -e "${YELLOW}Check the results above to see which services are working correctly.${NC}"
echo -e "\n${CYAN}Next steps:${NC}"
echo -e "${NC}1. If all tests passed, you can start the full stack with: docker-compose up -d${NC}"
echo -e "${NC}2. If any tests failed, check the Docker logs and configuration files${NC}"
echo -e "${NC}3. Ensure all required secrets are properly configured in ./secrets/${NC}"
echo -e "\n${NC}For full stack testing, run: docker-compose up -d && docker-compose logs -f${NC}"