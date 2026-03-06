#!/bin/bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# PROSD System Deployment Script
# 
# Usage: ./setup.sh [OPTIONS]
# 
# Options:
#   -o, --observability    Enable full observability (default)
#   -m, --metrics          Enable metrics only
#   -l, --logging          Enable logging only  
#   --no-observability     Disable all observability
#   -c, --clean            Clean start (remove volumes)
#   -n, --no-build         Skip building images
#   -h, --help             Show this help
# ═══════════════════════════════════════════════════════════════

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Defaults (can be overridden by .env)
ENABLE_OBSERVABILITY=true
ENABLE_METRICS=true
ENABLE_LOGGING=true
CLEAN_START=false
NO_BUILD=false
SHOW_HELP=false

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"


# Functions

show_help() {
printf "${CYAN}PROSD System Deployment v1.0${NC}

${YELLOW}USAGE:${NC}
    ./setup.sh [OPTIONS]

${YELLOW}OPTIONS:${NC}
    -o, --observability    Enable full observability stack (default)
    -m, --metrics          Enable metrics only (Prometheus + exporters)
    -l, --logging          Enable logging only (Loki)
    --no-observability     Disable all observability components
    --no-metrics           Disable metrics collection
    --no-logging           Disable log aggregation
    -c, --clean            Clean start: remove volumes & containers
    -n, --no-build         Skip building Docker images
    -h, --help             Show this help message

${YELLOW}EXAMPLES:${NC}
    ./setup.sh                          # Full deployment
    ./setup.sh --no-observability       # App only, minimal resources
    ./setup.sh -m -l                    # Metrics + Logging, no Grafana
    ./setup.sh -c                       # Clean start with defaults
    ./setup.sh -c --no-observability    # Clean start, app only

${YELLOW}DOCKER PROFILES:${NC}
    observability    - Full stack: Grafana + Prometheus + Loki
    metrics          - Prometheus + exporters only
    logging          - Loki only
"
exit 0
}

log_info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[✓]${NC} $*"; }
log_warn()    { echo -e "${YELLOW}[!]${NC} $*"; }
log_error()   { echo -e "${RED}[✗]${NC} $*"; }

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if docker compose version &> /dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
        log_success "Docker Compose v2 found"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        log_success "Docker Compose v1 found"
    else
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Verify Docker is running
    if ! $COMPOSE_CMD version &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "All prerequisites met"
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -o|--observability)
                ENABLE_OBSERVABILITY=true
                ENABLE_METRICS=true
                ENABLE_LOGGING=true
                shift
                ;;
            -m|--metrics)
                ENABLE_OBSERVABILITY=false
                ENABLE_METRICS=true
                ENABLE_LOGGING=false
                shift
                ;;
            -l|--logging)
                ENABLE_OBSERVABILITY=false
                ENABLE_METRICS=false
                ENABLE_LOGGING=true
                shift
                ;;
            --no-observability)
                ENABLE_OBSERVABILITY=false
                ENABLE_METRICS=false
                ENABLE_LOGGING=false
                shift
                ;;
            --no-metrics)
                ENABLE_METRICS=false
                shift
                ;;
            --no-logging)
                ENABLE_LOGGING=false
                shift
                ;;
            -c|--clean)
                CLEAN_START=true
                shift
                ;;
            -n|--no-build)
                NO_BUILD=true
                shift
                ;;
            -h|--help)
                SHOW_HELP=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use -h for help"
                exit 1
                ;;
        esac
    done
    
    # Observability implies both metrics and logging
    if [[ "$ENABLE_OBSERVABILITY" == "true" ]]; then
        ENABLE_METRICS=true
        ENABLE_LOGGING=true
    fi
}

load_env() {
    local env_file="$PROJECT_ROOT/.env"

    if [[ -f "$env_file" ]]; then
        log_info "Loading environment from $env_file"
        # Export for docker compose --env-file
        export COMPOSE_ENV_FILE="$env_file"
        # Also source for script-local variable access
        set -a
        source "$env_file"
        set +a
        log_success "Environment loaded"
    else
        log_warn ".env not found at $env_file, using defaults"
        # Set default for compose even if file missing
        export COMPOSE_ENV_FILE="$PROJECT_ROOT/.env"
    fi
}

