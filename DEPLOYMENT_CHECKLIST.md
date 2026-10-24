# Deployment checklist

## Required before deploy

1. Commit the updated stack changes.
2. Push to `main` so GitHub Actions publishes new images.
3. Confirm the following repo secrets exist in GitHub Actions:
   - `OPENSHIFT_SERVER`
   - `OPENSHIFT_TOKEN`
4. Ensure the OpenShift project has enough quota for:
   - Postgres PVC
   - Redis deployment
   - backend deployment
   - frontend deployment

## Runtime stack on OpenShift

- Postgres: `smartdailysavings-postgres`
- Redis: `smartdailysavings-redis`
- Backend: `smartdailysavings-backend`
- Frontend: `smartdailysavings-frontend`

## Apply manifests

```sh
oc apply -f openshift/deployment.yaml
oc rollout status deployment/smartdailysavings-postgres
oc rollout status deployment/smartdailysavings-redis
oc rollout status deployment/smartdailysavings-backend
oc rollout status deployment/smartdailysavings-frontend
```

## Post-deploy health checks

```sh
oc get pods
oc get routes
oc logs deployment/smartdailysavings-backend
```

## Notes

- The app is configured for PostgreSQL when `DATABASE_URL` is set.
- The app keeps SQLite fallback if no database URL is configured.
- Redis and OTEL are expected to be available in the cluster runtime environment.
