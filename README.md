# 📊 APIM Token Monitor

![Azure](https://img.shields.io/badge/Azure-0078D4?style=flat&logo=microsoft-azure&logoColor=white)
![APIM](https://img.shields.io/badge/API%20Management-BasicV2-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B)
![License](https://img.shields.io/badge/License-MIT-green)

## Overview

**APIM Token Monitor** is a real-time monitoring dashboard for Azure API Management token rate limiting. Track Azure OpenAI token consumption, visualize rate limiting behavior, and test your AI Gateway configurations.

### ✨ Features

- 📈 **Real-time Metrics** - Monitor APIM traffic via Azure Monitor
- 🚦 **Rate Limit Testing** - Interactive testing to trigger and observe token limits
- ⚙️ **Configurable** - Works with any APIM + Azure OpenAI deployment
- 📊 **Visual Analytics** - Charts showing request distribution and token usage

## 🏗️ Architecture

```
┌──────────┐     ┌─────────────────────────────────────┐     ┌─────────────────┐
│  Client  │────▶│      Azure API Management           │────▶│  Azure OpenAI   │
│   App    │     │          (BasicV2 SKU)              │     │    Service      │
└──────────┘     │  ┌─────────────────────────────┐   │     │  ┌───────────┐  │
                 │  │    llm-token-limit Policy   │   │     │  │gpt-4o-mini│  │
                 │  │  • Token counting per key   │   │     │  └───────────┘  │
                 │  │  • Configurable TPM limit   │   │     └─────────────────┘
                 │  │  • 429 when exceeded        │   │
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
                 │        (Streamlit Dashboard)        │
                 │  • Real-time metrics visualization  │
                 │  • Interactive rate limit testing   │
                 │  • Configurable for any deployment  │
                 └─────────────────────────────────────┘
```

## 📋 Prerequisites

- Azure subscription with Contributor access
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) installed
- [Azure OpenAI access](https://aka.ms/oai/access) enabled
- Python 3.8+

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/your-org/apim-token-monitor.git
cd apim-token-monitor
```

### 2. Deploy Infrastructure
```bash
cd labs/llm-rate-limit-dashboard
# Run the deployment notebook
code llm-rate-limit-dashboard.ipynb
```

### 3. Launch the Dashboard
```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

The dashboard opens at **http://localhost:8501**

### 4. Configure Your Deployment
Click **🔧 Configure Services** in the sidebar and enter:
- APIM Gateway URL
- API Key (subscription key)
- Model deployment name
- Azure Monitor settings (optional)

## 📁 Repository Structure

```
apim-token-monitor/
├── labs/
│   └── llm-rate-limit-dashboard/    # Main lab
│       ├── llm-rate-limit-dashboard.ipynb  # Deployment notebook
│       ├── main.bicep               # Infrastructure as Code
│       ├── policy.xml               # APIM policy with llm-token-limit
│       └── dashboard/               # Streamlit monitoring dashboard
│           ├── app.py               # Dashboard application
│           ├── requirements.txt     # Python dependencies
│           └── README.md            # Dashboard documentation
├── infrastructure/                  # Shared infrastructure templates
├── shared/                          # Shared utilities
└── README.md
```

## 🧪 Lab: LLM Rate Limit Dashboard

The main lab deploys:
- **Azure API Management** (BasicV2 SKU) - Required for `llm-token-limit` policy
- **Azure OpenAI** with gpt-4o-mini model
- **Token rate limiting** at 500 TPM (configurable)

See [labs/llm-rate-limit-dashboard/](labs/llm-rate-limit-dashboard/) for details.

## 📚 Resources

- [llm-token-limit Policy Reference](https://learn.microsoft.com/en-us/azure/api-management/llm-token-limit-policy)
- [Azure OpenAI Quotas and Limits](https://learn.microsoft.com/en-us/azure/ai-services/openai/quotas-limits)
- [APIM AI Gateway Overview](https://learn.microsoft.com/en-us/azure/api-management/api-management-ai-gateway-overview)
- [Azure-Samples/AI-Gateway](https://github.com/Azure-Samples/AI-Gateway)

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
