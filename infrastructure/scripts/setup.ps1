# PowerShell script for setting up the environment for Azure iPaaS AI Gateway

# This script installs necessary modules, sets up environment variables, and prepares the system for deployment.

# Check if Azure PowerShell module is installed
if (-not (Get-Module -ListAvailable -Name Az)) {
    Write-Host "Installing Azure PowerShell module..."
    Install-Module -Name Az -AllowClobber -Scope CurrentUser -Force
}

# Import the Azure module
Import-Module Az

# Login to Azure account
Write-Host "Logging in to Azure..."
Connect-AzAccount

# Set the subscription (replace with your subscription ID)
$subscriptionId = "your-subscription-id"
Set-AzContext -SubscriptionId $subscriptionId

# Set environment variables (replace with your values)
$env:RESOURCE_GROUP_NAME = "your-resource-group-name"
$env:LOCATION = "your-location"

Write-Host "Environment setup complete. You can now deploy the infrastructure."