# Microservices stack

## PostgreSQL failover automatique (Patroni + etcd)

Cette stack utilise un failover automatique:
- `etcd` (DCS Patroni)
- `patroni_1` et `patroni_2` (election primary/replica automatique)
- `pgpool_1` et `pgpool_2` (routage SQL)
- `haproxy_db_1` et `haproxy_db_2` (TCP 5432 devant les 2 pgpool)
- `haproxy_1` et `haproxy_2` (HTTP web/API)

Fichiers utilises:
- `docker-compose.yaml`
- `pgpool/pgpool.conf`
- `haproxy/haproxy-db.cfg`

## Connexion backend

Le backend ecrit sur:
- host: `haproxy-db.app.local`
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
- `http://localhost:8081` via `haproxy_1`
- `http://localhost:8080` via `haproxy_2`

Note DNS:
- Le domaine `app.local` est resolu uniquement a l'interieur du reseau Docker (via `coredns`).
- `app.local` retourne 2 enregistrements A (`172.31.0.100` et `172.31.0.101`) pour repartir les requetes entre `haproxy_1` et `haproxy_2`.
- `haproxy-db.app.local` retourne 2 enregistrements A (`172.31.0.102` et `172.31.0.103`) pour repartir les connexions DB entre `haproxy_db_1` et `haproxy_db_2`.
- Depuis la machine hote, utilise `http://localhost:8080` ou `http://localhost:8081`.
