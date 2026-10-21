# OpenShift deployment notes

This project is prepared for a two-service OpenShift deployment:

- backend: FastAPI + SQLite
- frontend: React static build served by Nginx

Steps:

1. Build and push both images to a registry available to OpenShift.
2. Update the image references in `openshift/deployment.yaml`.
3. Apply the manifests:

   oc apply -f openshift/deployment.yaml

4. Confirm both Routes are created and access the frontend route for the app.

Important:
- The frontend should be configured with `VITE_API_URL` pointing to the backend service.
- In a production cluster, prefer an internal service URL for backend connectivity instead of localhost.
