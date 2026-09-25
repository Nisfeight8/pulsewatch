# Kubernetes Basics — Reference Guide

A reference for the core building blocks, written for someone who already
knows Docker Compose and is learning k8s by converting a real project
(PulseWatch) into manifests.

---

## 1. The core concepts, in the order you meet them

### Cluster

A set of machines (nodes) that Kubernetes manages as one unit. `kind`
simulates a whole cluster inside a single Docker container, for local
learning — production clusters are real VMs/physical machines.

### Node

One machine (VM or physical) that's part of the cluster. Nodes run Pods.
A cluster usually has multiple nodes so that if one dies, workloads can
be rescheduled onto the others.

```bash
kubectl get nodes
kubectl describe node <name>   # see capacity, running pods, conditions
```

### Pod

The smallest deployable unit. Almost always **one container per Pod** in
practice (multi-container Pods exist for "sidecar" patterns, but that's
advanced). A Pod has its own IP address — but that IP is **ephemeral**:
if the Pod is recreated (crash, node failure, rollout), it gets a new one.

You rarely create Pods directly. You create a **Deployment**, which
creates and manages Pods for you.

```bash
kubectl get pods
kubectl logs <pod-name>
kubectl describe pod <pod-name>   # events, restarts, why it's not starting
kubectl exec -it <pod-name> -- sh   # shell into a running container
```

### Deployment

Declares "I want N replicas of this Pod template running, always." If a
Pod dies, the Deployment's controller notices and creates a replacement.
Also handles rolling updates (swap Pods to a new image version gradually,
zero downtime) and rollbacks.

This is the direct equivalent of `restart: unless-stopped` in Compose,
but active rather than passive — it doesn't just restart a crashed
container, it continuously reconciles "what's running" against "what I
declared should be running."

```bash
kubectl get deployments
kubectl rollout status deployment/<name>
kubectl rollout restart deployment/<name>
kubectl scale deployment/<name> --replicas=3
```

### Service

Gives a **stable name and virtual IP** that always routes to whichever
Pods currently match its label selector — even as those Pods are
replaced and get new (ephemeral) IPs underneath. This is what makes
Pod-to-Pod communication reliable despite Pods being disposable.

Three Service types worth knowing now:
- `ClusterIP` (default) — reachable only from inside the cluster. What
  you use for internal things like Postgres/Redis/your API talking to
  each other.
- `NodePort` — opens a port on every node, reachable from outside the
  cluster. Simple but rarely used in real production setups.
- `LoadBalancer` — asks the cloud provider (AWS/GCP/etc.) to provision an
  external load balancer pointing at the Service. `kind` doesn't support
  this without extra setup — for local learning, use port-forwarding
  instead (see below).

```bash
kubectl get services
kubectl port-forward service/<name> 8080:80   # reach a ClusterIP service from your machine
```

### ConfigMap and Secret

Both store key-value configuration that Pods can consume as environment
variables or mounted files — the equivalent of your `.env` files. The
only real difference: **Secret** values are base64-encoded at rest (not
encrypted by default in a bare cluster, just obscured — real encryption
needs additional setup) and Kubernetes treats them with slightly more
care (e.g. not printed in some `describe` output). Use ConfigMap for
non-sensitive config (`TICK_INTERVAL_SECONDS`), Secret for anything you'd
never want to commit in plaintext (`JWT_SECRET_KEY`, `POSTGRES_PASSWORD`).

```bash
kubectl create secret generic pulsewatch-secrets --from-env-file=.env
kubectl get secrets
kubectl get configmaps
```

### PersistentVolume (PV) and PersistentVolumeClaim (PVC)

Pods are disposable, but data (Postgres, Redis persistence) shouldn't be.
A PVC is a request for storage ("I need 1GB that survives Pod restarts");
a PV is the actual storage that fulfills it. In most clusters (including
`kind` with default setup), you just write a PVC and the cluster
auto-provisions a matching PV — you rarely write PVs by hand.

### Namespace

A way to partition a cluster into logical groups (e.g. `pulsewatch-dev`,
`pulsewatch-prod`) so resources don't collide by name and you can apply
access controls per group. Not essential for a single-project local
cluster, but worth knowing it exists.

---

## 2. How the concepts fit together (for PulseWatch specifically)

```
Deployment (redis)  →  manages  →  Pod(s) (redis-xxxxx)
       ↑                                    ↑
   selector: app=redis            labels: app=redis
                                             ↑
Service (redis)  →  selector: app=redis  →  routes traffic here
       ↑
  other Pods reach it at "redis:6379" (stable DNS name)
```

