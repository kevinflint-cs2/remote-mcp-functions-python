targetScope = 'resourceGroup'

@description('Name of the target Key Vault')
param vaultName string
@description('Secret name')
param secretName string
@secure()
@description('Secret value')
param secretValue string

resource targetKeyVault 'Microsoft.KeyVault/vaults@2023-02-01' existing = {
  name: vaultName
}

resource secret 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = {
  parent: targetKeyVault
  name: secretName
  properties: {
    value: secretValue
  }
}

output secretUri string = '${targetKeyVault.id}/secrets/${secretName}'
