targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources & Flex Consumption Function App')
@allowed([
  'australiaeast'
  'australiasoutheast'
  'brazilsouth'
  'canadacentral'
  'centralindia'
  'centralus'
  'eastasia'
  'eastus'
  'eastus2'
  'eastus2euap'
  'francecentral'
  'germanywestcentral'
  'italynorth'
  'japaneast'
  'koreacentral'
  'northcentralus'
  'northeurope'
  'norwayeast'
  'southafricanorth'
  'southcentralus'
  'southeastasia'
  'southindia'
  'spaincentral'
  'swedencentral'
  'uaenorth'
  'uksouth'
  'ukwest'
  'westcentralus'
  'westeurope'
  'westus'
  'westus2'
  'westus3'
])
@metadata({
  azd: {
    type: 'location'
  }
})
param location string
param vnetEnabled bool
param apiServiceName string = ''
param apiUserAssignedIdentityName string = ''
param applicationInsightsName string = ''
param appServicePlanName string = ''
param logAnalyticsName string = ''
param resourceGroupName string = ''
param storageAccountName string = ''
param vNetName string = ''
@description('Resource ID of an existing Key Vault that stores the AbuseIPDB API key.')
param keyVaultResourceId string = ''
@description('Optional name for the Key Vault to create when no existing vault is provided.')
param keyVaultName string = ''
@description('Enable purge protection on the Key Vault. Defaults to false to ease test teardown; enable in production.')
param keyVaultPurgeProtectionEnabled bool = false
@description('Secret URI for the AbuseIPDB API key in Key Vault.')
param abuseIpDbSecretUri string = ''
@secure()
@description('Optional AbuseIPDB API key value to seed into Key Vault as a secret named AbuseIpDbAPIKey.')
param abuseIpDbSecretValue string = ''
@description('Identity type for the Function App managed identity.')
@allowed(['SystemAssigned', 'UserAssigned'])
param identityType string = 'SystemAssigned'
@description('Id of the user identity to be used for testing and debugging. This is not required in production. Leave empty if not needed.')
param principalId string = deployer().objectId

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }
var functionAppName = !empty(apiServiceName) ? apiServiceName : '${abbrs.webSitesFunctions}api-${resourceToken}'
var deploymentStorageContainerName = 'app-package-${take(functionAppName, 32)}-${take(toLower(uniqueString(functionAppName, resourceToken)), 7)}'
var keyVaultResourceGroup = !empty(keyVaultResourceId) ? split(keyVaultResourceId, '/')[4] : ''
var keyVaultNameFromResourceId = !empty(keyVaultResourceId) ? split(keyVaultResourceId, '/')[8] : ''

// Organize resources in a resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

// Determine Key Vault naming and scoping when creating a dedicated vault
var keyVaultNameToCreate = !empty(keyVaultName) ? keyVaultName : 'kv-${resourceToken}'
var keyVaultResourceGroupEffective = !empty(keyVaultResourceGroup) ? keyVaultResourceGroup : rg.name

module keyVaultModule './app/keyvault.bicep' = if (empty(keyVaultResourceId)) {
  name: 'keyVault'
  scope: rg
  params: {
    name: keyVaultNameToCreate
    location: location
    tags: tags
    purgeProtectionEnabled: keyVaultPurgeProtectionEnabled
  }
}

var keyVaultResourceIdEffective = !empty(keyVaultResourceId) ? keyVaultResourceId : keyVaultModule.outputs.resourceId
var keyVaultNameEffective = !empty(keyVaultNameFromResourceId) ? keyVaultNameFromResourceId : keyVaultModule.outputs.name

// User assigned managed identity to be used by the function app to reach storage and other dependencies
// Assign specific roles to this identity in the RBAC module
module apiUserAssignedIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.4.1' = {
  name: 'apiUserAssignedIdentity'
  scope: rg
  params: {
    location: location
    tags: tags
    name: !empty(apiUserAssignedIdentityName) ? apiUserAssignedIdentityName : '${abbrs.managedIdentityUserAssignedIdentities}api-${resourceToken}'
  }
}

