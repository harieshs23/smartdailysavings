# OpenShift deployment notes

This project is prepared for a two-service OpenShift deployment:

- backend: FastAPI + SQLite
- frontend: React static build served by Nginx

GitHub Actions builds both images and publishes them to GitHub Container
Registry (GHCR) when changes are pushed to `main`. You can also start a build
manually from the Actions tab. Wait for the **Publish container images**
workflow to complete before deploying:

- `ghcr.io/harieshs23/smartdailysavings-backend`
- `ghcr.io/harieshs23/smartdailysavings-frontend`

Each image is tagged with `latest` and `sha-<commit>`. `latest` is updated by
each successful build; the SHA tag identifies the source commit. The GHCR
packages are public, so OpenShift can pull the images without a registry
secret. GitHub Actions only builds and stores images; deployment is a separate
step.

From a terminal logged in to the intended OpenShift project, apply the
manifests and wait for both deployments:

```sh
oc apply -f openshift/deployment.yaml
oc rollout status deployment/smartdailysavings-backend
oc rollout status deployment/smartdailysavings-frontend
```

The manifests use the `latest` tags. After a later image build succeeds,
restart the deployments to pull the updated images:

```sh
oc rollout restart deployment/smartdailysavings-backend
oc rollout restart deployment/smartdailysavings-frontend
```

The frontend proxies API requests through Nginx to the backend Service, so
browser requests remain same-origin.

Important:
- The backend Service exposes port 80 and forwards traffic to container port 8000.
- The SQLite database is stored on a 1 GiB PersistentVolumeClaim.
- Nginx listens on port 8080 so it can run under OpenShift's restricted security context.
- The Routes in `deployment.yaml` currently do not configure TLS. To serve HTTPS,
  configure TLS termination on the Routes for your cluster.
