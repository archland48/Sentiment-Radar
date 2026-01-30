#!/usr/bin/env python3
"""
Deployment script for Sentiment Alpha Radar
Uses the AI Builders deployment API to deploy to Koyeb
"""
import json
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

AI_BUILDER_TOKEN = os.getenv("AI_BUILDER_TOKEN")
AI_BUILDER_BASE_URL = "https://space.ai-builders.com/backend"

if not AI_BUILDER_TOKEN:
    print("Error: AI_BUILDER_TOKEN not found in environment variables")
    exit(1)

def load_deploy_config():
    """Load deployment configuration from deploy-config.json"""
    try:
        with open("deploy-config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: deploy-config.json not found")
        print("Please create deploy-config.json with your deployment settings")
        exit(1)

def deploy():
    """Deploy the application using AI Builders API"""
    config = load_deploy_config()
    
    # Validate required fields
    if config.get("repo_url") == "YOUR_GITHUB_REPO_URL_HERE":
        print("Error: Please update deploy-config.json with your GitHub repository URL")
        exit(1)
    
    print(f"Deploying {config['service_name']}...")
    print(f"Repository: {config['repo_url']}")
    print(f"Branch: {config['branch']}")
    print(f"Port: {config['port']}")
    
    # Prepare request payload
    payload = {
        "repo_url": config["repo_url"],
        "service_name": config["service_name"],
        "branch": config["branch"],
        "port": config["port"]
    }
    
    # Add environment variables if provided
    if config.get("env_vars"):
        payload["env_vars"] = config["env_vars"]
    
    # Make deployment request
    try:
        response = httpx.post(
            f"{AI_BUILDER_BASE_URL}/v1/deployments",
            json=payload,
            headers={
                "Authorization": f"Bearer {AI_BUILDER_TOKEN}",
                "Content-Type": "application/json"
            },
            timeout=120.0
        )
        
        if response.status_code == 202:
            data = response.json()
            print("\n✅ Deployment queued successfully!")
            print(f"\nService Name: {data.get('service_name')}")
            print(f"Status: {data.get('status')}")
            print(f"Public URL: {data.get('public_url', 'Will be available after deployment')}")
            print(f"\nMessage: {data.get('message', '')}")
            
            if data.get("streaming_logs"):
                print("\n--- Build Logs ---")
                print(data["streaming_logs"])
            
            print("\n⏳ Deployment typically takes 5-10 minutes.")
            print("Check status with:")
            print(f"  GET {AI_BUILDER_BASE_URL}/v1/deployments/{config['service_name']}")
        else:
            print(f"\n❌ Deployment failed!")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ Error during deployment: {e}")
        exit(1)

if __name__ == "__main__":
    deploy()