// Create an App Service Plan to group applications under the same payment plan and SKU
module appServicePlan 'br/public:avm/res/web/serverfarm:0.1.1' = {
  name: 'appserviceplan'
  scope: rg
  params: {
    name: !empty(appServicePlanName) ? appServicePlanName : '${abbrs.webServerFarms}${resourceToken}'
    sku: {
      name: 'FC1'
      tier: 'FlexConsumption'
    }
    reserved: true
    location: location
    tags: tags
  }
}

// Seed AbuseIPDB secret into the vault when provided
module abuseIpDbSecret './app/keyvault-secret.bicep' = if (!empty(abuseIpDbSecretValue)) {
  name: 'abuseIpDbSecret'
  scope: resourceGroup(keyVaultResourceGroupEffective)
  params: {
    vaultName: keyVaultNameEffective
    secretName: 'AbuseIpDbAPIKey'
    secretValue: abuseIpDbSecretValue
  }
}

module api './app/api.bicep' = {
  name: 'api'
  scope: rg
  params: {
    name: functionAppName
    location: location
    tags: tags
    applicationInsightsName: monitoring.outputs.name
    appServicePlanId: appServicePlan.outputs.resourceId
    runtimeName: 'python'
    runtimeVersion: '3.12'
    storageAccountName: storage.outputs.name
    enableBlob: storageEndpointConfig.enableBlob
    enableQueue: storageEndpointConfig.enableQueue
    enableTable: storageEndpointConfig.enableTable
    deploymentStorageContainerName: deploymentStorageContainerName
    identityId: apiUserAssignedIdentity.outputs.resourceId
    identityClientId: apiUserAssignedIdentity.outputs.clientId
    identityType: identityType
    appSettings: !empty(abuseIpDbSecretUriEffective) ? {
      ABUSEIPDB_API_KEY: '@Microsoft.KeyVault(SecretUri=${abuseIpDbSecretUriEffective})'
    } : {}
    virtualNetworkSubnetId: vnetEnabled ? serviceVirtualNetwork.outputs.appSubnetID : ''
  }
}

