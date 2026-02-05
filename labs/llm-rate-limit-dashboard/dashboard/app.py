"""
Token Rate Limiting Dashboard
Real-time monitoring of APIM traffic using Azure Monitor
Configurable for any Azure APIM + OpenAI deployment
"""

import streamlit as st
import requests
import time
import json
import pandas as pd
import subprocess
import os
from datetime import datetime, timedelta
from pathlib import Path

# Page config
st.set_page_config(page_title="Token Rate Limiting", page_icon="🎯", layout="wide")

# Default configuration (can be overridden via UI or environment variables)
DEFAULT_CONFIG = {
    "subscription_id": os.environ.get("AZURE_SUBSCRIPTION_ID", ""),
    "resource_group": os.environ.get("AZURE_RESOURCE_GROUP", ""),
    "apim_name": os.environ.get("AZURE_APIM_NAME", ""),
    "gateway_url": os.environ.get("APIM_GATEWAY_URL", ""),
    "api_key": os.environ.get("APIM_API_KEY", ""),
    "model_name": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
    "tpm_limit": int(os.environ.get("TPM_LIMIT", "500")),
    "api_version": os.environ.get("OPENAI_API_VERSION", "2024-02-01"),
}

# Config file path
CONFIG_FILE = Path(__file__).parent / "config.json"

