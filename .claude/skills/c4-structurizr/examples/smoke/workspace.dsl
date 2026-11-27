workspace "Multi-Domain Smoke Suite" "3 distinct system-design archetypes for C3-05 verification." {

    !identifiers hierarchical

    model {
        # ── Archetype 1: Transactional Microservices (Ledger + Outbox) ──
        client1 = person "Client App" "Submits idempotent transfer requests." "Person"
        psp1    = softwareSystem "Payment Rail" "Executes external settlements." "External"
        ms      = softwareSystem "Transfer Service" "Transactional microservices with outbox." {
            api1 = container "Transfer API" "Validates Idempotency-Key." "Go"
            db1  = container "Ledger DB" "Double-entry + outbox table." "PostgreSQL 16" "Database"
            wrk1 = container "Outbox Relay" "Drains pending transfers." "Go Worker"
        }
        client1 -> ms.api1 "POST /transfers" "HTTPS" "HTTPS"
        ms.api1 -> ms.db1 "Insert entry + outbox" "SQL" "Internal"
        ms.db1  -> ms.wrk1 "TransferQueued" "Outbox Event" "Event"
        ms.wrk1 -> psp1 "POST /v1/settle" "HTTPS" "HTTPS"

        # ── Archetype 2: Event / Streaming Data Platform ──
        iot = softwareSystem "Edge Sensors" "Emits telemetry events." "External"
        bi  = person "Data Analyst" "Queries real-time dashboards." "Person"
        dp  = softwareSystem "Telemetry Platform" "Real-time event ingestion and analytics." {
            gw   = container "Ingest Gateway" "Auth, schema check, batching." "Rust"
            bus  = container "Event Bus" "Partitioned durable log." "Kafka" "Queue"
            strm = container "Stream Processor" "Windowed rollups and alerts." "Flink"
            olap = container "Analytics Store" "Columnar real-time OLAP." "ClickHouse" "Database"
        }
        iot     -> dp.gw "Telemetry batch" "HTTPS" "HTTPS"
        dp.gw   -> dp.bus "Produce events" "Kafka" "Event"
        dp.bus  -> dp.strm "Consume partitions" "Kafka" "Event"
        dp.strm -> dp.olap "Write rollups" "Batch" "File"
        bi      -> dp.olap "SQL queries" "HTTPS" "HTTPS"

        # ── Archetype 3: Edge / Multi-Tier Caching Architecture ──
        usr3 = person "End User" "Reads product catalog pages." "Person"
        edge = softwareSystem "Global CDN" "Edge PoP HTTP caching." "External"
        cat  = softwareSystem "Catalog Platform" "Low-latency read-heavy catalog." {
            svc3   = container "Catalog Service" "Serves reads and invalidations." "Go"
            cache3 = container "Read Cache" "Hot key-value cache (TTL 60s)." "Redis" "Cache"
            db3    = container "Catalog DB" "Authoritative product store." "PostgreSQL" "Database"
        }
        usr3   -> edge "GET /items/{id}" "HTTPS" "HTTPS"
        edge   -> cat.svc3 "Origin miss" "HTTPS" "HTTPS"
        cat.svc3 -> cat.cache3 "GET / SET hot key" "Redis" "Sync"
        cat.svc3 -> cat.db3 "Read on cache miss" "SQL" "Internal"
    }

    views {
        container ms "smoke-01-microservices" "Archetype 1 — Transactional Microservices + Outbox" {
            include *
            autoLayout lr 90 60
        }

        container dp "smoke-02-streaming-data" "Archetype 2 — Event-Driven Streaming Data Platform" {
            include *
            autoLayout lr 90 60
        }

        container cat "smoke-03-edge-caching" "Archetype 3 — Edge CDN + Multi-Tier Caching" {
            include *
            autoLayout lr 90 60
        }

        !include ../../resources/c4-google-tokens.dsl
    }
}
