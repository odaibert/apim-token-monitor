param location string = resourceGroup().location
param environment string = 'dev'

var appName = 'aiGateway'
var apiManagementName = '${appName}APIM'
var functionAppName = '${appName}FunctionApp'
var aiServicesName = '${appName}AIServices'

resource apiManagement 'Microsoft.ApiManagement/service@2021-04-01-preview' = {
  name: apiManagementName
  location: location
  sku: {
    name: 'Consumption'
    capacity: 0
  }
  properties: {
    publisherEmail: 'publisher@example.com'
    publisherName: 'AI Gateway Publisher'
  }
}

resource functionApp 'Microsoft.Web/sites@2021-02-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp'
  properties: {
    serverFarmId: functionAppServicePlan.id
    httpsOnly: true
  }
}

resource functionAppServicePlan 'Microsoft.Web/serverfarms@2021-02-01' = {
  name: '${functionAppName}Plan'
  location: location
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
    capacity: 0
  }
}

resource aiServices 'Microsoft.CognitiveServices/accounts@2021-04-30' = {
  name: aiServicesName
  location: location
  sku: {
    name: 'S1'
    tier: 'Standard'
  }
  properties: {
    kind: 'TextAnalytics'
    apiProperties: {
      'apiVersion': 'v3.1'
    }
  }
}

output apiManagementEndpoint string = apiManagement.properties.gatewayUrl
output functionAppUrl string = 'https://${functionApp.name}.azurewebsites.net'
output aiServicesEndpoint string = 'https://${aiServices.name}.cognitiveservices.azure.com/'