// =============================================================================
// Event Hub Module - Real-time Metrics Streaming
// =============================================================================
// This module creates an Event Hub namespace and hub for streaming
// APIM token metrics to a real-time dashboard.
// =============================================================================

@description('Location for resources')
param location string = resourceGroup().location

@description('Base name for resources')
param baseName string

@description('Unique suffix for resource names')
param uniqueSuffix string

// =============================================================================
// Variables
// =============================================================================
var eventHubNamespaceName = 'evhns-${baseName}-${uniqueSuffix}'
var eventHubName = 'token-metrics'
var consumerGroupName = 'dashboard'

// =============================================================================
// Event Hub Namespace
// =============================================================================
resource eventHubNamespace 'Microsoft.EventHub/namespaces@2024-01-01' = {
  name: eventHubNamespaceName
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
    capacity: 1
  }
  properties: {
    isAutoInflateEnabled: false
    maximumThroughputUnits: 0
    kafkaEnabled: true
    disableLocalAuth: false  // Enable SAS authentication for APIM logger
  }
}

// =============================================================================
// Event Hub
// =============================================================================
resource eventHub 'Microsoft.EventHub/namespaces/eventhubs@2024-01-01' = {
  parent: eventHubNamespace
  name: eventHubName
  properties: {
    messageRetentionInDays: 1
    partitionCount: 2
  }
}

// =============================================================================
// Consumer Group for Dashboard
// =============================================================================
resource consumerGroup 'Microsoft.EventHub/namespaces/eventhubs/consumergroups@2024-01-01' = {
  parent: eventHub
  name: consumerGroupName
}

// =============================================================================
// Authorization Rules
// =============================================================================
// Send policy for APIM
resource sendPolicy 'Microsoft.EventHub/namespaces/eventhubs/authorizationRules@2024-01-01' = {
  parent: eventHub
  name: 'apim-send'
  properties: {
    rights: ['Send']
  }
}

// Listen policy for Dashboard
resource listenPolicy 'Microsoft.EventHub/namespaces/eventhubs/authorizationRules@2024-01-01' = {
  parent: eventHub
  name: 'dashboard-listen'
  properties: {
    rights: ['Listen']
  }
}

// =============================================================================
// Outputs
// =============================================================================
output eventHubNamespaceName string = eventHubNamespace.name
output eventHubName string = eventHub.name
output eventHubNamespaceId string = eventHubNamespace.id
output eventHubId string = eventHub.id
output consumerGroupName string = consumerGroup.name

// Connection strings (for dashboard)
output eventHubSendConnectionString string = sendPolicy.listKeys().primaryConnectionString
output eventHubListenConnectionString string = listenPolicy.listKeys().primaryConnectionString
