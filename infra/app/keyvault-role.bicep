targetScope = 'resourceGroup'

@description('Name of the existing Key Vault.')
param keyVaultName string
@description('Principal ID to grant Key Vault access to.')
param principalId string
@description('Role definition ID to assign.')
param roleDefinitionId string
@description('Function App name used to derive a stable role assignment name.')
param functionAppName string

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource keyVaultSecretsRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, functionAppName, roleDefinitionId)
  scope: keyVault
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionId)
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}
