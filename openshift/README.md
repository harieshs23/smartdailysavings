# OpenShift deployment notes

This project is prepared for a two-service OpenShift deployment:

- backend: FastAPI + SQLite
- frontend: React static build served by Nginx

GitHub Actions builds both images and publishes them to GitHub Container
Registry (GHCR) when changes are pushed to `main`. You can also start a build
manually from the Actions tab. Wait for the **Publish container images**
workflow to complete before deploying.

The GHCR packages are private by default. Create an OpenShift pull secret using
a GitHub personal access token with the `read:packages` permission. Run this
from a terminal where you are logged in to the intended OpenShift project:

```sh
read -rp "GitHub username: " GHCR_USERNAME
read -rsp "GitHub token (read:packages): " GHCR_TOKEN
echo
oc create secret docker-registry ghcr-pull-secret \
  --docker-server=ghcr.io \
  --docker-username="$GHCR_USERNAME" \
  --docker-password="$GHCR_TOKEN" \
  --dry-run=client -o yaml | oc apply -f -
unset GHCR_TOKEN

oc apply -f openshift/deployment.yaml
oc rollout status deployment/smartdailysavings-backend
oc rollout status deployment/smartdailysavings-frontend
```

The workflow publishes `latest` and a commit-specific `sha-...` tag for each
image. The manifests use `latest`; after a later image build, restart the
deployments to pull the updated images:

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