get_compose_profiles() {
    local profiles=()
    
    if [[ "$ENABLE_OBSERVABILITY" == "true" ]]; then
        profiles+=("observability")
    else
        [[ "$ENABLE_METRICS" == "true" ]] && profiles+=("metrics")
        [[ "$ENABLE_LOGGING" == "true" ]] && profiles+=("logging")
    fi
    
    if [[ ${#profiles[@]} -gt 0 ]]; then
        echo "${profiles[*]}" | tr ' ' ','
    fi
}

clean_environment() {
    if [[ "$CLEAN_START" != "true" ]]; then
        return
    fi
    
    log_info "Cleaning previous deployment..."
    
    if [[ -f "$SCRIPT_DIR/docker-compose.yml" ]]; then
        $COMPOSE_CMD --env-file "${COMPOSE_ENV_FILE:-$PROJECT_ROOT/.env}" \
            -f "$SCRIPT_DIR/docker-compose.yml" down -v --remove-orphans 2>/dev/null || true
    fi
    
    docker volume prune -f 2>/dev/null || true
    log_success "Clean complete"
}

build_images() {
    if [[ "$NO_BUILD" == "true" ]]; then
        log_info "Skipping image build (using existing)"
        return
    fi
    
    log_info "Building Docker images..."
    
    if [[ -f "$SCRIPT_DIR/docker-compose.yml" ]]; then
        $COMPOSE_CMD --env-file "${COMPOSE_ENV_FILE:-$PROJECT_ROOT/.env}" \
            -f "$SCRIPT_DIR/docker-compose.yml" build
    else
        log_error "docker-compose.yml not found in $SCRIPT_DIR"
        exit 1
    fi
    
    log_success "Build complete"
}

start_services() {
    local profiles=$(get_compose_profiles)
    
    log_info "Starting services..."
    
    local compose_base="$COMPOSE_CMD --env-file ${COMPOSE_ENV_FILE:-$PROJECT_ROOT/.env} -f $SCRIPT_DIR/docker-compose.yml"
    
    if [[ -n "$profiles" ]]; then
        log_info "Using profiles: ${CYAN}$profiles${NC}"
        $compose_base --profile "$profiles" up -d
    else
        log_info "No observability profiles enabled"
        $compose_base up -d
    fi
    
    log_success "Services started"
}

wait_for_health() {
    log_info "Waiting for services to be healthy..."
    sleep 20
    
    local compose_ps="$COMPOSE_CMD --env-file ${COMPOSE_ENV_FILE:-$PROJECT_ROOT/.env} -f $SCRIPT_DIR/docker-compose.yml ps"
    
    local core_services=("postgres" "rabbitmq" "minio" "gateway" "frontend")
    for svc in "${core_services[@]}"; do
        if $compose_ps 2>/dev/null | grep -q "$svc.*Up\|running"; then
            log_success "✓ $svc"
        else
            log_warn "○ $svc (starting)"
        fi
    done
    
    if [[ "$ENABLE_OBSERVABILITY" == "true" || "$ENABLE_METRICS" == "true" || "$ENABLE_LOGGING" == "true" ]]; then
        echo ""
        log_info "Observability services:"
        [[ "$ENABLE_METRICS" == "true" || "$ENABLE_OBSERVABILITY" == "true" ]] && \
            $compose_ps 2>/dev/null | grep -q "prometheus.*Up" && log_success "✓ Prometheus" || log_warn "○ Prometheus"
        [[ "$ENABLE_LOGGING" == "true" || "$ENABLE_OBSERVABILITY" == "true" ]] && \
            $compose_ps 2>/dev/null | grep -q "loki.*Up" && log_success "✓ Loki" || log_warn "○ Loki"
        [[ "$ENABLE_OBSERVABILITY" == "true" ]] && \
            $compose_ps 2>/dev/null | grep -q "grafana.*Up" && log_success "✓ Grafana" || log_warn "○ Grafana"
    fi
}

show_access_info() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}  ${CYAN}🎉 PROSD Deployment Complete!${NC}                 ${GREEN}║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo -e "${BLUE}📱 Application:${NC}"
    echo "   Frontend:     http://localhost:${FRONTEND_PORT:-3000}"
    echo "   API Gateway:  http://localhost:${GATEWAY_PORT:-5000}"
    echo "   Health Check: http://localhost:${GATEWAY_PORT:-5000}/health"
    echo ""
    
    if [[ "$ENABLE_OBSERVABILITY" == "true" || "$ENABLE_METRICS" == "true" || "$ENABLE_LOGGING" == "true" ]]; then
        echo -e "${BLUE}📊 Observability:${NC}"
        [[ "$ENABLE_METRICS" == "true" || "$ENABLE_OBSERVABILITY" == "true" ]] && \
            echo "   Prometheus:   http://localhost:${PROMETHEUS_PORT:-9090}"
        [[ "$ENABLE_LOGGING" == "true" || "$ENABLE_OBSERVABILITY" == "true" ]] && \
            echo "   Loki:         http://localhost:${LOKI_PORT:-3100}"
        [[ "$ENABLE_OBSERVABILITY" == "true" ]] && \
            echo "   Grafana:      http://localhost:${GRAFANA_PORT:-3001} (admin/${GRAFANA_ADMIN_PASSWORD:-admin123})"
        echo ""
    fi
    
    echo -e "${BLUE}📦 Infrastructure:${NC}"
    echo "   RabbitMQ:     http://localhost:${RABBITMQ_MANAGEMENT_PORT:-15672} (${RABBITMQ_DEFAULT_USER:-guest}/${RABBITMQ_DEFAULT_PASS:-guest})"
    echo "   MinIO:        http://localhost:${MINIO_CONSOLE_PORT:-9001} (${MINIO_ROOT_USER:-minioadmin})"
    echo "   PostgreSQL:   ${DB_HOST:-postgres}:${DB_PORT:-5432}"
    echo ""
    
    echo -e "${YELLOW}📝 Useful Commands:${NC}"
    echo "   View logs:     $COMPOSE_CMD logs -f [service]"
    echo "   Stop:          $COMPOSE_CMD down"
    echo "   Restart:       $COMPOSE_CMD restart [service]"
    echo "   Status:        $COMPOSE_CMD ps"
    echo "   Clean rebuild: $COMPOSE_CMD down -v && ./setup.sh -c"
    echo ""
}


# Main Execution

main() {
    load_env
    parse_args "$@"
    
    if [[ "$SHOW_HELP" == "true" ]]; then
        show_help
    fi
    
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  ${GREEN}PROSD System Deployment${NC}                       ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo -e "${YELLOW}Configuration:${NC}"
    echo "   Observability: ${ENABLE_OBSERVABILITY}"
    echo "   Metrics:       ${ENABLE_METRICS}"
    echo "   Logging:       ${ENABLE_LOGGING}"
    echo "   Clean Start:   ${CLEAN_START}"
    echo "   Skip Build:    ${NO_BUILD}"
    echo ""
    
    check_prerequisites
    clean_environment
    build_images
    start_services
    wait_for_health
    show_access_info
}

main "$@"