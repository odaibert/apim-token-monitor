# 🚦 LLM Rate Limit Dashboard

This lab demonstrates how to implement **token-based rate limiting** using Azure API Management with a real-time monitoring dashboard.

## Overview

The [`llm-token-limit`](https://learn.microsoft.com/en-us/azure/api-management/llm-token-limit-policy) policy prevents Azure OpenAI API usage spikes by limiting token consumption per minute per subscription key. When the token limit is exceeded, the caller receives a **429 Too Many Requests** response with a `Retry-After` header.

## What You'll Learn

- Deploy APIM (BasicV2 SKU) and Azure OpenAI using Bicep
- Configure token rate limiting policies (500 TPM)
- Test the API and observe rate limiting in action
- Monitor traffic with a real-time Streamlit dashboard

## Architecture

```
┌──────────┐     ┌─────────────────────────────────────┐     ┌─────────────────┐
│  Client  │────▶│      Azure API Management           │────▶│  Azure OpenAI   │
│   App    │     │          (BasicV2 SKU)              │     │    Service      │
└──────────┘     │  ┌─────────────────────────────┐   │     │  ┌───────────┐  │
                 │  │    llm-token-limit Policy   │   │     │  │gpt-4o-mini│  │
                 │  │  • 500 TPM per key          │   │     │  └───────────┘  │
                 │  │  • 429 when exceeded        │   │     └─────────────────┘
                 │  └─────────────────────────────┘   │
                 └─────────────────────────────────────┘
                                │
                                ▼
                 ┌─────────────────────────────────────┐
                 │        Azure Monitor Metrics        │
                 └─────────────────────────────────────┘
                                │
                                ▼
                 ┌─────────────────────────────────────┐
                 │     📊 APIM Token Monitor           │
                 │  • Real-time metrics visualization  │
                 │  • Interactive rate limit testing   │
                 └─────────────────────────────────────┘
```

## Prerequisites

- Azure subscription with Contributor access
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) installed
- [Python 3.8+](https://www.python.org/) with pip
- [Azure OpenAI access](https://aka.ms/oai/access) enabled

> ⚠️ **Important**: The `llm-token-limit` policy requires **APIM BasicV2 or higher** SKU.

## Quick Start

1. **Open the notebook**:
   ```bash
   code llm-rate-limit-dashboard.ipynb
   ```

2. **Run all cells** or execute step by step

3. **Observe rate limiting** when token quota is exceeded

4. **Launch the dashboard** for real-time monitoring:
   ```bash
   cd dashboard
   pip install -r requirements.txt
   streamlit run app.py
   ```

## Files

| File | Description |
|------|-------------|
| [llm-rate-limit-dashboard.ipynb](llm-rate-limit-dashboard.ipynb) | Main deployment & testing notebook |
| [main.bicep](main.bicep) | Infrastructure as Code (APIM + OpenAI) |
| [policy.xml](policy.xml) | APIM policy with `llm-token-limit` |
| [dashboard/](dashboard/) | Real-time monitoring dashboard |

## Key Policy Configuration

```xml
<llm-token-limit
    tokens-per-minute="500"
    counter-key="@(context.Subscription.Id)"
    estimate-prompt-tokens="true"
    remaining-tokens-header-name="x-ratelimit-remaining-tokens" />
```

## Expected Results

After running multiple requests, you'll see:
- ✅ Successful requests (200) until token limit reached
- 🚫 Rate limited requests (429) once limit exceeded
- 📊 Dashboard showing request distribution

## Monitoring Dashboard

The included Streamlit dashboard provides:
- **Real-time metrics** from Azure Monitor
- **Interactive testing** to trigger rate limiting
- **Configurable settings** for different deployments

See [dashboard/README.md](dashboard/README.md) for details.

## Clean Up

Delete all resources when finished:
```bash
az group delete --name lab-token-rate-limiting --yes --no-wait
```

## Resources

- [llm-token-limit Policy Reference](https://learn.microsoft.com/en-us/azure/api-management/llm-token-limit-policy)
- [Azure OpenAI Quotas and Limits](https://learn.microsoft.com/en-us/azure/ai-services/openai/quotas-limits)
- [APIM AI Gateway Overview](https://learn.microsoft.com/en-us/azure/api-management/api-management-ai-gateway-overview)
- [Azure-Samples/AI-Gateway](https://github.com/Azure-Samples/AI-Gateway)
