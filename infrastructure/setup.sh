#!/bin/bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# PROSD System Deployment Script
#
# Usage:
#   ./setup.sh [OPTIONS]               # Deploy stack
#   ./setup.sh down [OPTIONS]          # Safely stop stack
#
# Options (deploy):
#   -o, --observability    Enable full observability (default)
#   -m, --metrics          Enable metrics only
#   -l, --logging          Enable logging only
#   --no-observability     Disable all observability
#   -c, --clean            Clean start (remove volumes)
#   -n, --no-build         Skip building images
#   -h, --help             Show this help
#
# Options (down):
#   -v, --volumes          Remove volumes (clean data)
#   --duration TIME        Silence duration (default: 5m)
# ═══════════════════════════════════════════════════════════════

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# Defaults (for deploy command)
ENABLE_OBSERVABILITY=true
ENABLE_METRICS=true
ENABLE_LOGGING=true
CLEAN_START=false
NO_BUILD=false
SHOW_HELP=false

# Global command mode: "up" or "down"
COMMAND="up"

# Paths (project‑root relative)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
ENV_FILE="$PROJECT_ROOT/.env"

# ──────────────────────────────────────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────────────────────────────────────
log_info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[✓]${NC} $*"; }
log_warn()    { echo -e "${YELLOW}[!]${NC} $*"; }
log_error()   { echo -e "${RED}[✗]${NC} $*"; }

show_help() {
printf "${CYAN}PROSD System Deployment v1.0${NC}

${YELLOW}USAGE:${NC}
    ./setup.sh [OPTIONS]               # Deploy stack
    ./setup.sh down [OPTIONS]          # Safely stop stack

${YELLOW}DEPLOY OPTIONS:${NC}
    -o, --observability    Enable full observability stack (default)
    -m, --metrics          Enable metrics only (Prometheus + exporters)
    -l, --logging          Enable logging only (Loki)
    --no-observability     Disable all observability components
    --no-metrics           Disable metrics collection
    --no-logging           Disable log aggregation
    -c, --clean            Clean start: remove volumes & containers
    -n, --no-build         Skip building Docker images
    -h, --help             Show this help message

${YELLOW}SHUTDOWN OPTIONS:${NC}
    ./setup.sh down [OPTIONS]

    Options for down:
        -v, --volumes    Remove volumes as well (clean data)
        --duration TIME  Silence duration before shutdown (default: 5m)

${YELLOW}EXAMPLES:${NC}
    ./setup.sh                          # Full deployment
    ./setup.sh --no-observability       # App only, minimal resources
    ./setup.sh -c                       # Clean start with defaults
    ./setup.sh down                     # Safe shutdown with 5m silence
    ./setup.sh down -v                  # Safe shutdown and remove volumes
    ./setup.sh down --duration 10m      # Shutdown with 10‑minute silence

${YELLOW}DOCKER PROFILES:${NC}
    observability    - Full stack: Grafana + Prometheus + Loki
    metrics          - Prometheus + exporters only
    logging          - Loki only
"
exit 0
}

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

load_env() {
    if [[ -f "$ENV_FILE" ]]; then
        log_info "Loading base environment from $ENV_FILE"
        set -a
        source "$ENV_FILE"
        set +a
    fi

    LOCAL_ENV="$PROJECT_ROOT/.env.local"
    if [[ -f "$LOCAL_ENV" ]]; then
        log_info "Loading local overrides from $LOCAL_ENV"
        set -a
        source "$LOCAL_ENV"
        set +a
    fi

    # Important: pass correct env file to docker compose
    export COMPOSE_ENV_FILE="${LOCAL_ENV:-$ENV_FILE}"
}

parse_args() {
    # Check if first argument is "down" -> switch to down mode
    if [[ "${1:-}" == "down" ]]; then
        COMMAND="down"
        shift
        # Parse down-specific options
        DOWN_REMOVE_VOLUMES=false
        DOWN_SILENCE_DURATION="5m"
        while [[ $# -gt 0 ]]; do
            case $1 in
                -v|--volumes)
                    DOWN_REMOVE_VOLUMES=true
                    shift
                    ;;
                --duration)
                    DOWN_SILENCE_DURATION="$2"
                    shift 2
                    ;;
                -h|--help)
                    SHOW_HELP=true
                    shift
                    ;;
                *)
                    log_error "Unknown down option: $1"
                    echo "Use -h for help"
                    exit 1
                    ;;
            esac
        done
        return
    fi

    # Otherwise we are in deploy (up) mode
    COMMAND="up"
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

    if [[ -f "$COMPOSE_FILE" ]]; then
        $COMPOSE_CMD --env-file "${COMPOSE_ENV_FILE:-$ENV_FILE}" \
            -f "$COMPOSE_FILE" down -v --remove-orphans 2>/dev/null || true
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

    if [[ -f "$COMPOSE_FILE" ]]; then
        $COMPOSE_CMD --env-file "${COMPOSE_ENV_FILE:-$ENV_FILE}" \
            -f "$COMPOSE_FILE" build
    else
        log_error "docker-compose.yml not found at $COMPOSE_FILE"
        exit 1
    fi

    log_success "Build complete"
}

