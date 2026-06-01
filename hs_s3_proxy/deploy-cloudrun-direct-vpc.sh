#!/bin/bash
set -e

PROJECT_ID=hydroshare-403701
SERVICE_ACCOUNT=micro-auth-proxy@${PROJECT_ID}.iam.gserviceaccount.com
AUTH_SERVICE_URL=http://10.128.0.113:80
S3_BACKEND_URL=https://storage.googleapis.com
S3_BACKEND_BUCKET=hydroshare-resources
S3_BACKEND_ACCESS_KEY=GOOG1EQ2KX3UZJEN3D4ADSJITQABGI5WN7DRIM566AC6A5OKBOFZ47HFYCQT4
S3_PROXY_TIMEOUT=300
CORS_ALLOWED_ORIGINS="${CORS_ALLOWED_ORIGINS:-https://beta.hydroshare.org,https://hydroshare.org}"

# Configuration - from environment
# Required: PROJECT_ID, SERVICE_ACCOUNT, AUTH_SERVICE_URL,
#           S3_BACKEND_BUCKET, S3_BACKEND_ACCESS_KEY, S3_BACKEND_SECRET_KEY
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-hs-s3-proxy}"
IMAGE_NAME="${IMAGE_NAME:-${REGION}-docker.pkg.dev/${PROJECT_ID}/s3-proxy/proxy}"

# VPC Configuration (Direct VPC egress)
VPC_NETWORK="${VPC_NETWORK:-default}"
VPC_SUBNET="${VPC_SUBNET:-default}"

# Backend S3 Configuration (Google Cloud Storage with S3 compatibility)
S3_BACKEND_URL="${S3_BACKEND_URL:-https://storage.googleapis.com}"

# Build and push the container image
echo "Building container image..."
docker build --platform linux/amd64 -t ${IMAGE_NAME}:latest .

echo "Pushing to Container Registry..."
docker push ${IMAGE_NAME}:latest

# Deploy to Cloud Run with Direct VPC egress
echo "Deploying to Cloud Run with Direct VPC egress..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME}:latest \
  --platform managed \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --network ${VPC_NETWORK} \
  --subnet ${VPC_SUBNET} \
  --network-tags hs-s3-proxy \
  --service-account ${SERVICE_ACCOUNT} \
  --execution-environment gen2 \
  --timeout 3600 \
  --concurrency 80 \
  --cpu 2 \
  --memory 2Gi \
  --min-instances 1 \
  --max-instances 10 \
  --port 9000 \
  --set-env-vars "AUTH_SERVICE_URL=${AUTH_SERVICE_URL}" \
  --set-env-vars "S3_BACKEND_URL=${S3_BACKEND_URL}" \
  --set-env-vars "S3_BACKEND_BUCKET=${S3_BACKEND_BUCKET}" \
  --set-env-vars "S3_BACKEND_ACCESS_KEY=${S3_BACKEND_ACCESS_KEY}" \
  --set-env-vars "S3_BACKEND_SECRET_KEY=${S3_BACKEND_SECRET_KEY}" \
  --set-env-vars "S3_PROXY_TIMEOUT=300" \
  --set-env-vars "^|^CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS}" \
  --set-env-vars "PROXY_MODE=external" \
  --allow-unauthenticated

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Service URL:"
gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --format 'value(status.url)'

echo ""
echo "Next steps:"
echo "1. Set up Cloud Load Balancer with your custom domain (s3.yourdomain.com)"
echo "2. Configure firewall rules to allow Cloud Run to access your internal services"
echo "3. Test with: curl https://YOUR-SERVICE-URL/health"