The **label matching triangle** (Deployment's `selector.matchLabels`,
Pod template's `metadata.labels`, and the Service's `selector`) must all
agree on the same key/value — that's the thread connecting all three
objects. Everything else is comparatively mechanical once this clicks.

---

## 3. Anatomy of a manifest file

Every Kubernetes YAML manifest has the same four top-level fields:

```yaml
apiVersion: apps/v1      # which API group/version defines this resource type
kind: Deployment          # what kind of resource this is
metadata:                  # identifying info: name, labels, namespace
  name: redis
  labels:
    app: redis
spec:                        # the actual configuration — differs per kind
  ...
```

Common `apiVersion` values to recognize:
- `v1` — core resources: Pod, Service, ConfigMap, Secret, PersistentVolumeClaim, Namespace
- `apps/v1` — Deployment, StatefulSet, ReplicaSet, DaemonSet

You don't need to memorize which `kind` uses which `apiVersion` — copy
from a working example or let `kubectl explain <kind>` tell you.

```bash
kubectl explain deployment.spec       # inline docs for any field, right in the terminal
kubectl explain deployment.spec.template.spec.containers
```

### Deployment spec shape

```yaml
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis          # must match template.metadata.labels below
  template:                  # this whole block describes the Pod to create
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:8-alpine
          ports:
            - containerPort: 6379
          env:                              # equivalent of Compose's "environment:"
            - name: SOME_VAR
              value: "some-value"
          envFrom:                            # bulk-load all keys from a ConfigMap/Secret
            - configMapRef:
                name: pulsewatch-config
            - secretRef:
                name: pulsewatch-secrets
          resources:                             # optional but good practice: CPU/memory limits
            requests:
              memory: "64Mi"
              cpu: "100m"
            limits:
              memory: "128Mi"
              cpu: "250m"
          livenessProbe:                            # "is this container still alive?" — restart if it fails
            tcpSocket:
              port: 6379
            initialDelaySeconds: 5
            periodSeconds: 10
          readinessProbe:                             # "is this container ready for traffic?" — hold routing until true
            tcpSocket:
              port: 6379
            initialDelaySeconds: 5
            periodSeconds: 5
```

`livenessProbe`/`readinessProbe` are the direct equivalent of Compose's
`healthcheck:` — but split into two purposes. Liveness failing gets the
container **restarted**; readiness failing just gets it **removed from
Service routing** temporarily (useful for "still starting up, don't send
traffic yet" without treating it as a crash).

### Service spec shape

```yaml
spec:
  type: ClusterIP           # default, can be omitted
  selector:
    app: redis                # must match the Deployment's Pod labels
  ports:
    - port: 6379                # what other Pods use to reach this Service
      targetPort: 6379             # what the container actually listens on
```

### ConfigMap / Secret shape

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: pulsewatch-config
data:
  TICK_INTERVAL_SECONDS: "15"
  HTTP_TIMEOUT_SECONDS: "10.0"
```

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: pulsewatch-secrets
type: Opaque
stringData:                     # plaintext here; kubectl/etcd store it base64-encoded
  JWT_SECRET_KEY: change-me
  POSTGRES_PASSWORD: pulsewatch
```

(`stringData` lets you write plain values in the YAML — Kubernetes
base64-encodes them on storage. The older `data` field requires you to
pre-encode values yourself; `stringData` is the convenient modern way to
write these by hand.)

### PersistentVolumeClaim shape

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

Referenced from a Deployment like this:

```yaml
      containers:
        - name: postgres
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: postgres-data
```

---

## 4. File organization convention

One file per component, containing every resource that component needs,
separated by `---`:

```
k8s/
├── redis.yaml              # Deployment + Service
├── postgres.yaml            # Deployment + Service + PVC
├── config.yaml                # ConfigMap (shared, non-sensitive)
├── secrets.yaml                 # Secret (never commit real values — use a template + .gitignore)
├── api.yaml
├── consumer.yaml
├── celery-worker.yaml
├── worker-scheduler.yaml
├── worker-sync.yaml
└── frontend.yaml
```

Apply everything in a directory at once:

```bash
kubectl apply -f k8s/
```

---

## 5. Useful commands while learning

```bash
kubectl get all                        # everything in the current namespace, one glance
kubectl get pods -o wide                 # includes node placement, IP
kubectl delete -f k8s/redis.yaml           # tear down what a file created
kubectl apply -f k8s/redis.yaml --dry-run=client   # validate without applying
kind delete cluster --name pulsewatch        # nuke the whole local cluster, start fresh
```
