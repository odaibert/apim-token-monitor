#!/bin/bash

# This script deploys the Azure infrastructure for the AI Gateway Patterns.

# Exit immediately if a command exits with a non-zero status.
set -e

# Define variables
RESOURCE_GROUP_NAME="your-resource-group-name"
LOCATION="your-location"
BICEP_FILE="infrastructure/bicep/main.bicep"
PARAMETERS_FILE="infrastructure/bicep/parameters.json"

# Deploy the Bicep template
echo "Deploying Azure infrastructure..."
az deployment group create \
  --resource-group $RESOURCE_GROUP_NAME \
  --template-file $BICEP_FILE \
  --parameters @$PARAMETERS_FILE

echo "Deployment completed successfully."