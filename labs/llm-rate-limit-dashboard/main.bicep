// =============================================================================
// AI Gateway Lab - Token Rate Limiting
// =============================================================================
// This Bicep template deploys the infrastructure for the Token Rate Limiting lab:
// - Azure API Management (Consumption tier for fastest deployment ~2-3 min)
// - Azure OpenAI Service with GPT model deployment
// - Log Analytics Workspace and Application Insights
//
// WHY CONSUMPTION TIER?
// - Deploys in 2-3 minutes vs 30+ minutes for Developer/Standard tiers
// - Perfect for labs and educational purposes
// - Pay-per-execution model
// =============================================================================

@description('Location for all resources')
param location string = resourceGroup().location

@description('Base name for resources')
param baseName string = 'aigateway'

@description('APIM SKU - Use BasicV2 for LLM policies support')
@allowed(['Consumption', 'Developer', 'BasicV2', 'StandardV2'])
param apimSku string = 'BasicV2'

@description('Azure OpenAI model to deploy')
param modelName string = 'gpt-4o-mini'

@description('Model version')
param modelVersion string = '2024-07-18'

@description('Model deployment capacity (TPM in thousands)')
param modelCapacity int = 10

@description('Publisher email for APIM')
param publisherEmail string = 'admin@contoso.com'

@description('Publisher name for APIM')
param publisherName string = 'AI Gateway Lab'

@description('Unique suffix for resource names (ensures unique names per deployment)')
param deploymentSuffix string = utcNow('yyyyMMddHHmmss')

@description('Enable Event Hub for real-time dashboard streaming')
param enableEventHub bool = true

// =============================================================================
// Variables
// =============================================================================
// Combine resource group uniqueness + deployment timestamp for truly unique names
var uniqueSuffix = '${uniqueString(resourceGroup().id)}${substring(deploymentSuffix, 8, 6)}'
var apimName = 'apim-${baseName}-${uniqueSuffix}'
var openaiName = 'oai-${baseName}-${uniqueSuffix}'
var logAnalyticsName = 'log-${baseName}-${uniqueSuffix}'
var appInsightsName = 'appi-${baseName}-${uniqueSuffix}'

// Determine APIM capacity based on SKU
var apimCapacity = apimSku == 'Consumption' ? 0 : 1

// =============================================================================
// Event Hub Module (for real-time dashboard)
// =============================================================================
module eventHub 'modules/event-hub.bicep' = if (enableEventHub) {
  name: 'eventHubDeployment'
  params: {
    location: location
    baseName: baseName
    uniqueSuffix: uniqueSuffix
  }
}

// =============================================================================
// Log Analytics Workspace
// =============================================================================
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// =============================================================================
// Application Insights
// =============================================================================
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

// =============================================================================
// Azure OpenAI Service
// =============================================================================
resource openai 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: openaiName
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: openaiName
    publicNetworkAccess: 'Enabled'
  }
}

// =============================================================================
// GPT Model Deployment
// =============================================================================
resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openai
  name: modelName
  sku: {
    name: 'GlobalStandard'
    capacity: modelCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
  }
}

// =============================================================================
// API Management - Consumption Tier (Fastest Deployment)
// =============================================================================
resource apim 'Microsoft.ApiManagement/service@2023-09-01-preview' = {
  name: apimName
  location: location
  sku: {
    name: apimSku
    capacity: apimCapacity
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    publisherEmail: publisherEmail
    publisherName: publisherName
  }
}

// =============================================================================
// APIM Logger - Application Insights
// =============================================================================
resource apimLogger 'Microsoft.ApiManagement/service/loggers@2023-09-01-preview' = {
  parent: apim
  name: 'appinsights-logger'
  properties: {
    loggerType: 'applicationInsights'
    credentials: {
      instrumentationKey: appInsights.properties.InstrumentationKey
    }
    isBuffered: true
    resourceId: appInsights.id
  }
}

// =============================================================================
// APIM Logger - Event Hub (for real-time dashboard)
// =============================================================================
resource apimEventHubLogger 'Microsoft.ApiManagement/service/loggers@2023-09-01-preview' = if (enableEventHub) {
  parent: apim
  name: 'eventhub-logger'
  properties: {
    loggerType: 'azureEventHub'
    credentials: {
      connectionString: eventHub.outputs.eventHubSendConnectionString
      name: eventHub.outputs.eventHubName
    }
    isBuffered: false
  }
}

// =============================================================================
// APIM Diagnostics
// =============================================================================
resource apimDiagnostics 'Microsoft.ApiManagement/service/diagnostics@2023-09-01-preview' = {
  parent: apim
  name: 'applicationinsights'
  properties: {
    loggerId: apimLogger.id
    alwaysLog: 'allErrors'
    logClientIp: true
    sampling: {
      percentage: 100
      samplingType: 'fixed'
    }
  }
}

