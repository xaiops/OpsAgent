 #!/bin/bash
# Deploy OpsAgent to OpenShift

set -e

# Configuration
NAMESPACE="${1:-ops-agent}"
IMAGE_TAG="${2:-v1.1.0}"  # Default to working version

echo "🚀 Deploying OpsAgent to OpenShift namespace: ${NAMESPACE}"
echo "📦 Using image: quay.io/rbrhssa/ops-agents:${IMAGE_TAG}"

# Check if oc is installed
if ! command -v oc &> /dev/null; then
    echo "❌ Error: OpenShift CLI (oc) not found. Please install it first."
    exit 1
fi

# Check if logged in
if ! oc whoami &> /dev/null; then
    echo "❌ Error: Not logged in to OpenShift. Please run 'oc login' first."
    exit 1
fi

# Create namespace if it doesn't exist
if ! oc get project ${NAMESPACE} &> /dev/null; then
    echo "📦 Creating namespace: ${NAMESPACE}"
    oc new-project ${NAMESPACE}
else
    echo " Using existing namespace: ${NAMESPACE}"
    oc project ${NAMESPACE}
fi

# Check if secrets exist
if ! oc get secret ops-agent-secrets -n ${NAMESPACE} &> /dev/null; then
    echo "⚠️  Secret 'ops-agent-secrets' not found!"
    echo ""
    echo "Please create the secret with your LLM credentials:"
    echo ""
    echo "  oc create secret generic ops-agent-secrets \\"
    echo "    --from-literal=llm-api-key='your-api-key' \\"
    echo "    --from-literal=llm-base-url='https://your-llm-endpoint.com/v1' \\"
    echo "    -n ${NAMESPACE}"
    echo ""
    read -p "Create a placeholder secret now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        oc create secret generic ops-agent-secrets \
          --from-literal=llm-api-key='not-needed' \
          --from-literal=llm-base-url='https://lss-lss.apps.prod.rhoai.rh-aiservices-bu.com/v1/openai/v1' \
          -n ${NAMESPACE}
        echo " Placeholder secret created. Update it with actual credentials!"
    else
        exit 1
    fi
fi

# Apply ConfigMap
echo "📝 Applying ConfigMap..."
oc apply -f deploy/configmap.yaml -n ${NAMESPACE}

# Apply Deployment
echo "🚢 Applying Deployment..."
if [ "$IMAGE_TAG" != "v1.1.0" ]; then
    # Update image tag in deployment (default is v1.1.0)
    sed "s|quay.io/rbrhssa/ops-agents:v1.1.0|quay.io/rbrhssa/ops-agents:${IMAGE_TAG}|g" deploy/deployment.yaml | oc apply -f - -n ${NAMESPACE}
else
    oc apply -f deploy/deployment.yaml -n ${NAMESPACE}
fi

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
oc rollout status deployment/ops-agent -n ${NAMESPACE} --timeout=5m || true

# Get deployment status
echo ""
echo "📊 Deployment Status:"
oc get pods -n ${NAMESPACE} -l app=ops-agent

# Verify MCP tools loaded
echo ""
echo "🔍 Verifying MCP tools loading..."
sleep 5
TOOLS_COUNT=$(oc logs -l app=ops-agent -n ${NAMESPACE} --tail=50 | grep -o "Total tools available: [0-9]*" | tail -1 || echo "")
if [[ "$TOOLS_COUNT" =~ "47" ]]; then
    echo "✅ MCP Integration Working: $TOOLS_COUNT (46 MCP + 1 memory)"
else
    echo "⚠️  Tools status: $TOOLS_COUNT (expected: 47)"
    echo "   Check logs: oc logs -l app=ops-agent -n ${NAMESPACE} | grep -E 'MCP|tools'"
fi

# Get route URL
echo ""
if oc get route ops-agent -n ${NAMESPACE} &> /dev/null; then
    ROUTE_URL=$(oc get route ops-agent -n ${NAMESPACE} -o jsonpath='{.spec.host}')
    echo "✅ OpsAgent is available at: https://${ROUTE_URL}"
    echo ""
    echo "🔗 Access LangGraph Studio:"
    echo "   https://smith.langchain.com/studio/?baseUrl=https://${ROUTE_URL}"
    echo ""
    echo "🧪 Test the agent:"
    echo "   curl -k -X POST \"https://${ROUTE_URL}/runs/stream\" \\"
    echo "     -H \"Content-Type: application/json\" \\"
    echo "     -d '{\"assistant_id\": \"agent\", \"input\": {\"messages\": [{\"role\": \"human\", \"content\": \"List all Ansible inventories\"}]}, \"stream_mode\": \"values\"}'"
else
    echo "⚠️  Route not found. Check deployment."
fi

echo ""
echo "📝 Useful commands:"
echo "  View logs:        oc logs -f deployment/ops-agent -n ${NAMESPACE}"
echo "  Check MCP tools:  oc logs -l app=ops-agent -n ${NAMESPACE} | grep -E 'MCP|tools'"
echo "  Get pods:         oc get pods -n ${NAMESPACE}"
echo "  Get route:        oc get route ops-agent -n ${NAMESPACE}"
echo "  Restart:          oc rollout restart deployment/ops-agent -n ${NAMESPACE}"
echo "  Delete all:       oc delete all -l app=ops-agent -n ${NAMESPACE}"
echo ""
echo "✅ Deployment complete!"
