# 📊 APIM Token Monitor Dashboard

Real-time monitoring dashboard for Azure API Management token rate limiting.

## Features

- **Live Metrics** - View APIM traffic from Azure Monitor
- **Interactive Testing** - Run rate limiting tests directly from the UI
- **Configurable** - Works with any APIM + Azure OpenAI deployment
- **Auto-refresh** - Metrics update every 30 seconds

## Quick Start

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Dashboard
```bash
streamlit run app.py
```

Dashboard opens at **http://localhost:8501**

## Configuration

### Option 1: UI Configuration
1. Click **🔧 Configure Services** in the sidebar
2. Enter your deployment details:
   - **Gateway URL**: `https://your-apim.azure-api.net`
   - **API Key**: Your APIM subscription key
   - **Model Name**: e.g., `gpt-4o-mini`
3. Click **💾 Save**

### Option 2: Environment Variables
```bash
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_RESOURCE_GROUP="your-resource-group"
export AZURE_APIM_NAME="your-apim-name"
export APIM_GATEWAY_URL="https://your-apim.azure-api.net"
export APIM_API_KEY="your-api-key"
export OPENAI_MODEL="gpt-4o-mini"
```

### Option 3: Config File
Create `config.json` in the dashboard directory:
```json
{
  "gateway_url": "https://your-apim.azure-api.net",
  "api_key": "your-subscription-key",
  "model_name": "gpt-4o-mini",
  "subscription_id": "your-subscription-id",
  "resource_group": "your-resource-group",
  "apim_name": "your-apim-name"
}
```

## Dashboard Sections

### APIM Traffic (Azure Monitor)
- Shows all requests to your APIM instance
- Includes traffic from any source (dashboard, notebooks, external apps)
- Has 1-2 minute delay due to Azure Monitor ingestion

### Rate Limiting Test
- Send configurable number of requests
- Observe success (200) vs rate limited (429) responses
- Live results appear immediately
- Metrics appear in Azure Monitor section after 1-2 minutes

## Requirements

- Python 3.8+
- Azure CLI (for Azure Monitor metrics)
- Active Azure subscription with APIM deployed

## Troubleshooting

### "Failed to fetch metrics"
- Ensure you're logged in: `az login`
- Verify Subscription ID, Resource Group, and APIM Name are correct
- Check Azure CLI is in PATH

### "Connection Error" on tests
- Verify Gateway URL is correct (no trailing slash)
- Check API Key is valid
- Ensure APIM is running and accessible