// Backing storage for Azure functions backend API
module storage 'br/public:avm/res/storage/storage-account:0.8.3' = {
  name: 'storage'
  scope: rg
  params: {
    name: !empty(storageAccountName) ? storageAccountName : '${abbrs.storageStorageAccounts}${resourceToken}'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false // Disable local authentication methods as per policy
    dnsEndpointType: 'Standard'
    publicNetworkAccess: vnetEnabled ? 'Disabled' : 'Enabled'
    networkAcls: vnetEnabled ? {
      defaultAction: 'Deny'
      bypass: 'None'
    } : {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
    blobServices: {
      containers: [{name: deploymentStorageContainerName}]
    }
    minimumTlsVersion: 'TLS1_2'  // Enforcing TLS 1.2 for better security
    location: location
    tags: tags
  }
}

// Define the configuration object locally to pass to the modules
var storageEndpointConfig = {
  enableBlob: true  // Required for AzureWebJobsStorage, .zip deployment, Event Hubs trigger and Timer trigger checkpointing
  enableQueue: true  // Required for Durable Functions and MCP trigger
  enableTable: false  // Required for Durable Functions and OpenAI triggers and bindings
  enableFiles: false   // Not required, used in legacy scenarios
  allowUserIdentityPrincipal: true   // Allow interactive user identity to access for testing and debugging
}

// Resolve secret URI preference: seeded secret takes precedence, otherwise use provided URI
var abuseIpDbSecretUriEffective = !empty(abuseIpDbSecretValue) ? abuseIpDbSecret.outputs.secretUri : (!empty(abuseIpDbSecretUri) ? abuseIpDbSecretUri : '')

// Resolve which principal should receive storage and monitoring roles
var functionIdentityPrincipalId = identityType == 'SystemAssigned' ? api.outputs.SERVICE_API_IDENTITY_PRINCIPAL_ID : apiUserAssignedIdentity.outputs.principalId

// Consolidated Role Assignments
module rbac 'app/rbac.bicep' = {
  name: 'rbacAssignments'
  scope: rg
  params: {
    storageAccountName: storage.outputs.name
    appInsightsName: monitoring.outputs.name
    functionIdentityPrincipalId: functionIdentityPrincipalId
    userIdentityPrincipalId: principalId
    enableBlob: storageEndpointConfig.enableBlob
    enableQueue: storageEndpointConfig.enableQueue
    enableTable: storageEndpointConfig.enableTable
    allowUserIdentityPrincipal: storageEndpointConfig.allowUserIdentityPrincipal
  }
  dependsOn: [
    api
  ]
}

// Grant the Function App system-assigned identity access to Key Vault secrets
module keyVaultAccess 'app/keyvault-role.bicep' = if (identityType == 'SystemAssigned' && !empty(keyVaultNameEffective)) {
  name: 'keyVaultSecretsAccess'
  scope: resourceGroup(keyVaultResourceGroupEffective)
  params: {
    keyVaultName: keyVaultNameEffective
    principalId: functionIdentityPrincipalId
    roleDefinitionId: '4633458b-17de-408a-b874-0445c86b69e6'
    functionAppName: functionAppName
  }
}

// Virtual Network & private endpoint to blob storage
module serviceVirtualNetwork 'app/vnet.bicep' =  if (vnetEnabled) {
  name: 'serviceVirtualNetwork'
  scope: rg
  params: {
    location: location
    tags: tags
    vNetName: !empty(vNetName) ? vNetName : '${abbrs.networkVirtualNetworks}${resourceToken}'
  }
}

module storagePrivateEndpoint 'app/storage-PrivateEndpoint.bicep' = if (vnetEnabled) {
  name: 'servicePrivateEndpoint'
  scope: rg
  params: {
    location: location
    tags: tags
    virtualNetworkName: !empty(vNetName) ? vNetName : '${abbrs.networkVirtualNetworks}${resourceToken}'
    subnetName: vnetEnabled ? serviceVirtualNetwork.outputs.peSubnetName : '' // Keep conditional check for safety, though module won't run if !vnetEnabled
    resourceName: storage.outputs.name
    enableBlob: storageEndpointConfig.enableBlob
    enableQueue: storageEndpointConfig.enableQueue
    enableTable: storageEndpointConfig.enableTable
  }
}

// Monitor application with Azure Monitor - Log Analytics and Application Insights
module logAnalytics 'br/public:avm/res/operational-insights/workspace:0.11.1' = {
  name: '${uniqueString(deployment().name, location)}-loganalytics'
  scope: rg
  params: {
    name: !empty(logAnalyticsName) ? logAnalyticsName : '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    location: location
    tags: tags
    dataRetention: 30
  }
}
 
module monitoring 'br/public:avm/res/insights/component:0.6.0' = {
  name: '${uniqueString(deployment().name, location)}-appinsights'
  scope: rg
  params: {
    name: !empty(applicationInsightsName) ? applicationInsightsName : '${abbrs.insightsComponents}${resourceToken}'
    location: location
    tags: tags
    workspaceResourceId: logAnalytics.outputs.resourceId
    disableLocalAuth: true
  }
}

// App outputs
output APPLICATIONINSIGHTS_CONNECTION_STRING string = monitoring.outputs.connectionString
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output SERVICE_API_NAME string = api.outputs.SERVICE_API_NAME
output AZURE_FUNCTION_NAME string = api.outputs.SERVICE_API_NAME
output KEY_VAULT_RESOURCE_ID string = keyVaultResourceIdEffective
output ABUSEIPDB_SECRET_URI string = abuseIpDbSecretUriEffective
