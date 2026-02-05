# =============================================================================
# AI Gateway - Shared Utilities
# =============================================================================
# Helper functions for running Azure CLI commands, printing formatted output,
# and managing Azure resources. Based on the Azure-Samples/AI-Gateway pattern.
# =============================================================================

import datetime
import json
import os
import subprocess
import time
import traceback

# =============================================================================
# ANSI Color Codes for Terminal Output
# =============================================================================
RESET_FORMATTING = "\x1b[0m"
BOLD_BLUE = "\x1b[1;34m"
BOLD_RED = "\x1b[1;31m"
BOLD_GREEN = "\x1b[1;32m"
BOLD_YELLOW = "\x1b[1;33m"

# =============================================================================
# Print Helper Functions
# =============================================================================
print_command = lambda command='': print(f"⚙️ {BOLD_BLUE}Running: {command} {RESET_FORMATTING}")
print_error = lambda message, output='', duration='': print(f"❌ {BOLD_RED}{message}{RESET_FORMATTING} ⌚ {datetime.datetime.now().time()} {duration}{' ' if output else ''}{output}")
print_info = lambda message: print(f"👉🏽 {BOLD_BLUE}{message}{RESET_FORMATTING}")
print_message = lambda message, output='', duration='': print(f"👉🏽 {BOLD_GREEN}{message}{RESET_FORMATTING} ⌚ {datetime.datetime.now().time()} {duration}{' ' if output else ''}{output}")
print_ok = lambda message, output='', duration='': print(f"✅ {BOLD_GREEN}{message}{RESET_FORMATTING} ⌚ {datetime.datetime.now().time()} {duration}{' ' if output else ''}{output}")
print_warning = lambda message, output='', duration='': print(f"⚠️ {BOLD_YELLOW}{message}{RESET_FORMATTING} ⌚ {datetime.datetime.now().time()} {duration}{' ' if output else ''}{output}")


# =============================================================================
# Output Class - Wraps command execution results
# =============================================================================
class Output:
    """Wrapper for command execution results with JSON parsing support."""
    
    def __init__(self, success: bool, text: str):
        self.success = success
        self.text = text
        
        try:
            self.json_data = json.loads(text)
        except:
            self.json_data = {}  # Return empty dict if not valid JSON


# =============================================================================
# Azure CLI Path Configuration
# =============================================================================
# Use the user-installed Azure CLI path directly
AZ_CLI_PATH = '/Users/odaibert/Library/Python/3.12/bin/az'


# =============================================================================
# Command Execution
# =============================================================================
def run(command: str, ok_message: str = '', error_message: str = '', 
        print_output: bool = False, print_command_to_run: bool = True) -> Output:
    """
    Execute a shell command and return the result.
    
    Args:
        command: The shell command to execute
        ok_message: Message to print on success
        error_message: Message to print on failure
        print_output: Whether to print command output
        print_command_to_run: Whether to print the command being executed
    
    Returns:
        Output object with success status, text output, and parsed JSON
    """
    # Replace 'az ' with the full path to Azure CLI
    if command.startswith('az '):
        command = AZ_CLI_PATH + command[2:]
    
    if print_command_to_run:
        print_command(command)
    
    start_time = time.time()
    
    try:
        completed_process = subprocess.run(
            command, 
            shell=True, 
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, 
            text=True
        )
        output_text = completed_process.stdout
        success = completed_process.returncode == 0
    except subprocess.CalledProcessError as e:
        output_text = e.output.decode("utf-8") if hasattr(e.output, 'decode') else str(e.output)
        success = False
    
    minutes, seconds = divmod(time.time() - start_time, 60)
    duration = f"[{int(minutes)}m:{int(seconds)}s]"
    
    print_fn = print_ok if success else print_error
    
    if ok_message or error_message:
        msg = ok_message if success else error_message
        output_to_print = output_text if not success or print_output else ""
        print_fn(msg, output_to_print, duration)
    
    return Output(success, output_text)


# =============================================================================
# Azure Subscription Functions
# =============================================================================
def get_current_subscription() -> str | None:
    """Get the current Azure subscription ID."""
    try:
        output = run("az account show", "Retrieved az account", "Failed to get the current az account")
        
        if output.success and output.json_data:
            subscription_id = output.json_data['id']
            subscription_name = output.json_data['name']
            print_info(f"Using Subscription ID: {subscription_id} ({subscription_name})")
            return subscription_id
        else:
            print_error("No current subscription found.")
            return None
    except Exception as e:
        print_error(f"Error retrieving current subscription: {e}")
        return None


# =============================================================================
# Resource Group Functions
# =============================================================================
def create_resource_group(resource_group_name: str, resource_group_location: str = None):
    """
    Create an Azure resource group if it doesn't exist.
    
    Args:
        resource_group_name: Name of the resource group
        resource_group_location: Azure region for the resource group
    """
    if not resource_group_name:
        print_error('Please specify the resource group name.')
        return
    
    output = run(f"az group show --name {resource_group_name}", print_command_to_run=False)
    
    if output.success:
        print_info(f"Using existing resource group '{resource_group_name}'")
    else:
        if not resource_group_location:
            print_error('Please specify the resource group location.')
            return
        
        print_info(f"Resource group {resource_group_name} does not exist. Creating...")
        output = run(
            f"az group create --name {resource_group_name} --location {resource_group_location} --tags source=ai-gateway",
            f"Resource group '{resource_group_name}' created",
            f"Failed to create the resource group '{resource_group_name}'"
        )


