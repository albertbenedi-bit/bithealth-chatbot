# Create or switch to the namespace for your application
kubectl create namespace rag-app # If you want a dedicated namespace
kubectl config set-context --current --namespace=rag-app # Set default namespace for kubectl

# Create the secret containing your database URL
kubectl create secret generic rag-service-secrets \
  --from-literal=DATABASE_URL="postgresql+psycopg2://postgres:BTxg8LN5lH@my-rag-postgres-postgresql.data.svc.cluster.local:5432/rag_db" \
  --from-literal=GOOGLE_API_KEY="AIzaSyBsErNvPHekr4z2meNLLek9z1sMUC-TeU8" -n rag-app # Specify the namespace
# Add other secrets as --from-literal=KEY="VALUE"

# Replace values with your actual credentials and the internal K8s service name for Postgres
# Internal Postgres Service Name format: <service-name>.<namespace>.svc.cluster.local
# Our Postgres service is named 'my-rag-postgres' in the 'data' namespace