# Microservices stack

## PostgreSQL failover automatique (Patroni + etcd)

Cette stack utilise un failover automatique:
- `etcd` (DCS Patroni)
- `patroni_1` et `patroni_2` (election primary/replica automatique)
- `pgpool_1` et `pgpool_2` (routage SQL)
- `haproxy_db` (TCP 5432 devant les 2 pgpool)
- `haproxy_1` et `haproxy_2` (HTTP web/API)

Fichiers utilises:
- `docker-compose.yaml`
- `pgpool/pgpool.conf`
- `haproxy/haproxy-db.cfg`

## Connexion backend

Le backend ecrit sur:
- host: `haproxy_db`
- port: `5432`
- database: `postgres`
- user: `postgres`
- password: `postgres_password`

Ces variables sont dans:
- `backend/.env`
- `backend/.env.example`

## Commandes utiles

Demarrage:
`docker compose -f docker-compose.yaml up -d --build`

Arret + suppression des volumes:
`docker compose -f docker-compose.yaml down -v`

Verifier les noeuds pgpool:
`docker compose -f docker-compose.yaml exec -T pgpool_1 sh -lc "PGPASSWORD=postgres_password psql -h localhost -U postgres -d postgres -c 'show pool_nodes;'"`

Verifier le leader Patroni:
`docker compose -f docker-compose.yaml exec -T patroni_1 curl -fsS http://localhost:8008/cluster`

Ports web:
- `http://localhost:80` via `haproxy_1`
- `http://localhost:8080` via `haproxy_2`
