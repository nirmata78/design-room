workspace "SD-03 · Event counting and billing rollups" "Count ad impressions and clicks once: live for the dashboard, exact and versioned for the bill." {

    # One workspace for every C4 picture of SD-03 (video and Markdown). Drawn by .claude/skills/c4-structurizr (native renderer;
    # placement is the "grid" of each view in views.json, so the autoLayout lines below only matter to Structurizr tools):
    #   render_c4.py --dsl workspace.dsl --spec views.json --out video/svg
    # Version deltas (V1 … V4), flows, challenge break/fix views and the recap are all derived in views.json from the
    # one master container view below, so every box keeps its pixel position from V1 to the recap.

    !identifiers hierarchical
    !impliedRelationships false

    model {
        cli   = softwareSystem "Ad clients" "SDKs, browsers, ad servers." "External"
        adv   = person "Advertiser" "Watches campaigns; is billed."
        fraud = softwareSystem "Fraud system" "Flags invalid traffic." "External"
        invo  = softwareSystem "Invoicing" "Bills final hours." "External"

        ac = softwareSystem "Ad event counting" "Live counts; exact hourly totals." {
            col    = container "Collector" "Validate, stamp, append." "Go" "App"
            log    = container "Event log" "The one copy: 1,024 partitions, by event ID." "Kafka" "Queue"
            stream = container "Live aggregator" "Dedup, combine, windows." "Flink" "App" {
                src   = component "Kafka source" "Offsets in the checkpoint." "Flink"
                time  = component "Time assigner" "Clamps time; watermarks." "Flink"
                dedup = component "Deduplicator" "Seen IDs in RocksDB, 10 min."  "Flink"
                comb  = component "Combiner" "Partial sums every 1 s." "Flink"
                win   = component "Window counter" "Ad × minute, early fires." "Flink"
                sink  = component "Store sink" "Versioned rows." "Flink"
                ckpt  = component "Checkpoints" "State + offsets, 30 s." "GCS" "Bucket"
            }
            live   = container "Live store" "Versioned minutes." "ClickHouse" "Database"
            lake   = container "Event lake" "Parquet, by event hour." "Iceberg" "Database"
            batch  = container "Billing job" "Same code, exact, per hour." "Flink batch" "App" {
                close = component "Hour closer" "Closes at H + 48 h." "Scheduler"
                read  = component "Reader" "Pinned hour H." "Iceberg"
                xdup  = component "Exact dedup" "First copy per ID." "Flink"
                filt  = component "Invalid filter" "Pinned invalid list." "Flink"
                price = component "Price and sum" "Integer micros." "Flink"
                write = component "Writer" "Commits v + 1." "Iceberg"
                adj   = component "Adjuster" "New minus invoiced." "Flink"
                recon = component "Reconciler" "Live vs final, hourly." "Flink"
            }
            bill   = container "Billing tables" "Hour × version." "Iceberg" "Database"
            api    = container "Reporting API" "Live hours and final hours." "Go" "App"
        }

        # ── L1 context ── arrows point from the user to what it uses (C4 "uses" direction), which also keeps the layout shallow
        cli -> ac "Sends events, batched" "HTTPS"
        adv -> ac "Reads dashboards and bills" "HTTPS"
        fraud -> ac "Invalidates events, late" "Kafka topic"
        invo -> ac "Reads final hours" "Batch, daily"

        # ── L2 containers ──
        cli -> ac.col "POST /v1/events" "HTTPS"
        ac.col -> ac.log "Appends, acks=all" "Kafka"
        ac.lake -> ac.log "Loads files every 5 min" "Kafka Connect"
        ac.stream -> ac.log "Consumes" "Kafka"
        ac.stream -> ac.live "Upserts minute rows" "SQL insert"
        ac.batch -> ac.lake "Reads hour H"
        ac.batch -> ac.bill "Writes v+1"
        adv -> ac.api "Dashboards" "HTTPS"
        ac.api -> ac.live "Open hours" "SQL"
        ac.api -> ac.bill "Final hours" "SQL"
        fraud -> ac.batch "Invalidations" "Kafka topic"

        # ── the alternate path (chapter 5): below ~200,000 events/s one ClickHouse cluster is buffer, truth and dashboard.
        # Tagged so the master container view leaves it out.
        ac.col -> ac.live "Inserts with dedup token" "SQL" "Alternate"

        # ── L3 live aggregator ──
        ac.stream.src -> ac.log "Reads partitions"
        ac.stream.src -> ac.stream.time "Events"
        ac.stream.time -> ac.stream.dedup "Keyed by ID"
        ac.stream.dedup -> ac.stream.comb "First copies"
        ac.stream.comb -> ac.stream.win "Partial sums"
        ac.stream.win -> ac.stream.sink "Early, on time, late"
        ac.stream.sink -> ac.live "Rows (ad, min, v)"
        ac.stream.dedup -> ac.stream.ckpt "Snapshots state"

        # ── L3 billing job ──
        ac.batch.read -> ac.lake "Reads hour H"
        ac.batch.close -> ac.batch.read "Manifest"
        ac.batch.read -> ac.batch.xdup "Events"
        ac.batch.xdup -> ac.batch.filt "Unique events"
        fraud -> ac.batch.filt "Invalid IDs"
        ac.batch.filt -> ac.batch.price "Valid events"
        ac.batch.price -> ac.batch.write "Hour totals"
        ac.batch.write -> ac.bill "Version v+1"
        ac.batch.write -> ac.batch.adj "New version"
        invo -> ac.batch.adj "Pulls adjustments"
        ac.batch.recon -> ac.batch.write "Final totals"
        ac.batch.recon -> ac.live "Live totals, hour H"
    }

    views {
        systemContext ac "c4-context" "Ad event counting — system context" {
            include *
            autoLayout lr 260 140
        }

        # The master container view: every container that ever appears. V1 … V4 are filters of it (views.json).
        container ac "containers" "Ad event counting — containers" {
            include cli adv fraud ac.col ac.log ac.stream ac.live ac.lake ac.batch ac.bill ac.api
            exclude "relationship.tag==Alternate"
            autoLayout tb 80 30
        }

        # Chapter 5: the one-cluster design, drawn on its own (it is a different system, not a delta of V3).
        container ac "alt" "Ad event counting — the one-cluster alternate" {
            include cli adv ac.col ac.live ac.api
            autoLayout lr 200 80
        }

        component ac.stream "comp-stream" "Live aggregator — components" {
            include ac.log ac.stream.src ac.stream.time ac.stream.dedup ac.stream.comb ac.stream.win ac.stream.sink ac.stream.ckpt ac.live
            autoLayout lr 160 120
        }

        component ac.batch "comp-billing" "Billing job — components" {
            include ac.lake fraud invo ac.bill ac.batch.close ac.batch.read ac.batch.xdup ac.batch.filt ac.batch.price ac.batch.write ac.batch.adj ac.batch.recon ac.live
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