def load_config():
    """Load configuration from file or defaults"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                saved = json.load(f)
                return {**DEFAULT_CONFIG, **saved}
        except:
            pass
    return DEFAULT_CONFIG

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Failed to save config: {e}")
        return False

def detect_az_cli():
    """Detect Azure CLI path"""
    # Try common paths
    paths = [
        "/usr/local/bin/az",
        "/opt/homebrew/bin/az",
        os.path.expanduser("~/Library/Python/3.12/bin/az"),
        os.path.expanduser("~/Library/Python/3.11/bin/az"),
        os.path.expanduser("~/.local/bin/az"),
        "az"  # Fall back to PATH
    ]
    for p in paths:
        if p == "az" or os.path.exists(p):
            try:
                result = subprocess.run([p, "--version"], capture_output=True, timeout=5)
                if result.returncode == 0:
                    return p
            except:
                continue
    return "az"

def fetch_azure_metrics(config):
    """Get APIM metrics from Azure Monitor"""
    az_cli = detect_az_cli()
    resource = f"/subscriptions/{config['subscription_id']}/resourceGroups/{config['resource_group']}/providers/Microsoft.ApiManagement/service/{config['apim_name']}"
    cmd = [az_cli, "monitor", "metrics", "list", "--resource", resource, 
           "--metrics", "Requests", "--aggregation", "Total", "--interval", "PT1M", "-o", "json"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return {"error": result.stderr or "Failed to fetch metrics. Check your Azure CLI login and configuration."}
        
        data = json.loads(result.stdout)
        metrics = {"total": 0, "timeline": []}
        
        for m in data.get("value", []):
            for ts in m.get("timeseries", []):
                for pt in ts.get("data", []):
                    count = int(pt.get("total", 0) or 0)
                    metrics["total"] += count
                    metrics["timeline"].append({
                        "time": pd.to_datetime(pt["timeStamp"]).strftime("%H:%M"),
                        "requests": count
                    })
        
        metrics["timeline"] = metrics["timeline"][-15:]  # Last 15 minutes
        return metrics
    except subprocess.TimeoutExpired:
        return {"error": "Azure CLI command timed out"}
    except Exception as e:
        return {"error": str(e)}

def send_test_request(config, prompt):
    """Send request to APIM"""
    url = f"{config['gateway_url']}/openai/deployments/{config['model_name']}/chat/completions?api-version={config['api_version']}"
    headers = {"Content-Type": "application/json", "api-key": config['api_key']}
    payload = {"messages": [{"role": "user", "content": prompt}], "max_tokens": 100}
    
    start = time.time()
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        latency = round((time.time() - start) * 1000)
        
        if r.status_code == 200:
            tokens = r.json().get("usage", {}).get("total_tokens", 0)
            return {"status": "✅ Success", "code": 200, "tokens": tokens, "latency": latency}
        elif r.status_code == 429:
            retry_after = r.headers.get("Retry-After", "N/A")
            return {"status": "🚫 Rate Limited", "code": 429, "tokens": 0, "latency": latency, "retry_after": retry_after}
        else:
            return {"status": "❌ Error", "code": r.status_code, "tokens": 0, "latency": latency}
    except requests.exceptions.ConnectionError:
        return {"status": "❌ Connection Error", "code": 0, "tokens": 0, "latency": round((time.time()-start)*1000)}
    except requests.exceptions.Timeout:
        return {"status": "❌ Timeout", "code": 0, "tokens": 0, "latency": 30000}
    except Exception as e:
        return {"status": f"❌ {type(e).__name__}", "code": 0, "tokens": 0, "latency": round((time.time()-start)*1000)}

def validate_config(config):
    """Check if configuration is complete"""
    required = ["gateway_url", "api_key", "model_name"]
    missing = [k for k in required if not config.get(k)]
    return len(missing) == 0, missing

def validate_metrics_config(config):
    """Check if metrics configuration is complete"""
    required = ["subscription_id", "resource_group", "apim_name"]
    missing = [k for k in required if not config.get(k)]
    return len(missing) == 0, missing

# Initialize session state
if 'config' not in st.session_state:
    st.session_state.config = load_config()
if 'test_results' not in st.session_state:
    st.session_state.test_results = []
if 'metrics' not in st.session_state:
    st.session_state.metrics = None
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'show_config' not in st.session_state:
    # Show config panel if not configured
    valid, _ = validate_config(st.session_state.config)
    st.session_state.show_config = not valid

# =============================================================================
# SIDEBAR - Configuration
# =============================================================================
st.sidebar.title("⚙️ Configuration")

# Toggle config panel
if st.sidebar.button("🔧 Configure Services" if not st.session_state.show_config else "✅ Hide Configuration", 
                     use_container_width=True):
    st.session_state.show_config = not st.session_state.show_config
    st.rerun()

if st.session_state.show_config:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🌐 APIM Gateway")
    
    gateway_url = st.sidebar.text_input(
        "Gateway URL",
        value=st.session_state.config.get("gateway_url", ""),
        placeholder="https://your-apim.azure-api.net",
        help="Your APIM gateway URL (without trailing slash)"
    )
    
    api_key = st.sidebar.text_input(
        "API Key (Subscription Key)",
        value=st.session_state.config.get("api_key", ""),
        type="password",
        help="APIM subscription key for authentication"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🤖 OpenAI Settings")
    
    model_name = st.sidebar.text_input(
        "Model Deployment Name",
        value=st.session_state.config.get("model_name", "gpt-4o-mini"),
        help="The deployment name of your OpenAI model"
    )
    
    api_version = st.sidebar.text_input(
        "API Version",
        value=st.session_state.config.get("api_version", "2024-02-01"),
        help="Azure OpenAI API version"
    )
    
    tpm_limit = st.sidebar.number_input(
        "TPM Limit (for display)",
        value=st.session_state.config.get("tpm_limit", 500),
        min_value=1,
        help="Token per minute limit configured in your policy"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Azure Monitor (Optional)")
    st.sidebar.caption("Required for fetching APIM metrics")
    
    subscription_id = st.sidebar.text_input(
        "Subscription ID",
        value=st.session_state.config.get("subscription_id", ""),
        help="Azure subscription ID (GUID)"
    )
    
    resource_group = st.sidebar.text_input(
        "Resource Group",
        value=st.session_state.config.get("resource_group", ""),
        help="Resource group containing your APIM"
    )
    
    apim_name = st.sidebar.text_input(
        "APIM Service Name",
        value=st.session_state.config.get("apim_name", ""),
        help="Name of your API Management service"
    )
    
    st.sidebar.markdown("---")
    col1, col2 = st.sidebar.columns(2)
    
    if col1.button("💾 Save", use_container_width=True):
        new_config = {
            "gateway_url": gateway_url.rstrip("/"),
            "api_key": api_key,
            "model_name": model_name,
            "api_version": api_version,
            "tpm_limit": tpm_limit,
            "subscription_id": subscription_id,
            "resource_group": resource_group,
            "apim_name": apim_name
        }
        st.session_state.config = new_config
        if save_config(new_config):
            st.sidebar.success("✅ Saved!")
            time.sleep(0.5)
            st.rerun()
    
    if col2.button("🔄 Reset", use_container_width=True):
        st.session_state.config = DEFAULT_CONFIG
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
        st.rerun()

# Validation status
valid_api, missing_api = validate_config(st.session_state.config)
valid_metrics, missing_metrics = validate_metrics_config(st.session_state.config)

if not valid_api:
    st.sidebar.warning(f"⚠️ Configure: {', '.join(missing_api)}")
else:
    st.sidebar.success("✅ API Configured")

st.sidebar.markdown("---")
st.sidebar.subheader("🧪 Test Settings")
num_requests = st.sidebar.slider("Requests", 1, 50, 20)
delay = st.sidebar.slider("Delay (ms)", 0, 1000, 100)

if st.sidebar.button("🗑️ Clear Results"):
    st.session_state.test_results = []
    st.rerun()

# =============================================================================
# MAIN CONTENT
# =============================================================================
st.title("🎯 Token Rate Limiting Dashboard")

# Show current config summary
config = st.session_state.config
if valid_api:
    st.caption(f"**APIM:** `{config.get('apim_name') or 'Custom Gateway'}` | **Model:** `{config['model_name']}` | **Limit:** {config['tpm_limit']} TPM")
else:
    st.warning("👈 Please configure your Azure services in the sidebar to get started.")
    st.stop()

# =============================================================================
# AZURE METRICS SECTION
# =============================================================================
st.header("📊 APIM Traffic (All Sources)")
st.caption("⏱️ Azure Monitor has 1-2 min delay. Shows traffic from dashboards, notebooks, scripts, etc.")

col1, col2 = st.columns([3, 1])
with col2:
    metrics_enabled = valid_metrics
    if metrics_enabled:
        if st.button("🔄 Fetch Metrics", use_container_width=True):
            with st.spinner("Loading metrics..."):
                st.session_state.metrics = fetch_azure_metrics(config)
                st.session_state.last_update = datetime.now()
            st.rerun()
    else:
        st.button("🔄 Fetch Metrics", disabled=True, use_container_width=True)
        st.caption("⚠️ Configure Azure Monitor settings")

with col1:
    if st.session_state.metrics:
        m = st.session_state.metrics
        if "error" in m:
            st.error(m["error"])
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Requests (30 min)", m["total"])
            c2.metric("Data Points", len(m["timeline"]))
            if st.session_state.last_update:
                c3.metric("Updated", st.session_state.last_update.strftime("%H:%M:%S"))
            
            if m["timeline"]:
                df = pd.DataFrame(m["timeline"])
                st.bar_chart(df.set_index("time"), height=200)
    elif metrics_enabled:
        st.info("👆 Click **Fetch Metrics** to see all APIM traffic")
    else:
        st.info("📝 Configure **Subscription ID**, **Resource Group**, and **APIM Name** in the sidebar to enable metrics")

st.divider()

# =============================================================================
# TEST SECTION
# =============================================================================
st.header("🧪 Rate Limiting Test")

if st.button("🚀 Run Test", type="primary", use_container_width=True):
    st.session_state.test_results = []
    progress = st.progress(0)
    results_container = st.empty()
    
    for i in range(num_requests):
        progress.progress((i+1)/num_requests, f"Request {i+1}/{num_requests}")
        result = send_test_request(config, f"Say hello {i+1}")
        result["#"] = i + 1
        st.session_state.test_results.append(result)
        
        # Live update
        with results_container.container():
            df = pd.DataFrame(st.session_state.test_results)
            success = len(df[df["code"] == 200])
            limited = len(df[df["code"] == 429])
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total", len(df))
            c2.metric("✅ Success", success)
            c3.metric("🚫 Rate Limited", limited)
            c4.metric("📊 Tokens", df["tokens"].sum())
        
        if delay > 0 and i < num_requests - 1:
            time.sleep(delay / 1000)
    
    progress.empty()
    st.success(f"Done! {success}/{num_requests} succeeded, {limited} rate limited")
    if metrics_enabled:
        st.info("💡 Wait 1-2 min, then click **Fetch Metrics** to see these in Azure Monitor")

# Show results
if st.session_state.test_results:
    df = pd.DataFrame(st.session_state.test_results)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📋 Results")
        display_cols = ["#", "status", "code", "tokens", "latency"]
        if "retry_after" in df.columns:
            display_cols.append("retry_after")
        st.dataframe(df[display_cols], hide_index=True, height=300)
    
    with col2:
        st.subheader("📊 Distribution")
        counts = df["status"].value_counts()
        st.bar_chart(counts, height=300)

# =============================================================================
# FOOTER
# =============================================================================
st.divider()
with st.expander("ℹ️ Connection Info"):
    st.json({
        "gateway_url": config.get("gateway_url", "Not configured"),
        "model": config.get("model_name", "Not configured"),
        "api_version": config.get("api_version", "Not configured"),
        "tpm_limit": config.get("tpm_limit", "Not configured"),
        "apim_name": config.get("apim_name", "Not configured"),
        "resource_group": config.get("resource_group", "Not configured"),
    })
