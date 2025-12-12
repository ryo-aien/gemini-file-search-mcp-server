#!/bin/bash

# Fix Cloud Run deployment by setting environment variables

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Fixing Cloud Run deployment...${NC}"
echo ""

# Configuration from your deployment
PROJECT_ID="able-engine-467515-k8"
REGION="asia-northeast1"
SERVICE_NAME="gemini-file-search-mcp-server"

# Load GEMINI_API_KEY from .env file
if [ -f .env ]; then
    source .env
fi

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}❌ GEMINI_API_KEY is not set${NC}"
    echo "Please set it in your .env file or export it:"
    echo "export GEMINI_API_KEY=your_api_key"
    exit 1
fi

echo -e "${YELLOW}📝 Configuration:${NC}"
echo "  Project: ${PROJECT_ID}"
echo "  Region: ${REGION}"
echo "  Service: ${SERVICE_NAME}"
echo "  API Key: ${GEMINI_API_KEY:0:20}..." # Show only first 20 chars
echo ""

# Update the Cloud Run service with environment variables
echo -e "${BLUE}🚀 Updating Cloud Run service with environment variables...${NC}"
gcloud run services update ${SERVICE_NAME} \
    --region ${REGION} \
    --project ${PROJECT_ID} \
    --set-env-vars GEMINI_API_KEY=${GEMINI_API_KEY},DEFAULT_MODEL=gemini-2.5-flash,LOG_LEVEL=INFO \
    --timeout 300 \
    --memory 1Gi \
    --cpu 1

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Update failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Service updated successfully!${NC}"
echo ""

# Get the service URL
echo -e "${BLUE}🔍 Getting service URL...${NC}"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region ${REGION} \
    --project ${PROJECT_ID} \
    --format 'value(status.url)')

echo -e "${GREEN}🎉 Service is ready!${NC}"
echo ""
echo -e "${BLUE}Service URL:${NC} ${SERVICE_URL}"
echo -e "${BLUE}Health Check:${NC} ${SERVICE_URL}/health"
echo -e "${BLUE}MCP Endpoint:${NC} ${SERVICE_URL}/mcp"
echo ""

# Test the health endpoint
echo -e "${BLUE}🏥 Testing health endpoint...${NC}"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "${SERVICE_URL}/health")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n 1)
BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
    echo -e "${RED}❌ Health check failed (HTTP $HTTP_CODE)${NC}"
    echo "$BODY"
fi

echo ""
echo -e "${BLUE}To test the MCP endpoint:${NC}"
echo ""
echo "curl -X POST ${SERVICE_URL}/mcp \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{"
echo "    \"jsonrpc\": \"2.0\","
echo "    \"id\": 1,"
echo "    \"method\": \"tools/list\""
echo "  }'"
echo ""
