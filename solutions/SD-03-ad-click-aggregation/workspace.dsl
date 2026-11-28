workspace "SD-03 · Event counting and billing rollups" "Count ad impressions and clicks once: live for the dashboard, exact and versioned for the bill." {

    # One workspace for every C4 picture of SD-03 (video and Markdown). Rendered by .claude/skills/c4-structurizr:
    #   render_c4.py --dsl workspace.dsl --spec views.json --out video/svg
    # Version deltas (V1 … V4), flows, challenge break/fix views and the recap are all derived in views.json from the
    # one master container view below, so every box keeps its pixel position from V1 to the recap.

    !identifiers hierarchical
    !impliedRelationships false

    model {
        cli   = softwareSystem "Ad clients" "SDKs, browsers, ad servers." "External"
        adv   = person "Advertiser" "Watches campaigns; is billed."
        fraud = softwareSystem "Fraud system" "Flags invalid traffic, late." "External"
        invo  = softwareSystem "Invoicing" "Turns final hours into bills." "External"

        ac = softwareSystem "Ad event counting" "Live counts; exact hourly totals." {
            col    = container "Collector" "Validate, stamp, append." "Go on Kubernetes"
            log    = container "Event log" "The one copy, by event ID." "Kafka, 1,024 partitions" "Queue"
            stream = container "Live aggregator" "Dedup, combine, windows." "Flink, streaming" {
                src   = component "Kafka source" "Offsets in the checkpoint." "Flink source"
                time  = component "Time assigner" "Clamp; watermark." "Event time"
                dedup = component "Deduplicator" "Seen IDs, TTL 10 min." "Keyed state"
                comb  = component "Combiner" "Partial sums every 1 s." "Per subtask"
                win   = component "Window counter" "Ad × minute, early fires." "Event time"
                sink  = component "Store sink" "Versioned rows." "Flink sink"
                ckpt  = component "Checkpoints" "State + offsets, 30 s." "Object storage" "Database"
            }
            live   = container "Live store" "Minute rows, by version." "ClickHouse" "Database"
            lake   = container "Event lake" "Parquet, by event hour." "Iceberg on GCS" "Database"
            batch  = container "Billing job" "Same code, exact, per hour." "Flink, batch mode" {
                close = component "Hour closer" "At H + 48 h; dirty hours." "Scheduler"
                read  = component "Reader" "Hour H, pinned snapshot." "Iceberg scan"
                xdup  = component "Exact dedup" "First copy per ID." "Batch operator"
                filt  = component "Invalid filter" "Pinned invalid list." "Anti-join"
                price = component "Price and sum" "Integer micros." "Batch operator"
                write = component "Writer" "Commits version v + 1." "Iceberg commit"
                adj   = component "Adjuster" "New minus invoiced." "Batch operator"
                recon = component "Reconciler" "Live against final, per hour." "Batch operator"
            }
            bill   = container "Billing tables" "Hour × version." "Iceberg, versioned" "Database"
            api    = container "Reporting API" "Live hours and final hours." "Go on Kubernetes"
        }

        # ── L1 context ── arrows point from the user to what it uses (C4 "uses" direction), which also keeps the layout shallow
        cli -> ac "Sends events, batched" "" "HTTPS"
        adv -> ac "Reads dashboards" "" "HTTPS"
        fraud -> ac "Invalidates events" "" "Event"
        invo -> ac "Reads final hours" "" "Batch"

        # ── L2 containers ──
        cli -> ac.col "POST /v1/events" "" "HTTPS"
        ac.col -> ac.log "Appends, acks=all" "" "Sync"
        ac.lake -> ac.log "Loads files every 5 min" "" "Batch"
        ac.stream -> ac.log "Consumes" "" "Event"
        ac.stream -> ac.live "Upserts minute rows" "" "Internal"
        ac.batch -> ac.lake "Reads hour H" "" "Batch"
        ac.batch -> ac.bill "Writes v + 1" "" "Internal"
        adv -> ac.api "Dashboards" "" "HTTPS"
        ac.api -> ac.live "Open hours" "" "Internal"
        ac.api -> ac.bill "Final hours" "" "Internal"
        fraud -> ac.batch "Invalidations" "" "Event"

        # ── the alternate path (chapter 5): below ~200,000 events/s one ClickHouse cluster is buffer, truth and dashboard.
        # Tagged so the master container view leaves it out.
        ac.col -> ac.live "Inserts with dedup token" "" "Internal,Alternate"

        # ── L3 live aggregator ──
        ac.stream.src -> ac.log "Reads partitions" "" "Event"
        ac.stream.src -> ac.stream.time "Events" "" "Internal"
        ac.stream.time -> ac.stream.dedup "Keyed by ID" "" "Internal"
        ac.stream.dedup -> ac.stream.comb "First copies" "" "Internal"
        ac.stream.comb -> ac.stream.win "Partial sums" "" "Internal"
        ac.stream.win -> ac.stream.sink "Early, on time, late" "" "Internal"
        ac.stream.sink -> ac.live "Rows (ad, min, v)" "" "Internal"
        ac.stream.dedup -> ac.stream.ckpt "Snapshots state" "" "Batch"

        # ── L3 billing job ──
        ac.batch.read -> ac.lake "Reads hour H" "" "Batch"
        ac.batch.close -> ac.batch.read "Manifest" "" "Internal"
        ac.batch.read -> ac.batch.xdup "Events" "" "Internal"
        ac.batch.xdup -> ac.batch.filt "Unique events" "" "Internal"
        fraud -> ac.batch.filt "Invalid IDs" "" "Event"
        ac.batch.filt -> ac.batch.price "Valid events" "" "Internal"
        ac.batch.price -> ac.batch.write "Hour totals" "" "Internal"
        ac.batch.write -> ac.bill "Version v + 1" "" "Internal"
        ac.batch.write -> ac.batch.adj "New version" "" "Internal"
        invo -> ac.batch.adj "Pulls adjustments" "" "Batch"
        ac.batch.recon -> ac.batch.write "Final totals" "" "Internal"
        ac.batch.recon -> ac.live "Live totals, hour H" "" "Internal"
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
