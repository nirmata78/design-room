"""Spoken-only respellings for the whole course: the caption keeps the real word. Longest keys first."""
_S = {
 "API":"A-P-I","APIs":"A-P-Is","RPC":"R-P-C","RPCs":"R-P-Cs","gRPC":"G-R-P-C","HTTP":"H-T-T-P","TCP":"T-C-P","DNS":"D-N-S","TTL":"T-T-L","TTLs":"T-T-Ls","IP":"I-P",
 "SQL":"sequel","LSM":"L-S-M","SSTable":"S-S-table","SSTables":"S-S-tables","MVCC":"M-V-C-C","WAL":"wall","fsync":"F-sync","SSD":"S-S-D","SSDs":"S-S-Ds","HDD":"H-D-D","IOPS":"eye-ops",
 "CAP":"cap","PACELC":"pack-elk","FLP":"F-L-P","NTP":"N-T-P","HLC":"H-L-C","CRDT":"C-R-D-T","CRDTs":"C-R-D-Ts","CDC":"C-D-C","RPO":"R-P-O","RTO":"R-T-O",
 "SLO":"S-L-O","SLOs":"S-L-Os","SLI":"S-L-I","SLIs":"S-L-Is","SLA":"S-L-A","QPS":"Q-P-S","CPU":"C-P-U","CPUs":"C-P-Us","GPU":"G-P-U","GPUs":"G-P-Us","RAM":"ram","NIC":"nick",
 "p50":"P fifty","p95":"P ninety-five","p99":"P ninety-nine","p999":"P three nines","ID":"I-D","IDs":"I-Ds","UUID":"U-U-I-D","UUIDs":"U-U-I-Ds","JWT":"jot","JWTs":"jots",
 "LRU":"L-R-U","LFU":"L-F-U","CDN":"C-D-N","SSE":"S-S-E","TLS":"T-L-S","mTLS":"mutual T-L-S","L4":"layer four","L7":"layer seven","GC":"G-C","OS":"O-S","I/O":"I-O",
 "etcd":"et-see-dee","Paxos":"Packsos","GitOps":"git-ops","Kubernetes":"koo-ber-net-eez","CoDel":"co-dell","LIFO":"lie-foe","FIFO":"fie-foe","Raft":"raft","ZooKeeper":"zoo-keeper",
 "idempotent":"eye-dem-potent","idempotency":"eye-dem-potency","linearizable":"linear-izable","linearizability":"linear-izability","serializable":"serial-izable","serializability":"serial-izability",
 "HyperLogLog":"hyper-log-log","t-digest":"T-digest","Bigtable":"Big-table","Pub/Sub":"pub sub","2PC":"two-phase commit","OLAP":"oh-lap","KB":"kilobytes","MB":"megabytes","GB":"gigabytes","TB":"terabytes","PB":"petabytes","EB":"exabytes",
 "rota":"rotation","rotas":"rotations", "ACID":"acid","OLTP":"O-L-T-P","JSON":"jay-son","XML":"X-M-L","CSV":"C-S-V","SSI":"S-S-I","GDPR":"G-D-P-R","XA":"X-A","UDP":"U-D-P","NoSQL":"no-sequel","OpenAPI":"open A-P-I",
 "Avro":"Ah-vro","Zab":"zab","Kleppmann":"Klep-man","Kleppmann's":"Klep-man's","memtable":"mem-table","Jepsen":"Jep-sen","Lamport":"Lam-port","Hudi":"hoo-dee","Iceberg":"ice-berg",
 "idempotence":"eye-dem-potence","Idempotence":"Eye-dem-potence","Idempotent":"Eye-dem-potent","Linearizability":"Linear-izability","Linearizable":"Linear-izable","Serializability":"Serial-izability","Serializable":"Serial-izable",
 "MessagePack":"message-pack","Protobuf":"proto-buf","BSON":"B-son","B-trees":"bee-trees","B-tree":"bee-tree","LSM-tree":"L-S-M tree","LSM-trees":"L-S-M trees","SSTable,":"S-S-table,","Bloom":"bloom","Cypher":"sigh-fer","SPARQL":"sparkle","Datalog":"data-log","ETL":"E-T-L","ERD":"E-R-D","VM":"V-M","TTL":"T-T-L","PG":"P-G",
 "InnoDB":"inno-D-B","Kafka":"Kahf-kuh","RPCs":"R-P-Cees","DDSketch":"D-D-sketch","Count-Min":"count min","IPv4":"I-P-v-four","IPv6":"I-P-v-six",
 "ms":"milliseconds","vs":"versus","etag":"E-tag","ETag":"E-tag","M/M/1":"M-M-one","N+1":"N plus one","N+2":"N plus two",
}
SAY = dict(sorted(_S.items(), key=lambda kv: -len(kv[0])))
