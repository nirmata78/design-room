#!/usr/bin/env bash
# Manage the containerized Structurizr Playwright runtime (zero host Java/Browser deps).
# Usage:
#   c4_runtime.sh ensure      # pull/build local/structurizr-c4:playwright once + start warm daemon
#   c4_runtime.sh start       # start warm daemon mounting WORKSPACE_ROOT (default: git root or PWD)
#   c4_runtime.sh stop        # stop and remove warm daemon
#   c4_runtime.sh status      # print image and daemon state
#   c4_runtime.sh healthcheck # validate + export a minimal DSL via docker exec and report timing
#   c4_runtime.sh exec <args> # run /usr/local/structurizr.sh <args> inside the warm daemon
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${C4_STRUCTURIZR_IMAGE:-local/structurizr-c4:playwright}"
UPSTREAM="${C4_STRUCTURIZR_UPSTREAM:-structurizr/structurizr:preview}"
CONTAINER="${C4_STRUCTURIZR_CONTAINER:-structurizr-c4-daemon}"
LOCAL_WAR="${C4_STRUCTURIZR_WAR:-$HOME/Projects/structurizr/structurizr-application/target/structurizr-1.0.0.war}"
WORKSPACE_ROOT="${C4_WORKSPACE_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

require_docker() {
    docker info >/dev/null 2>&1 || { echo "ERROR: Docker daemon is not running." >&2; exit 1; }
}

build_image() {
    if docker image inspect "$IMAGE" >/dev/null 2>&1; then
        return 0
    fi

    echo "[c4_runtime] Checking upstream image: $UPSTREAM"
    if docker pull "$UPSTREAM" >/dev/null 2>&1; then
        echo "[c4_runtime] Building font-hermetic layer $IMAGE over $UPSTREAM ..."
        docker build -q -f "$SKILL_DIR/docker/Dockerfile.c4" \
            --build-arg "BASE_IMAGE=$UPSTREAM" \
            -t "$IMAGE" "$SKILL_DIR"
        return 0
    fi

    echo "[c4_runtime] Upstream $UPSTREAM unavailable; building locally from WAR ($LOCAL_WAR)..."
    if [[ ! -f "$LOCAL_WAR" ]]; then
        echo "ERROR: Local Structurizr WAR not found at $LOCAL_WAR" >&2
        exit 1
    fi
    tmpctx="$(mktemp -d)"
    trap 'rm -rf "$tmpctx"' RETURN
    cp "$LOCAL_WAR" "$tmpctx/structurizr.war"
    cp -r "$SKILL_DIR/resources/fonts" "$tmpctx/fonts"
    cat << 'EOF' > "$tmpctx/structurizr.sh"
#!/bin/bash
if [ "$#" -eq 0 ]; then
    java --enable-native-access=ALL-UNNAMED -jar /usr/local/structurizr.war help
    exit 1
fi
java -Dserver.port=${PORT:-8080} -Dio.netty.noUnsafe=true --enable-native-access=ALL-UNNAMED -jar /usr/local/structurizr.war "$@"
EOF
    docker build -q -f "$SKILL_DIR/docker/Dockerfile.local-war" -t "$IMAGE" "$tmpctx"
}

start_daemon() {
    if docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
        # Verify mount matches WORKSPACE_ROOT
        cur_mount="$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/workspace"}}{{.Source}}{{end}}{{end}}' "$CONTAINER" 2>/dev/null || true)"
        if [[ "$cur_mount" == "$WORKSPACE_ROOT" ]]; then
            return 0
        fi
        docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
    elif docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER"; then
        docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
    fi

    echo "[c4_runtime] Starting warm container $CONTAINER (mount: $WORKSPACE_ROOT -> /workspace)..."
    docker run -d \
        --name "$CONTAINER" \
        --restart unless-stopped \
        --shm-size=1gb \
        -v "$WORKSPACE_ROOT:/workspace" \
        --entrypoint tail \
        "$IMAGE" -f /dev/null >/dev/null
}

run_exec() {
    start_daemon
    docker exec "$CONTAINER" /usr/local/structurizr.sh "$@"
}

run_healthcheck() {
    require_docker
    build_image
    start_daemon
    t0="$(python3 -c 'import time; print(time.time())')"
    tmpd="$WORKSPACE_ROOT/.c4-healthcheck-$$"
    mkdir -p "$tmpd/out"
    trap 'rm -rf "$tmpd"' RETURN
    cat << 'EOF' > "$tmpd/hc.dsl"
workspace "Healthcheck" {
    model {
        u = person "User"
        s = softwareSystem "System"
        u -> s "Uses"
    }
    views {
        systemContext s "hc-ctx" {
            include *
            autoLayout lr
        }
    }
}
EOF
    rel="/workspace/.c4-healthcheck-$$"
    docker exec "$CONTAINER" /usr/local/structurizr.sh validate -w "$rel/hc.dsl" >/dev/null
    docker exec "$CONTAINER" /usr/local/structurizr.sh export -w "$rel/hc.dsl" -f svg -o "$rel/out" >/dev/null
    test -s "$tmpd/out/hc-ctx.svg"
    dt="$(python3 -c "import time; print(f'{time.time()-float($t0):.2f}')")"
    echo "[c4_runtime] HEALTHCHECK OK (${dt}s): $IMAGE -> $CONTAINER (hc-ctx.svg $(wc -c < "$tmpd/out/hc-ctx.svg" | tr -d ' ') bytes)"
}

cmd="${1:-status}"
shift || true

case "$cmd" in
    ensure)
        require_docker
        build_image
        start_daemon
        echo "[c4_runtime] Ready: image=$IMAGE container=$CONTAINER mount=$WORKSPACE_ROOT"
        ;;
    start)
        require_docker
        start_daemon
        ;;
    stop)
        require_docker
        docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
        echo "[c4_runtime] Stopped $CONTAINER"
        ;;
    status)
        require_docker
        docker image inspect "$IMAGE" --format 'image={{index .RepoTags 0}} arch={{.Architecture}} size={{.Size}}' 2>/dev/null || echo "image=MISSING"
        docker ps -a --filter "name=^/${CONTAINER}$" --format 'container={{.Names}} status={{.Status}}' 2>/dev/null || true
        ;;
    healthcheck)
        run_healthcheck
        ;;
    exec)
        require_docker
        run_exec "$@"
        ;;
    *)
        echo "Usage: $0 {ensure|start|stop|status|healthcheck|exec ...}" >&2
        exit 2
        ;;
esac
