workspace "SD-25 · Rate limiter (distributed)" "Per-customer quotas enforced across 500 API servers in three regions, in under a millisecond." {

    # One workspace for every C4 picture of SD-25 (video and Markdown). Drawn by .claude/skills/c4-structurizr (native renderer;
    # placement is the "grid" of each view in views.json, so the autoLayout lines below only matter to Structurizr tools):
    #   render_c4.py --dsl workspace.dsl --spec views.json --out video/svg
    # Version deltas (V1 … V4), flows, challenge break/fix views and the recap are all derived in views.json from the
    # one master container view below, so every box keeps its pixel position from V1 to the recap.

    !identifiers hierarchical
    !impliedRelationships false

    model {
        cli   = softwareSystem "API clients" "Customers' apps and jobs." "External"
        team  = person "Account team" "Sets limits; answers why."
        be    = softwareSystem "Backend services" "Serve admitted requests." "External"
        meter = softwareSystem "Usage metering" "Bills from request logs." "External"
        peer  = softwareSystem "Other regions" "Their quota services." "External"

        rl = softwareSystem "API rate limiting" "Per-customer quotas, fleet-wide." {
            api = container "API server" "Auth, limit, route." "Go + limiter" "App" {
                handler = component "Request handler" "Auth, limit, route." "Go"
                pcache  = component "Policy cache" "Last-known-good on disk." "Go"
                bucket  = component "Local buckets" "Tokens, lease per key." "Go"
                exact   = component "Exact client" "Script, 2 ms timeout." "Go"
                sync    = component "Share syncer" "Batches every 100 ms." "Go"
                fallb   = component "Fallback" "Last lease, then floor." "Go"
                dsamp   = component "Decision recorder" "Every 429; 1 % of allows." "Go"
            }
            store  = container "Limit store" "Exact keys only." "Redis" "Database"
            quota  = container "Quota service" "Leases by demand." "Go" "App"
            pol    = container "Policy service" "Versions; staged rollout." "Go" "App"
            pdb    = container "Policy store" "Versioned limits." "PostgreSQL" "Database"
            dlog   = container "Decision log" "Every 429; 1 % of allows." "Kafka" "Queue"
            dstore = container "Decision store" "Why was I limited?" "ClickHouse" "Database"
        }

        # ── L1 context ── arrows point from the user to what it uses (C4 "uses" direction)
        cli -> rl "Calls the API" "HTTPS"
        rl -> be "Forwards admitted requests" "gRPC"
        team -> rl "Sets limits; asks why" "HTTPS"
        meter -> rl "Reads request logs" "Kafka topic"

        # ── L2 containers ──
        cli -> rl.api "Calls the API" "HTTPS"
        rl.api -> be "Admitted requests" "gRPC"
        rl.api -> rl.store "Token bucket script" "RESP"
        rl.api -> rl.pol "Watches policies" "gRPC stream"
        rl.pol -> rl.pdb "Versions" "SQL"
        team -> rl.pol "Sets limits; asks why" "HTTPS"
        rl.api -> rl.quota "Demand; leases" "gRPC, 100 ms"
        rl.quota -> peer "Regional totals" "gRPC, 2 s"
        rl.api -> rl.dlog "Appends decisions" "Kafka"
        rl.dstore -> rl.dlog "Loads" "Kafka"
        rl.pol -> rl.dstore "Explains a 429" "SQL"

        # ── L3 API server: the limiter library ──
        cli -> rl.api.handler "Requests" "HTTPS"
        rl.api.handler -> be "Admitted" "gRPC"
        rl.api.handler -> rl.api.pcache "Policy for key"
        rl.api.handler -> rl.api.bucket "Takes tokens"
        rl.api.handler -> rl.api.exact "Exact-mode keys"
        rl.api.handler -> rl.api.dsamp "Decision"
        rl.api.pcache -> rl.pol "Watches versions" "gRPC stream"
        rl.api.sync -> rl.api.bucket "Sets leases"
        rl.api.sync -> rl.quota "Demand; leases" "gRPC"
        rl.api.fallb -> rl.api.bucket "Floors old leases"
        rl.api.fallb -> rl.api.sync "Watches sync age"
        rl.api.exact -> rl.store "Script" "RESP"
        rl.api.dsamp -> rl.dlog "Appends" "Kafka"
    }

    views {
        systemContext rl "c4-context" "API rate limiting — system context" {
            include rl cli team be meter
            autoLayout lr 260 140
        }

        # The master container view: every container that ever appears. V1 … V4 are filters of it (views.json).
        container rl "containers" "API rate limiting — containers" {
            include cli team be peer rl.api rl.store rl.quota rl.pol rl.pdb rl.dlog rl.dstore
            autoLayout tb 80 30
        }

        # Chapter 5: one Redis and one script, drawn on its own (a different, smaller system, not a delta of V4).
        container rl "alt" "API rate limiting — the one-Redis alternate" {
            include cli be rl.api rl.store
            autoLayout lr 200 80
        }

        component rl.api "comp-api" "API server — the limiter's components" {
            include cli be rl.pol rl.quota rl.store rl.dlog rl.api.handler rl.api.pcache rl.api.bucket rl.api.exact rl.api.sync rl.api.fallb rl.api.dsamp
            autoLayout lr 160 120
        }

        !include ../../.claude/skills/c4-structurizr/resources/c4-google-tokens.dsl

        styles {
            relationship "Relationship" {
                routing Direct
                fontSize 40
                width 300
            }
            element "Boundary" {
                fontSize 32
            }
            element "Person" {
                width 400
                height 300
            }
            element "Element" {
                width 400
                height 240
                fontSize 40
            }
        }
    }
}
