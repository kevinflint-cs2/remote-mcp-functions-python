targetScope = 'resourceGroup'

@description('Key Vault name')
param name string
@description('Deployment location')
param location string
@description('Tags to apply to the Key Vault')
param tags object = {}
@description('Enable purge protection; defaults to false to ease test teardown. If an existing vault has purge protection enabled, this is ignored.')
param purgeProtectionEnabled bool = false

resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    tenantId: tenant().tenantId
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    // Purge protection can only be enabled (irreversible). Skip setting when false to avoid BadRequest on create.
    enablePurgeProtection: purgeProtectionEnabled ? true : null
    enableRbacAuthorization: true
    publicNetworkAccess: 'Enabled'
    sku: {
      family: 'A'
      name: 'standard'
    }
  }
}

output resourceId string = keyVault.id
output name string = keyVault.name
