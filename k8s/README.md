# PulseWatch on Kubernetes

A parallel deployment path to `docker-compose.yml`, built as a learning
exercise: every service in the stack (API, event consumer, Celery worker,
checker scheduler, monitor sync, frontend) runs as its own Kubernetes
Deployment, backed by Postgres and Redis, with Secrets/ConfigMaps for
configuration and a Job for migrations.

This is a **local learning setup** (`kind`), not a production deployment.
The manifests themselves are close to production-shape — see
[Path to production](#path-to-production) for exactly what would change
and why.

## Structure

```
k8s/
├── kind-config.yaml          # local cluster config (port mappings to the host)
├── config.yaml                 # ConfigMap — non-sensitive shared config
├── secrets.yaml.example          # Secret template (real secrets.yaml is gitignored)
├── postgres.yaml                   # Deployment + Service + PVC
├── redis.yaml
├── mailpit.yaml
├── migrate-job.yaml                    # Job — runs Alembic migrations once
├── api.yaml                              # Deployment + Service (NodePort)
├── consumer.yaml                           # Deployment only (no inbound traffic)
├── celery-worker.yaml
├── worker-scheduler.yaml
├── worker-sync.yaml
└── frontend.yaml                                # Deployment + Service (NodePort)
```

## Running it

```bash
# 1. Create the local cluster with host port mappings
kind create cluster --name pulsewatch --config k8s/kind-config.yaml

# 2. Build and load the images kind can't pull from a registry
docker build -t pulsewatch-api:latest ./api
docker build -t pulsewatch-worker:latest ./worker
docker build -t pulsewatch-frontend:latest \
  --build-arg VITE_API_URL=http://localhost:8000 ./frontend

kind load docker-image pulsewatch-api:latest --name pulsewatch
kind load docker-image pulsewatch-worker:latest --name pulsewatch
kind load docker-image pulsewatch-frontend:latest --name pulsewatch

# 3. Config and secrets first — Postgres and the API need these at boot
cp k8s/secrets.yaml.example k8s/secrets.yaml   # edit with real values
kubectl apply -f k8s/config.yaml
kubectl apply -f k8s/secrets.yaml

# 4. Stateful/infra services
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/mailpit.yaml

# 5. Migrations — must complete before the API/consumer are useful
kubectl apply -f k8s/migrate-job.yaml
kubectl logs -f job/migrate

# 6. Application services
kubectl apply -f k8s/api.yaml
kubectl apply -f k8s/consumer.yaml
kubectl apply -f k8s/celery-worker.yaml
kubectl apply -f k8s/worker-scheduler.yaml
kubectl apply -f k8s/worker-sync.yaml
kubectl apply -f k8s/frontend.yaml
```

- API: `http://localhost:8000/docs`
- Frontend: `http://localhost:5173`
- Mailpit: `http://localhost:8025`

Re-running a migration after a new Alembic revision requires deleting the
old Job first — Jobs are immutable once created:

```bash
kubectl delete job migrate
kubectl apply -f k8s/migrate-job.yaml
```

## What this demonstrates

- **Deployments** for every long-running service, each with its own
  label selector triangle (Deployment `selector.matchLabels` ↔ Pod
  template labels ↔ Service `selector`) — the mechanism that lets
  Kubernetes route traffic to Pods correctly even as they're replaced
  and get new IPs.
- **Services** (`ClusterIP` by default) giving stable internal DNS names
  (`postgres`, `redis`, `api`, ...) — the direct equivalent of Compose's
  service-name resolution, but resilient to Pod IPs changing.
- **A Job**, not a Deployment, for migrations — a one-shot task that
  should run to completion and stop, not be restarted forever.
- **ConfigMap vs. Secret** split — non-sensitive shared config
  (`POSTGRES_USER`, `REDIS_URL`) versus anything sensitive
  (`POSTGRES_PASSWORD`, `JWT_SECRET_KEY`), consumed via `envFrom` so
  services pick up every key without listing them one by one.
- **A PersistentVolumeClaim** for Postgres, so data survives Pod restarts
  (though not `kind` cluster deletion — the underlying volume lives
  inside the kind node container).
- **Readiness probes** (`exec` for Postgres's `pg_isready`, `httpGet` for
  the API's `/health`) — the Kubernetes equivalent of Compose's
  `healthcheck:`, but split from liveness: a failing readiness probe
  pulls a Pod out of Service routing without restarting it.
- **`kind`'s `extraPortMappings`** to expose specific services
  (api, mailpit, frontend) on fixed host ports for local access —
  the local-dev equivalent of a real cluster's Ingress + LoadBalancer.

## Path to production

The manifests here are close to what you'd actually run — this is the
main point of Kubernetes as an abstraction. What changes is almost
entirely in what surrounds them, not their shape:

- **Cluster provisioning.** `kind` simulates a multi-node cluster inside
  one Docker container. A real deployment uses a managed control plane
  (EKS, GKE, AKS) or self-managed nodes (`kubeadm`) — you stop creating
  the cluster yourself and start adding real VMs as nodes. Scheduling
  which Pod lands on which node is handled automatically either way; you
  don't hand-assign services to machines.
- **Image registry.** `kind load docker-image` is a local-only shortcut.
  Production needs a real registry (GHCR, Docker Hub, ECR) and versioned
  tags (`v1.2.3` or a commit SHA) — never `:latest`, so rollbacks are
  deterministic.
- **Secrets management.** Plaintext `stringData` in a YAML file (even
  gitignored) doesn't belong in a real deployment. Production pulls
  secrets from an external source (Sealed Secrets, External Secrets
  Operator backed by AWS Secrets Manager/Vault, or CI/CD-time injection)
  rather than committing them anywhere, ever.
- **External access.** The `NodePort` + `kind` port-mapping setup here is
  a local convenience. Production uses an `Ingress` resource with a real
  domain and TLS (typically via `cert-manager`), not raw node ports.
- **Managed database.** Running Postgres as a Pod (as done here) works
  for a demo; a production system would more likely use a managed
  database (RDS, Cloud SQL) for backups, replication, and failover
  without reimplementing them on top of a PVC.
- **Resource requests/limits become load-bearing, not optional.** With
  a real multi-node scheduler, these numbers are what it uses to decide
  placement — omitting them risks one greedy Pod starving its node.
- **Observability.** `kubectl logs` on a handful of Pods works for local
  learning; a real cluster needs centralized logging (Loki/ELK) and
  metrics (Prometheus + Grafana, the standard k8s pairing).

What stays identical: the Deployment/Service/ConfigMap/Secret shapes,
the label-matching mechanism, probes, and volume mounts. That's the
actual value of learning Kubernetes this way — the manifests you write
against a local `kind` cluster are the same ones a real cluster runs.