// =============================================================================
// APIM Named Value - OpenAI Endpoint
// =============================================================================
resource namedValueEndpoint 'Microsoft.ApiManagement/service/namedValues@2023-09-01-preview' = {
  parent: apim
  name: 'openai-endpoint'
  properties: {
    displayName: 'openai-endpoint'
    value: openai.properties.endpoint
    secret: false
  }
}

// =============================================================================
// APIM Backend - Azure OpenAI
// =============================================================================
resource backend 'Microsoft.ApiManagement/service/backends@2023-09-01-preview' = {
  parent: apim
  name: 'openai-backend'
  properties: {
    title: 'Azure OpenAI Backend'
    description: 'Backend pointing to Azure OpenAI Service'
    url: openai.properties.endpoint
    protocol: 'http'
    tls: {
      validateCertificateChain: true
      validateCertificateName: true
    }
  }
}

// =============================================================================
// OpenAI API Definition
// =============================================================================
resource openaiApi 'Microsoft.ApiManagement/service/apis@2023-09-01-preview' = {
  parent: apim
  name: 'openai'
  properties: {
    displayName: 'Azure OpenAI'
    description: 'Azure OpenAI Service API'
    path: 'openai'
    protocols: ['https']
    subscriptionRequired: true
    subscriptionKeyParameterNames: {
      header: 'api-key'
      query: 'api-key'
    }
    serviceUrl: '${openai.properties.endpoint}openai'
  }
}

// =============================================================================
// API Operations - Chat Completions
// =============================================================================
resource chatCompletionsOperation 'Microsoft.ApiManagement/service/apis/operations@2023-09-01-preview' = {
  parent: openaiApi
  name: 'chat-completions'
  properties: {
    displayName: 'Creates a completion for the chat message'
    method: 'POST'
    urlTemplate: '/deployments/{deployment-id}/chat/completions'
    templateParameters: [
      {
        name: 'deployment-id'
        required: true
        type: 'string'
        description: 'The deployment name'
      }
    ]
    request: {
      queryParameters: [
        {
          name: 'api-version'
          required: true
          type: 'string'
          description: 'API version'
        }
      ]
    }
  }
}

// =============================================================================
// API Policy - Token Rate Limiting
// =============================================================================
resource apiPolicy 'Microsoft.ApiManagement/service/apis/policies@2023-09-01-preview' = {
  parent: openaiApi
  name: 'policy'
  properties: {
    format: 'rawxml'
    value: loadTextContent('policy.xml')
  }
}

// =============================================================================
// Test Subscription
// =============================================================================
resource subscription 'Microsoft.ApiManagement/service/subscriptions@2023-09-01-preview' = {
  parent: apim
  name: 'test-subscription'
  properties: {
    displayName: 'Test Subscription'
    scope: '/apis/${openaiApi.name}'
    state: 'active'
    allowTracing: true
  }
}

// =============================================================================
// Role Assignment - Cognitive Services OpenAI User
// =============================================================================
// Allows APIM to call Azure OpenAI using managed identity
resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openai.id, apim.id, 'Cognitive Services OpenAI User')
  scope: openai
  properties: {
    principalId: apim.identity.principalId
    principalType: 'ServicePrincipal'
    // Cognitive Services OpenAI User role ID
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
  }
}

// =============================================================================
// Outputs
// =============================================================================
output apimName string = apim.name
output apimResourceId string = apim.id
output apimGatewayUrl string = apim.properties.gatewayUrl
output apimManagedIdentityPrincipalId string = apim.identity.principalId

output openaiName string = openai.name
output openaiEndpoint string = openai.properties.endpoint
output modelDeploymentName string = modelDeployment.name

output appInsightsConnectionString string = appInsights.properties.ConnectionString
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
output logAnalyticsWorkspaceId string = logAnalytics.properties.customerId

output subscriptionName string = subscription.name
output subscriptionId string = subscription.id

// Event Hub outputs (for dashboard connection)
output eventHubNamespace string = enableEventHub ? eventHub.outputs.eventHubNamespaceName : ''
output eventHubName string = enableEventHub ? eventHub.outputs.eventHubName : ''
output eventHubListenConnectionString string = enableEventHub ? eventHub.outputs.eventHubListenConnectionString : ''
output eventHubConsumerGroup string = enableEventHub ? eventHub.outputs.consumerGroupName : ''
output eventHubLoggerName string = enableEventHub ? apimEventHubLogger.name : ''
