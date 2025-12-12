#!/bin/bash

# Cloud Run Deployment Script for Gemini File Search MCP Server

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-gcp-project-id}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="gemini-file-search-mcp"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Deploying Gemini File Search MCP Server to Cloud Run${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed${NC}"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}❌ GEMINI_API_KEY environment variable is not set${NC}"
    echo "Please set it with: export GEMINI_API_KEY=your_api_key"
    exit 1
fi

# Step 1: Build the Docker image
echo -e "${BLUE}📦 Step 1: Building Docker image...${NC}"
gcloud builds submit --tag ${IMAGE_NAME} --project ${PROJECT_ID}

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker image built successfully${NC}"
echo ""

# Step 2: Deploy to Cloud Run
echo -e "${BLUE}🚀 Step 2: Deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --set-env-vars GEMINI_API_KEY=${GEMINI_API_KEY},LOG_LEVEL=INFO \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --port 8080 \
    --startup-cpu-boost \
    --project ${PROJECT_ID}

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Deployment successful!${NC}"
echo ""

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --platform managed \
    --region ${REGION} \
    --project ${PROJECT_ID} \
    --format 'value(status.url)')

echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo -e "${BLUE}Service URL:${NC} ${SERVICE_URL}"
echo -e "${BLUE}Health Check:${NC} ${SERVICE_URL}/health"
echo -e "${BLUE}MCP Endpoint:${NC} ${SERVICE_URL}/mcp"
echo ""
echo -e "${BLUE}To use with Claude Desktop, add this to your config:${NC}"
echo ""
cat <<EOF
{
  "mcpServers": {
    "gemini-file-search": {
      "url": "${SERVICE_URL}/mcp"
    }
  }
}
EOF
echo ""
