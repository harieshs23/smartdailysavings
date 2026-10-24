# smartdailysavings

AI-powered deal aggregator for India.

## Container images

GitHub Actions builds the backend and frontend container images and publishes
them to GitHub Container Registry (GHCR):

- `ghcr.io/harieshs23/smartdailysavings-backend`
- `ghcr.io/harieshs23/smartdailysavings-frontend`

Images are published when commits are pushed to `main`, or when the workflow
is run manually from GitHub Actions. Each build gets a mutable `latest` tag and
a commit-specific `sha-<commit>` tag. The GHCR packages are public, allowing
OpenShift to pull images without a registry credential. GitHub Actions builds
and stores images; it does not automatically deploy them.

## OpenShift deployment

After the **Publish container images** workflow succeeds, deploy the manifests
to the OpenShift project you are logged in to:

```sh
oc apply -f openshift/deployment.yaml
oc rollout status deployment/smartdailysavings-backend
oc rollout status deployment/smartdailysavings-frontend
oc get routes
```

The manifests run the FastAPI backend and Nginx-served frontend. The backend
uses a 1 GiB persistent volume for SQLite, and the frontend proxies API
requests to the backend Service. Routes in the current manifest do not configure
TLS. This project is designed for local experimentation and OpenShift demo
workloads. For full setup details and how to refresh deployments after new images
are published, see [OpenShift deployment notes](./openshift/README.md).
