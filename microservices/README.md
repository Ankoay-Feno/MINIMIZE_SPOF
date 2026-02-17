# Microservices stack

## PostgreSQL primary + replica + Pgpool-II

Cette stack suit l'approche de la doc que tu as fournie, avec Pgpool-II:
- `postgres_primary` (read/write)
- `postgres_replica` (read-only, alimentee par `pg_basebackup`)
- `pgpool` (point d'entree unique pour le backend)

Fichiers utilises:
- `postgres/00_init.sql`
- `docker-compose.yaml`

Le script SQL cree:
- l'utilisateur de replication `replicator`
- le slot physique `replication_slot`

## Connexion backend

Le backend ecrit sur:
- host: `pgpool`
- port: `5432`
- database: `app_db`
- user: `app_user`
- password: `app_password`

Ces variables sont dans:
- `backend/.env`
- `backend/.env.example`

## Commandes utiles

Demarrage:
`docker compose -f docker-compose.yaml up -d --build`

Arret + suppression des volumes:
`docker compose -f docker-compose.yaml down -v`

Verifier la replication (slot cote primary):
`docker compose -f docker-compose.yaml exec -T postgres_primary psql -U app_user -d app_db -c "select slot_name, active, restart_lsn from pg_replication_slots;"`