start_services() {
    local profiles=$(get_compose_profiles)

    log_info "Starting services..."

    local compose_base="$COMPOSE_CMD --env-file ${COMPOSE_ENV_FILE:-$ENV_FILE} -f $COMPOSE_FILE"

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

    local compose_ps="$COMPOSE_CMD --env-file ${COMPOSE_ENV_FILE:-$ENV_FILE} -f $COMPOSE_FILE ps"

    # Core services
    local core_services=("postgres" "minio" "backend")
    for svc in "${core_services[@]}"; do
        if $compose_ps 2>/dev/null | grep -q "$svc.*Up\|running"; then
            log_success "✓ $svc"
        else
            log_warn "○ $svc (starting)"
        fi
    done

    # Workers
    echo ""
    log_info "Worker services:"
    for w in worker-math worker-analyzer worker-profiler worker-generator; do
        if $compose_ps 2>/dev/null | grep -q "$w.*Up"; then
            log_success "✓ $w"
        else
            log_warn "○ $w"
        fi
    done

    # Observability services
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
    echo "   Backend API:  http://localhost:${BACKEND_PORT:-5000}"
    echo "   Health Check: http://localhost:${BACKEND_PORT:-5000}/health"
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
    echo "   MinIO:        http://localhost:${MINIO_CONSOLE_PORT:-9001} (${MINIO_ROOT_USER:-minio_admin})"
    echo "   PostgreSQL:   postgres:${DB_PORT:-5432}"
    echo ""

    echo -e "${YELLOW}📝 Useful Commands:${NC}"
    echo "   View logs:     $COMPOSE_CMD logs -f [service]"
    echo "   Stop:          ./setup.sh down"
    echo "   Restart:       $COMPOSE_CMD restart [service]"
    echo "   Status:        $COMPOSE_CMD ps"
    echo "   Clean rebuild: ./setup.sh down -v && ./setup.sh -c"
    echo ""
}

# ──────────────────────────────────────────────────────────────────────────────
# Safe shutdown (down command) implementation
# ──────────────────────────────────────────────────────────────────────────────
safe_down() {
    local remove_volumes="$1"
    local silence_duration="$2"

    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  ${YELLOW}PROSD System Shutdown${NC}                         ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════╝${NC}"
    echo ""

    log_info "Preparing safe shutdown (alerts will be silenced for ${silence_duration})"

    # Check if Alertmanager container is running
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "prosd_alertmanager"; then
        # Use the backend container (which has curl) to create the silence
        local exec_container="prosd_backend"
        if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "$exec_container"; then
            local start_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
            local end_time
            if date -d "+${silence_duration}" &>/dev/null; then
                end_time=$(date -u -d "+${silence_duration}" +"%Y-%m-%dT%H:%M:%SZ")
            elif date -v "+${silence_duration}" &>/dev/null 2>&1; then
                end_time=$(date -u -v +"${silence_duration}" +"%Y-%m-%dT%H:%M:%SZ")
            else
                end_time=$(date -u -d "+5 minutes" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")
            fi

            log_info "Creating Alertmanager silence for all PROSD alerts via container $exec_container..."
            local silence_response
            
silence_response=$(docker exec -i "$exec_container" curl -s -o /dev/null -w "%{http_code}" \
    -X POST "http://alertmanager:9093/api/v2/silences" \
    -H "Content-Type: application/json" \
    -d @- <<EOF
{
  "matchers": [
    { "name": "cluster", "value": "prosd", "isRegex": false }
  ],
  "startsAt": "$start_time",
  "endsAt": "$end_time",
  "createdBy": "setup.sh",
  "comment": "Planned shutdown of PROSD stack"
}
EOF
)
            if [[ "$silence_response" == "200" || "$silence_response" == "201" ]]; then
                log_success "Silence created (expires at $end_time)"
            else
                log_warn "Could not create silence (HTTP $silence_response). Continuing anyway."
            fi
        else
            log_warn "Container $exec_container not running, cannot create silence via internal network. Continuing anyway."
        fi
    else
        log_warn "Alertmanager is not running, skipping silence creation"
    fi

    log_info "Stopping all services..."
    local compose_base="$COMPOSE_CMD --env-file ${COMPOSE_ENV_FILE:-$ENV_FILE} -f $COMPOSE_FILE"

    if [[ "$remove_volumes" == "true" ]]; then
        log_info "Also removing volumes..."
        $compose_base --profile observability down -v
    else
        $compose_base --profile observability down
    fi

    log_success "All services stopped"
    echo ""
    echo -e "${YELLOW}💡 Tip: To restart, run: ./setup.sh${NC}"
}

# ──────────────────────────────────────────────────────────────────────────────
# Deploy command implementation (up)
# ──────────────────────────────────────────────────────────────────────────────
deploy_stack() {
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

# ──────────────────────────────────────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────────────────────────────────────
main() {
    load_env
    parse_args "$@"

    if [[ "$SHOW_HELP" == "true" ]]; then
        show_help
    fi

    check_prerequisites
    
    if [[ "$COMMAND" == "down" ]]; then
        safe_down "$DOWN_REMOVE_VOLUMES" "$DOWN_SILENCE_DURATION"
        exit 0
    fi

    deploy_stack
}

main "$@"