workspace "C4 Bake-Off Reference" "Four canonical C4 diagram types for progressive video evaluation (10-15s each)." {

    !identifiers hierarchical

    model {
        # ── Actors & External Systems ──
        cus  = person "Customer" "Repays & pays off early." "Person"
        mer  = person "Merchant" "Submits order refunds." "Person,External"
        proc = softwareSystem "Card Processor" "Charges tokens; reports." "External"
        bank = softwareSystem "Bank Rail" "ACH batches & returns." "External"

        # ── Main Software System (L1 Context, L2 Container, L3 Component) ──
        ls = softwareSystem "Loan Servicing" "Schedules, collects, ledger." {
            api = container "Servicing API" "Keys, refunds, quotes." "Go"
            svc = container "Schedule Service" "Schedules & state machine." "Go"
            db  = container "Servicing DB" "Ledger, intents, outbox." "PostgreSQL 16" "Database"
            dsp = container "Rail Dispatcher" "Charges under rail budget." "Go Worker" {
                poll  = component "Outbox Poller" "Claims via SKIP LOCKED." "Go"
                plan  = component "Day Plan" "Windows back from 14:00." "Go"
                bkt   = component "Token Bucket" "90 req/s + pause switch." "Go"
                card  = component "Card Client" "Idempotency-Key calls." "Go"
                batch = component "File Builder" "Validated ACH debit file." "Go"
            }
        }

        # L1 System Context relationships
        cus -> ls "Pays instalments, requests payoff" "HTTPS" "HTTPS"
        mer -> ls "Submits refunds" "HTTPS" "HTTPS"
        ls -> proc "Charges tokens, queries by key" "HTTPS" "HTTPS"
        ls -> bank "Submits debit batch (10:30)" "File" "File"

        # L2 Container relationships
        cus -> ls.api "POST /payoff-quote" "HTTPS" "HTTPS"
        mer -> ls.api "POST /refunds" "HTTPS" "HTTPS"
        ls.api -> ls.svc "Open intent" "gRPC" "Sync"
        ls.svc -> ls.db "Ledger + outbox (1 tx)" "SQL" "Internal"
        ls.db -> ls.dsp "PaymentDue" "Outbox Event" "Event"
        ls.dsp -> proc "POST /v1/charges" "HTTPS" "HTTPS"
        ls.dsp -> bank "Debit batch" "SFTP / File" "File"

        # L3 Component relationships (Dispatcher)
        ls.db -> ls.dsp.poll "Poll outbox" "SKIP LOCKED" "Event"
        ls.dsp.poll -> ls.dsp.bkt "Acquire rail token" "In-process" "Internal"
        ls.dsp.plan -> ls.dsp.bkt "Rate by hour" "In-process" "Internal"
        ls.dsp.bkt -> ls.dsp.card "Card items (90/s)" "In-process" "Internal"
        ls.dsp.bkt -> ls.dsp.batch "ACH items" "In-process" "Internal"
        ls.dsp.card -> proc "POST /v1/charges" "HTTPS" "HTTPS"
        ls.dsp.batch -> bank "Debit file" "SFTP / File" "File"

        # ── Version Delta Model (V1 -> V2 with NEW highlight) ──
        v2 = softwareSystem "Loan Servicing V2" "Adds double-entry ledger and rail-bounded dispatcher." {
            api = container "Servicing API" "Keys and quotes." "Go"
            svc = container "Scheduler" "Claims due rows." "Go"
            db  = container "Servicing DB" "Ledger + outbox." "PostgreSQL" "Database,New"
            dsp = container "Dispatcher" "Token bucket per rail." "Go Worker" "New"
        }
        cus -> v2.api "POST /refunds" "HTTPS" "HTTPS"
        v2.api -> v2.svc "Call" "gRPC" "Sync"
        v2.svc -> v2.db "One commit" "SQL" "Internal"
        v2.db -> v2.dsp "PaymentDue" "Outbox Event" "Event"
        v2.dsp -> proc "Charge + key" "HTTPS" "HTTPS"
    }

    views {
        systemContext ls "01-system-context" "Loan Servicing — System Context" {
            include *
            autoLayout lr 220 120
            animation {
                cus mer ls
                proc
                bank
            }
        }

        container ls "02-container-view" "Loan Servicing — Core Containers" {
            include cus mer ls.api ls.svc ls.db ls.dsp proc bank
            autoLayout lr 180 110
            animation {
                cus mer ls.api
                ls.svc
                ls.db
                ls.dsp
                proc bank
            }
        }

        component ls.dsp "03-component-view" "Rail Dispatcher — Component Internals" {
            include ls.db ls.dsp.poll ls.dsp.plan ls.dsp.bkt ls.dsp.card ls.dsp.batch proc bank
            autoLayout lr 180 110
            animation {
                ls.db ls.dsp.poll
                ls.dsp.plan ls.dsp.bkt
                ls.dsp.card proc
                ls.dsp.batch bank
            }
        }

        container v2 "04-version-delta" "Architecture Evolution — V1 to V2 Delta" {
            include cus v2.api v2.svc v2.db v2.dsp proc
            autoLayout lr 180 110
            animation {
                cus v2.api v2.svc proc
                v2.db
                v2.dsp
            }
        }

        !include ../../resources/c4-google-tokens.dsl
    }
}
