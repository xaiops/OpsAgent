#!/bin/bash
# Deploy OpsAgent to OpenShift

set -e

# Configuration
NAMESPACE="${1:-ops-agent}"
IMAGE_TAG="${2:-latest}"

echo "🚀 Deploying OpsAgent to OpenShift namespace: ${NAMESPACE}"
echo "Using image: quay.io/rbrhssa/ops-agents:${IMAGE_TAG}"

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
    echo "✅ Using existing namespace: ${NAMESPACE}"
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
        echo "✅ Placeholder secret created. Update it with actual credentials!"
    else
        exit 1
    fi
fi

# Apply ConfigMap
echo "📝 Applying ConfigMap..."
oc apply -f deploy/configmap.yaml -n ${NAMESPACE}

# Apply Deployment
echo "🚢 Applying Deployment..."
if [ "$IMAGE_TAG" != "latest" ]; then
    # Update image tag in deployment
    sed "s|quay.io/rbrhssa/ops-agents:latest|quay.io/rbrhssa/ops-agents:${IMAGE_TAG}|g" deploy/deployment.yaml | oc apply -f - -n ${NAMESPACE}
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

# Get route URL
echo ""
if oc get route ops-agent -n ${NAMESPACE} &> /dev/null; then
    ROUTE_URL=$(oc get route ops-agent -n ${NAMESPACE} -o jsonpath='{.spec.host}')
    echo "✅ OpsAgent is available at: https://${ROUTE_URL}"
    echo ""
    echo "🔗 Access LangGraph Studio:"
    echo "   https://smith.langchain.com/studio/?baseUrl=https://${ROUTE_URL}"
else
    echo "⚠️  Route not found. Check deployment."
fi

echo ""
echo "📝 Useful commands:"
echo "  View logs:    oc logs -f deployment/ops-agent -n ${NAMESPACE}"
echo "  Get pods:     oc get pods -n ${NAMESPACE}"
echo "  Get route:    oc get route ops-agent -n ${NAMESPACE}"
echo "  Delete all:   oc delete all -l app=ops-agent -n ${NAMESPACE}"