# =============================================================================
# Deployment Output Functions
# =============================================================================
def get_deployment_output(output: Output, output_property: str, 
                          output_label: str = '', secure: bool = False) -> str:
    """
    Extract a specific output from a deployment result.
    
    Args:
        output: The Output object from a deployment show command
        output_property: The name of the output property to extract
        output_label: Label to print with the output value
        secure: If True, mask the output value in logs
    
    Returns:
        The output value as a string
    """
    try:
        deployment_output = output.json_data['properties']['outputs'][output_property]['value']
        
        if output_label:
            if secure:
                print_info(f"{output_label}: ****{str(deployment_output)[-4:]}")
            else:
                print_info(f"{output_label}: {deployment_output}")
        
        return str(deployment_output)
    except Exception as e:
        error = f"Failed to retrieve output property: '{output_property}'\nError: {e}"
        print_error(error)
        raise Exception(error)


# =============================================================================
# Response Printing Functions
# =============================================================================
def print_response(response):
    """Print HTTP response details."""
    print("Response headers: ", response.headers)
    
    if response.status_code == 200:
        print_ok(f"Status Code: {response.status_code}")
        data = json.loads(response.text)
        print(json.dumps(data, indent=4))
    else:
        print_warning(f"Status Code: {response.status_code}")
        print(response.text)


def print_response_code(response):
    """Print formatted HTTP response status code."""
    if 200 <= response.status_code < 300:
        status_code_str = f"{BOLD_GREEN}{response.status_code} - {response.reason}{RESET_FORMATTING}"
    elif response.status_code >= 400:
        status_code_str = f"{BOLD_RED}{response.status_code} - {response.reason}{RESET_FORMATTING}"
    else:
        status_code_str = str(response.status_code)
    
    print(f"Response status: {status_code_str}")


# =============================================================================
# Cleanup Functions
# =============================================================================
def cleanup_resources(deployment_name: str, resource_group_name: str = None):
    """
    Clean up all resources associated with a deployment.
    
    Args:
        deployment_name: Name of the deployment
        resource_group_name: Name of the resource group (defaults to lab-{deployment_name})
    """
    if not deployment_name:
        print_error("Missing deployment name parameter.")
        return
    
    if not resource_group_name:
        resource_group_name = f"lab-{deployment_name}"
    
    try:
        print_info(f"🧹 Cleaning up resource group '{resource_group_name}'...")
        
        # Check if deployment exists
        output = run(
            f"az deployment group show --name {deployment_name} -g {resource_group_name} -o json",
            "Deployment retrieved",
            "Failed to retrieve the deployment"
        )
        
        if output.success and output.json_data:
            provisioning_state = output.json_data.get("properties", {}).get("provisioningState")
            print_info(f"Deployment provisioning state: {provisioning_state}")
            
            # Delete Cognitive Services accounts (with purge)
            output = run(
                f"az cognitiveservices account list -g {resource_group_name}",
                "Listed Cognitive Services accounts",
                "Failed to list Cognitive Services accounts"
            )
            if output.success and output.json_data:
                for resource in output.json_data:
                    name = resource['name']
                    location = resource['location']
                    print_info(f"Deleting Cognitive Services '{name}'...")
                    run(f"az cognitiveservices account delete -g {resource_group_name} -n {name}",
                        f"Cognitive Services '{name}' deleted",
                        f"Failed to delete Cognitive Services '{name}'")
                    run(f"az cognitiveservices account purge -g {resource_group_name} -n {name} -l \"{location}\"",
                        f"Cognitive Services '{name}' purged",
                        f"Failed to purge Cognitive Services '{name}'")
            
            # Delete APIM resources (with purge)
            output = run(
                f"az apim list -g {resource_group_name}",
                "Listed APIM resources",
                "Failed to list APIM resources"
            )
            if output.success and output.json_data:
                for resource in output.json_data:
                    name = resource['name']
                    location = resource['location']
                    print_info(f"Deleting API Management '{name}'...")
                    run(f"az apim delete -n {name} -g {resource_group_name} -y",
                        f"API Management '{name}' deleted",
                        f"Failed to delete API Management '{name}'")
                    run(f"az apim deletedservice purge --service-name {name} --location \"{location}\"",
                        f"API Management '{name}' purged",
                        f"Failed to purge API Management '{name}'")
            
            # Delete the resource group
            print_message(f"🧹 Deleting resource group '{resource_group_name}'...")
            run(
                f"az group delete --name {resource_group_name} -y",
                f"Resource group '{resource_group_name}' deleted",
                f"Failed to delete resource group '{resource_group_name}'"
            )
            
            print_message("🧹 Cleanup completed.")
    
    except Exception as e:
        print_error(f"An error occurred during cleanup: {e}")
        traceback.print_exc()


# =============================================================================
# Cost Calculation Constants
# =============================================================================
# GPT-4 pricing (per 1K tokens) - Update as needed
PRICING = {
    "gpt-4": {"prompt": 0.03, "completion": 0.06},
    "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
    "gpt-4o": {"prompt": 0.005, "completion": 0.015},
    "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
    "gpt-35-turbo": {"prompt": 0.0015, "completion": 0.002},
}


def calculate_cost(prompt_tokens: int, completion_tokens: int, model: str = "gpt-4o") -> float:
    """
    Calculate the estimated cost for a request.
    
    Args:
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        model: The model name (default: gpt-4o)
    
    Returns:
        Estimated cost in USD
    """
    pricing = PRICING.get(model, PRICING["gpt-4o"])
    prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
    completion_cost = (completion_tokens / 1000) * pricing["completion"]
    return prompt_cost + completion_cost
