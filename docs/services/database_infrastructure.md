# Thanatos Enterprise Scalable Multi-Engine Database Infrastructure
> Architectural Blueprint & Operations Catalog for Relational, Document, Vector, and Graph Storage

---

## 1. Executive Summary

Thanatos employs a resilient hybrid data architecture composed of four enterprise containerized engines alongside local embedded fallbacks:
- **PostgreSQL 16**: Strict relational persistence, transactional ledger, career deduplication tables, and operational audit trails.
- **MongoDB 7.0**: High-throughput document store for dynamic transcripts, unformatted dossiers, and unstructured memories.
- **Milvus 2.4.13 Standalone**: High-dimensional vector database powered by MinIO and etcd for RAG semantic search.
- **Neo4j 5.20 Community**: Graph database representing character arcs, interpersonal relationship graphs, and multi-agent knowledge topologies.

---

## 2. Container Topology & Resource Quotas

All engines are configured in [`docker-compose.enterprise.yml`](file:///c:/Users/ACER/Desktop/Self-Projects/Thanatos/docker-compose.enterprise.yml) under the isolated bridge network `thanatos_enterprise_net`.

| Engine | Container Name | Host Port | Internal Port | Memory Cap | Persistent Volume |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PostgreSQL 16** | `thanatos-postgres` | `5432` | `5432` | 1024 MB | `thanatos_postgres_data` |
| **MongoDB 7.0** | `thanatos-mongodb` | `27017` | `27017` | 1024 MB | `thanatos_mongo_data` |
| **Milvus Standalone** | `milvus-standalone` | `19530`, `9091` | `19530`, `9091` | 2048 MB | `thanatos_milvus_data` |
| **Milvus MinIO** | `milvus-minio` | `9000`, `9001` | `9000`, `9001` | 512 MB | `thanatos_minio_data` |
| **Milvus etcd** | `milvus-etcd` | - | `2379` | 512 MB | `thanatos_etcd_data` |
| **Neo4j 5.20** | `thanatos-neo4j` | `7474`, `7687` | `7474`, `7687` | 1536 MB | `thanatos_neo4j_data` |

---

## 3. Autonomous Orchestration

The supervisor in [`services/database/db_orchestrator.py`](file:///c:/Users/ACER/Desktop/Self-Projects/Thanatos/services/database/db_orchestrator.py) performs automated management:
- **Pre-flight Check**: Queries `docker info` to verify Docker availability. If offline, Thanatos falls back seamlessly to embedded SQLite and Milvus Lite.
- **On-Demand Auto-Start**: If an agent requests enterprise capabilities, the orchestrator triggers `docker compose -f docker-compose.enterprise.yml up -d [service]` automatically.
- **RAM Guardrails**: Every container is bounded with strict memory constraints in compose to prevent host system starvation.

---

## 4. Backup & Disaster Recovery Procedures

### PostgreSQL
- **Backup**:
  ```powershell
  docker exec -t thanatos-postgres pg_dumpall -c -U thanatos > backups/postgres_dump.sql
  ```
- **Restore**:
  ```powershell
  Get-Content backups/postgres_dump.sql | docker exec -i thanatos-postgres psql -U thanatos -d thanatos_memory
  ```

### MongoDB
- **Backup**:
  ```powershell
  docker exec thanatos-mongodb mongodump --out /data/db/backup
  ```
- **Restore**:
  ```powershell
  docker exec thanatos-mongodb mongorestore /data/db/backup
  ```

### Milvus
- Volume snapshot or backup via Milvus Backup CLI tool of `thanatos_milvus_data`, `thanatos_etcd_data`, and `thanatos_minio_data`.

### Neo4j
- **Backup**:
  ```powershell
  docker exec -it thanatos-neo4j neo4j-admin database dump neo4j --to-path=/data/backup
  ```
- **Restore**:
  ```powershell
  docker exec -it thanatos-neo4j neo4j-admin database load neo4j --from-path=/data/backup --overwrite-destination=true
  ```
