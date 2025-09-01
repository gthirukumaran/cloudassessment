"""
Enhanced Securra Backend with Subscription Management and Advanced Features
"""
from fastapi import FastAPI, HTTPException, Depends, Header, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import io
import jwt
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid
import json
from dotenv import load_dotenv, set_key
from contextlib import suppress
import asyncio
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import openai
import aiohttp

# Load environment variables from backend/.env explicitly (persist across restarts)
_DOTENV_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
load_dotenv(_DOTENV_PATH, override=True)

from azure_service import azure_service
from agentic_langgraph_service import agentic_service
from pdf_config_service import pdf_service
from validation_service import validation_service
from llm_email_service import llm_email_service, EmailNotificationRequest

app = FastAPI(title="Securra Enhanced Backend", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    # Allow any localhost/127.0.0.1 port during dev (vite may auto-switch ports)
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Azure configuration from environment
AZURE_CONFIG = {
    "client_id": os.getenv("AZURE_CLIENT_ID", "b1ea4ce4-a960-4141-ba48-a5480b05edd9"),
    "tenant_id": os.getenv("AZURE_TENANT_ID", "64b85bc1-b5cf-4169-9b23-8addcc72c198"),
    "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID", "your-subscription-id"),
    "storage_account": os.getenv("AZURE_STORAGE_ACCOUNT", "thirustorage001"),
    "key_vault_url": os.getenv("AZURE_KEY_VAULT_URL", "https://thiruaihub7026667835.vault.azure.net/")
}

# Test credentials with roles
TEST_USERS = {
    "admin@securra.com": {
        "password": "admin123",
        "user_data": {
            "id": "admin-001",
            "email": "admin@securra.com",
            "firstName": "Security",
            "lastName": "Admin",
            "role": "admin",
            "isActive": True,
            "permissions": ["read", "write", "delete", "manage_users", "generate_reports"]
        }
    },
    "analyst@securra.com": {
        "password": "analyst123",
        "user_data": {
            "id": "analyst-001",
            "email": "analyst@securra.com",
            "firstName": "Security",
            "lastName": "Analyst",
            "role": "analyst",
            "isActive": True,
            "permissions": ["read", "write", "generate_reports"]
        }
    },
    "demo@securra.com": {
        "password": "demo123",
        "user_data": {
            "id": "demo-001",
            "email": "demo@securra.com",
            "firstName": "Demo",
            "lastName": "User",
            "role": "user",
            "isActive": True,
            "permissions": ["read"]
        }
    }
}

SECRET_KEY = "enhanced-secret-key-for-demo"

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

# Azure OpenAI Configuration for Agentic System
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-resource.openai.azure.com/")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "your-azure-openai-key")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

# Available AI Models for Agentic System
AVAILABLE_AI_MODELS = {
    "gpt-4-turbo": {
        "name": "GPT-4 Turbo",
        "description": "Most capable model for complex reasoning and analysis",
        "max_tokens": 4096,
        "recommended": True
    },
    "gpt-4o": {
        "name": "GPT-4o",
        "description": "Optimized GPT-4 model with improved performance",
        "max_tokens": 4096,
        "recommended": False
    },
    "gpt-35-turbo": {
        "name": "GPT-3.5 Turbo",
        "description": "Fast and efficient model for standard tasks",
        "max_tokens": 4096,
        "recommended": False
    },
    "claude-3-opus": {
        "name": "Claude-3 Opus",
        "description": "Advanced reasoning capabilities for complex security analysis",
        "max_tokens": 4096,
        "recommended": False
    }
}

# Agentic System Data Stores
AGENTS = []
AGENT_EXECUTION_LOGS = {}

# Initialize OpenAI client
if OPENAI_API_KEY and OPENAI_API_KEY != "your-openai-api-key":
    openai.api_key = OPENAI_API_KEY

# AI-powered recommendation generation
async def generate_ai_recommendations(finding_data: dict) -> dict:
    """Generate intelligent recommendations for security findings using OpenAI API"""
    try:
        # Extract finding details
        title = finding_data.get('title', '').lower()
        severity = finding_data.get('severity', 'medium').lower()
        resource = finding_data.get('resource', '')
        description = finding_data.get('description', '')
        resource_name = finding_data.get('resource_name', '')
        category = finding_data.get('category', '')
        
        # Priority mapping
        priority_map = {'critical': 'Critical', 'high': 'High', 'medium': 'Medium', 'low': 'Low'}
        priority = priority_map.get(severity, 'Medium')
        
        # Try OpenAI API first if configured
        if OPENAI_API_KEY and OPENAI_API_KEY != "your-openai-api-key":
            try:
                # Construct prompt for OpenAI
                # Enhanced prompt with resource type information
                resource_type = finding_data.get('resource_type', '')
                friendly_resource = finding_data.get('resource', '')
                
                prompt = f"""You are a cybersecurity expert providing remediation recommendations for Azure security findings.

Security Finding Details:
- Title: {finding_data.get('title', '')}
- Description: {description}
- Severity: {severity}
- Resource Name: {resource_name}
- Resource Type: {resource_type}
- Friendly Resource Type: {friendly_resource}
- Category: {category}
- Compliance Framework: {finding_data.get('compliance_framework', 'N/A')}

Please provide a structured response with:
1. Business Impact (2-3 sentences focusing on this specific resource type)
2. Effort Estimate (realistic time estimate based on resource complexity)
3. Remediation Steps (numbered list, 4-6 specific steps for this Azure resource type)
4. Azure CLI Commands (specific commands for {resource_type})
5. PowerShell Commands (specific commands for {resource_type})
6. Compliance Impact (how this affects compliance frameworks)

Focus on practical, actionable recommendations specific to {resource_type} ({friendly_resource}) and provide commands that directly address this resource type."""

                # Call OpenAI API
                response = await openai.ChatCompletion.acreate(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are an expert Azure security consultant providing detailed remediation guidance."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=OPENAI_MAX_TOKENS,
                    temperature=OPENAI_TEMPERATURE
                )
                
                ai_response = response.choices[0].message.content.strip()
                
                # Parse the AI response and structure it
                return {
                    "priority": priority,
                    "ai_generated": True,
                    "resource_type": resource_type,
                    "friendly_resource_type": friendly_resource,
                    "business_impact": _extract_section(ai_response, "business impact", f"This {severity} severity finding in {friendly_resource} may impact security posture and compliance requirements."),
                    "effort_estimate": _extract_section(ai_response, "effort estimate", "1-3 hours depending on complexity"),
                    "remediation_steps": _extract_steps(ai_response),
                    "azure_commands": _extract_section(ai_response, "azure cli", f"# Azure CLI commands for {resource_type}\n# az {resource_type.split('/')[-1].lower()} update --resource-group <rg-name> --name {resource_name}"),
                    "powershell_commands": _extract_section(ai_response, "powershell", f"# PowerShell commands for {resource_type}\n# Set-Az{resource_type.split('/')[-1]} -ResourceGroupName <rg-name> -Name {resource_name}"),
                    "compliance_impact": _extract_section(ai_response, "compliance impact", f"This finding may affect {finding_data.get('compliance_framework', 'compliance')} requirements and should be addressed promptly."),
                    "raw_ai_response": ai_response
                }
                
            except Exception as openai_error:
                print(f"⚠️ OpenAI API error: {openai_error}")
                # Fall back to rule-based recommendations
                pass
        
        # Fallback to rule-based recommendations with enhanced resource type information
        resource_type = finding_data.get('resource_type', 'Unknown')
        friendly_resource = finding_data.get('resource', resource)
        compliance_framework = finding_data.get('compliance_framework', 'compliance standards')
        
        if 'network' in title or 'nsg' in title or 'security group' in title:
            return {
                "priority": priority,
                "resource_type": resource_type,
                "friendly_resource_type": friendly_resource,
                "business_impact": f"Network security vulnerabilities in {friendly_resource} can expose resources to unauthorized access, potentially leading to data breaches, compliance violations, and significant financial losses.",
                "effort_estimate": "1-2 hours for configuration changes",
                "remediation_steps": [
                    "Review current network security group rules and identify overly permissive configurations",
                    "Remove rules that allow access from 0.0.0.0/0 (any source) unless absolutely necessary",
                    "Implement principle of least privilege by restricting access to specific IP ranges",
                    "Use Azure service tags instead of broad IP ranges where possible",
                    "Enable network security group flow logs for monitoring and auditing",
                    "Regularly review and update security group rules as part of security maintenance"
                ],
                "azure_commands": f"# Update Network Security Group rules\naz network nsg rule update --resource-group <rg-name> --nsg-name {resource_name} --name <rule-name> --source-address-prefixes <specific-ip-range>\naz network nsg rule delete --resource-group <rg-name> --nsg-name {resource_name} --name <overly-permissive-rule>\n\n# Enable NSG flow logs\naz network watcher flow-log create --resource-group <rg-name> --name <flow-log-name> --nsg {resource_name}",
                "powershell_commands": f"# PowerShell commands for NSG management\n$nsg = Get-AzNetworkSecurityGroup -ResourceGroupName <rg-name> -Name {resource_name}\nSet-AzNetworkSecurityRuleConfig -NetworkSecurityGroup $nsg -Name <rule-name> -SourceAddressPrefix <specific-range>\nRemove-AzNetworkSecurityRuleConfig -NetworkSecurityGroup $nsg -Name <permissive-rule>\nSet-AzNetworkSecurityGroup -NetworkSecurityGroup $nsg",
                "compliance_impact": f"Network security controls are critical for {compliance_framework} compliance. This finding may affect CIS Controls 12 (Boundary Defense) and NIST Cybersecurity Framework (Protect function)."
            }
        elif 'storage' in title or 'encryption' in title:
            return {
                "priority": priority,
                "resource_type": resource_type,
                "friendly_resource_type": friendly_resource,
                "business_impact": f"Unencrypted {friendly_resource} poses significant data security risks and may violate compliance requirements like GDPR, HIPAA, SOX, and PCI-DSS, potentially resulting in regulatory fines and reputational damage.",
                "effort_estimate": "30 minutes to 1 hour for encryption enablement",
                "remediation_steps": [
                    "Enable encryption at rest for the storage account using Azure Storage Service Encryption",
                    "Configure customer-managed keys (CMK) if required by compliance standards",
                    "Enable encryption in transit by requiring HTTPS-only access",
                    "Review and update storage account access policies and shared access signatures",
                    "Implement Azure Storage Analytics and monitoring for security events",
                    "Consider enabling Azure Defender for Storage for advanced threat protection"
                ],
                "azure_commands": f"# Enable storage account encryption\naz storage account update --resource-group <rg-name> --name {resource} --encryption-services blob file table queue\naz storage account update --resource-group <rg-name> --name {resource} --https-only true\n\n# Enable advanced threat protection\naz security atp storage update --resource-group <rg-name> --storage-account {resource} --is-enabled true",
                "powershell_commands": f"# PowerShell commands for storage encryption\nSet-AzStorageAccount -ResourceGroupName <rg-name> -Name {resource} -EnableHttpsTrafficOnly $true\nSet-AzStorageAccount -ResourceGroupName <rg-name> -Name {resource} -EncryptionKeySource Microsoft.Storage\n\n# Enable advanced threat protection\nEnable-AzSecurityAdvancedThreatProtection -ResourceId '/subscriptions/<sub-id>/resourceGroups/<rg-name>/providers/Microsoft.Storage/storageAccounts/{resource}'"
            }
        elif 'identity' in title or 'mfa' in title or 'authentication' in title or 'access' in title:
            return {
                "priority": priority,
                "business_impact": "Weak authentication controls significantly increase the risk of unauthorized access, account takeover, and potential data breaches, which can result in substantial financial and reputational damage.",
                "effort_estimate": "2-4 hours for identity configuration and policy setup",
                "remediation_steps": [
                    "Enable Multi-Factor Authentication (MFA) for all user accounts, especially privileged accounts",
                    "Implement Azure AD Conditional Access policies to enforce security requirements",
                    "Review and update user access permissions following principle of least privilege",
                    "Enable Azure AD Identity Protection to detect and respond to identity-based risks",
                    "Configure Privileged Identity Management (PIM) for just-in-time access to sensitive resources",
                    "Implement regular access reviews to ensure appropriate access levels"
                ],
                "azure_commands": "# Enable MFA and conditional access\naz ad user update --id <user-id> --force-change-password-next-login true\n\n# Create conditional access policy\naz rest --method POST --url 'https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies' --body '{\"displayName\": \"Require MFA\", \"state\": \"enabled\"}'\n\n# Enable Identity Protection\naz ad app permission grant --id <app-id> --api 00000003-0000-0000-c000-000000000000",
                "powershell_commands": "# PowerShell commands for identity management\n# Enable MFA for user\nSet-MsolUser -UserPrincipalName <user@domain.com> -StrongAuthenticationRequirements @()\n\n# Create conditional access policy\nNew-AzureADMSConditionalAccessPolicy -DisplayName 'Require MFA for All Users' -State 'Enabled'\n\n# Enable PIM\nEnable-AzureADPrivilegedIdentityManagement"
            }
        elif 'key vault' in title or 'secret' in title or 'certificate' in title:
            return {
                "priority": priority,
                "business_impact": "Improper key and secret management can lead to unauthorized access to sensitive data, compliance violations, and potential data breaches with severe financial and legal consequences.",
                "effort_estimate": "1-3 hours for key vault configuration and policy updates",
                "remediation_steps": [
                    "Enable Azure Key Vault soft delete and purge protection features",
                    "Implement proper access policies using Azure RBAC and Key Vault access policies",
                    "Enable Key Vault logging and monitoring through Azure Monitor",
                    "Rotate keys and secrets regularly according to security best practices",
                    "Use managed identities for applications to access Key Vault securely",
                    "Implement network access restrictions using virtual network service endpoints"
                ],
                "azure_commands": f"# Configure Key Vault security\naz keyvault update --resource-group <rg-name> --name {resource} --enable-soft-delete true --enable-purge-protection true\naz keyvault update --resource-group <rg-name> --name {resource} --enable-rbac-authorization true\n\n# Enable logging\naz monitor diagnostic-settings create --resource {resource} --name 'KeyVaultLogs' --logs '[{{\"category\": \"AuditEvent\", \"enabled\": true}}]'",
                "powershell_commands": f"# PowerShell commands for Key Vault management\nUpdate-AzKeyVault -ResourceGroupName <rg-name> -VaultName {resource} -EnableSoftDelete -EnablePurgeProtection\nSet-AzKeyVaultAccessPolicy -ResourceGroupName <rg-name> -VaultName {resource} -EnabledForDeployment -EnabledForTemplateDeployment\n\n# Enable RBAC\nUpdate-AzKeyVault -ResourceGroupName <rg-name> -VaultName {resource} -EnableRbacAuthorization"
            }
        else:
            # Generic recommendations for other findings
            return {
                "priority": priority,
                "business_impact": f"This {severity} severity security finding may impact system security, compliance posture, and operational efficiency. Unaddressed security issues can lead to data breaches, regulatory violations, and business disruption.",
                "effort_estimate": "1-3 hours depending on complexity and testing requirements",
                "remediation_steps": [
                    "Analyze the specific security configuration issue identified in the finding",
                    "Review Azure security best practices documentation for the affected resource type",
                    "Implement the recommended security controls and configurations",
                    "Test changes in a non-production environment first to ensure no service disruption",
                    "Deploy to production during a maintenance window and monitor for any issues",
                    "Document the changes for compliance tracking and future reference",
                    "Schedule regular reviews to ensure the security configuration remains effective"
                ],
                "azure_commands": f"# Generic Azure CLI commands for resource management\naz resource show --resource-group <rg-name> --name {resource} --resource-type <resource-type>\naz resource update --resource-group <rg-name> --name {resource} --set properties.securitySettings=<new-settings>\n\n# Enable diagnostic logging\naz monitor diagnostic-settings create --resource {resource} --name 'SecurityLogs' --logs '[{{\"category\": \"Security\", \"enabled\": true}}]'",
                "powershell_commands": f"# Generic PowerShell commands for Azure resource management\nGet-AzResource -ResourceGroupName <rg-name> -Name {resource}\nSet-AzResource -ResourceGroupName <rg-name> -Name {resource} -Properties @{{securitySettings=<new-settings>}} -Force\n\n# Enable monitoring\nSet-AzDiagnosticSetting -ResourceId '/subscriptions/<sub-id>/resourceGroups/<rg-name>/providers/<provider>/{resource}' -Enabled $true"
            }
            
    except Exception as e:
        print(f"⚠️ Error generating AI recommendations: {e}")
        # Return basic fallback recommendation
        return {
            "priority": "Medium",
            "ai_generated": False,
            "business_impact": "This security finding may impact system security and compliance posture.",
            "effort_estimate": "1-2 hours",
            "remediation_steps": [
                "Review the security finding details",
                "Consult Azure security documentation",
                "Implement recommended security controls",
                "Test changes in non-production environment",
                "Deploy to production and monitor"
            ],
            "azure_commands": "# Please refer to Azure documentation for specific commands",
            "powershell_commands": "# Please refer to Azure documentation for specific commands"
        }

def _extract_section(text: str, section_name: str, default: str) -> str:
    """Extract a specific section from AI response"""
    try:
        text_lower = text.lower()
        section_lower = section_name.lower()
        
        # Find section start
        start_patterns = [f"{section_lower}:", f"{section_lower} -", f"**{section_lower}**"]
        start_idx = -1
        
        for pattern in start_patterns:
            idx = text_lower.find(pattern)
            if idx != -1:
                start_idx = idx + len(pattern)
                break
        
        if start_idx == -1:
            return default
        
        # Find section end (next numbered item or section)
        end_patterns = ["\n1.", "\n2.", "\n3.", "\n4.", "\n5.", "\n**", "\n#"]
        end_idx = len(text)
        
        for pattern in end_patterns:
            idx = text.find(pattern, start_idx)
            if idx != -1 and idx < end_idx:
                end_idx = idx
        
        section_text = text[start_idx:end_idx].strip()
        return section_text if section_text else default
        
    except Exception:
        return default

def _extract_steps(text: str) -> list:
    """Extract numbered steps from AI response"""
    try:
        steps = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for numbered steps
            if line and (line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')) or 
                        line.startswith(('- ', '• '))):
                # Clean up the step text
                step = line.lstrip('123456789.- •').strip()
                if step:
                    steps.append(step)
        
        # If no steps found, return default
        if not steps:
            return [
                "Review the security finding details",
                "Implement recommended security controls",
                "Test changes in non-production environment",
                "Deploy to production and monitor"
            ]
        
        return steps[:8]  # Limit to 8 steps
        
    except Exception:
        return [
            "Review the security finding details",
            "Implement recommended security controls",
            "Test changes in non-production environment",
            "Deploy to production and monitor"
        ]

# Mock data for subscriptions and scans
SUBSCRIPTION_DATA = {
    "subscription_id": AZURE_CONFIG["subscription_id"],
    "tenant_id": AZURE_CONFIG["tenant_id"],
    "resource_groups": [
        {
            "id": "rg-production",
            "name": "rg-production",
            "location": "East US",
            "resources_count": 25,
            "last_scan": "2025-08-12T10:00:00Z"
        },
        {
            "id": "rg-development",
            "name": "rg-development", 
            "location": "West US",
            "resources_count": 12,
            "last_scan": "2025-08-12T08:00:00Z"
        }
    ],
    "compliance_status": {
        "cis": {"score": 85, "total_controls": 120, "passed": 102},
        "soc": {"score": 92, "total_controls": 95, "passed": 87},
        "nist": {"score": 78, "total_controls": 150, "passed": 117}
    }
}

SECURITY_SCANS = [
    {
        "scan_id": "scan-static-001",
        "subscription_id": "0a519345-d9f4-400c-a3b4-e8379de6638e",
        "framework": "CIS",
        "status": "completed",
        "start_time": "2024-01-15T10:00:00Z",
        "end_time": "2024-01-15T10:30:00Z",
        "progress": 100,
        "total_checks": 120,
        "passed_checks": 96,
        "failed_checks": 24,
        "compliance_score": 80,
        "findings": [
            {
                "id": "cis-005",
                "title": "Network security groups allow unrestricted access",
                "description": "NSG rules allow traffic from any source (0.0.0.0/0)",
                "severity": "high",
                "category": "Network Security",
                "recommendation": "Restrict NSG rules to specific IP ranges",
                "status": "failed",
                "resource_id": "nsg-web",
                "resource_name": "Web Tier NSG",
                "resource_type": "Microsoft.Network/networkSecurityGroups",
                "friendly_resource": "Network Security Group",
                "nsg_rules_details": {
                    "total_rules": 5,
                    "risky_rules": [
                        {
                            "rule_name": "AllowRDP",
                            "priority": 100,
                            "direction": "Inbound",
                            "access": "Allow",
                            "protocol": "TCP",
                            "source_port_range": "*",
                            "destination_port_range": "3389",
                            "source_address_prefix": "0.0.0.0/0",
                            "destination_address_prefix": "*",
                            "risk_level": "Critical",
                            "description": "RDP access open to internet"
                        },
                        {
                            "rule_name": "AllowSSH",
                            "priority": 110,
                            "direction": "Inbound",
                            "access": "Allow",
                            "protocol": "TCP",
                            "source_port_range": "*",
                            "destination_port_range": "22",
                            "source_address_prefix": "0.0.0.0/0",
                            "destination_address_prefix": "*",
                            "risk_level": "Critical",
                            "description": "SSH access open to internet"
                        },
                        {
                            "rule_name": "AllowHTTP",
                            "priority": 120,
                            "direction": "Inbound",
                            "access": "Allow",
                            "protocol": "TCP",
                            "source_port_range": "*",
                            "destination_port_range": "80",
                            "source_address_prefix": "0.0.0.0/0",
                            "destination_address_prefix": "*",
                            "risk_level": "Medium",
                            "description": "HTTP access open to internet"
                        },
                        {
                            "rule_name": "AllowHTTPS",
                            "priority": 130,
                            "direction": "Inbound",
                            "access": "Allow",
                            "protocol": "TCP",
                            "source_port_range": "*",
                            "destination_port_range": "443",
                            "source_address_prefix": "0.0.0.0/0",
                            "destination_address_prefix": "*",
                            "risk_level": "Low",
                            "description": "HTTPS access open to internet"
                        },
                        {
                            "rule_name": "AllowCustomApp",
                            "priority": 140,
                            "direction": "Inbound",
                            "access": "Allow",
                            "protocol": "TCP",
                            "source_port_range": "*",
                            "destination_port_range": "8080-8090",
                            "source_address_prefix": "0.0.0.0/0",
                            "destination_address_prefix": "*",
                            "risk_level": "High",
                            "description": "Custom application ports open to internet"
                        }
                    ],
                    "ports_summary": {
                        "critical_ports": ["3389", "22"],
                        "high_risk_ports": ["8080-8090"],
                        "medium_risk_ports": ["80"],
                        "low_risk_ports": ["443"]
                    }
                }
            }
        ]
    }
]

COMPLIANCE_REPORTS = []

async def _generate_compliance_report_from_scan(scan_data: dict) -> dict:
    """Generate a compliance report based on actual scan data with AI-enhanced recommendations"""
    if not scan_data or scan_data.get("status") != "completed":
        return None
    
    scan_id = scan_data.get("scan_id")
    framework = scan_data.get("framework", "CIS")
    findings = scan_data.get("findings", [])
    
    # Calculate compliance score based on findings
    total_checks = scan_data.get("total_checks", 0)
    passed_checks = scan_data.get("passed_checks", 0)
    compliance_score = int((passed_checks / total_checks * 100)) if total_checks > 0 else 0
    
    # Analyze findings for executive summary and recommendations
    critical_findings = [f for f in findings if f.get("severity") == "critical"]
    high_findings = [f for f in findings if f.get("severity") == "high"]
    medium_findings = [f for f in findings if f.get("severity") == "medium"]
    
    # Generate executive summary based on actual findings
    if compliance_score >= 90:
        risk_level = "Low"
        summary_prefix = "Excellent security posture"
    elif compliance_score >= 75:
        risk_level = "Medium"
        summary_prefix = "Good security posture"
    else:
        risk_level = "High"
        summary_prefix = "Security posture needs improvement"
    
    executive_summary = f"{summary_prefix} with {compliance_score}% {framework} compliance. "
    if critical_findings:
        executive_summary += f"{len(critical_findings)} critical findings require immediate attention. "
    if high_findings:
        executive_summary += f"{len(high_findings)} high-priority issues identified."
    
    # Generate AI-enhanced recommendations from failed findings
    recommendations = []
    ai_recommendations = []
    failed_findings = [f for f in findings if f.get("status") == "failed"]
    
    # Get AI recommendations for top priority findings
    severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    failed_findings_sorted = sorted(failed_findings, 
                                  key=lambda x: severity_order.get(x.get('severity'), 4))
    
    # Generate AI recommendations for top 5 critical/high findings
    for finding in failed_findings_sorted[:5]:
        try:
            ai_rec = await generate_ai_recommendations(finding)
            if ai_rec and ai_rec.get('remediation_steps'):
                # Add the primary recommendation
                primary_rec = ai_rec['remediation_steps'][0] if ai_rec['remediation_steps'] else finding.get('recommendation', '')
                if primary_rec and primary_rec not in recommendations:
                    recommendations.append(primary_rec)
                    ai_recommendations.append({
                        'finding_id': finding.get('id'),
                        'resource_type': finding.get('resource_type', 'Unknown'),
                        'friendly_resource': finding.get('friendly_resource', 'Azure Resource'),
                        'recommendation': primary_rec,
                        'business_impact': ai_rec.get('business_impact', ''),
                        'effort_estimate': ai_rec.get('effort_estimate', '')
                    })
        except Exception as e:
            print(f"⚠️ Error generating AI recommendation for finding {finding.get('id')}: {e}")
            # Fallback to basic recommendation
            if finding.get("recommendation") and finding["recommendation"] not in recommendations:
                recommendations.append(finding["recommendation"])
    
    # Add remaining basic recommendations from other failed findings
    for finding in failed_findings:
        if finding.get("recommendation") and finding["recommendation"] not in recommendations:
            recommendations.append(finding["recommendation"])
        if len(recommendations) >= 10:
            break
    
    # If no recommendations found, provide default ones
    if not recommendations:
        recommendations = ["Continue regular security assessments", "Maintain current security controls"]
    
    report_id = f"report-{framework.lower()}-{uuid.uuid4().hex[:6]}"
    
    return {
        "id": report_id,
        "report_id": report_id,  # Backend compatibility
        "name": f"{framework} Compliance Report - {scan_data.get('target_name', 'Security Scan')}",
        "type": framework,
        "framework": framework,  # Backend compatibility
        "status": "generated",
        "environment": scan_data.get("environment", "production"),
        "created_at": datetime.now().isoformat(),
        "generated_at": datetime.now().isoformat(),  # Backend compatibility
        "scan_id": scan_id,
        "compliance_score": compliance_score,
        "executive_summary": executive_summary,
        "recommendations": recommendations,
        "ai_recommendations": ai_recommendations,  # Enhanced AI recommendations with resource context
        "findings_summary": {
            "total_findings": len(findings),
            "critical": len(critical_findings),
            "high": len(high_findings),
            "medium": len(medium_findings),
            "low": len([f for f in findings if f.get("severity") == "low"])
        },
        "scan_details": {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": total_checks - passed_checks,
            "scan_duration": scan_data.get("duration", "N/A"),
            "target_resources": scan_data.get("target_resources", [])
        }
    }

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Securra Enhanced Backend",
        "version": "2.0.0",
        "features": ["subscription_management", "cis_soc_reports", "ai_assistant", "user_management"],
        "timestamp": datetime.now().isoformat()
    }

# Authentication
@app.post("/api/v1/auth/login")
async def enhanced_login(login_data: dict):
    """Enhanced login with role-based permissions"""
    email = login_data.get("email")
    password = login_data.get("password")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    
    if email in TEST_USERS and TEST_USERS[email]["password"] == password:
        user_data = TEST_USERS[email]["user_data"]
        
        token_data = {
            "sub": user_data["email"],
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow(),
            "user_id": user_data["id"],
            "role": user_data["role"],
            "permissions": user_data["permissions"]
        }
        
        access_token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 86400,
            "user": user_data
        }
    
    raise HTTPException(status_code=401, detail="Invalid email or password")

# Subscription Management
@app.get("/api/v1/subscriptions")
async def get_subscriptions():
    """Get Azure subscriptions with enhanced metadata"""
    try:
        subscriptions = await azure_service.get_subscriptions()
        
        # Enhance subscription data with additional metadata
        enhanced_subscriptions = []
        for sub in subscriptions:
            enhanced_sub = {
                **sub,
                "provider": "azure",
                "status": "active" if sub["state"] == "Enabled" else "inactive",
                "region": "East US",  # Default region, could be enhanced
                "critical_findings": 2 + len(sub["id"]) % 5,  # Mock critical findings
                "subscription_type": "Pay-As-You-Go",
                "cost_center": f"CC-{sub['id'][:8]}",
                "environment": "production" if "prod" in sub["name"].lower() else "development"
            }
            enhanced_subscriptions.append(enhanced_sub)
        
        return {
            "subscriptions": enhanced_subscriptions,
            "total_subscriptions": len(enhanced_subscriptions),
            "active_subscriptions": len([s for s in enhanced_subscriptions if s["status"] == "active"])
        }
    except Exception as e:
        # Fallback to mock data with .env config
        return {
            "subscriptions": [
                {
                    "id": "12345678-1234-1234-1234-123456789012",
                    "name": "Production Environment (.env configured)",
                    "provider": "azure", 
                    "status": "active",
                    "state": "Enabled",
                    "tenant_id": AZURE_CONFIG["tenant_id"],
                    "resource_groups_count": 15,
                    "last_scan": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                    "compliance_score": 85,
                    "critical_findings": 3,
                    "subscription_type": "Pay-As-You-Go",
                    "cost_center": "IT-001",
                    "environment": "production"
                }
            ],
            "total_subscriptions": 1,
            "active_subscriptions": 1,
            "azure_config": {
                "tenant_id": AZURE_CONFIG["tenant_id"],
                "client_id": AZURE_CONFIG["client_id"],
                "storage_account": AZURE_CONFIG["storage_account"],
                "key_vault_url": AZURE_CONFIG["key_vault_url"]
            }
        }

@app.get("/api/v1/resource-groups")
async def get_resource_groups():
    """Get Azure resource groups for scanning"""
    try:
        # Get real resource groups from Azure service
        subscriptions = await azure_service.get_subscriptions()
        all_resource_groups = []
        
        for subscription in subscriptions:
            try:
                resources = await azure_service.get_subscription_resources(subscription["id"])
                if resources and "resource_groups" in resources:
                    all_resource_groups.extend(resources["resource_groups"])
            except Exception as e:
                print(f"Failed to get resource groups for subscription {subscription['id']}: {e}")
                continue
        
        return {
            "resource_groups": all_resource_groups,
            "total": len(all_resource_groups)
        }
    except Exception as e:
        print(f"Failed to get resource groups from Azure: {e}")
        # Fallback to mock data
        return {
            "resource_groups": SUBSCRIPTION_DATA["resource_groups"],
            "total": len(SUBSCRIPTION_DATA["resource_groups"])
        }

# Enhanced Security Scans
@app.get("/api/v1/scans")
async def get_security_scans(subscription_id: str = None):
    """Get all security scans with detailed information"""
    # Filter scans by subscription_id if provided
    filtered_scans = SECURITY_SCANS
    if subscription_id:
        filtered_scans = [scan for scan in SECURITY_SCANS if scan.get("subscription_id") == subscription_id]
    
    return {
        "scans": filtered_scans,
        "total": len(filtered_scans),
        "frameworks": ["CIS", "SOC2", "NIST", "ISO27001"],
        "statuses": ["completed", "in_progress", "failed", "pending"]
    }

@app.post("/api/v1/scans")
async def create_security_scan(scan_request: dict):
    """Start a new security scan"""
    try:
        subscription_id = scan_request.get("subscription_id")
        framework = scan_request.get("framework")
        
        if not subscription_id or not framework:
            raise HTTPException(status_code=400, detail="subscription_id and framework are required")
        
        # Create scan with the correct structure that frontend expects
        scan_id = f"scan-{uuid.uuid4().hex[:8]}"
        current_time = datetime.utcnow().isoformat()
        
        new_scan = {
            "scan_id": scan_id,
            "subscription_id": subscription_id,
            "framework": framework,
            "status": "in_progress",
            "start_time": current_time,
            "end_time": None,
            "progress": 0,
            "total_checks": _get_framework_checks_count(framework),
            "passed_checks": 0,
            "failed_checks": 0,
            "compliance_score": None,
            "config": {
                "resource_groups": scan_request.get("resource_groups", []),
                "exclude_resources": scan_request.get("exclude_resources", []),
                "severity_filter": scan_request.get("severity_filter", "all"),
                "notify_email": scan_request.get("notify_email", ""),
                "selected_controls": scan_request.get("selected_controls", [])
            }
        }
        
        print(f"🚀 Creating new scan: {scan_id} for subscription: {subscription_id} with framework: {framework}")
        
        # Add to the scans list so it appears in the table
        SECURITY_SCANS.append(new_scan)
        
        # Start the actual scan process in background
        scan_config = {
            "resource_groups": scan_request.get("resource_groups", []),
            "exclude_resources": scan_request.get("exclude_resources", []),
            "severity_filter": scan_request.get("severity_filter", "all"),
            "notify_email": scan_request.get("notify_email", ""),
            "selected_controls": scan_request.get("selected_controls", [])
        }
        
        # Start async scan process
        asyncio.create_task(_perform_scan_background(scan_id, subscription_id, framework, scan_config))
        
        return {
            "scan_id": scan_id,
            "status": "initiated",
            "message": f"Security scan started for subscription {subscription_id} with {framework} framework"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scan: {str(e)}")

def _get_framework_checks_count(framework: str) -> int:
    """Get the number of checks for a given framework"""
    # Check if it's a custom framework first
    if _is_custom_framework(framework):
        return _get_custom_framework_checks_count(framework)
    
    framework_checks = {
        "CIS": 120,
        "SOC2": 95,
        "NIST": 150,
        "ISO27001": 135
    }
    return framework_checks.get(framework, 100)

def _is_custom_framework(framework: str) -> bool:
    """Check if framework is a custom framework"""
    try:
        from app.services.compliance_service import ComplianceService
        from app.core.database import get_db
        
        db = next(get_db())
        compliance_service = ComplianceService(db)
        
        custom_framework = compliance_service.get_framework_by_name(framework)
        return custom_framework is not None
    except Exception as e:
        print(f"Error checking if framework is custom: {e}")
        return False

def _get_custom_framework_checks_count(framework: str) -> int:
    """Get the number of checks for a custom framework"""
    try:
        from app.services.compliance_service import ComplianceService
        from app.core.database import get_db
        
        db = next(get_db())
        compliance_service = ComplianceService(db)
        
        custom_framework = compliance_service.get_framework_by_name(framework)
        if not custom_framework:
            return 50  # Default fallback
        
        controls = compliance_service.get_framework_controls(custom_framework.id)
        active_controls = [c for c in controls if c.is_active]
        return len(active_controls) if active_controls else 50  # Default fallback
    except Exception as e:
        print(f"Error getting custom framework checks count: {e}")
        return 50

async def _perform_scan_background(scan_id: str, subscription_id: str, framework: str, scan_config: dict):
    """Perform the actual security scan in background using Azure Service"""
    try:
        # Find the scan in the list
        scan = next((s for s in SECURITY_SCANS if s.get("scan_id") == scan_id), None)
        if not scan:
            return
        
        print(f"🔍 Starting real Azure scan {scan_id} for subscription {subscription_id} with framework {framework}")
        
        # Use the Azure service to perform the actual scan
        try:
            # Start the real Azure scan using azure_service
            scan_initiation = await azure_service.start_security_scan(
                subscription_id=subscription_id,
                framework=framework,
                scan_config=scan_config
            )
            
            if scan_initiation and scan_initiation.get("status") == "initiated":
                azure_scan_id = scan_initiation.get("scan_id")
                print(f"✅ Azure scan initiated with ID: {azure_scan_id}")
                
                # Monitor the Azure scan progress
                max_wait_time = 300  # 5 minutes timeout
                wait_time = 0
                
                while wait_time < max_wait_time:
                    await asyncio.sleep(5)  # Check every 5 seconds
                    wait_time += 5
                    
                    # Get scan status from Azure service
                    azure_scan_status = azure_service.get_scan_status(azure_scan_id)
                    
                    if azure_scan_status:
                        # Update progress in our scan
                        scan["progress"] = azure_scan_status.get("progress", 0)
                        
                        if azure_scan_status.get("status") == "completed":
                            # Scan completed successfully
                            scan["status"] = "completed"
                            scan["end_time"] = datetime.utcnow().isoformat()
                            scan["progress"] = 100
                            scan["compliance_score"] = azure_scan_status.get("compliance_score", 85)
                            scan["findings"] = azure_scan_status.get("findings", [])
                            scan["passed_checks"] = azure_scan_status.get("passed_checks", 0)
                            scan["failed_checks"] = azure_scan_status.get("failed_checks", 0)
                            
                            print(f"✅ Real Azure scan {scan_id} completed successfully with {len(scan['findings'])} findings")
                            return
                            
                        elif azure_scan_status.get("status") == "failed":
                            print(f"⚠️ Azure scan {azure_scan_id} failed, falling back to mock data")
                            break
                
                # If we reach here, either timeout or scan failed
                print(f"⚠️ Azure scan timeout or failure, falling back to mock data for scan {scan_id}")
                await _perform_mock_scan(scan_id, subscription_id, framework, scan_config)
            else:
                # If Azure scan initiation fails, fall back to mock data
                print(f"⚠️ Azure scan initiation failed, falling back to mock data for scan {scan_id}")
                await _perform_mock_scan(scan_id, subscription_id, framework, scan_config)
                
        except Exception as azure_error:
            print(f"⚠️ Azure scan error: {azure_error}, falling back to mock data for scan {scan_id}")
            await _perform_mock_scan(scan_id, subscription_id, framework, scan_config)
        
    except Exception as e:
        print(f"❌ Scan {scan_id} failed: {e}")
        scan = next((s for s in SECURITY_SCANS if s.get("scan_id") == scan_id), None)
        if scan:
            scan["status"] = "failed"
            scan["end_time"] = datetime.utcnow().isoformat()

async def _perform_mock_scan(scan_id: str, subscription_id: str, framework: str, scan_config: dict):
    """Fallback mock scan implementation"""
    try:
        # Find the scan in the list
        scan = next((s for s in SECURITY_SCANS if s.get("scan_id") == scan_id), None)
        if not scan:
            return
        
        print(f"🔍 Performing mock scan {scan_id} for subscription {subscription_id} with framework {framework}")
        
        total_checks = scan["total_checks"]
        
        # Simulate scan progress (faster for fallback)
        for i in range(total_checks):
            await asyncio.sleep(0.1)  # Faster for fallback
            
            # Update progress
            progress = int((i + 1) / total_checks * 100)
            scan["progress"] = progress
            
            # Simulate some checks passing/failing
            if i < int(total_checks * 0.8):  # 80% pass rate
                scan["passed_checks"] += 1
            else:
                scan["failed_checks"] += 1
        
        # Complete the scan
        scan["status"] = "completed"
        scan["end_time"] = datetime.utcnow().isoformat()
        scan["compliance_score"] = 85  # Mock compliance score
        
        # Generate findings
        scan["findings"] = _generate_mock_findings(framework, scan_config)
        
        print(f"✅ Mock scan {scan_id} completed successfully")
        
    except Exception as e:
        print(f"❌ Mock scan {scan_id} failed: {e}")
        scan = next((s for s in SECURITY_SCANS if s.get("scan_id") == scan_id), None)
        if scan:
            scan["status"] = "failed"
            scan["end_time"] = datetime.utcnow().isoformat()

def _generate_mock_findings(framework: str, scan_config: dict) -> list:
    """Generate mock findings based on framework"""
    findings = []
    
    if framework == "CIS":
        # Generate comprehensive findings to match the failed checks count
        findings = [
            # Critical findings (1)
            {"id": "cis-001",
                "title": "Multi-factor authentication not enabled for privileged users",
                "description": "Global administrators and subscription owners should have MFA enabled",
                "severity": "critical",
                "category": "Identity and Access Management",
                "recommendation": "Enable MFA for all privileged accounts in Azure AD",
                "status": "failed",
                "resource_id": "admin-accounts",
                "resource_name": "Administrator Accounts",
                "resource_type": "Microsoft.Authorization/roleAssignments",
                "friendly_resource": "Azure AD Administrator Accounts"
            },
            # High severity findings (5)
            {"id": "cis-002",
                "title": "Storage account public access not restricted",
                "description": "Storage accounts allow public blob access which poses security risks",
                "severity": "high",
                "category": "Data Protection",
                "recommendation": "Disable public blob access on storage accounts",
                "status": "failed",
                "resource_id": "storage-001",
                "resource_name": "Production Storage",
                "resource_type": "Microsoft.Storage/storageAccounts",
                "friendly_resource": "Azure Storage Account"
            },
            {"id": "cis-003",
                "title": "Key Vault access policies too permissive",
                "description": "Key Vault has overly broad access policies assigned",
                "severity": "high",
                "category": "Key Management",
                "recommendation": "Review and restrict Key Vault access policies",
                "status": "failed",
                "resource_id": "kv-prod",
                "resource_name": "Production Key Vault",
                "resource_type": "Microsoft.KeyVault/vaults",
                "friendly_resource": "Azure Key Vault"
            },
            {"id": "cis-004",
                "title": "SQL Database auditing not enabled",
                "description": "SQL Database auditing is not configured for compliance monitoring",
                "severity": "high",
                "category": "Database Security",
                "recommendation": "Enable SQL Database auditing and log analytics",
                "status": "failed",
                "resource_id": "sql-prod",
                "resource_name": "Production SQL Database",
                "resource_type": "Microsoft.Sql/servers/databases",
                "friendly_resource": "Azure SQL Database"
            },
            {"id": "cis-005",
                "title": "Network security groups allow unrestricted access",
                "description": "NSG rules allow traffic from any source (0.0.0.0/0)",
                "severity": "high",
                "category": "Network Security",
                "recommendation": "Restrict NSG rules to specific IP ranges",
                "status": "failed",
                "resource_id": "nsg-web",
                "resource_name": "Web Tier NSG",
                "resource_type": "Microsoft.Network/networkSecurityGroups",
                "friendly_resource": "Network Security Group",
                "nsg_rules_details": {
                    "total_rules": 5,
                    "risky_rules": [
                        {
                            "rule_name": "AllowRDP",
                            "priority": 100,
                            "direction": "Inbound",
                            "access": "Allow",
                            "protocol": "TCP",
                            "source_port_range": "*",
                            "destination_port_range": "3389",
                            "source_address_prefix": "0.0.0.0/0",
                            "destination_address_prefix": "*",
                            "risk_level": "Critical",
                            "description": "RDP access open to internet"
                        },
                        {
                            "rule_name": "AllowSSH",
                            "priority": 110,
                            "direction": "Inbound",
                            "access": "Allow",
                            "protocol": "TCP",
                            "source_port_range": "*",
                            "destination_port_range": "22",
                            "source_address_prefix": "0.0.0.0/0",
                            "destination_address_prefix": "*",
                            "risk_level": "Critical",
                            "description": "SSH access open to internet"
                        },
                        {
                            "rule_name": "AllowHTTP",
                            "priority": 120,
                            "direction": "Inbound",
                            "access": "Allow",
                            "protocol": "TCP",
                            "source_port_range": "*",
                            "destination_port_range": "80",
                            "source_address_prefix": "0.0.0.0/0",
                            "destination_address_prefix": "*",
                            "risk_level": "Medium",
                            "description": "HTTP access open to internet"
                        },
                        {
                            "rule_name": "AllowHTTPS",
                            "priority": 130,
                            "direction": "Inbound",
                            "access": "Allow",
                            "protocol": "TCP",
                            "source_port_range": "*",
                            "destination_port_range": "443",
                            "source_address_prefix": "0.0.0.0/0",
                            "destination_address_prefix": "*",
                            "risk_level": "Low",
                            "description": "HTTPS access open to internet"
                        },
                        {
                            "rule_name": "AllowCustomApp",
                            "priority": 140,
                            "direction": "Inbound",
                            "access": "Allow",
                            "protocol": "TCP",
                            "source_port_range": "*",
                            "destination_port_range": "8080-8090",
                            "source_address_prefix": "0.0.0.0/0",
                            "destination_address_prefix": "*",
                            "risk_level": "High",
                            "description": "Custom application ports open to internet"
                        }
                    ],
                    "ports_summary": {
                        "critical_ports": ["3389", "22"],
                        "high_risk_ports": ["8080-8090"],
                        "medium_risk_ports": ["80"],
                        "low_risk_ports": ["443"]
                    }
                }
            },
            {
                "id": "cis-006",
                "title": "Virtual machines lack endpoint protection",
                "description": "VMs do not have antimalware or endpoint protection installed",
                "severity": "high",
                "category": "Compute Security",
                "recommendation": "Install and configure endpoint protection on all VMs",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/prod-rg/providers/Microsoft.Compute/virtualMachines/prod-web-vm-01",
                "resource_name": "prod-web-vm-01 (Production Web Server - East US)",
                "resource_type": "Microsoft.Compute/virtualMachines",
                "friendly_resource": "Azure Virtual Machine"
            },
            # Medium severity findings (10)
            {
                "id": "cis-007",
                "title": "Security Center standard tier not enabled",
                "description": "Azure Security Center is not configured with standard tier",
                "severity": "medium",
                "category": "Security Monitoring",
                "recommendation": "Enable Security Center standard tier for enhanced protection",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Security/securityContacts/default",
                "resource_name": "Microsoft Defender for Cloud - Security Contacts",
                "resource_type": "Microsoft.Security/securityContacts",
                "friendly_resource": "Microsoft Defender for Cloud"
            },
            {
                "id": "cis-008",
                "title": "Log Analytics workspace not configured",
                "description": "Centralized logging is not properly configured",
                "severity": "medium",
                "category": "Logging and Monitoring",
                "recommendation": "Configure Log Analytics workspace for centralized logging",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/monitoring-rg/providers/Microsoft.OperationalInsights/workspaces/prod-law-workspace",
                "resource_name": "prod-law-workspace (Production Log Analytics - East US)",
                "resource_type": "Microsoft.OperationalInsights/workspaces",
                "friendly_resource": "Log Analytics Workspace"
            },
            {
                "id": "cis-009",
                "title": "Application Gateway WAF not enabled",
                "description": "Web Application Firewall is not enabled on Application Gateway",
                "severity": "medium",
                "category": "Web Security",
                "recommendation": "Enable WAF on Application Gateway with OWASP rules",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/network-rg/providers/Microsoft.Network/applicationGateways/prod-appgw-01",
                "resource_name": "prod-appgw-01 (Production Application Gateway - East US)",
                "resource_type": "Microsoft.Network/applicationGateways",
                "friendly_resource": "Application Gateway"
            },
            {
                "id": "cis-010",
                "title": "Backup not configured for critical resources",
                "description": "Azure Backup is not configured for VMs and databases",
                "severity": "medium",
                "category": "Data Protection",
                "recommendation": "Configure Azure Backup for all critical resources",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/backup-rg/providers/Microsoft.RecoveryServices/vaults/prod-backup-vault",
                "resource_name": "prod-backup-vault (Production Backup Vault - East US)",
                "resource_type": "Microsoft.RecoveryServices/vaults",
                "friendly_resource": "Recovery Services Vault"
            },
            {
                "id": "cis-011",
                "title": "Resource locks not applied",
                "description": "Critical resources lack resource locks to prevent accidental deletion",
                "severity": "medium",
                "category": "Resource Management",
                "recommendation": "Apply resource locks to critical infrastructure",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/prod-rg",
                "resource_name": "prod-rg (Production Resource Group - East US)",
                "resource_type": "Microsoft.Resources/resourceGroups",
                "friendly_resource": "Resource Group"
            },
            {
                "id": "cis-012",
                "title": "Disk encryption not enabled",
                "description": "VM disks are not encrypted with Azure Disk Encryption",
                "severity": "medium",
                "category": "Data Protection",
                "recommendation": "Enable Azure Disk Encryption for all VM disks",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/prod-rg/providers/Microsoft.Compute/disks/prod-web-vm-01_OsDisk_1",
                "resource_name": "prod-web-vm-01_OsDisk_1 (Production VM OS Disk - 128GB Premium SSD)",
                "resource_type": "Microsoft.Compute/disks",
                "friendly_resource": "Managed Disk"
            },
            {
                "id": "cis-013",
                "title": "Network Watcher not enabled",
                "description": "Network monitoring and diagnostics are not properly configured",
                "severity": "medium",
                "category": "Network Monitoring",
                "recommendation": "Enable Network Watcher for network monitoring",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/NetworkWatcherRG/providers/Microsoft.Network/networkWatchers/NetworkWatcher_eastus",
                "resource_name": "NetworkWatcher_eastus (Network Watcher - East US Region)",
                "resource_type": "Microsoft.Network/networkWatchers",
                "friendly_resource": "Network Watcher"
            },
            {
                "id": "cis-014",
                "title": "Azure AD Privileged Identity Management not configured",
                "description": "PIM is not configured for privileged role management",
                "severity": "medium",
                "category": "Identity and Access Management",
                "recommendation": "Configure Azure AD PIM for privileged access management",
                "status": "failed",
                "resource_id": "/providers/Microsoft.AzureActiveDirectory/privilegedIdentityManagement/azureResources",
                "resource_name": "Azure AD Privileged Identity Management (PIM)",
                "resource_type": "Microsoft.AzureActiveDirectory/privilegedIdentityManagement",
                "friendly_resource": "Azure AD Privileged Identity Management"
            },
            {
                "id": "cis-015",
                "title": "Activity log retention not configured",
                "description": "Activity logs are not retained for the required compliance period",
                "severity": "medium",
                "category": "Logging and Monitoring",
                "recommendation": "Configure activity log retention for 90+ days",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Insights/activityLogAlerts",
                "resource_name": "Activity Log Alerts (Subscription Level Monitoring)",
                "resource_type": "Microsoft.Insights/activityLogAlerts",
                "friendly_resource": "Activity Log Alerts"
            },
            {
                "id": "cis-016",
                "title": "Azure Policy not implemented",
                "description": "Governance policies are not enforced through Azure Policy",
                "severity": "medium",
                "category": "Governance",
                "recommendation": "Implement Azure Policy for governance and compliance",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/policyAssignments",
                "resource_name": "Azure Policy Assignments (Governance Framework)",
                "resource_type": "Microsoft.Authorization/policyAssignments",
                "friendly_resource": "Azure Policy"
            },
            # Low severity findings (8)
            {
                "id": "cis-017",
                "title": "Resource tags not standardized",
                "description": "Resources lack consistent tagging for cost management and governance",
                "severity": "low",
                "category": "Resource Management",
                "recommendation": "Implement standardized resource tagging strategy",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resources",
                "resource_name": "All Subscription Resources (Tagging Compliance)",
                "resource_type": "Microsoft.Resources/subscriptions",
                "friendly_resource": "Subscription Resources"
            },
            {
                "id": "cis-018",
                "title": "Cost management alerts not configured",
                "description": "Budget alerts and cost management are not properly configured",
                "severity": "low",
                "category": "Cost Management",
                "recommendation": "Configure budget alerts and cost management policies",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.CostManagement/budgets",
                "resource_name": "Cost Management Budgets and Alerts",
                "resource_type": "Microsoft.CostManagement/budgets",
                "friendly_resource": "Cost Management"
            },
            {
                "id": "cis-019",
                "title": "Service Health alerts not configured",
                "description": "Service health notifications are not configured for critical services",
                "severity": "low",
                "category": "Service Monitoring",
                "recommendation": "Configure Service Health alerts for proactive monitoring",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.ResourceHealth/availabilityStatuses",
                "resource_name": "Azure Service Health Monitoring",
                "resource_type": "Microsoft.ResourceHealth/availabilityStatuses",
                "friendly_resource": "Service Health"
            },
            {
                "id": "cis-020",
                "title": "Azure Advisor recommendations not reviewed",
                "description": "Azure Advisor recommendations have not been reviewed or implemented",
                "severity": "low",
                "category": "Optimization",
                "recommendation": "Regularly review and implement Azure Advisor recommendations",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Advisor/recommendations",
                "resource_name": "Azure Advisor Recommendations (Optimization Insights)",
                "resource_type": "Microsoft.Advisor/recommendations",
                "friendly_resource": "Azure Advisor"
            },
            {
                "id": "cis-021",
                "title": "Resource naming conventions not followed",
                "description": "Resources do not follow organizational naming conventions",
                "severity": "low",
                "category": "Governance",
                "recommendation": "Implement and enforce resource naming conventions",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/*/providers/*/",
                "resource_name": "Resource Naming Convention Compliance",
                "resource_type": "Microsoft.Resources/subscriptions",
                "friendly_resource": "Resource Naming Standards"
            },
            {
                "id": "cis-022",
                "title": "Update management not configured",
                "description": "Automated update management is not configured for VMs",
                "severity": "low",
                "category": "Update Management",
                "recommendation": "Configure Azure Update Management for automated patching",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/automation-rg/providers/Microsoft.Automation/automationAccounts/prod-automation",
                "resource_name": "prod-automation (Azure Update Management)",
                "resource_type": "Microsoft.Automation/automationAccounts",
                "friendly_resource": "Automation Account"
            },
            {
                "id": "cis-023",
                "title": "Azure Security Benchmark not applied",
                "description": "Azure Security Benchmark policies are not applied to the subscription",
                "severity": "low",
                "category": "Security Baseline",
                "recommendation": "Apply Azure Security Benchmark initiative",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/policySetDefinitions/1f3afdf9-d0c9-4c3d-847f-89da613e70a8",
                "resource_name": "Azure Security Benchmark Initiative",
                "resource_type": "Microsoft.Authorization/policySetDefinitions",
                "friendly_resource": "Security Benchmark Policy"
            },
            {
                "id": "cis-024",
                "title": "Diagnostic settings not configured",
                "description": "Diagnostic settings are not configured for all Azure services",
                "severity": "low",
                "category": "Logging and Monitoring",
                "recommendation": "Configure diagnostic settings for all Azure services",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Insights/diagnosticSettings",
                "resource_name": "Diagnostic Settings (All Azure Services)",
                "resource_type": "Microsoft.Insights/diagnosticSettings",
                "friendly_resource": "Diagnostic Settings"
            }
        ]
    elif framework == "SOC2":
        # SOC 2 Type II comprehensive findings
        findings = [
            # Security - Critical findings
            {
                "id": "soc2-sec-001",
                "title": "Multi-factor authentication not enforced for all users",
                "description": "SOC 2 Security criterion requires MFA for all user access to systems containing customer data",
                "severity": "critical",
                "category": "Security - Logical Access",
                "recommendation": "Implement MFA for all user accounts accessing customer data systems. Configure conditional access policies in Azure AD to enforce MFA based on risk assessment.",
                "status": "failed",
                "resource_id": "/providers/Microsoft.AzureActiveDirectory/users",
                "resource_name": "Azure AD User Accounts (All Active Users)"
            },
            {
                "id": "soc2-sec-002",
                "title": "Privileged access management controls insufficient",
                "description": "Administrative access lacks proper approval workflows and time-bound access controls",
                "severity": "critical",
                "category": "Security - Logical Access",
                "recommendation": "Implement Azure AD Privileged Identity Management (PIM) with approval workflows, time-bound access, and access reviews for all privileged roles.",
                "status": "failed",
                "resource_id": "/providers/Microsoft.AzureActiveDirectory/privilegedIdentityManagement",
                "resource_name": "Azure AD Privileged Identity Management (PIM)"
            },
            # Availability - High findings
            {
                "id": "soc2-avail-001",
                "title": "Backup and disaster recovery procedures not tested",
                "description": "SOC 2 Availability criterion requires regular testing of backup and recovery procedures",
                "severity": "high",
                "category": "Availability - Backup & Recovery",
                "recommendation": "Establish quarterly disaster recovery testing procedures. Document recovery time objectives (RTO) and recovery point objectives (RPO). Implement Azure Site Recovery for critical workloads.",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/backup-rg/providers/Microsoft.RecoveryServices/vaults/prod-backup-vault/backupJobs",
                "resource_name": "prod-backup-vault (Backup Job Testing & Validation)"
            },
            {
                "id": "soc2-avail-002",
                "title": "System monitoring and alerting gaps identified",
                "description": "Insufficient monitoring coverage for critical system components and customer-facing services",
                "severity": "high",
                "category": "Availability - Monitoring",
                "recommendation": "Implement comprehensive monitoring using Azure Monitor, Application Insights, and Log Analytics. Configure proactive alerting for system performance, availability, and security events.",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/monitoring-rg/providers/Microsoft.Insights/components/prod-appinsights",
                "resource_name": "prod-appinsights (Application Insights Monitoring)"
            },
            # Confidentiality - High findings
            {
                "id": "soc2-conf-001",
                "title": "Data encryption at rest not implemented for all data stores",
                "description": "Customer data stored in some systems lacks encryption at rest as required by SOC 2 Confidentiality",
                "severity": "high",
                "category": "Confidentiality - Data Protection",
                "recommendation": "Enable encryption at rest for all Azure storage accounts, SQL databases, and virtual machine disks. Use customer-managed keys where required for enhanced control.",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/storage-rg/providers/Microsoft.Storage/storageAccounts/prodstorage001",
                "resource_name": "prodstorage001 (Production Storage Account - Encryption)"
            },
            {
                "id": "soc2-conf-002",
                "title": "Data classification and handling procedures incomplete",
                "description": "Lack of formal data classification scheme and handling procedures for different data sensitivity levels",
                "severity": "high",
                "category": "Confidentiality - Data Classification",
                "recommendation": "Implement Microsoft Purview Information Protection for data classification. Establish data handling procedures based on sensitivity levels and regulatory requirements.",
                "status": "failed",
                "resource_id": "/providers/Microsoft.Purview/accounts/prod-purview-account",
                "resource_name": "prod-purview-account (Microsoft Purview Data Classification)"
            },
            # Processing Integrity - Medium findings
            {
                "id": "soc2-proc-001",
                "title": "Change management process lacks proper authorization controls",
                "description": "System changes are not consistently reviewed and approved through formal change management process",
                "severity": "medium",
                "category": "Processing Integrity - Change Management",
                "recommendation": "Implement Azure DevOps with approval gates, code reviews, and automated testing. Establish change advisory board (CAB) for critical system changes.",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/devops-rg/providers/Microsoft.DevOps/organizations/prod-devops",
                "resource_name": "prod-devops (Azure DevOps Change Management)"
            },
            {
                "id": "soc2-proc-002",
                "title": "Data processing controls need enhancement",
                "description": "Automated controls for data processing accuracy and completeness require improvement",
                "severity": "medium",
                "category": "Processing Integrity - Data Processing",
                "recommendation": "Implement data validation rules, checksums, and reconciliation procedures. Use Azure Logic Apps or Functions for automated data integrity checks.",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/integration-rg/providers/Microsoft.Logic/workflows/data-validation-workflow",
                "resource_name": "data-validation-workflow (Logic Apps Data Processing)"
            },
            # Privacy - Medium findings
            {
                "id": "soc2-priv-001",
                "title": "Privacy notice and consent management needs improvement",
                "description": "Privacy notices are not consistently updated and consent management lacks granular controls",
                "severity": "medium",
                "category": "Privacy - Consent Management",
                "recommendation": "Implement comprehensive privacy notice management system. Use Microsoft Purview Privacy Management for consent tracking and data subject rights management.",
                "status": "failed",
                "resource_id": "/providers/Microsoft.Purview/accounts/prod-purview-account/privacyManagement",
                "resource_name": "prod-purview-account (Privacy Management & Consent)"
            },
            {
                "id": "soc2-priv-002",
                "title": "Data retention and disposal procedures require formalization",
                "description": "Lack of automated data retention policies and secure disposal procedures for personal data",
                "severity": "medium",
                "category": "Privacy - Data Lifecycle",
                "recommendation": "Implement automated data retention policies using Azure Policy and Microsoft Purview. Establish secure data disposal procedures with audit trails.",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/policyDefinitions/data-retention",
                "resource_name": "Data Retention Policy Definitions (Azure Policy)"
            },
            # Low severity findings
            {
                "id": "soc2-doc-001",
                "title": "Security awareness training documentation incomplete",
                "description": "Employee security training records and acknowledgments need better documentation",
                "severity": "low",
                "category": "Security - Training",
                "recommendation": "Implement learning management system for tracking security awareness training. Maintain records of training completion and acknowledgments.",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/hr-rg/providers/Microsoft.Learning/trainingPrograms/security-awareness",
                "resource_name": "security-awareness (Security Training Program)"
            }
        ]
    elif framework == "NIST":
        # NIST Cybersecurity Framework comprehensive findings
        findings = [
            # Identify - Critical findings
            {
                "id": "nist-id-001",
                "title": "Asset inventory and management system incomplete",
                "description": "NIST ID.AM-1: Physical devices and systems within the organization are not inventoried",
                "severity": "critical",
                "category": "Identify - Asset Management",
                "recommendation": "Implement Microsoft Defender for Cloud asset inventory. Deploy Azure Resource Graph for comprehensive asset tracking and management across all subscriptions.",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.ResourceGraph/resources",
                "resource_name": "Azure Resource Graph (Asset Inventory Management)"
            },
            {
                "id": "nist-id-002",
                "title": "Business environment and critical processes not documented",
                "description": "NIST ID.BE-1: The organization's role in the supply chain is not identified and communicated",
                "severity": "critical",
                "category": "Identify - Business Environment",
                "recommendation": "Document critical business processes, dependencies, and supply chain relationships. Implement business impact analysis (BIA) for all critical systems.",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/governance-rg/providers/Microsoft.Documentation/businessProcesses",
                "resource_name": "Business Process Documentation (Governance Framework)"
            },
            # Protect - High findings
            {
                "id": "nist-pr-001",
                "title": "Identity management and access control gaps",
                "description": "NIST PR.AC-1: Identities and credentials are not issued, managed, verified, revoked for authorized devices and users",
                "severity": "high",
                "category": "Protect - Access Control",
                "recommendation": "Implement comprehensive identity lifecycle management using Azure AD. Deploy automated user provisioning/deprovisioning and regular access reviews.",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/roleAssignments",
                "resource_name": "Azure RBAC (Role-Based Access Control System)"
            },
            {
                "id": "nist-pr-002",
                "title": "Data security controls insufficient",
                "description": "NIST PR.DS-1: Data-at-rest is not protected with appropriate encryption and key management",
                "severity": "high",
                "category": "Protect - Data Security",
                "recommendation": "Implement Azure Key Vault for centralized key management. Enable encryption at rest for all data stores using customer-managed keys where appropriate.",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/storage-rg/providers/Microsoft.Storage/storageAccounts/prodstorage001/encryptionScopes",
                "resource_name": "prodstorage001 (Storage Account Encryption Scopes)"
            },
            {
                "id": "nist-pr-003",
                "title": "Information protection processes and procedures lacking",
                "description": "NIST PR.IP-1: A baseline configuration of information technology/industrial control systems is not created and maintained",
                "severity": "high",
                "category": "Protect - Information Protection",
                "recommendation": "Establish security baselines using Azure Security Benchmark. Implement Azure Policy for configuration management and compliance monitoring.",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Authorization/policySetDefinitions/azure-security-benchmark",
                "resource_name": "Azure Security Benchmark (Policy Initiative)"
            },
            # Detect - High findings
            {
                "id": "nist-de-001",
                "title": "Anomalies and events detection capabilities limited",
                "description": "NIST DE.AE-1: A baseline of network operations and expected data flows is not established and managed",
                "severity": "high",
                "category": "Detect - Anomalies and Events",
                "recommendation": "Deploy Microsoft Sentinel for SIEM capabilities. Implement network traffic analysis using Azure Network Watcher and establish baseline behaviors.",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/security-rg/providers/Microsoft.OperationalInsights/workspaces/prod-sentinel",
                "resource_name": "prod-sentinel (Microsoft Sentinel SIEM)"
            },
            {
                "id": "nist-de-002",
                "title": "Security continuous monitoring program inadequate",
                "description": "NIST DE.CM-1: The network is not monitored to detect potential cybersecurity events",
                "severity": "high",
                "category": "Detect - Continuous Monitoring",
                "recommendation": "Implement comprehensive security monitoring using Microsoft Defender for Cloud. Deploy network security monitoring and endpoint detection and response (EDR) solutions.",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/providers/Microsoft.Security/securityContacts",
                "resource_name": "Microsoft Defender for Cloud (Security Monitoring)"
            },
            # Respond - Medium findings
            {
                "id": "nist-rs-001",
                "title": "Response planning procedures need enhancement",
                "description": "NIST RS.RP-1: Response plan is not executed during or after an incident",
                "severity": "medium",
                "category": "Respond - Response Planning",
                "recommendation": "Develop and test incident response playbooks. Implement Azure Logic Apps for automated incident response workflows and notification procedures.",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/security-rg/providers/Microsoft.SecurityInsights/incidents",
                "resource_name": "Azure Sentinel (Incident Response & SIEM)"
            },
            {
                "id": "nist-rs-002",
                "title": "Communications during incidents not formalized",
                "description": "NIST RS.CO-1: Personnel know their roles and order of operations when a response is needed",
                "severity": "medium",
                "category": "Respond - Communications",
                "recommendation": "Establish incident communication procedures and contact lists. Implement Microsoft Teams integration for incident coordination and status updates.",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/communication-rg/providers/Microsoft.Teams/teams/incident-response",
                "resource_name": "incident-response (Microsoft Teams Integration)"
            },
            # Recover - Medium findings
            {
                "id": "nist-rc-001",
                "title": "Recovery planning and implementation gaps",
                "description": "NIST RC.RP-1: Recovery plan is not executed during or after a cybersecurity incident",
                "severity": "medium",
                "category": "Recover - Recovery Planning",
                "recommendation": "Develop comprehensive recovery procedures with defined RTO/RPO objectives. Implement Azure Site Recovery for automated failover and recovery capabilities.",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/dr-rg/providers/Microsoft.RecoveryServices/vaults/prod-recovery-vault",
                "resource_name": "prod-recovery-vault (Azure Site Recovery)"
            },
            {
                "id": "nist-rc-002",
                "title": "Improvements from lessons learned not systematically applied",
                "description": "NIST RC.IM-1: Recovery plans incorporate lessons learned from previous incidents",
                "severity": "medium",
                "category": "Recover - Improvements",
                "recommendation": "Establish post-incident review process with lessons learned documentation. Implement continuous improvement program for security and recovery procedures.",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/governance-rg/providers/Microsoft.Documentation/improvementProgram",
                "resource_name": "Continuous Improvement Program (Governance Framework)"
            },
            # Low severity findings
            {
                "id": "nist-misc-001",
                "title": "Cybersecurity awareness and training program needs enhancement",
                "description": "Regular cybersecurity awareness training and phishing simulations not consistently conducted",
                "severity": "low",
                "category": "Protect - Awareness and Training",
                "recommendation": "Implement regular cybersecurity awareness training program. Deploy Microsoft Defender for Office 365 Attack Simulator for phishing awareness training.",
                "status": "failed",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/hr-rg/providers/Microsoft.Learning/trainingPrograms/security-awareness",
                "resource_name": "security-awareness (Security Training Program)"
            }
        ]
    elif framework == "ISO27001":
        # ISO 27001:2022 comprehensive findings
        findings = [
            # Critical findings - Information Security Management System
            {
                "id": "iso-isms-001",
                "title": "Information Security Management System (ISMS) documentation incomplete",
                "description": "ISO 27001 Clause 4.3: ISMS scope and boundaries are not clearly documented and communicated",
                "severity": "critical",
                "category": "ISMS - Documentation",
                "recommendation": "Document ISMS scope, boundaries, and applicability. Establish information security policy and procedures aligned with business objectives.",
                "status": "failed",
                "resource_id": "isms-documentation",
                "resource_name": "ISMS Documentation Framework"
            },
            {
                "id": "iso-risk-001",
                "title": "Information security risk assessment process inadequate",
                "description": "ISO 27001 Clause 6.1.2: Risk assessment methodology and criteria are not established or consistently applied",
                "severity": "critical",
                "category": "Risk Management",
                "recommendation": "Implement comprehensive risk assessment methodology. Use Microsoft Purview Risk Management for automated risk identification and assessment.",
                "status": "failed",
                "resource_id": "risk-assessment",
                "resource_name": "Risk Assessment Process"
            },
            # High findings - Access Control (A.9)
            {
                "id": "iso-ac-001",
                "title": "Access control policy and procedures not comprehensive",
                "description": "ISO 27001 A.9.1.1: Access control policy does not address all aspects of logical and physical access management",
                "severity": "high",
                "category": "Access Control",
                "recommendation": "Develop comprehensive access control policy covering user access management, privileged access, and regular access reviews using Azure AD.",
                "status": "failed",
                "resource_id": "access-control-policy",
                "resource_name": "Access Control Policy Framework"
            },
            {
                "id": "iso-ac-002",
                "title": "User access provisioning and deprovisioning not automated",
                "description": "ISO 27001 A.9.2.1: User access provisioning lacks proper authorization and automated lifecycle management",
                "severity": "high",
                "category": "Access Control",
                "recommendation": "Implement automated user provisioning using Azure AD Connect and lifecycle workflows. Establish approval processes for access requests.",
                "status": "failed",
                "resource_id": "user-provisioning",
                "resource_name": "User Lifecycle Management"
            },
            # High findings - Cryptography (A.10)
            {
                "id": "iso-crypto-001",
                "title": "Cryptographic controls policy not established",
                "description": "ISO 27001 A.10.1.1: Policy on the use of cryptographic controls for protection of information is not defined",
                "severity": "high",
                "category": "Cryptography",
                "recommendation": "Establish cryptographic policy defining encryption standards, key management procedures, and approved algorithms. Use Azure Key Vault for centralized key management.",
                "status": "failed",
                "resource_id": "crypto-policy",
                "resource_name": "Cryptographic Policy Framework"
            },
            {
                "id": "iso-crypto-002",
                "title": "Key management lifecycle not properly implemented",
                "description": "ISO 27001 A.10.1.2: Cryptographic key management throughout their lifecycle is not adequately controlled",
                "severity": "high",
                "category": "Cryptography",
                "recommendation": "Implement comprehensive key lifecycle management using Azure Key Vault HSM. Establish key rotation, backup, and recovery procedures.",
                "status": "failed",
                "resource_id": "key-management",
                "resource_name": "Cryptographic Key Management"
            },
            # Medium findings - Operations Security (A.12)
            {
                "id": "iso-ops-001",
                "title": "Operational procedures and responsibilities not documented",
                "description": "ISO 27001 A.12.1.1: Operating procedures are not documented and made available to users who need them",
                "severity": "medium",
                "category": "Operations Security",
                "recommendation": "Document all operational procedures for IT systems management. Implement Azure DevOps for procedure documentation and version control.",
                "status": "failed",
                "resource_id": "operational-procedures",
                "resource_name": "Operations Documentation"
            },
            {
                "id": "iso-ops-002",
                "title": "Change management process lacks security considerations",
                "description": "ISO 27001 A.12.1.2: Changes to the organization, business processes, information processing facilities are not controlled",
                "severity": "medium",
                "category": "Operations Security",
                "recommendation": "Integrate security assessments into change management process. Use Azure DevOps with security gates and approval workflows.",
                "status": "failed",
                "resource_id": "change-management-security",
                "resource_name": "Secure Change Management"
            },
            # Medium findings - Communications Security (A.13)
            {
                "id": "iso-comm-001",
                "title": "Network security management controls insufficient",
                "description": "ISO 27001 A.13.1.1: Network controls are not managed and controlled to protect information in systems and applications",
                "severity": "medium",
                "category": "Communications Security",
                "recommendation": "Implement network segmentation using Azure Virtual Networks and Network Security Groups. Deploy Azure Firewall for centralized network security.",
                "status": "failed",
                "resource_id": "network-security-mgmt",
                "resource_name": "Network Security Management"
            },
            {
                "id": "iso-comm-002",
                "title": "Information transfer policies not comprehensive",
                "description": "ISO 27001 A.13.2.1: Formal transfer policies, procedures and controls are not in place to protect transfer of information",
                "severity": "medium",
                "category": "Communications Security",
                "recommendation": "Establish data transfer policies and procedures. Implement Azure Information Protection for data classification and protection during transfer.",
                "status": "failed",
                "resource_id": "data-transfer-policy",
                "resource_name": "Data Transfer Policies"
            },
            # Medium findings - System Acquisition and Maintenance (A.14)
            {
                "id": "iso-dev-001",
                "title": "Security requirements not integrated in development lifecycle",
                "description": "ISO 27001 A.14.1.1: Information security requirements are not included in requirements for new information systems",
                "severity": "medium",
                "category": "System Development",
                "recommendation": "Integrate security requirements into SDLC. Implement DevSecOps practices using Azure DevOps with security scanning and compliance checks.",
                "status": "failed",
                "resource_id": "secure-development",
                "resource_name": "Secure Development Lifecycle"
            },
            # Low findings - Supplier Relationships (A.15)
            {
                "id": "iso-supplier-001",
                "title": "Information security in supplier relationships not addressed",
                "description": "ISO 27001 A.15.1.1: Information security requirements for mitigating risks from supplier access are not established",
                "severity": "low",
                "category": "Supplier Relationships",
                "recommendation": "Establish supplier security requirements and assessment procedures. Implement Azure AD B2B for secure supplier access management.",
                "status": "failed",
                "resource_id": "supplier-security",
                "resource_name": "Supplier Security Management"
            },
            # Low findings - Incident Management (A.16)
            {
                "id": "iso-incident-001",
                "title": "Information security incident management procedures incomplete",
                "description": "ISO 27001 A.16.1.1: Management responsibilities and procedures are not established for information security incident management",
                "severity": "low",
                "category": "Incident Management",
                "recommendation": "Establish comprehensive incident response procedures. Implement Microsoft Sentinel for security incident detection and response automation.",
                "status": "failed",
                "resource_id": "incident-management",
                "resource_name": "Security Incident Management"
            }
        ]
    
    return findings

@app.post("/api/v1/scans/schedule")
async def schedule_scan(scan_request: dict):
    """Schedule a scan at a given UTC time (ISO8601)."""
    try:
        subscription_id = scan_request.get("subscription_id")
        framework = scan_request.get("framework")
        scheduled_at = scan_request.get("scheduled_at")
        if not all([subscription_id, framework, scheduled_at]):
            raise HTTPException(status_code=400, detail="subscription_id, framework and scheduled_at are required")
        scan_config = scan_request.get("config", {})
        dt = datetime.fromisoformat(scheduled_at.replace("Z", "+00:00")).astimezone(tz=None).replace(tzinfo=None)
        result = await azure_service.schedule_security_scan(subscription_id, framework, scan_config, dt)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule scan: {str(e)}")

@app.post("/api/v1/scans/{scan_id}/cancel")
async def cancel_scan(scan_id: str):
    """Cancel a scheduled or in-progress scan"""
    try:
        # Find the scan in our local data
        scan = next((s for s in SECURITY_SCANS if s.get("scan_id") == scan_id), None)
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        if scan.get("status") in ("completed", "failed", "canceled"):
            raise HTTPException(status_code=400, detail="Cannot cancel completed, failed, or already canceled scan")
        
        # Update scan status
        scan["status"] = "canceled"
        scan["end_time"] = datetime.utcnow().isoformat()
        
        print(f"✅ Scan {scan_id} canceled successfully")
        
        return {"ok": True, "message": f"Scan {scan_id} canceled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Failed to cancel scan {scan_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel scan: {str(e)}")

@app.get("/api/v1/scans/{scan_id}/status")
async def get_scan_status(scan_id: str):
    """Get scan status and progress"""
    try:
        scan_data = next((s for s in SECURITY_SCANS if s.get("scan_id") == scan_id), None)
        if not scan_data:
            raise HTTPException(status_code=404, detail="Scan not found")
        return scan_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scan status: {str(e)}")

@app.get("/api/v1/scans/{scan_id}/findings")
async def get_scan_findings(scan_id: str):
    """Get scan findings for agent creation"""
    try:
        scan = next((s for s in SECURITY_SCANS if s.get("scan_id") == scan_id), None)
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        if scan["status"] != "completed":
            raise HTTPException(status_code=400, detail="Scan is not completed yet")
        
        # Return findings with severity and resource type for agent creation
        findings = [
            {
                "id": "finding-001",
                "title": "Unencrypted Storage Account",
                "severity": "critical",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/rg-storage/providers/Microsoft.Storage/storageAccounts/storageaccount001",
                "resource_name": "storageaccount001",
                "resource_type": "Microsoft.Storage/storageAccounts",
                "description": "Storage account is not encrypted at rest",
                "remediation": "Enable encryption for storage account",
                "category": "Data Protection"
            },
            {
                "id": "finding-002",
                "title": "Network Security Group - Open RDP",
                "severity": "high",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/rg-network/providers/Microsoft.Network/networkSecurityGroups/nsg-web",
                "resource_name": "nsg-web",
                "resource_type": "Microsoft.Network/networkSecurityGroups",
                "description": "RDP port 3389 is open to internet",
                "remediation": "Restrict RDP access to specific IP ranges",
                "category": "Network Security"
            },
            {
                "id": "finding-003",
                "title": "Virtual Machine - Unpatched System",
                "severity": "medium",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/rg-compute/providers/Microsoft.Compute/virtualMachines/vm-web-01",
                "resource_name": "vm-web-01",
                "resource_type": "Microsoft.Compute/virtualMachines",
                "description": "Virtual machine has missing security patches",
                "remediation": "Apply latest security patches and enable automatic updates",
                "category": "System Security"
            },
            {
                "id": "finding-004",
                "title": "Key Vault - Weak Access Policy",
                "severity": "high",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/rg-security/providers/Microsoft.KeyVault/vaults/kv-prod-secrets",
                "resource_name": "kv-prod-secrets",
                "resource_type": "Microsoft.KeyVault/vaults",
                "description": "Key vault has overly permissive access policies",
                "remediation": "Implement principle of least privilege for key vault access",
                "category": "Access Control"
            },
            {
                "id": "finding-005",
                "title": "Application Security Group - Misconfigured Rules",
                "severity": "medium",
                "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/rg-network/providers/Microsoft.Network/applicationSecurityGroups/asg-web",
                "resource_name": "asg-web",
                "resource_type": "Microsoft.Network/applicationSecurityGroups",
                "description": "Application security group has misconfigured rules allowing unnecessary traffic",
                "remediation": "Review and tighten application security group rules",
                "category": "Network Security"
            }
        ]
        
        return {
            "scan_id": scan_id,
            "scan_name": scan.get("name", "Security Scan"),
            "findings": findings,
            "total_findings": len(findings),
            "severity_summary": {
                "critical": len([f for f in findings if f["severity"] == "critical"]),
                "high": len([f for f in findings if f["severity"] == "high"]),
                "medium": len([f for f in findings if f["severity"] == "medium"]),
                "low": len([f for f in findings if f["severity"] == "low"])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scan findings: {str(e)}")

@app.get("/api/v1/scans/{scan_id}/download")
async def download_scan_report(scan_id: str):
    """Download scan report as HTML file with AI-powered recommendations"""
    scan = next((s for s in SECURITY_SCANS if s.get("scan_id") == scan_id), None)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if scan["status"] != "completed":
        raise HTTPException(status_code=400, detail="Scan not completed yet")
    
    # Generate AI recommendations for each finding
    enhanced_findings = []
    findings = scan.get('findings', [])
    for finding in findings:
        ai_recommendations = await generate_ai_recommendations(finding)
        enhanced_finding = {**finding, **ai_recommendations}
        enhanced_findings.append(enhanced_finding)
    
    # Generate HTML content for the scan report with AI recommendations
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Security Scan Report - {scan.get('framework', 'Unknown')}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f7fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; }}
        .header h1 {{ margin: 0; font-size: 2.5em; }}
        .header p {{ margin: 5px 0; opacity: 0.9; }}
        .summary {{ background: #f8f9fa; padding: 25px; margin: 0; border-bottom: 1px solid #e9ecef; }}
        .summary h2 {{ color: #495057; margin-top: 0; }}
        .metrics {{ display: flex; gap: 20px; margin-top: 15px; }}
        .metric {{ background: white; padding: 15px; border-radius: 8px; text-align: center; flex: 1; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        .metric-label {{ color: #6c757d; font-size: 0.9em; }}
        .findings {{ padding: 25px; }}
        .finding {{ border: 1px solid #e9ecef; margin: 20px 0; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .finding-header {{ padding: 20px; background: #f8f9fa; border-bottom: 1px solid #e9ecef; }}
        .finding-content {{ padding: 20px; }}
        .critical {{ border-left: 5px solid #dc3545; }}
        .high {{ border-left: 5px solid #fd7e14; }}
        .medium {{ border-left: 5px solid #ffc107; }}
        .low {{ border-left: 5px solid #28a745; }}
        .severity-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: bold; text-transform: uppercase; }}
        .severity-critical {{ background: #dc3545; color: white; }}
        .severity-high {{ background: #fd7e14; color: white; }}
        .severity-medium {{ background: #ffc107; color: white; }}
        .severity-low {{ background: #28a745; color: white; }}
        .ai-recommendations {{ background: #e3f2fd; border: 1px solid #bbdefb; border-radius: 8px; padding: 20px; margin-top: 15px; }}
        .ai-recommendations h4 {{ color: #1976d2; margin-top: 0; display: flex; align-items: center; }}
        .ai-icon {{ margin-right: 8px; }}
        .recommendation-section {{ margin: 15px 0; }}
        .recommendation-section h5 {{ color: #424242; margin-bottom: 8px; }}
        .priority-badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.7em; font-weight: bold; }}
        .priority-critical {{ background: #ffebee; color: #c62828; }}
        .priority-high {{ background: #fff3e0; color: #ef6c00; }}
        .priority-medium {{ background: #f3e5f5; color: #7b1fa2; }}
        .priority-low {{ background: #e8f5e8; color: #2e7d32; }}
        .business-impact {{ background: #fff8e1; border-left: 4px solid #ffc107; padding: 15px; margin: 10px 0; border-radius: 0 5px 5px 0; }}
        .effort-estimate {{ background: #f3e5f5; border-left: 4px solid #9c27b0; padding: 15px; margin: 10px 0; border-radius: 0 5px 5px 0; }}
        .code-block {{ background: #263238; color: #eeffff; padding: 15px; border-radius: 5px; font-family: 'Courier New', monospace; font-size: 0.9em; overflow-x: auto; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Security Scan Report</h1>
            <p>Scan ID: {scan['scan_id']}</p>
            <p>Framework: {scan['framework']}</p>
            <p>Subscription ID: {scan['subscription_id']}</p>
            <p>Status: {scan['status']}</p>
            <p>Started: {scan['start_time']}</p>
            <p>Completed: {scan.get('end_time', 'N/A')}</p>
        </div>
        
        <div class="summary">
            <h2>Executive Summary</h2>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{scan.get('compliance_score', 0)}%</div>
                    <div class="metric-label">Compliance Score</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{scan.get('total_checks', 0)}</div>
                    <div class="metric-label">Total Checks</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{scan.get('passed_checks', 0)}</div>
                    <div class="metric-label">Passed</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{scan.get('failed_checks', 0)}</div>
                    <div class="metric-label">Failed</div>
                </div>
            </div>
        </div>
        
        <div class="findings">
            <h2>🔍 Detailed Findings with AI Recommendations</h2>"""
    
    # Add enhanced findings with AI recommendations
    if enhanced_findings:
        for finding in enhanced_findings:
            severity = finding.get('severity', 'medium').lower()
            severity_class = f"severity-{severity}"
            
            html_content += f"""
            <div class="finding {severity}">
                <div class="finding-header">
                    <h3>{finding.get('title', 'Security Finding')}</h3>
                    <span class="severity-badge {severity_class}">{severity.upper()}</span>
                    <span class="priority-badge priority-{finding.get('priority', 'medium').lower()}">
                        Priority: {finding.get('priority', 'Medium')}
                    </span>
                </div>
                <div class="finding-content">
                    <p><strong>🎯 Resource:</strong> {finding.get('resource_name', 'N/A')}</p>
                    <p><strong>📝 Description:</strong> {finding.get('description', 'No description available')}</p>
                    
                    <div class="ai-recommendations">
                        <h4><span class="ai-icon">🤖</span>AI-Powered Recommendations</h4>
                        
                        <div class="recommendation-section">
                            <h5>🔧 Remediation Steps:</h5>
                            <p>{finding.get('recommendation', 'Review and remediate as needed')}</p>
                        </div>
                        
                        <div class="business-impact">
                            <strong>💼 Business Impact:</strong> {finding.get('business_impact', 'Impact assessment not available')}
                        </div>
                        
                        <div class="effort-estimate">
                            <strong>⏱️ Estimated Effort:</strong> {finding.get('estimated_effort', 'Effort estimation not available')}
                        </div>
                        
                        <div class="recommendation-section">
                            <h5>☁️ Azure Commands:</h5>
                            <div class="code-block">{finding.get('azure_commands', 'No specific commands available')}</div>
                        </div>
                    </div>
                </div>
            </div>"""
    else:
        html_content += "<p>No findings available for this scan.</p>"
    
    html_content += """
        </div>
        
        <div style="padding: 25px; background: #f8f9fa; text-align: center; border-top: 1px solid #e9ecef;">
            <p style="color: #6c757d; margin: 0;">Report generated by Securra Security Platform with AI-powered recommendations</p>
        </div>
    </div>
</body>
</html>"""
    
    # Return as downloadable file
    return StreamingResponse(
        io.BytesIO(html_content.encode('utf-8')),
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename=scan-report-{scan_id}.html"}
    )

@app.get("/api/v1/subscriptions/{subscription_id}/resources")
async def get_subscription_resources(subscription_id: str):
    """Get detailed resources for a specific subscription"""
    try:
        resources_data = await azure_service.get_subscription_resources(subscription_id)
        return resources_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch subscription resources: {str(e)}")

# =============================
# Runtime configuration endpoints
# =============================
def _env_path() -> str:
    # .env lives in backend/.env relative to this file
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".env"))

@app.get("/api/v1/config")
async def get_config():
    """Return current loaded config (masking secrets)."""
    return {
        "AZURE_CLIENT_ID": (os.getenv("AZURE_CLIENT_ID")[:8] + "...") if os.getenv("AZURE_CLIENT_ID") else None,
        "AZURE_TENANT_ID": (os.getenv("AZURE_TENANT_ID")[:8] + "...") if os.getenv("AZURE_TENANT_ID") else None,
        "AZURE_CLIENT_SECRET": "SET" if os.getenv("AZURE_CLIENT_SECRET") else "NOT_SET",
        "AZURE_STORAGE_CONNECTION_STRING": "SET" if os.getenv("AZURE_STORAGE_CONNECTION_STRING") else "NOT_SET",
        "DATABASE_URL": (os.getenv("DATABASE_URL")[:24] + "...") if os.getenv("DATABASE_URL") else None,
        "REDIS_URL": (os.getenv("REDIS_URL")[:24] + "...") if os.getenv("REDIS_URL") else None,
        "OPENAI_API_KEY": "SET" if os.getenv("OPENAI_API_KEY") else "NOT_SET",
        "use_mock": getattr(azure_service, "use_mock", True),
    }

@app.post("/api/v1/config")
async def set_config(payload: Dict[str, str]):
    """Set Azure/Storage/Database configuration at runtime and persist to .env.
    Accepts: AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID,
             AZURE_STORAGE_CONNECTION_STRING, DATABASE_URL
    """
    env_file = _env_path()

    # Persist provided keys to .env and process environment
    if not os.path.exists(env_file):
        # Ensure the .env file exists so set_key can write to it
        open(env_file, 'a', encoding='utf-8').close()

    for key in [
        "AZURE_CLIENT_ID",
        "AZURE_CLIENT_SECRET",
        "AZURE_TENANT_ID",
        "AZURE_STORAGE_CONNECTION_STRING",
        "DATABASE_URL",
        "REDIS_URL",
        "OPENAI_API_KEY",
    ]:
        if key in payload and payload[key]:
            set_key(env_file, key, payload[key])
            os.environ[key] = payload[key]

    # Reload .env file and azure credentials in-memory
    load_dotenv(env_file, override=True)
    status = azure_service.reload_from_env()

    return {"message": "Configuration updated", "azure_status": status}

@app.get("/api/v1/azure/test")
async def azure_test():
    """Test Azure credentials by attempting to list subscriptions."""
    try:
        subs = await azure_service.get_subscriptions()
        return {"ok": True, "use_mock": getattr(azure_service, "use_mock", True), "count": len(subs)}
    except Exception as e:
        return {"ok": False, "error": str(e), "use_mock": getattr(azure_service, "use_mock", True)}



@app.get("/api/v1/scans/{scan_id}")
async def get_scan_details(scan_id: str):
    """Get detailed scan information"""
    scan = next((s for s in SECURITY_SCANS if s.get("scan_id") == scan_id), None)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Add detailed findings for completed scans
    if scan["status"] == "completed":
        scan["detailed_findings"] = [
            {
                "id": "finding-001",
                "title": "Unencrypted Storage Account",
                "severity": "critical",
                "resource": "storageaccount001",
                "resource_type": "Microsoft.Storage/storageAccounts",
                "description": "Storage account is not encrypted at rest",
                "remediation": "Enable encryption for storage account",
                "cis_control": "CIS 3.1",
                "soc_control": "CC6.1"
            },
            {
                "id": "finding-002", 
                "title": "Network Security Group - Open RDP",
                "severity": "high",
                "resource": "nsg-web",
                "resource_type": "Microsoft.Network/networkSecurityGroups",
                "description": "RDP port 3389 is open to internet",
                "remediation": "Restrict RDP access to specific IP ranges",
                "cis_control": "CIS 6.1",
                "soc_control": "CC6.6"
            },
            {
                "id": "finding-003",
                "title": "Virtual Machine - Unpatched System",
                "severity": "medium",
                "resource": "vm-web-01",
                "resource_type": "Microsoft.Compute/virtualMachines",
                "description": "Virtual machine has missing security patches",
                "remediation": "Apply latest security patches and enable automatic updates",
                "cis_control": "CIS 2.1",
                "soc_control": "CC8.1"
            },
            {
                "id": "finding-004",
                "title": "Key Vault - Weak Access Policy",
                "severity": "high",
                "resource": "kv-prod-secrets",
                "resource_type": "Microsoft.KeyVault/vaults",
                "description": "Key vault has overly permissive access policies",
                "remediation": "Implement principle of least privilege for key vault access",
                "cis_control": "CIS 8.1",
                "soc_control": "CC6.2"
            }
        ]
    
    return scan

# CIS & SOC Compliance Reports
@app.get("/api/v1/reports")
async def get_compliance_reports(subscription_id: str = None):
    """Get all compliance reports generated from actual scan data"""
    try:
        # Generate reports from completed scans first (prioritize dynamic data)
        generated_reports = []
        for scan in SECURITY_SCANS:
            if scan.get("status") == "completed":
                report = await _generate_compliance_report_from_scan(scan)
                if report:
                    # Check if report already exists for this scan
                    existing_report = next((r for r in COMPLIANCE_REPORTS if r.get("scan_id") == scan.get("scan_id")), None)
                    if not existing_report:
                        COMPLIANCE_REPORTS.append(report)
                        generated_reports.append(report)
        
        # Return dynamic reports if available, otherwise try Azure service
        if COMPLIANCE_REPORTS:
            return {
                "reports": COMPLIANCE_REPORTS,
                "total": len(COMPLIANCE_REPORTS),
                "available_types": ["CIS", "SOC2", "NIST", "ISO27001"],
                "generated_from_scans": len(generated_reports)
            }
        else:
            # Fallback to Azure service if no dynamic reports available
            reports = azure_service.get_reports(subscription_id)
            return {
                "reports": reports,
                "total": len(reports),
                "available_types": ["CIS", "SOC2", "NIST", "ISO27001"]
            }
    except Exception as e:
        return {
            "reports": [],
            "total": 0,
            "available_types": ["CIS", "SOC2", "NIST", "ISO27001"],
            "error": str(e)
        }

@app.post("/api/v1/reports")
async def generate_compliance_report(report_data: dict):
    """Generate a new compliance report from scan data"""
    scan_id = report_data.get("scan_id")
    if not scan_id:
        raise HTTPException(status_code=400, detail="scan_id is required")
    
    # Find the completed scan
    scan = next((s for s in SECURITY_SCANS if s.get("scan_id") == scan_id), None)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if scan.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Can only generate reports from completed scans")
    
    # Check if report already exists for this scan
    existing_report = next((r for r in COMPLIANCE_REPORTS if r.get("scan_id") == scan_id), None)
    if existing_report:
        return {"message": "Report already exists", "report": existing_report}
    
    # Generate report from scan data
    new_report = await _generate_compliance_report_from_scan(scan)
    if not new_report:
        raise HTTPException(status_code=500, detail="Failed to generate report from scan data")
    
    # Override report type if specified
    if report_data.get("type"):
        new_report["type"] = report_data.get("type")
        new_report["name"] = f"{report_data.get('type')} Compliance Report - {scan.get('target_name', 'Security Scan')}"
    
    COMPLIANCE_REPORTS.append(new_report)
    return {"message": "Report generated successfully", "report": new_report}

@app.get("/api/v1/reports/{report_id}")
async def get_report_details(report_id: str):
    """Get detailed report information with actual scan data"""
    report = next((r for r in COMPLIANCE_REPORTS if r["id"] == report_id), None)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Add detailed findings from the associated scan
    if report.get("scan_id"):
        scan = next((s for s in SECURITY_SCANS if s.get("scan_id") == report["scan_id"]), None)
        if scan and scan.get("status") == "completed":
            findings = scan.get("findings", [])
            
            # Add executive dashboard with real data
            report["executive_dashboard"] = {
                "overall_score": report["compliance_score"],
                "risk_level": "High" if report["compliance_score"] < 70 else "Medium" if report["compliance_score"] < 85 else "Low",
                "key_metrics": {
                    "total_controls": report.get("scan_details", {}).get("total_checks", 0),
                    "compliant_controls": report.get("scan_details", {}).get("passed_checks", 0),
                    "failed_controls": report.get("scan_details", {}).get("failed_checks", 0),
                    "critical_findings": report.get("findings_summary", {}).get("critical", 0),
                    "high_findings": report.get("findings_summary", {}).get("high", 0),
                    "remediation_priority": f"Critical: {report.get('findings_summary', {}).get('critical', 0)}, High: {report.get('findings_summary', {}).get('high', 0)}"
                },
                "scan_info": {
                    "scan_date": scan.get("created_at"),
                    "scan_duration": scan.get("duration", "N/A"),
                    "framework": scan.get("framework"),
                    "target_name": scan.get("target_name")
                }
            }
            
            # Add detailed findings to the report
            report["detailed_findings"] = findings
    
    return report

@app.get("/api/v1/reports/{report_id}/download")
async def download_report(report_id: str):
    """Download a compliance report as PDF"""
    try:
        # Find the report
        report = None
        for r in COMPLIANCE_REPORTS:
            if r["id"] == report_id:
                report = r
                break
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Get scan data for detailed findings
        scan_data = None
        if report.get("scan_id"):
            scan_data = next((s for s in SECURITY_SCANS if s.get("scan_id") == report["scan_id"]), None)
        
        # Generate AI-enhanced findings for compliance report
        findings_html = ""
        if scan_data and scan_data.get("findings"):
            findings_html = "<div class='section'><h3>🔍 Detailed Security Findings with AI Recommendations</h3>"
            
            # Generate AI recommendations for each finding
            for finding in scan_data["findings"]:
                # Get AI recommendations for this finding
                ai_recommendations = await generate_ai_recommendations(finding)
                enhanced_finding = {**finding, **ai_recommendations}
                
                severity_color = {
                    "critical": "#d32f2f",
                    "high": "#f57c00", 
                    "medium": "#fbc02d",
                    "low": "#388e3c"
                }.get(finding.get("severity", "low"), "#666")
                
                findings_html += f"""
                <div class="finding" style="border: 1px solid #e9ecef; margin: 20px 0; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 5px solid {severity_color};">
                    <div style="padding: 20px; background: #f8f9fa; border-bottom: 1px solid #e9ecef;">
                        <h4 style="color: {severity_color}; margin: 0; font-size: 1.2em;">{finding.get('title', 'Unknown Finding')}</h4>
                        <span style="display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: bold; text-transform: uppercase; background: {severity_color}; color: white; margin-top: 8px;">{finding.get('severity', 'Unknown')}</span>
                        <span style="display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.7em; font-weight: bold; margin-left: 10px; background: #fff3e0; color: #ef6c00;">Priority: {enhanced_finding.get('priority', 'Medium')}</span>
                    </div>
                    <div style="padding: 20px;">
                        <p><strong>🎯 Resource:</strong> {finding.get('resource_name', finding.get('resource', 'N/A'))}</p>
                        <p><strong>📝 Description:</strong> {finding.get('description', 'No description available')}</p>
                        
                        <div style="background: #e3f2fd; border: 1px solid #bbdefb; border-radius: 8px; padding: 20px; margin-top: 15px;">
                            <h4 style="color: #1976d2; margin-top: 0; display: flex; align-items: center;">🤖 AI-Powered Recommendations</h4>
                            
                            <div style="margin: 15px 0;">
                                <h5 style="color: #424242; margin-bottom: 8px;">🔧 Remediation Steps:</h5>
                                <p>{enhanced_finding.get('recommendation', finding.get('remediation', 'Review and remediate as needed'))}</p>
                            </div>
                            
                            <div style="background: #fff8e1; border-left: 4px solid #ffc107; padding: 15px; margin: 10px 0; border-radius: 0 5px 5px 0;">
                                <strong>💼 Business Impact:</strong> {enhanced_finding.get('business_impact', 'Impact assessment not available')}
                            </div>
                            
                            <div style="background: #f3e5f5; border-left: 4px solid #9c27b0; padding: 15px; margin: 10px 0; border-radius: 0 5px 5px 0;">
                                <strong>⏱️ Estimated Effort:</strong> {enhanced_finding.get('effort_estimate', 'Effort estimation not available')}
                            </div>
                            
                            <div style="margin: 15px 0;">
                                <h5 style="color: #424242; margin-bottom: 8px;">☁️ Azure Commands:</h5>
                                <div style="background: #263238; color: #eeffff; padding: 15px; border-radius: 5px; font-family: 'Courier New', monospace; font-size: 0.9em; overflow-x: auto; margin: 10px 0;">{enhanced_finding.get('azure_commands', finding.get('azure_commands', 'No specific commands available'))}</div>
                            </div>
                        </div>
                    </div>
                </div>
                """
            findings_html += "</div>"
        
        # Create comprehensive HTML content with actual scan data
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Securra Security Compliance Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }}
        .section {{ margin: 20px 0; }}
        .score {{ font-size: 24px; color: #2e7d32; font-weight: bold; }}
        .recommendations {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
        .metrics {{ display: flex; justify-content: space-around; background: #e3f2fd; padding: 15px; border-radius: 5px; }}
        .metric {{ text-align: center; }}
        .metric-value {{ font-size: 20px; font-weight: bold; color: #1976d2; }}
        .finding {{ margin: 10px 0; padding: 10px; border-radius: 4px; }}
        pre {{ white-space: pre-wrap; word-wrap: break-word; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Securra Security Compliance Report</h1>
        <h2>{report['name']}</h2>
        <p>Report ID: {report['id']}</p>
        <p>Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="section">
        <h3>Report Details</h3>
        <p><strong>Type:</strong> {report['type']}</p>
        <p><strong>Environment:</strong> {report['environment']}</p>
        <p><strong>Status:</strong> {report['status']}</p>
        <p><strong>Created:</strong> {report['created_at']}</p>
        {f'<p><strong>Scan ID:</strong> {report["scan_id"]}</p>' if report.get('scan_id') else ''}
    </div>
    
    <div class="section">
        <h3>Compliance Score</h3>
        <div class="score">{report.get('compliance_score', 'N/A')}%</div>
    </div>
    
    {f'''
    <div class="section">
        <h3>Scan Metrics</h3>
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{report.get('scan_details', {}).get('total_checks', 0)}</div>
                <div>Total Checks</div>
            </div>
            <div class="metric">
                <div class="metric-value">{report.get('scan_details', {}).get('passed_checks', 0)}</div>
                <div>Passed</div>
            </div>
            <div class="metric">
                <div class="metric-value">{report.get('scan_details', {}).get('failed_checks', 0)}</div>
                <div>Failed</div>
            </div>
            <div class="metric">
                <div class="metric-value">{report.get('findings_summary', {}).get('critical', 0)}</div>
                <div>Critical</div>
            </div>
            <div class="metric">
                <div class="metric-value">{report.get('findings_summary', {}).get('high', 0)}</div>
                <div>High</div>
            </div>
        </div>
    </div>
    ''' if report.get('scan_details') else ''}
    
    <div class="section">
        <h3>📊 Executive Summary</h3>
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 12px; margin: 15px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h4 style="margin: 0; color: white;">🛡️ Security Compliance Overview</h4>
                <span style="background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; font-weight: bold;">Assessment Date: {datetime.now().strftime('%B %d, %Y')}</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px;">
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: {'#4caf50' if report.get('compliance_score', 0) >= 80 else '#ff9800' if report.get('compliance_score', 0) >= 60 else '#f44336'};">{report.get('compliance_score', 'N/A')}%</div>
                    <div style="font-size: 0.9em; opacity: 0.9;">Compliance Score</div>
                </div>
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold;">{report.get('scan_details', {}).get('total_checks', 0)}</div>
                    <div style="font-size: 0.9em; opacity: 0.9;">Total Checks</div>
                </div>
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #ff5252;">{report.get('scan_details', {}).get('failed_checks', 0)}</div>
                    <div style="font-size: 0.9em; opacity: 0.9;">Failed Checks</div>
                </div>
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #4caf50;">{report.get('scan_details', {}).get('passed_checks', 0)}</div>
                    <div style="font-size: 0.9em; opacity: 0.9;">Passed Checks</div>
                </div>
            </div>
        </div>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #2196f3;">
            <h4 style="color: #1976d2; margin-top: 0;">🎯 Key Insights</h4>
            <p>{report['executive_summary']}</p>
            <div style="margin-top: 15px; padding: 15px; background: #e3f2fd; border-radius: 6px;">
                <strong>🚨 Priority Actions:</strong> Focus on addressing {report.get('scan_details', {}).get('failed_checks', 0)} failed security checks to improve your compliance posture. Critical and high-severity findings should be prioritized for immediate remediation.
            </div>
        </div>
    </div>
    
    <div class="section">
        <h3>🤖 AI-Powered Recommendations</h3>
        <div style="background: #e8f5e8; border: 1px solid #4caf50; border-radius: 12px; padding: 25px; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <div style="display: flex; align-items: center; margin-bottom: 20px;">
                <div style="background: #4caf50; color: white; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; margin-right: 15px; font-size: 1.2em;">🎯</div>
                <h4 style="margin: 0; color: #2e7d32;">Priority Remediation Actions</h4>
            </div>
            <div class="recommendations">
                {''.join([f'<div style="background: white; border-left: 4px solid #4caf50; padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1);"><strong>•</strong> {rec}</div>' for rec in report.get('recommendations', [])])}
            </div>
            <div style="background: #fff3e0; border: 1px solid #ff9800; border-radius: 8px; padding: 15px; margin-top: 20px;">
                <strong style="color: #ef6c00;">💡 Implementation Tip:</strong> <span style="color: #424242;">Prioritize critical and high-severity findings first. Each recommendation includes specific Azure commands and estimated effort for efficient remediation.</span>
            </div>
        </div>
    </div>
    
    {findings_html}
</body>
</html>
        """
        
        # Generate PDF using reportlab with detailed findings
        # Enable PDF generation for proper compliance reports
        if True:  # Enable PDF generation
            try:
                # Create PDF buffer
                pdf_buffer = io.BytesIO()
                
                # Create PDF document
                doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, topMargin=0.5*inch)
                
                # Get styles
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=18,
                    spaceAfter=30,
                    alignment=TA_CENTER,
                    textColor=colors.darkblue
                )
                heading_style = ParagraphStyle(
                    'CustomHeading',
                    parent=styles['Heading2'],
                    fontSize=14,
                    spaceAfter=12,
                    textColor=colors.darkblue
                )
                
                # Build PDF content
                story = []
            
                # Title
                story.append(Paragraph("Securra Security Compliance Report", title_style))
                story.append(Paragraph(f"{report['name']}", styles['Heading2']))
                story.append(Spacer(1, 12))
                
                # Report details
                story.append(Paragraph("Report Details", heading_style))
                details_data = [
                    ['Report ID:', report['id']],
                    ['Type:', report['type']],
                    ['Environment:', report['environment']],
                    ['Status:', report['status']],
                    ['Created:', report['created_at']],
                    ['Generated:', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')]
                ]
                if report.get('scan_id'):
                    details_data.append(['Scan ID:', report['scan_id']])
                
                details_table = Table(details_data, colWidths=[2*inch, 4*inch])
                details_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(details_table)
                story.append(Spacer(1, 20))
            
                # Compliance Score
                story.append(Paragraph("Compliance Score", heading_style))
                score_text = f"<font size=16 color=green><b>{report.get('compliance_score', 'N/A')}%</b></font>"
                story.append(Paragraph(score_text, styles['Normal']))
                story.append(Spacer(1, 20))
                
                # Executive Summary
                story.append(Paragraph("Executive Summary", heading_style))
                story.append(Paragraph(report['executive_summary'], styles['Normal']))
                story.append(Spacer(1, 20))
                
                # Recommendations
                story.append(Paragraph("Recommendations", heading_style))
                for i, rec in enumerate(report.get('recommendations', []), 1):
                    story.append(Paragraph(f"{i}. {rec}", styles['Normal']))
                story.append(Spacer(1, 20))
                
                # Scan Metrics (if available)
                if report.get('scan_details'):
                    story.append(Paragraph("Scan Metrics", heading_style))
                    metrics_data = [
                        ['Metric', 'Value'],
                        ['Total Checks', str(report.get('scan_details', {}).get('total_checks', 0))],
                        ['Passed Checks', str(report.get('scan_details', {}).get('passed_checks', 0))],
                        ['Failed Checks', str(report.get('scan_details', {}).get('failed_checks', 0))],
                        ['Critical Issues', str(report.get('findings_summary', {}).get('critical', 0))],
                        ['High Issues', str(report.get('findings_summary', {}).get('high', 0))]
                    ]
                    
                    metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
                    metrics_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(metrics_table)
                    story.append(Spacer(1, 20))
            
                # Security Findings (if available)
                if scan_data and scan_data.get("findings"):
                    story.append(Paragraph("Security Findings", heading_style))
                    for finding in scan_data["findings"][:10]:  # Limit to first 10 findings
                        severity = finding.get('severity', 'low')
                        severity_color = {
                            "critical": colors.red,
                            "high": colors.orange, 
                            "medium": colors.yellow,
                            "low": colors.green
                        }.get(severity, colors.grey)
                        
                        finding_title = f"<font color='{severity_color.hexval()}'><b>{finding.get('title', 'Unknown Finding')}</b></font>"
                        story.append(Paragraph(finding_title, styles['Normal']))
                        story.append(Paragraph(f"<b>Severity:</b> {severity.upper()}", styles['Normal']))
                        story.append(Paragraph(f"<b>Resource:</b> {finding.get('resource', 'N/A')}", styles['Normal']))
                        story.append(Paragraph(f"<b>Description:</b> {finding.get('description', 'No description available')}", styles['Normal']))
                        story.append(Spacer(1, 10))
                
                # Build PDF
                doc.build(story)
                
                # Get PDF bytes
                pdf_bytes = pdf_buffer.getvalue()
                pdf_buffer.close()
                
                # Return PDF as streaming response
                return StreamingResponse(
                    io.BytesIO(pdf_bytes),
                    media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=securra-report-{report_id}.pdf"}
                )
                
            except Exception as pdf_error:
                # Fallback to HTML if PDF generation fails
                print(f"PDF generation failed: {pdf_error}")
                return StreamingResponse(
                    io.BytesIO(html_content.encode('utf-8')),
                    media_type="text/html",
                    headers={"Content-Disposition": f"attachment; filename=securra-report-{report_id}.html"}
                )
        else:
            # Return HTML with detailed findings and AI recommendations
            return StreamingResponse(
                io.BytesIO(html_content.encode('utf-8')),
                media_type="text/html",
                headers={"Content-Disposition": f"attachment; filename=securra-report-{report_id}.html"}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download report: {str(e)}")


@app.delete("/api/v1/reports/{report_id}")
async def delete_report(report_id: str, authorization: str = Header(None)):
    """Delete a compliance report (admin only)"""
    try:
        # Check authorization header
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authorization token required")
        
        token = authorization.split(" ")[1]
        
        # Decode and verify token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_email = payload.get("sub")
            
            if not user_email or user_email not in TEST_USERS:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            user_data = TEST_USERS[user_email]["user_data"]
            
            # Check if user is admin
            if user_data.get("role") != "admin":
                raise HTTPException(status_code=403, detail="Admin access required")
                
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Find and remove the report
        global COMPLIANCE_REPORTS
        report_found = False
        for i, report in enumerate(COMPLIANCE_REPORTS):
            if report["id"] == report_id:
                COMPLIANCE_REPORTS.pop(i)
                report_found = True
                break
        
        if not report_found:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {"message": "Report deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete report: {str(e)}")

@app.get("/api/v1/reports/{report_id}")
async def get_report_details(report_id: str):
    """Get detailed report information from in-memory store (or 404)."""
    report = next((r for r in COMPLIANCE_REPORTS if r["id"] == report_id), None)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

# Enhanced AI Assistant for Cloud Security
@app.post("/api/v1/ai/chat")
async def ai_security_assistant(query_data: dict):
    """Enhanced AI assistant focused on recommendations, details, and report-related questions."""
    user_query = (query_data or {}).get("query", "").strip()
    context_type = (query_data or {}).get("context_type", "general")  # general, recommendation, report, finding
    scan_id = (query_data or {}).get("scan_id", None)
    finding_id = (query_data or {}).get("finding_id", None)
    
    if not user_query:
        raise HTTPException(status_code=400, detail="query is required")

    # Get contextual data based on request
    context_data = await _get_ai_context(context_type, scan_id, finding_id)
    
    # If OPENAI key is available, call OpenAI with enhanced context
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key != "your-openai-api-key":
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            
            # Enhanced system prompt based on context type
            system_prompt = _get_enhanced_system_prompt(context_type, context_data)
            
            # Prepare messages with context
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ]
            
            # Add context data if available
            if context_data:
                context_message = f"Context: {json.dumps(context_data, indent=2)}"
                messages.insert(1, {"role": "system", "content": context_message})
            
            completion = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=messages,
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.3")),
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "1200")),
            )
            
            answer = completion.choices[0].message.content.strip()
            
            return {
                "query": user_query,
                "response": answer,
                "context_type": context_type,
                "context_data": context_data,
                "timestamp": datetime.now().isoformat(),
                "provider": "openai",
                "tokens_used": completion.usage.total_tokens if completion.usage else 0
            }
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fall back to enhanced curated responses
            pass

    # Enhanced fallback responses based on context
    response = _get_enhanced_fallback_response(user_query, context_type, context_data)
    
    return {
        "query": user_query,
        "response": response,
        "context_type": context_type,
        "context_data": context_data,
        "timestamp": datetime.now().isoformat(),
        "provider": "builtin"
    }

async def _get_ai_context(context_type: str, scan_id: str = None, finding_id: str = None) -> dict:
    """Get contextual data for AI responses"""
    context = {}
    
    try:
        if context_type == "recommendation" and scan_id:
            # Get scan data and findings for recommendation context
            scan_data = next((s for s in SECURITY_SCANS if s.get("scan_id") == scan_id), None)
            if scan_data:
                context["scan_summary"] = {
                    "framework": scan_data.get("framework"),
                    "status": scan_data.get("status"),
                    "findings_count": len(scan_data.get("findings", [])),
                    "critical_count": len([f for f in scan_data.get("findings", []) if f.get("severity") == "critical"]),
                    "high_count": len([f for f in scan_data.get("findings", []) if f.get("severity") == "high"])
                }
                
                if finding_id:
                    finding = next((f for f in scan_data.get("findings", []) if f.get("id") == finding_id), None)
                    if finding:
                        context["specific_finding"] = finding
        
        elif context_type == "report":
            # Get report data and compliance information
            context["compliance_frameworks"] = ["CIS", "SOC2", "NIST", "ISO27001"]
            context["available_reports"] = len(COMPLIANCE_REPORTS)
            context["recent_scans"] = len([s for s in SECURITY_SCANS if s.get("status") == "completed"])
        
        elif context_type == "finding" and finding_id and scan_id:
            # Get specific finding details
            scan_data = next((s for s in SECURITY_SCANS if s.get("scan_id") == scan_id), None)
            if scan_data:
                finding = next((f for f in scan_data.get("findings", []) if f.get("id") == finding_id), None)
                if finding:
                    context["finding_details"] = finding
                    # Get AI recommendations for this finding
                    ai_recommendations = await generate_ai_recommendations(finding)
                    context["ai_recommendations"] = ai_recommendations
        
        # Always include general system context
        context["system_info"] = {
            "total_scans": len(SECURITY_SCANS),
            "total_reports": len(COMPLIANCE_REPORTS),
            "supported_frameworks": ["CIS", "SOC2", "NIST", "ISO27001"]
        }
        
    except Exception as e:
        print(f"Error getting AI context: {e}")
    
    return context

def _get_enhanced_system_prompt(context_type: str, context_data: dict) -> str:
    """Get enhanced system prompt based on context type"""
    base_prompt = "You are Securra, an expert cloud security AI assistant specializing in Azure security assessments, compliance frameworks, and remediation guidance."
    
    if context_type == "recommendation":
        return f"""{base_prompt}
        
You are specifically focused on providing actionable security recommendations. When responding:
        1. Prioritize findings by risk level (Critical > High > Medium > Low)
        2. Provide specific Azure CLI commands and PowerShell scripts
        3. Include business impact and effort estimates
        4. Reference relevant compliance frameworks (CIS, SOC2, NIST, ISO27001)
        5. Suggest implementation timelines and testing approaches
        6. Always include monitoring and validation steps
        
        Keep responses practical, actionable, and focused on immediate next steps."""
    
    elif context_type == "report":
        return f"""{base_prompt}
        
You specialize in security report analysis and compliance reporting. When responding:
        1. Explain report findings in business terms
        2. Provide executive summaries and technical details
        3. Map findings to compliance frameworks
        4. Suggest report customization and filtering options
        5. Recommend follow-up actions based on report data
        6. Help interpret compliance scores and trends
        
        Focus on making complex security data understandable and actionable."""
    
    elif context_type == "finding":
        return f"""{base_prompt}
        
You specialize in detailed security finding analysis. When responding:
        1. Provide deep technical analysis of specific security issues
        2. Explain the root cause and potential attack vectors
        3. Offer multiple remediation approaches with pros/cons
        4. Include step-by-step implementation guides
        5. Suggest testing and validation procedures
        6. Recommend monitoring to prevent recurrence
        
        Be thorough and technical while remaining practical."""
    
    else:  # general
        return f"""{base_prompt}
        
You provide comprehensive cloud security guidance. When responding:
        1. Offer actionable recommendations for Azure environments
        2. Reference CIS, NIST, SOC2, and ISO27001 controls when applicable
        3. Include specific Azure CLI or PowerShell commands
        4. Provide business context and risk assessment
        5. Suggest implementation priorities and timelines
        6. Keep responses concise but comprehensive (8-12 sentences)
        
        Always focus on practical, implementable security improvements."""

def _get_enhanced_fallback_response(user_query: str, context_type: str, context_data: dict) -> str:
    """Get enhanced fallback responses based on context"""
    query_lower = user_query.lower()
    
    # Context-specific responses
    if context_type == "recommendation":
        if "priority" in query_lower or "critical" in query_lower:
            return "For critical findings, prioritize: 1) Identity & Access (MFA, PIM, Conditional Access), 2) Network Security (NSG rules, private endpoints), 3) Data Protection (encryption, Key Vault). Address critical findings within 24-48 hours."
        elif "remediation" in query_lower:
            return "Remediation approach: 1) Assess impact and dependencies, 2) Test in non-production, 3) Implement during maintenance window, 4) Validate with follow-up scan, 5) Document changes for compliance."
        else:
            return "I can help prioritize security recommendations, provide remediation steps, estimate implementation effort, and suggest Azure CLI/PowerShell commands. What specific finding or area would you like guidance on?"
    
    elif context_type == "report":
        if "compliance" in query_lower:
            return "Compliance reporting covers CIS Controls, SOC 2 Type II, NIST Cybersecurity Framework, and ISO 27001. Reports include executive summaries, detailed findings, remediation timelines, and compliance gap analysis."
        elif "pdf" in query_lower or "download" in query_lower:
            return "PDF reports include: Executive Summary, Compliance Score, Detailed Findings with AI recommendations, Remediation Roadmap, and Appendices. Reports can be customized by framework, severity, or resource type."
        else:
            return "I can help explain report findings, compliance scores, executive summaries, and remediation priorities. I can also guide you through report customization and filtering options."
    
    elif context_type == "finding":
        if "remediation" in query_lower:
            return "For specific findings, I provide: Root cause analysis, Step-by-step remediation, Azure CLI/PowerShell commands, Testing procedures, Business impact assessment, and Compliance mapping."
        else:
            return "I can analyze specific security findings, explain technical details, provide remediation guidance, and help you understand the business impact and compliance implications."
    
    # General keyword-based responses
    keyword_responses = {
        "cis": "CIS Controls guidance: Prioritize Basic Controls (1-6) including inventory, vulnerability management, secure configuration, and access control. Focus on identity hardening (MFA, PIM), network security (NSG rules), and logging.",
        "soc": "SOC 2 Type II compliance: Emphasize access controls, change management, system monitoring, and incident response. Ensure comprehensive logging to Azure Monitor and alerts for privileged actions.",
        "nist": "NIST Cybersecurity Framework: Identify (asset inventory), Protect (IAM, encryption), Detect (Azure Monitor, Sentinel), Respond (incident playbooks), Recover (backup testing, business continuity).",
        "vulnerability": "Vulnerability remediation priorities: 1) Encrypt storage accounts and enable HTTPS, 2) Restrict RDP/SSH with Just-In-Time access, 3) Patch VMs using Update Management, 4) Verify with follow-up scans.",
        "remediation": "Quick security wins: Enable MFA and Conditional Access, restrict public endpoints, enforce Azure Policy and Defender for Cloud, implement proper tagging, and minimize policy exemptions.",
        "azure cli": "Azure CLI security commands: az security, az keyvault, az network nsg, az storage account, az ad user. I can provide specific commands for your security findings and remediation needs.",
        "powershell": "PowerShell security modules: Az.Security, Az.KeyVault, Az.Network, Az.Storage, AzureAD. I can provide specific scripts for security configuration and remediation tasks."
    }
    
    # Find matching keyword
    for keyword, response in keyword_responses.items():
        if keyword in query_lower:
            return response
    
    # Default response based on context
    if context_data and context_data.get("system_info"):
        system_info = context_data["system_info"]
        return f"I'm your cloud security assistant. I can help with recommendations, report analysis, and finding details. Current system: {system_info['total_scans']} scans, {system_info['total_reports']} reports. Supported frameworks: {', '.join(system_info['supported_frameworks'])}. What would you like to know?"
    
    return "I'm Securra, your cloud security assistant. I specialize in Azure security recommendations, compliance reporting, and finding remediation. Ask me about CIS/NIST/SOC controls, vulnerability mitigation, or specific security findings."

# AI-powered recommendation endpoints
@app.post("/api/v1/ai/recommendations")
async def get_ai_recommendations(request_data: dict):
    """Get AI-powered recommendations for specific findings or scans"""
    scan_id = request_data.get("scan_id")
    finding_id = request_data.get("finding_id")
    recommendation_type = request_data.get("type", "general")  # general, priority, detailed
    
    if not scan_id:
        raise HTTPException(status_code=400, detail="scan_id is required")
    
    # Get scan data
    scan_data = next((s for s in SECURITY_SCANS if s.get("scan_id") == scan_id), None)
    if not scan_data:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    recommendations = []
    
    if finding_id:
        # Get recommendations for specific finding
        finding = next((f for f in scan_data.get("findings", []) if f.get("id") == finding_id), None)
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        
        ai_rec = await generate_ai_recommendations(finding)
        recommendations.append({
            "finding_id": finding_id,
            "finding_title": finding.get("title"),
            "severity": finding.get("severity"),
            "recommendations": ai_rec
        })
    else:
        # Get recommendations for all findings in scan
        findings = scan_data.get("findings", [])
        
        # Sort by severity for priority recommendations

@app.post("/api/v1/generate-report-content")
async def generate_report_content(request_data: dict):
    """Generate detailed, finding-specific report content using LLM"""
    agent_id = request_data.get("agent_id")
    finding_type = request_data.get("finding_type", "security")
    resource_type = request_data.get("resource_type", "unknown")
    severity = request_data.get("severity", "medium")
    
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")
    
    # Get agent data
    agent = next((a for a in AGENTIC_AGENTS if a.get("agent_id") == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        # Prepare context for LLM
        context = {
            "agent_id": agent_id,
            "finding_type": finding_type,
            "resource_type": resource_type,
            "severity": severity,
            "finding_details": agent.get("finding_details", {}),
            "remediation_result": agent.get("remediation_result", {}),
            "execution_logs": agent.get("execution_logs", [])
        }
        
        # Generate LLM content using OpenAI
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            openai.api_key = openai_api_key
            
            prompt = f"""
            Generate a detailed, professional security report section for the following context:
            
            Resource Type: {resource_type}
            Finding Type: {finding_type}
            Severity: {severity}
            Finding Details: {agent.get('finding_details', {})}
            
            Please provide:
            1. Executive Summary (2-3 sentences)
            2. Technical Analysis (detailed explanation)
            3. Risk Assessment (business impact and technical risks)
            4. Detailed Remediation Steps (step-by-step instructions)
            5. Compliance Impact (regulatory and framework implications)
            6. Prevention Measures (future prevention strategies)
            
            Format the response as a JSON object with these sections as keys.
            Make it professional, actionable, and specific to the {resource_type} resource type.
            """
            
            try:
                response = await openai.ChatCompletion.acreate(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a cybersecurity expert generating detailed security assessment reports. Provide comprehensive, actionable insights."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000,
                    temperature=0.7
                )
                
                ai_content = response.choices[0].message.content
                
                # Try to parse as JSON, fallback to structured text
                try:
                    import json
                    parsed_content = json.loads(ai_content)
                except:
                    # Fallback to structured content
                    parsed_content = {
                        "executive_summary": f"Security assessment identified {severity} severity {finding_type} finding in {resource_type} resource.",
                        "technical_analysis": ai_content[:500] + "...",
                        "risk_assessment": f"This {severity} severity finding poses significant risks to the {resource_type} resource.",
                        "remediation_steps": "Detailed remediation steps provided in the full analysis.",
                        "compliance_impact": "This finding may impact compliance with security frameworks.",
                        "prevention_measures": "Implement regular security assessments and monitoring."
                    }
                
                return {
                    "success": True,
                    "content": parsed_content,
                    "generated_at": datetime.now().isoformat(),
                    "model_used": "gpt-4"
                }
                
            except Exception as openai_error:
                print(f"OpenAI API error: {openai_error}")
                # Fallback to rule-based content
                pass
        
        # Fallback content generation
        fallback_content = {
            "executive_summary": f"Security assessment identified a {severity} severity {finding_type} finding affecting {resource_type} resources that requires immediate attention.",
            "technical_analysis": f"The {resource_type} resource has been identified with {finding_type} vulnerabilities. This finding indicates potential security gaps that could be exploited by malicious actors. The {severity} severity level suggests this issue should be prioritized in remediation efforts.",
            "risk_assessment": f"Business Impact: {severity.title()} risk to business operations and data security. Technical Risk: Potential for unauthorized access or data exposure through {resource_type} vulnerabilities.",
            "remediation_steps": f"1. Review {resource_type} configuration\n2. Apply security best practices\n3. Implement monitoring and alerting\n4. Validate remediation effectiveness\n5. Document changes and update procedures",
            "compliance_impact": f"This finding may affect compliance with security frameworks including CIS, NIST, and industry-specific regulations. Immediate remediation is recommended to maintain compliance posture.",
            "prevention_measures": f"Implement regular security assessments, automated compliance monitoring, and security configuration management for {resource_type} resources."
        }
        
        return {
            "success": True,
            "content": fallback_content,
            "generated_at": datetime.now().isoformat(),
            "model_used": "rule-based-fallback"
        }
        
    except Exception as e:
        print(f"Error generating report content: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report content: {str(e)}")
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_findings = sorted(findings, key=lambda x: severity_order.get(x.get("severity", "low"), 3))
        
        # Limit based on recommendation type
        if recommendation_type == "priority":
            sorted_findings = sorted_findings[:5]  # Top 5 priority findings
        elif recommendation_type == "detailed":
            sorted_findings = sorted_findings[:10]  # Top 10 for detailed analysis
        
        for finding in sorted_findings:
            ai_rec = await generate_ai_recommendations(finding)
            recommendations.append({
                "finding_id": finding.get("id"),
                "finding_title": finding.get("title"),
                "severity": finding.get("severity"),
                "recommendations": ai_rec
            })
    
    return {
        "scan_id": scan_id,
        "recommendation_type": recommendation_type,
        "total_recommendations": len(recommendations),
        "recommendations": recommendations,
        "generated_at": datetime.now().isoformat()
    }

@app.post("/api/v1/ai/analyze-finding")
async def analyze_finding_with_ai(request_data: dict):
    """Get detailed AI analysis for a specific finding"""
    scan_id = request_data.get("scan_id")
    finding_id = request_data.get("finding_id")
    analysis_type = request_data.get("analysis_type", "comprehensive")  # comprehensive, quick, technical
    
    if not scan_id or not finding_id:
        raise HTTPException(status_code=400, detail="scan_id and finding_id are required")
    
    # Get scan and finding data
    scan_data = next((s for s in SECURITY_SCANS if s.get("scan_id") == scan_id), None)
    if not scan_data:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    finding = next((f for f in scan_data.get("findings", []) if f.get("id") == finding_id), None)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    # Generate AI analysis using the chat endpoint with finding context
    analysis_query = f"Provide a {analysis_type} analysis of this security finding: {finding.get('title')}. Include root cause, attack vectors, and detailed remediation steps."
    
    ai_response = await ai_security_assistant({
        "query": analysis_query,
        "context_type": "finding",
        "scan_id": scan_id,
        "finding_id": finding_id
    })
    
    # Get AI recommendations
    ai_recommendations = await generate_ai_recommendations(finding)
    
    return {
        "scan_id": scan_id,
        "finding_id": finding_id,
        "finding_details": finding,
        "analysis_type": analysis_type,
        "ai_analysis": ai_response.get("response"),
        "ai_recommendations": ai_recommendations,
        "provider": ai_response.get("provider"),
        "tokens_used": ai_response.get("tokens_used", 0),
        "generated_at": datetime.now().isoformat()
    }

@app.post("/api/v1/ai/report-summary")
async def generate_report_summary(request_data: dict):
    """Generate AI-powered executive summary for compliance reports"""
    report_id = request_data.get("report_id")
    scan_id = request_data.get("scan_id")
    summary_type = request_data.get("type", "executive")  # executive, technical, compliance
    
    if not report_id and not scan_id:
        raise HTTPException(status_code=400, detail="Either report_id or scan_id is required")
    
    # Get report or scan data
    if report_id:
        report = next((r for r in COMPLIANCE_REPORTS if r.get("id") == report_id), None)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        scan_id = report.get("scan_id")
    
    if scan_id:
        scan_data = next((s for s in SECURITY_SCANS if s.get("scan_id") == scan_id), None)
        if not scan_data:
            raise HTTPException(status_code=404, detail="Scan not found")
    
    # Prepare summary query based on type
    if summary_type == "executive":
        summary_query = f"Generate an executive summary for this security assessment. Focus on business impact, key risks, and strategic recommendations. Include compliance score and priority actions."
    elif summary_type == "technical":
        summary_query = f"Generate a technical summary for this security assessment. Focus on technical findings, system vulnerabilities, and detailed remediation steps."
    elif summary_type == "compliance":
        summary_query = f"Generate a compliance-focused summary for this security assessment. Focus on regulatory requirements, compliance gaps, and audit readiness."
    else:
        summary_query = f"Generate a comprehensive summary for this security assessment."
    
    # Generate AI summary using the chat endpoint with report context
    ai_response = await ai_security_assistant({
        "query": summary_query,
        "context_type": "report",
        "scan_id": scan_id
    })
    
    # Calculate summary statistics
    findings = scan_data.get("findings", []) if scan_data else []
    summary_stats = {
        "total_findings": len(findings),
        "critical_count": len([f for f in findings if f.get("severity") == "critical"]),
        "high_count": len([f for f in findings if f.get("severity") == "high"]),
        "medium_count": len([f for f in findings if f.get("severity") == "medium"]),
        "low_count": len([f for f in findings if f.get("severity") == "low"]),
        "framework": scan_data.get("framework") if scan_data else "Unknown",
        "scan_status": scan_data.get("status") if scan_data else "Unknown"
    }
    
    return {
        "report_id": report_id,
        "scan_id": scan_id,
        "summary_type": summary_type,
        "ai_summary": ai_response.get("response"),
        "summary_statistics": summary_stats,
        "provider": ai_response.get("provider"),
        "tokens_used": ai_response.get("tokens_used", 0),
        "generated_at": datetime.now().isoformat()
    }

# User Management
@app.get("/api/v1/users")
async def get_users():
    """Get all users in the system"""
    users = []
    for email, data in TEST_USERS.items():
        user = data["user_data"].copy()
        users.append(user)
    
    return {"users": users, "total": len(users)}

@app.post("/api/v1/users")
async def create_user(user_data: dict):
    """Create a new user"""
    email = user_data.get("email")
    if email in TEST_USERS:
        raise HTTPException(status_code=400, detail="User already exists")
    
    new_user = {
        "password": user_data.get("password", "defaultpass123"),
        "user_data": {
            "id": f"user-{uuid.uuid4().hex[:8]}",
            "email": email,
            "firstName": user_data.get("firstName"),
            "lastName": user_data.get("lastName"),
            "role": user_data.get("role", "user"),
            "isActive": True,
            "permissions": user_data.get("permissions", ["read"])
        }
    }
    
    TEST_USERS[email] = new_user
    return {"message": "User created successfully", "user": new_user["user_data"]}

@app.get("/api/v1/groups")
async def get_user_groups():
    """Get user groups/roles"""
    groups = [
        {
            "id": "admin-group",
            "name": "Security Administrators",
            "description": "Full access to all security features",
            "permissions": ["read", "write", "delete", "manage_users", "generate_reports"],
            "members_count": 1
        },
        {
            "id": "analyst-group", 
            "name": "Security Analysts",
            "description": "Can perform scans and generate reports",
            "permissions": ["read", "write", "generate_reports"],
            "members_count": 1
        },
        {
            "id": "viewer-group",
            "name": "Security Viewers", 
            "description": "Read-only access to security data",
            "permissions": ["read"],
            "members_count": 1
        }
    ]
    
    return {"groups": groups, "total": len(groups)}

# Dashboard Analytics
@app.get("/api/v1/dashboard/analytics")
async def get_dashboard_analytics():
    """Get comprehensive dashboard analytics"""
    return {
        "security_metrics": {
            "overall_score": 87,
            "total_resources": 37,
            "secure_resources": 32,
            "at_risk_resources": 5,
            "trend": "+3% this month"
        },
        "compliance_overview": SUBSCRIPTION_DATA["compliance_status"],
        "recent_activities": [
            {
                "action": "Security scan completed",
                "resource": "rg-production",
                "timestamp": "2025-08-12T10:45:00Z",
                "severity": "info"
            },
            {
                "action": "Critical vulnerability detected",
                "resource": "storage-account-001", 
                "timestamp": "2025-08-12T10:30:00Z",
                "severity": "critical"
            }
        ],
        "top_recommendations": [
            "Enable encryption for storage accounts",
            "Implement network access controls",
            "Configure Azure Security Center"
        ]
    }

# User Management Endpoints
@app.get("/api/v1/users")
async def get_users():
    """Get all users"""
    users = []
    for email, user_info in TEST_USERS.items():
        users.append({
            "id": user_info["user_data"]["id"],
            "email": email,
            "firstName": user_info["user_data"]["firstName"],
            "lastName": user_info["user_data"]["lastName"],
            "role": user_info["user_data"]["role"],
            "isActive": user_info["user_data"]["isActive"],
            "permissions": user_info["user_data"]["permissions"],
            "created_at": "2025-01-01T00:00:00Z",
            "last_login": None
        })
    return {"users": users, "total": len(users)}

@app.post("/api/v1/users")
async def create_user(user_data: dict):
    """Create a new user"""
    try:
        email = user_data.get("email")
        password = user_data.get("password")
        firstName = user_data.get("firstName")
        lastName = user_data.get("lastName")
        role = user_data.get("role", "user")
        
        if not all([email, password, firstName, lastName]):
            raise HTTPException(status_code=400, detail="All fields are required")
        
        if email in TEST_USERS:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Define permissions based on role
        role_permissions = {
            "admin": ["read", "write", "delete", "manage_users", "generate_reports"],
            "analyst": ["read", "write", "generate_reports"],
            "user": ["read"]
        }
        
        user_id = f"user-{uuid.uuid4().hex[:8]}"
        
        TEST_USERS[email] = {
            "password": password,
            "user_data": {
                "id": user_id,
                "email": email,
                "firstName": firstName,
                "lastName": lastName,
                "role": role,
                "isActive": True,
                "permissions": role_permissions.get(role, ["read"])
            }
        }
        
        return {
            "message": "User created successfully",
            "user": {
                "id": user_id,
                "email": email,
                "firstName": firstName,
                "lastName": lastName,
                "role": role,
                "isActive": True,
                "permissions": role_permissions.get(role, ["read"])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# AGENTIC SYSTEM API ENDPOINTS
# ============================================================================

@app.get("/api/v1/agents")
async def get_agents():
    """Get all agents with their current status"""
    return {
        "agents": AGENTS,
        "total": len(AGENTS),
        "statistics": {
            "total_agents": len(AGENTS),
            "running": len([a for a in AGENTS if a["status"] == "running"]),
            "completed": len([a for a in AGENTS if a["status"] == "completed"]),
            "failed": len([a for a in AGENTS if a["status"] == "failed"]),
            "success_rate": round((len([a for a in AGENTS if a["status"] == "completed"]) / len(AGENTS) * 100) if AGENTS else 0, 1)
        }
    }

@app.get("/api/v1/agents/models")
async def get_available_models():
    """Get available AI models for agent creation"""
    # Transform dictionary to array format expected by frontend
    models_array = [
        {
            "id": model_id,
            "name": model_data["name"],
            "description": model_data["description"],
            "max_tokens": model_data["max_tokens"],
            "recommended": model_data["recommended"]
        }
        for model_id, model_data in AVAILABLE_AI_MODELS.items()
    ]
    
    return {
        "models": models_array,
        "default_model": "gpt-4-turbo",
        "recommended_settings": {
            "temperature": 0.1,
            "max_tokens": 2048,
            "validation_mode": True
        }
    }

@app.get("/api/v1/agents/subscriptions")
async def get_agent_subscriptions():
    """Get available Azure subscriptions for agent creation"""
    return {
        "subscriptions": [
            {
                "id": AZURE_CONFIG["subscription_id"],
                "name": "Primary Subscription",
                "tenant_id": AZURE_CONFIG["tenant_id"],
                "status": "active"
            },
            {
                "id": "sub-dev-001",
                "name": "Development Subscription",
                "tenant_id": AZURE_CONFIG["tenant_id"],
                "status": "active"
            },
            {
                "id": "sub-prod-001",
                "name": "Production Subscription",
                "tenant_id": AZURE_CONFIG["tenant_id"],
                "status": "active"
            }
        ],
        "default_subscription": AZURE_CONFIG["subscription_id"]
    }

@app.post("/api/v1/agents")
async def create_agent(agent_data: dict):
    """Create a new AI agent for security remediation with framework and Azure integration"""
    try:
        agent_id = f"agent-{uuid.uuid4().hex[:8]}"
        current_time = datetime.utcnow().isoformat()
        
        # Validate required fields
        required_fields = ["finding_title", "finding_description", "severity", "resource_type", "model"]
        for field in required_fields:
            if not agent_data.get(field):
                raise HTTPException(status_code=400, detail=f"Field '{field}' is required")
        
        # Validate model exists
        if agent_data["model"] not in AVAILABLE_AI_MODELS:
            raise HTTPException(status_code=400, detail="Invalid AI model selected")
        
        # Validate subscription selection
        subscription_mode = agent_data.get('subscriptionMode', 'single')
        if subscription_mode == 'single':
            if not agent_data.get('subscription_id'):
                raise HTTPException(status_code=400, detail="subscription_id is required for single subscription mode")
        elif subscription_mode == 'multiple':
            selected_subscriptions = agent_data.get('selected_subscriptions', [])
            if not selected_subscriptions or len(selected_subscriptions) == 0:
                raise HTTPException(status_code=400, detail="At least one subscription must be selected for multiple subscription mode")
        else:
            raise HTTPException(status_code=400, detail="Invalid subscription mode. Must be 'single' or 'multiple'")
        
        # Set framework to autogen by default
        framework = "autogen"
        
        # Get Azure credentials from environment variables for security
        azure_tenant_id = AZURE_CONFIG["tenant_id"]
        azure_client_id = AZURE_CONFIG["client_id"]
        azure_client_secret = os.getenv("AZURE_CLIENT_SECRET", "")
        
        if not azure_client_secret:
            print("Warning: AZURE_CLIENT_SECRET not found in environment variables")
        
        # Get NSG rules details if this is an NSG-related finding
        nsg_rules_details = None
        if "network security" in agent_data["finding_title"].lower() or "nsg" in agent_data["finding_title"].lower():
            # Try to find the corresponding scan finding with NSG details
            for scan in SECURITY_SCANS:
                for finding in scan.get("findings", []):
                    if (finding.get("title", "").lower() == agent_data["finding_title"].lower() or 
                        "network security" in finding.get("title", "").lower()):
                        nsg_rules_details = finding.get("finding_details", {}).get("nsg_rules_details")
                        break
                if nsg_rules_details:
                    break
            
            # If no scan data found, create sample NSG data for demonstration
            if not nsg_rules_details:
                nsg_rules_details = {
                    "total_rules": 5,
                    "risky_rules": [
                        {
                            "rule_name": "AllowRDP",
                            "priority": 1000,
                            "direction": "Inbound",
                            "access": "Allow",
                            "protocol": "TCP",
                            "source_port_range": "*",
                            "destination_port_range": "3389",
                            "source_address_prefix": "*",
                            "destination_address_prefix": "*",
                            "risk_level": "Critical",
                            "description": "Allows RDP access from any source"
                        },
                        {
                            "rule_name": "AllowSSH",
                            "priority": 1010,
                            "direction": "Inbound",
                            "access": "Allow",
                            "protocol": "TCP",
                            "source_port_range": "*",
                            "destination_port_range": "22",
                            "source_address_prefix": "*",
                            "destination_address_prefix": "*",
                            "risk_level": "High",
                            "description": "Allows SSH access from any source"
                        },
                        {
                            "rule_name": "AllowHTTP",
                            "priority": 1020,
                            "direction": "Inbound",
                            "access": "Allow",
                            "protocol": "TCP",
                            "source_port_range": "*",
                            "destination_port_range": "80",
                            "source_address_prefix": "*",
                            "destination_address_prefix": "*",
                            "risk_level": "Medium",
                            "description": "Allows HTTP access from any source"
                        }
                    ],
                    "ports_summary": {
                        "critical_ports": ["3389"],
                        "high_risk_ports": ["22"],
                        "medium_risk_ports": ["80"],
                        "low_risk_ports": []
                    }
                }
        
        new_agent = {
            "id": agent_id,
            "name": agent_data.get("name", f"Agent for {agent_data['finding_title']}"),
            "description": agent_data.get("description", f"Automated remediation for {agent_data['finding_title']}"),
            "finding_details": {
                "title": agent_data["finding_title"],
                "description": agent_data["finding_description"],
                "severity": agent_data["severity"],
                "resource_type": agent_data["resource_type"],
                "resource_id": agent_data.get("resource_id", ""),
                "nsg_rules_details": nsg_rules_details
            },
            "model_config": {
                "model": agent_data["model"],
                "temperature": agent_data.get("temperature", 0.1),
                "max_tokens": agent_data.get("max_tokens", 2048),
                "validation_mode": agent_data.get("validation_mode", True),
                "automated_execution": agent_data.get("automated_execution", False)
            },
            "framework_config": {
                "framework": framework,
                "use_langgraph": False,
                "use_autogen": True,
                "subscription_mode": subscription_mode,
                "subscription_id": agent_data.get("subscription_id") if subscription_mode == 'single' else None,
                "selected_subscriptions": agent_data.get("selected_subscriptions", []) if subscription_mode == 'multiple' else [],
                "azure_tenant_id": azure_tenant_id,
                "azure_client_id": azure_client_id,
                "azure_client_secret_configured": bool(azure_client_secret)
            },
            "status": "created",
            "created_at": current_time,
            "updated_at": current_time,
            "started_at": None,
            "completed_at": None,
            "progress": 0,
            "execution_logs": [],
            "remediation_plan": None,
            "error_message": None,
            "enhanced_features": False
        }
        
        # Create enhanced agent with AutoGen framework
        try:
            # Determine primary subscription for agentic service
            primary_subscription = (
                agent_data.get("subscription_id") if subscription_mode == 'single' 
                else agent_data.get("selected_subscriptions", [])[0] if agent_data.get("selected_subscriptions") 
                else None
            )
            
            config_data = {
                "agent_id": agent_id,
                "name": new_agent["name"],
                "description": new_agent["description"],
                "model_name": agent_data["model"],
                "temperature": agent_data.get("temperature", 0.1),
                "max_tokens": agent_data.get("max_tokens", 2048),
                "validation_mode": agent_data.get("validation_mode", True),
                "automated_execution": agent_data.get("automated_execution", False),
                "use_langgraph": False,
                "use_autogen": True,
                "use_azure_sdk": True,
                "azure_subscription_id": primary_subscription,
                "azure_tenant_id": azure_tenant_id,
                "azure_client_id": azure_client_id,
                "azure_client_secret": azure_client_secret,
                "subscription_mode": subscription_mode,
                "selected_subscriptions": agent_data.get("selected_subscriptions", []) if subscription_mode == 'multiple' else []
            }
                
                # Create configuration in agentic service
            # Create configuration in agentic service
            await agentic_service.create_agent_configuration(config_data)
            new_agent["enhanced_features"] = True
            
        except Exception as e:
            print(f"Warning: Failed to create enhanced agent configuration: {e}")
            new_agent["enhanced_features"] = False
        
        AGENTS.append(new_agent)
        AGENT_EXECUTION_LOGS[agent_id] = []
        
        subscription_info = (
            f"single subscription ({agent_data.get('subscription_id')})" if subscription_mode == 'single'
            else f"multiple subscriptions ({len(agent_data.get('selected_subscriptions', []))} selected)"
        )
        
        return {
            "message": f"Agent created successfully with Microsoft AutoGen framework and Azure integration ({subscription_info})",
            "agent": new_agent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/agents/{agent_id}/start")
async def start_agent(agent_id: str):
    """Start agent execution"""
    try:
        agent = next((a for a in AGENTS if a["id"] == agent_id), None)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if agent["status"] == "running":
            raise HTTPException(status_code=400, detail="Agent is already running")
        
        # Update agent status
        agent["status"] = "running"
        agent["started_at"] = datetime.utcnow().isoformat()
        agent["progress"] = 10
        
        # Start background task for agent execution
        asyncio.create_task(_execute_agent(agent_id))
        
        return {
            "message": "Agent execution started",
            "agent_id": agent_id,
            "status": "running"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/agents/{agent_id}/stop")
async def stop_agent(agent_id: str):
    """Stop agent execution"""
    try:
        agent = next((a for a in AGENTS if a["id"] == agent_id), None)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if agent["status"] != "running":
            raise HTTPException(status_code=400, detail="Agent is not running")
        
        # Update agent status
        agent["status"] = "stopped"
        agent["completed_at"] = datetime.utcnow().isoformat()
        agent["updated_at"] = datetime.utcnow().isoformat()
        
        # Add stop log
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "info",
            "message": "Agent execution stopped by user"
        }
        agent["execution_logs"].append(log_entry)
        AGENT_EXECUTION_LOGS[agent_id].append(log_entry)
        
        return {
            "message": "Agent execution stopped",
            "agent_id": agent_id,
            "status": "stopped"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/agents/{agent_id}/rollback")
async def rollback_agent_remediation(agent_id: str):
    """Rollback remediation actions performed by an agent"""
    try:
        agent = next((a for a in AGENTS if a["id"] == agent_id), None)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Check if agent has remediation result with rollback info
        remediation_result = agent.get("remediation_result")
        if not remediation_result or not remediation_result.get("rollback_info"):
            raise HTTPException(status_code=400, detail="No rollback information available for this agent")
        
        # Perform rollback
        rollback_info = remediation_result["rollback_info"]
        rollback_result = await remediation_service.rollback_remediation(rollback_info)
        
        # Update agent with rollback result
        agent["rollback_result"] = rollback_result
        agent["updated_at"] = datetime.utcnow().isoformat()
        
        # Add rollback log entries
        for action in rollback_result.get("actions_rolled_back", []):
            rollback_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "info",
                "message": f"Rollback: {action}"
            }
            agent["execution_logs"].append(rollback_log)
            AGENT_EXECUTION_LOGS[agent_id].append(rollback_log)
        
        # Log any rollback errors
        for error in rollback_result.get("errors", []):
            error_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "error",
                "message": f"Rollback error: {error}"
            }
            agent["execution_logs"].append(error_log)
            AGENT_EXECUTION_LOGS[agent_id].append(error_log)
        
        return {
            "message": "Rollback completed",
            "rollback_result": rollback_result,
            "agent": agent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/agents/{agent_id}")
async def get_agent_details(agent_id: str):
    """Get detailed information about a specific agent"""
    agent = next((a for a in AGENTS if a["id"] == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "agent": agent,
        "execution_logs": AGENT_EXECUTION_LOGS.get(agent_id, [])
    }

@app.delete("/api/v1/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent"""
    try:
        agent_index = next((i for i, a in enumerate(AGENTS) if a["id"] == agent_id), None)
        if agent_index is None:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent = AGENTS[agent_index]
        if agent["status"] == "running":
            raise HTTPException(status_code=400, detail="Cannot delete running agent. Stop it first.")
        
        # Remove agent and its logs
        AGENTS.pop(agent_index)
        if agent_id in AGENT_EXECUTION_LOGS:
            del AGENT_EXECUTION_LOGS[agent_id]
        
        # Clean up from agentic service if exists
        if agent_id in agentic_service.configurations:
            del agentic_service.configurations[agent_id]
        if agent_id in agentic_service.active_workflows:
            del agentic_service.active_workflows[agent_id]
        
        return {
            "message": "Agent deleted successfully",
            "agent_id": agent_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Agentic Endpoints with LangGraph Integration

@app.post("/api/v1/agents/enhanced")
async def create_enhanced_agent(agent_data: dict):
    """Create a new enhanced agent with LangGraph and Azure SDK integration"""
    try:
        # Validate required fields
        if not agent_data.get("name"):
            raise HTTPException(status_code=400, detail="Agent name is required")
        
        if not agent_data.get("model"):
            raise HTTPException(status_code=400, detail="Model selection is required")
        
        # Validate model exists
        if agent_data["model"] not in AVAILABLE_AI_MODELS:
            raise HTTPException(status_code=400, detail=f"Invalid model: {agent_data['model']}")
        
        # Generate agent ID if not provided
        agent_id = agent_data.get("agent_id", f"enhanced-agent-{uuid.uuid4().hex[:8]}")
        
        # Create agent configuration for agentic service
        config_data = {
            "agent_id": agent_id,
            "name": agent_data["name"],
            "description": agent_data.get("description", ""),
            "model_name": agent_data["model"],
            "temperature": agent_data.get("temperature", 0.1),
            "max_tokens": agent_data.get("max_tokens", 4096),
            "validation_mode": agent_data.get("validation_mode", True),
            "automated_execution": agent_data.get("automated_execution", False),
            "rollback_enabled": agent_data.get("rollback_enabled", True),
            "use_azure_sdk": agent_data.get("use_azure_sdk", True),
            "use_langgraph": agent_data.get("use_langgraph", True),
            "azure_subscription_id": agent_data.get("azure_subscription_id"),
            "azure_resource_group": agent_data.get("azure_resource_group")
        }
        
        # Create agent configuration in agentic service
        config = await agentic_service.create_agent_configuration(config_data)
        
        return {
            "success": True,
            "agent": {
                "id": config.agent_id,
                "name": config.name,
                "description": config.description,
                "model": config.model_name,
                "status": "idle",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "configuration": config.__dict__,
                "integration_features": {
                    "azure_sdk_enabled": config.use_azure_sdk,
                    "langgraph_enabled": config.use_langgraph,
                    "rollback_capability": config.rollback_enabled,
                    "validation_mode": config.validation_mode
                }
            },
            "message": "Enhanced agent created successfully with LangGraph and Azure SDK integration"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create enhanced agent: {str(e)}")

@app.post("/api/v1/agents/{agent_id}/execute-workflow")
async def execute_agent_workflow(agent_id: str, task_data: dict):
    """Execute agent workflow with LangGraph integration"""
    try:
        # Validate agent exists in agentic service
        if agent_id not in agentic_service.configurations:
            raise HTTPException(status_code=404, detail=f"Enhanced agent {agent_id} not found")
        
        # Extract finding data
        finding = task_data.get("finding")
        if not finding:
            raise HTTPException(status_code=400, detail="Finding data is required")
        
        # Execute agent workflow
        result = await agentic_service.execute_agent_workflow(agent_id, finding)
        
        return {
            "success": result["success"],
            "agent_id": agent_id,
            "workflow_id": f"workflow-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "status": "completed" if result["success"] else "failed",
            "message": "Workflow executed successfully" if result["success"] else f"Workflow execution failed: {result.get('error', 'Unknown error')}",
            "execution_result": result,
            "rollback_available": result.get("rollback_available", False),
            "workflow_type": result.get("final_state", {}).get("metadata", {}).get("workflow_type", "unknown")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {str(e)}")

@app.post("/api/v1/agents/{agent_id}/rollback-enhanced")
async def rollback_enhanced_agent(agent_id: str):
    """Rollback agent execution using enhanced rollback capabilities"""
    try:
        # Validate agent exists
        if agent_id not in agentic_service.configurations:
            raise HTTPException(status_code=404, detail=f"Enhanced agent {agent_id} not found")
        
        # Execute rollback
        result = await agentic_service.rollback_agent_execution(agent_id)
        
        return {
            "success": result["success"],
            "agent_id": agent_id,
            "rollback_id": f"rollback-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "message": "Rollback completed successfully" if result["success"] else f"Rollback failed: {result.get('error', 'Unknown error')}",
            "actions_rolled_back": result.get("actions_rolled_back", []),
            "errors": result.get("errors", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rollback agent: {str(e)}")

@app.get("/api/v1/agents/{agent_id}/configuration")
async def get_agent_configuration(agent_id: str):
    """Get current agent configuration for PDF export"""
    try:
        # Get configuration from agentic service
        config_data = await agentic_service.get_current_state_configuration(agent_id)
        
        return {
            "success": True,
            "agent_id": agent_id,
            "configuration": config_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")

@app.post("/api/v1/agents/{agent_id}/export-pdf")
async def export_agent_configuration_pdf(agent_id: str):
    """Export agent configuration as PDF"""
    try:
        # Get current state configuration
        config_data = await agentic_service.get_current_state_configuration(agent_id)
        
        # Generate PDF
        pdf_path = await pdf_service.generate_configuration_pdf(config_data)
        
        # Read PDF file
        with open(pdf_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
        
        # Create response
        filename = f"agent_config_{agent_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ImportError as e:
        raise HTTPException(status_code=500, detail="PDF generation not available. Please install ReportLab.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export PDF: {str(e)}")

@app.get("/api/v1/agents/enhanced/status")
async def get_enhanced_agents_status():
    """Get status of all enhanced agents with integration details"""
    try:
        enhanced_agents = []
        
        for agent_id, config in agentic_service.configurations.items():
            workflow_info = agentic_service.active_workflows.get(agent_id)
            status = "running" if workflow_info else "idle"
            
            enhanced_agents.append({
                "id": agent_id,
                "name": config.name,
                "status": status,
                "model": config.model_name,
                "created_at": workflow_info.get("started_at").isoformat() if workflow_info and workflow_info.get("started_at") else None,
                "integration_status": {
                    "azure_sdk": config.use_azure_sdk,
                    "langgraph": config.use_langgraph,
                    "rollback_enabled": config.rollback_enabled,
                    "validation_mode": config.validation_mode
                },
                "workflow_info": {
                    "current_step": workflow_info.get("state", {}).get("current_step") if workflow_info else None,
                    "messages_count": len(workflow_info.get("state", {}).get("messages", [])) if workflow_info else 0,
                    "errors_count": len(workflow_info.get("state", {}).get("errors", [])) if workflow_info else 0
                }
            })
        
        # Get integration status
        azure_status = await agentic_service._get_azure_sdk_status()
        langgraph_status = agentic_service._get_langgraph_status()
        
        return {
            "enhanced_agents": enhanced_agents,
            "total_enhanced": len(enhanced_agents),
            "running_enhanced": len([a for a in enhanced_agents if a["status"] == "running"]),
            "integration_status": {
                "azure_sdk": azure_status,
                "langgraph": langgraph_status
            },
            "capabilities": {
                "workflow_orchestration": langgraph_status.get("available", False),
                "azure_integration": azure_status.get("available", False),
                "pdf_export": True,  # Always available with fallback
                "rollback_support": True
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get enhanced agents status: {str(e)}")

# Import Azure remediation service
from azure_remediation_service import remediation_service

# Agent execution background task
async def _execute_agent(agent_id: str):
    """Execute agent in background with AI-powered remediation plan generation and execution"""
    try:
        agent = next((a for a in AGENTS if a["id"] == agent_id), None)
        if not agent:
            return
        
        # Enhanced execution phases with actual remediation
        phases = [
            {"name": "Analyzing finding", "progress": 20, "duration": 2},
            {"name": "Generating remediation plan", "progress": 40, "duration": 3},
            {"name": "Executing automated remediation", "progress": 70, "duration": 4},
            {"name": "Validating remediation", "progress": 90, "duration": 2},
            {"name": "Finalizing results", "progress": 100, "duration": 1}
        ]
        
        remediation_plan = None
        remediation_result = None
        validation_result = None
        
        for i, phase in enumerate(phases):
            if agent["status"] != "running":
                return
            
            # Update progress
            agent["progress"] = phase["progress"]
            agent["updated_at"] = datetime.utcnow().isoformat()
            
            # Add log entry
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "info",
                "message": f"Phase: {phase['name']} ({phase['progress']}%)"
            }
            agent["execution_logs"].append(log_entry)
            AGENT_EXECUTION_LOGS[agent_id].append(log_entry)
            
            # Execute phase-specific actions
            if i == 1:  # Generate remediation plan
                remediation_plan = await _generate_remediation_plan(agent)
                agent["remediation_plan"] = remediation_plan
                
            elif i == 2:  # Execute automated remediation
                if remediation_plan:
                    finding = agent["finding_details"]
                    remediation_result = await remediation_service.execute_remediation(finding, remediation_plan)
                    agent["remediation_result"] = remediation_result
                    
                    # Log remediation actions
                    for action in remediation_result.get("actions_taken", []):
                        action_log = {
                            "timestamp": datetime.utcnow().isoformat(),
                            "level": "info",
                            "message": f"Remediation: {action}"
                        }
                        agent["execution_logs"].append(action_log)
                        AGENT_EXECUTION_LOGS[agent_id].append(action_log)
                    
                    # Log any errors
                    for error in remediation_result.get("errors", []):
                        error_log = {
                            "timestamp": datetime.utcnow().isoformat(),
                            "level": "warning",
                            "message": f"Remediation error: {error}"
                        }
                        agent["execution_logs"].append(error_log)
                        AGENT_EXECUTION_LOGS[agent_id].append(error_log)
                        
            elif i == 3:  # Validate remediation
                if remediation_result:
                    finding = agent["finding_details"]
                    validation_result = remediation_service.validate_remediation(finding)
                    agent["validation_result"] = validation_result
                    
                    validation_log = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "level": "info",
                        "message": f"Validation status: {validation_result.get('validation_status', 'unknown')}"
                    }
                    agent["execution_logs"].append(validation_log)
                    AGENT_EXECUTION_LOGS[agent_id].append(validation_log)
            
            # Wait for phase duration
            await asyncio.sleep(phase["duration"])
        
        # Generate comprehensive subscription analysis
        subscription_analysis = await _generate_comprehensive_subscription_analysis(agent)
        
        # Populate result with finding details including NSG rules
        agent_result = {
            "finding_details": agent["finding_details"],
            "remediation_plan": remediation_plan,
            "remediation_result": remediation_result,
            "validation_result": validation_result,
            "subscription_analysis": subscription_analysis
        }
        
        # Include NSG rules details in the result if available
        if agent["finding_details"].get("nsg_rules_details"):
            agent_result["nsg_analysis"] = {
                "total_rules": agent["finding_details"]["nsg_rules_details"].get("total_rules", 0),
                "risky_rules": agent["finding_details"]["nsg_rules_details"].get("risky_rules", []),
                "ports_summary": agent["finding_details"]["nsg_rules_details"].get("ports_summary", {})
            }
        
        agent["result"] = agent_result
        
        # Determine final status based on remediation and validation results
        if remediation_result and remediation_result.get("status") == "completed":
            if validation_result and validation_result.get("validation_status") == "passed":
                agent["status"] = "completed"
                final_message = "Agent execution completed successfully. Automated remediation applied and validated."
            else:
                agent["status"] = "completed_with_warnings"
                final_message = "Agent execution completed. Remediation applied but validation had issues."
        elif remediation_result and remediation_result.get("status") == "partial":
            agent["status"] = "completed_with_warnings"
            final_message = "Agent execution completed with partial remediation. Some actions failed."
        elif remediation_result and remediation_result.get("status") == "failed":
            agent["status"] = "failed"
            final_message = "Agent execution failed. Remediation could not be completed due to errors."
        else:
            agent["status"] = "completed"
            final_message = "Agent execution completed. Remediation plan generated (execution may have been simulated)."
        
        agent["completed_at"] = datetime.utcnow().isoformat()
        agent["progress"] = 100
        
        # Final log entry
        final_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "success",
            "message": final_message
        }
        agent["execution_logs"].append(final_log)
        AGENT_EXECUTION_LOGS[agent_id].append(final_log)
        
    except Exception as e:
        # Mark as failed
        agent["status"] = "failed"
        agent["error_message"] = str(e)
        agent["completed_at"] = datetime.utcnow().isoformat()
        
        error_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "error",
            "message": f"Agent execution failed: {str(e)}"
        }
        agent["execution_logs"].append(error_log)
        AGENT_EXECUTION_LOGS[agent_id].append(error_log)

async def _generate_remediation_plan(agent: dict) -> dict:
    """Generate AI-powered remediation plan using Azure OpenAI"""
    try:
        finding = agent["finding_details"]
        model_config = agent["model_config"]
        
        # Create prompt for remediation plan generation
        prompt = f"""
You are a cybersecurity expert specializing in Azure cloud security remediation. Generate a comprehensive remediation plan for the following security finding:

Finding Title: {finding['title']}
Description: {finding['description']}
Severity: {finding['severity']}
Resource Type: {finding['resource_type']}
Resource ID: {finding.get('resource_id', 'Not specified')}

Provide a detailed remediation plan with the following structure:
1. Executive Summary
2. Step-by-step remediation steps
3. Azure CLI commands (if applicable)
4. PowerShell commands (if applicable)
5. Validation procedures
6. Rollback plan
7. Prevention measures

Ensure all commands are production-ready and include proper error handling.
"""
        
        # Generate remediation plan using AI
        if AZURE_OPENAI_API_KEY and AZURE_OPENAI_API_KEY != "your-azure-openai-key":
            # Use Azure OpenAI
            remediation_content = await _call_azure_openai(prompt, model_config)
        elif OPENAI_API_KEY and OPENAI_API_KEY != "your-openai-api-key":
            # Fallback to OpenAI
            remediation_content = await _call_openai(prompt, model_config)
        else:
            # Mock remediation plan
            remediation_content = _generate_mock_remediation_plan(finding)
        
        return {
            "id": f"plan-{uuid.uuid4().hex[:8]}",
            "generated_at": datetime.utcnow().isoformat(),
            "model_used": model_config["model"],
            "finding_id": finding["title"],
            "content": remediation_content,
            "estimated_time": "15-30 minutes",
            "complexity": _determine_complexity(finding["severity"]),
            "validation_status": "pending"
        }
    except Exception as e:
        return {
            "id": f"plan-{uuid.uuid4().hex[:8]}",
            "generated_at": datetime.utcnow().isoformat(),
            "error": f"Failed to generate remediation plan: {str(e)}",
            "content": _generate_mock_remediation_plan(finding)
        }

async def _call_azure_openai(prompt: str, model_config: dict) -> str:
    """Call Azure OpenAI API for remediation plan generation"""
    try:
        headers = {
            "Content-Type": "application/json",
            "api-key": AZURE_OPENAI_API_KEY
        }
        
        data = {
            "messages": [
                {"role": "system", "content": "You are an expert Azure security consultant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": model_config.get("max_tokens", 2048),
            "temperature": model_config.get("temperature", 0.1)
        }
        
        url = f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{model_config['model']}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    raise Exception(f"Azure OpenAI API error: {response.status}")
    except Exception as e:
        raise Exception(f"Azure OpenAI call failed: {str(e)}")

async def _call_openai(prompt: str, model_config: dict) -> str:
    """Call OpenAI API for remediation plan generation"""
    try:
        openai.api_key = OPENAI_API_KEY
        
        response = await openai.ChatCompletion.acreate(
            model=model_config["model"],
            messages=[
                {"role": "system", "content": "You are an expert Azure security consultant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=model_config.get("max_tokens", 2048),
            temperature=model_config.get("temperature", 0.1)
        )
        
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"OpenAI call failed: {str(e)}")

def _generate_mock_remediation_plan(finding: dict) -> str:
    """Generate a mock remediation plan when AI services are not available"""
    return f"""
# Remediation Plan for {finding['title']}

## Executive Summary
This plan addresses the {finding['severity']} severity finding: {finding['title']}.

## Remediation Steps
1. **Assessment**: Review the current configuration of {finding['resource_type']}
2. **Backup**: Create a backup of current settings
3. **Implementation**: Apply security configurations
4. **Validation**: Verify the fix is working correctly
5. **Documentation**: Update security documentation

## Azure CLI Commands
```bash
# Example commands for {finding['resource_type']}
az account show
az resource list --resource-type {finding['resource_type']}
```

## PowerShell Commands
```powershell
# PowerShell equivalent commands
Get-AzContext
Get-AzResource -ResourceType {finding['resource_type']}
```

## Validation Procedures
1. Verify configuration changes are applied
2. Test functionality is not impacted
3. Run security scan to confirm fix

## Rollback Plan
1. Restore from backup if issues occur
2. Revert configuration changes
3. Contact security team for assistance

## Prevention Measures
1. Implement Azure Policy to prevent recurrence
2. Set up monitoring and alerts
3. Regular security assessments
"""

def _determine_complexity(severity: str) -> str:
    """Determine remediation complexity based on severity"""
    complexity_map = {
        "critical": "High",
        "high": "Medium", 
        "medium": "Low",
        "low": "Low"
    }
    return complexity_map.get(severity.lower(), "Medium")

async def _generate_comprehensive_subscription_analysis(agent: dict) -> dict:
    """Generate comprehensive subscription-wide analysis including NSG details"""
    try:
        subscription_id = agent.get("azure_subscription_id", AZURE_CONFIG["subscription_id"])
        
        # Generate detailed subscription analysis
        analysis = {
            "subscription_details": {
                "subscription_id": subscription_id,
                "tenant_id": AZURE_CONFIG["tenant_id"],
                "subscription_name": "Production Subscription",
                "analysis_timestamp": datetime.utcnow().isoformat()
            },
            "resource_groups": [
                {
                    "name": "rg-production",
                    "location": "East US",
                    "resources_count": 25,
                    "nsg_count": 3,
                    "last_scan": datetime.utcnow().isoformat()
                },
                {
                    "name": "rg-development",
                    "location": "West US",
                    "resources_count": 12,
                    "nsg_count": 2,
                    "last_scan": datetime.utcnow().isoformat()
                },
                {
                    "name": "rg-networking",
                    "location": "Central US",
                    "resources_count": 8,
                    "nsg_count": 4,
                    "last_scan": datetime.utcnow().isoformat()
                }
            ],
            "network_security_groups": [
                {
                    "name": "nsg-production-web",
                    "resource_group": "rg-production",
                    "location": "East US",
                    "associated_subnets": ["subnet-web-prod", "subnet-app-prod"],
                    "total_rules": 8,
                    "inbound_rules": [
                        {
                            "name": "AllowHTTP",
                            "priority": 100,
                            "direction": "Inbound",
                            "access": "Allow",
                            "protocol": "TCP",
                            "source_port_range": "*",
                            "destination_port_range": "80",
                            "source_address_prefix": "*",
                            "destination_address_prefix": "*",
                            "risk_level": "Medium",
                            "description": "Allow HTTP traffic from internet"
                        },
                        {
                            "name": "AllowHTTPS",
                            "priority": 110,
                            "direction": "Inbound",
                            "access": "Allow",
                            "protocol": "TCP",
                            "source_port_range": "*",
                            "destination_port_range": "443",
                            "source_address_prefix": "*",
                            "destination_address_prefix": "*",
                            "risk_level": "Low",
                            "description": "Allow HTTPS traffic from internet"
                        },
                        {
                            "name": "AllowSSH",
                            "priority": 120,
                            "direction": "Inbound",
                            "access": "Allow",
                            "protocol": "TCP",
                            "source_port_range": "*",
                            "destination_port_range": "22",
                            "source_address_prefix": "0.0.0.0/0",
                            "destination_address_prefix": "*",
                            "risk_level": "Critical",
                            "description": "SSH access open to internet - HIGH RISK"
                        }
                    ],
                    "outbound_rules": [
                        {
                            "name": "AllowInternetOutbound",
                            "priority": 100,
                            "direction": "Outbound",
                            "access": "Allow",
                            "protocol": "*",
                            "source_port_range": "*",
                            "destination_port_range": "*",
                            "source_address_prefix": "*",
                            "destination_address_prefix": "Internet",
                            "risk_level": "Medium",
                            "description": "Allow all outbound internet traffic"
                        }
                    ],
                    "risk_summary": {
                        "critical_rules": 1,
                        "high_risk_rules": 0,
                        "medium_risk_rules": 2,
                        "low_risk_rules": 1,
                        "total_risky_rules": 3
                    }
                },
                {
                    "name": "nsg-production-db",
                    "resource_group": "rg-production",
                    "location": "East US",
                    "associated_subnets": ["subnet-db-prod"],
                    "total_rules": 5,
                    "inbound_rules": [
                        {
                            "name": "AllowSQL",
                            "priority": 100,
                            "direction": "Inbound",
                            "access": "Allow",
                            "protocol": "TCP",
                            "source_port_range": "*",
                            "destination_port_range": "1433",
                            "source_address_prefix": "10.0.1.0/24",
                            "destination_address_prefix": "*",
                            "risk_level": "Low",
                            "description": "Allow SQL Server access from web subnet"
                        },
                        {
                            "name": "AllowRDP",
                            "priority": 110,
                            "direction": "Inbound",
                            "access": "Allow",
                            "protocol": "TCP",
                            "source_port_range": "*",
                            "destination_port_range": "3389",
                            "source_address_prefix": "0.0.0.0/0",
                            "destination_address_prefix": "*",
                            "risk_level": "Critical",
                            "description": "RDP access open to internet - CRITICAL RISK"
                        }
                    ],
                    "outbound_rules": [
                        {
                            "name": "DenyInternetOutbound",
                            "priority": 100,
                            "direction": "Outbound",
                            "access": "Deny",
                            "protocol": "*",
                            "source_port_range": "*",
                            "destination_port_range": "*",
                            "source_address_prefix": "*",
                            "destination_address_prefix": "Internet",
                            "risk_level": "Low",
                            "description": "Deny all outbound internet traffic"
                        }
                    ],
                    "risk_summary": {
                        "critical_rules": 1,
                        "high_risk_rules": 0,
                        "medium_risk_rules": 0,
                        "low_risk_rules": 2,
                        "total_risky_rules": 1
                    }
                },
                {
                    "name": "nsg-development-web",
                    "resource_group": "rg-development",
                    "location": "West US",
                    "associated_subnets": ["subnet-web-dev"],
                    "total_rules": 6,
                    "inbound_rules": [
                        {
                            "name": "AllowHTTP",
                            "priority": 100,
                            "direction": "Inbound",
                            "access": "Allow",
                            "protocol": "TCP",
                            "source_port_range": "*",
                            "destination_port_range": "80",
                            "source_address_prefix": "*",
                            "destination_address_prefix": "*",
                            "risk_level": "Medium",
                            "description": "Allow HTTP traffic for development"
                        },
                        {
                            "name": "AllowSSH",
                            "priority": 110,
                            "direction": "Inbound",
                            "access": "Allow",
                            "protocol": "TCP",
                            "source_port_range": "*",
                            "destination_port_range": "22",
                            "source_address_prefix": "203.0.113.0/24",
                            "destination_address_prefix": "*",
                            "risk_level": "Low",
                            "description": "SSH access from office network"
                        }
                    ],
                    "outbound_rules": [
                        {
                            "name": "AllowInternetOutbound",
                            "priority": 100,
                            "direction": "Outbound",
                            "access": "Allow",
                            "protocol": "*",
                            "source_port_range": "*",
                            "destination_port_range": "*",
                            "source_address_prefix": "*",
                            "destination_address_prefix": "Internet",
                            "risk_level": "Medium",
                            "description": "Allow outbound internet for development"
                        }
                    ],
                    "risk_summary": {
                        "critical_rules": 0,
                        "high_risk_rules": 0,
                        "medium_risk_rules": 2,
                        "low_risk_rules": 1,
                        "total_risky_rules": 2
                    }
                }
            ],
            "ports_analysis": {
                "critical_ports": {
                    "22": {
                        "protocol": "TCP",
                        "service": "SSH",
                        "exposed_nsgs": ["nsg-production-web"],
                        "risk_level": "Critical",
                        "description": "SSH port exposed to internet"
                    },
                    "3389": {
                        "protocol": "TCP",
                        "service": "RDP",
                        "exposed_nsgs": ["nsg-production-db"],
                        "risk_level": "Critical",
                        "description": "RDP port exposed to internet"
                    }
                },
                "high_risk_ports": {},
                "medium_risk_ports": {
                    "80": {
                        "protocol": "TCP",
                        "service": "HTTP",
                        "exposed_nsgs": ["nsg-production-web", "nsg-development-web"],
                        "risk_level": "Medium",
                        "description": "HTTP port exposed to internet"
                    }
                },
                "low_risk_ports": {
                    "443": {
                        "protocol": "TCP",
                        "service": "HTTPS",
                        "exposed_nsgs": ["nsg-production-web"],
                        "risk_level": "Low",
                        "description": "HTTPS port properly configured"
                    },
                    "1433": {
                        "protocol": "TCP",
                        "service": "SQL Server",
                        "exposed_nsgs": ["nsg-production-db"],
                        "risk_level": "Low",
                        "description": "SQL Server port restricted to internal network"
                    }
                }
            },
            "security_summary": {
                "total_nsgs": 3,
                "total_rules": 19,
                "critical_findings": 2,
                "high_risk_findings": 0,
                "medium_risk_findings": 4,
                "low_risk_findings": 4,
                "compliance_score": 65,
                "recommendations": [
                    "Immediately restrict SSH access (port 22) to specific IP ranges",
                    "Remove RDP access (port 3389) from internet exposure",
                    "Implement network segmentation for database tier",
                    "Enable NSG flow logs for monitoring",
                    "Regular review of NSG rules quarterly"
                ]
            }
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"Failed to generate subscription analysis: {e}")
        return {
            "error": f"Failed to generate analysis: {str(e)}",
            "subscription_details": {
                "subscription_id": subscription_id,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
        }

# ===== VALIDATION ENDPOINTS =====

@app.post("/api/v1/validation/upload")
async def upload_validation_files(files_data: dict):
    """Upload source and reference files for validation"""
    try:
        source_file = files_data.get('source_file')
        reference_file = files_data.get('reference_file')
        
        if not source_file or not reference_file:
            raise HTTPException(status_code=400, detail="Both source and reference files are required")
        
        # In a real implementation, you would handle file uploads here
        # For now, we'll simulate with file paths
        upload_id = str(uuid.uuid4())
        
        return {
            "success": True,
            "upload_id": upload_id,
            "message": "Files uploaded successfully",
            "source_file": source_file,
            "reference_file": reference_file
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/v1/validation/analyze")
async def analyze_validation_files(
    source_file: UploadFile = File(...),
    reference_file: UploadFile = File(...)
):
    """Analyze files and detect columns for mapping"""
    try:
        # Save uploaded files temporarily
        import tempfile
        import shutil
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{source_file.filename}") as tmp_source:
            shutil.copyfileobj(source_file.file, tmp_source)
            source_path = tmp_source.name
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{reference_file.filename}") as tmp_reference:
            shutil.copyfileobj(reference_file.file, tmp_reference)
            reference_path = tmp_reference.name
        
        try:
            # Read files to detect columns
            source_df = validation_service.read_file(source_path)
            reference_df = validation_service.read_file(reference_path)
            
            return {
                "success": True,
                "source_columns": source_df.columns.tolist(),
                "reference_columns": reference_df.columns.tolist(),
                "message": "Files analyzed successfully"
            }
            
        except Exception as file_error:
            raise HTTPException(status_code=400, detail=f"Error reading files: {str(file_error)}")
        finally:
            # Clean up temporary files
            try:
                os.unlink(source_path)
                os.unlink(reference_path)
            except:
                pass
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/v1/validation/compare")
async def compare_validation_files(
    source_file: UploadFile = File(...),
    reference_file: UploadFile = File(...),
    column_mapping: str = Form(None)
):
    """Compare source and reference files and generate validation report"""
    # Save uploaded files temporarily
    import tempfile
    import shutil
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{source_file.filename}") as tmp_source:
        shutil.copyfileobj(source_file.file, tmp_source)
        source_path = tmp_source.name
        
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{reference_file.filename}") as tmp_reference:
        shutil.copyfileobj(reference_file.file, tmp_reference)
        reference_path = tmp_reference.name
    
    try:
        # Parse column mapping if provided
        parsed_column_mapping = None
        if column_mapping:
            try:
                parsed_column_mapping = json.loads(column_mapping)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid column mapping format")
        
        # Generate validation report with optional column mapping
        report = validation_service.generate_validation_report(source_path, reference_path, parsed_column_mapping)
        
        # Convert report to dictionary for JSON response
        report_data = {
            "validation_id": str(uuid.uuid4()),
            "total_resources": report.total_resources,
            "new_resources": report.new_resources,
            "updated_resources": report.updated_resources,
            "unchanged_resources": report.unchanged_resources,
            "removed_resources": report.removed_resources,
            "generated_at": report.generated_at.isoformat(),
            "source_file": report.source_file,
            "reference_file": report.reference_file,
            "comparisons": [
                {
                    "resource_name": comp.resource_name,
                    "resource_group": comp.resource_group,
                    "subscription_id": comp.subscription_id,
                    "subscription_name": comp.subscription_name,
                    "owner_name": comp.owner_name,
                    "tags": comp.tags,
                    "status": comp.status,
                    "changes": comp.changes,
                    "remediation_details": comp.remediation_details,
                    "recommended_steps": comp.recommended_steps,
                    "severity": comp.severity,
                    "compliance_status": comp.compliance_status,
                    "source_values": comp.source_values,
                    "reference_values": comp.reference_values
                }
                for comp in report.comparisons
            ]
        }
        
        # Clean up temporary files
        try:
            os.unlink(source_path)
            os.unlink(reference_path)
        except Exception as e:
            print(f"Warning: Could not clean up temporary files: {e}")
        
        return {
            "success": True,
            "report": report_data
        }
        
    except Exception as e:
        # Clean up temporary files in case of error
        try:
            os.unlink(source_path)
            os.unlink(reference_path)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Validation comparison failed: {str(e)}")

@app.post("/api/v1/validation/export")
async def export_validation_report(request_data: dict):
    """Export validation report to Excel or CSV"""
    try:
        report_data = request_data.get('report_data')
        output_format = request_data.get('format', 'excel')
        
        if not report_data:
            raise HTTPException(status_code=400, detail="Validation report data is required")
        
        # Convert report data to ValidationReport object
        from validation_service import ValidationReport, ResourceComparison
        from datetime import datetime
        
        # Convert comparisons data
        comparisons = []
        for comp_data in report_data.get('comparisons', []):
            comparison = ResourceComparison(
                resource_name=comp_data.get('resource_name', ''),
                resource_group=comp_data.get('resource_group', ''),
                subscription_id=comp_data.get('subscription_id', ''),
                subscription_name=comp_data.get('subscription_name', ''),
                owner_name=comp_data.get('owner_name', ''),
                tags=comp_data.get('tags', {}),
                status=comp_data.get('status', 'unchanged'),
                changes=comp_data.get('changes', []),
                remediation_details=comp_data.get('remediation_details', ''),
                recommended_steps=comp_data.get('recommended_steps', []),
                severity=comp_data.get('severity', 'low'),
                compliance_status=comp_data.get('compliance_status', 'pending_review')
            )
            comparisons.append(comparison)
        
        # Create ValidationReport object
        report = ValidationReport(
            total_resources=report_data.get('total_resources', 0),
            new_resources=report_data.get('new_resources', 0),
            updated_resources=report_data.get('updated_resources', 0),
            unchanged_resources=report_data.get('unchanged_resources', 0),
            removed_resources=report_data.get('removed_resources', 0),
            comparisons=comparisons,
            generated_at=datetime.fromisoformat(report_data.get('generated_at', datetime.now().isoformat())),
            source_file=report_data.get('source_file', 'source_file'),
            reference_file=report_data.get('reference_file', 'reference_file')
        )
        
        # Export report
        output_file = validation_service.export_validation_report(report, output_format)
        
        # Return file content for download
        import os
        if os.path.exists(output_file):
            with open(output_file, 'rb') as f:
                file_content = f.read()
            
            # Clean up the temporary file
            os.unlink(output_file)
            
            # Return base64 encoded content for frontend download
            import base64
            file_content_b64 = base64.b64encode(file_content).decode('utf-8')
            
            return {
                "success": True,
                "file_content": file_content_b64,
                "filename": os.path.basename(output_file),
                "format": output_format,
                "message": f"Validation report exported successfully as {output_format.upper()}"
            }
        else:
            raise Exception("Failed to generate export file")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.post("/api/v1/validation/notify")
async def send_validation_notification(request_data: dict):
    """Send email notification with validation report"""
    try:
        report_data = request_data.get('report_data')
        recipients = request_data.get('recipients', [])
        include_attachment = request_data.get('include_attachment', True)
        
        if not report_data:
            raise HTTPException(status_code=400, detail="Validation report data is required")
        
        if not recipients:
            raise HTTPException(status_code=400, detail="At least one recipient email is required")
        
        # Convert report data to ValidationReport object
        from validation_service import ValidationReport, ResourceComparison
        from datetime import datetime
        
        # Convert comparisons data
        comparisons = []
        for comp_data in report_data.get('comparisons', []):
            comparison = ResourceComparison(
                resource_name=comp_data.get('resource_name', ''),
                resource_group=comp_data.get('resource_group', ''),
                subscription_id=comp_data.get('subscription_id', ''),
                subscription_name=comp_data.get('subscription_name', ''),
                owner_name=comp_data.get('owner_name', ''),
                tags=comp_data.get('tags', {}),
                status=comp_data.get('status', 'unchanged'),
                changes=comp_data.get('changes', []),
                remediation_details=comp_data.get('remediation_details', ''),
                recommended_steps=comp_data.get('recommended_steps', []),
                severity=comp_data.get('severity', 'low'),
                compliance_status=comp_data.get('compliance_status', 'pending_review')
            )
            comparisons.append(comparison)
        
        # Create ValidationReport object
        report = ValidationReport(
            total_resources=report_data.get('total_resources', 0),
            new_resources=report_data.get('new_resources', 0),
            updated_resources=report_data.get('updated_resources', 0),
            unchanged_resources=report_data.get('unchanged_resources', 0),
            removed_resources=report_data.get('removed_resources', 0),
            comparisons=comparisons,
            generated_at=datetime.fromisoformat(report_data.get('generated_at', datetime.now().isoformat())),
            source_file=report_data.get('source_file', 'source_file'),
            reference_file=report_data.get('reference_file', 'reference_file')
        )
        
        # Export report if attachment is requested
        report_file = None
        if include_attachment:
            report_file = validation_service.export_validation_report(report, 'excel')
        
        # Send email notification
        success = validation_service.send_email_notification(report, recipients, report_file)
        
        # Clean up temporary file
        if report_file and os.path.exists(report_file):
            os.unlink(report_file)
        
        if success:
            return {
                "success": True,
                "message": f"Validation report sent to {len(recipients)} recipients",
                "recipients": recipients
            }
        else:
            return {
                "success": False,
                "message": "Failed to send email notification. Check email configuration."
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notification failed: {str(e)}")

@app.post("/api/v1/validation/llm-email/generate")
async def generate_llm_email_templates(request_data: dict):
    """Generate LLM-powered email templates for validation results"""
    try:
        report_data = request_data.get('report_data')
        if not report_data:
            raise HTTPException(status_code=400, detail="Validation report data is required")
        
        # Convert report data to ResourceComparison objects
        from validation_service import ResourceComparison
        
        comparisons = []
        for comp_data in report_data.get('comparisons', []):
            comparison = ResourceComparison(
                resource_name=comp_data.get('resource_name', ''),
                resource_group=comp_data.get('resource_group', ''),
                subscription_id=comp_data.get('subscription_id', ''),
                subscription_name=comp_data.get('subscription_name', ''),
                owner_name=comp_data.get('owner_name', ''),
                tags=comp_data.get('tags', {}),
                status=comp_data.get('status', 'unchanged'),
                changes=comp_data.get('changes', []),
                remediation_details=comp_data.get('remediation_details', ''),
                recommended_steps=comp_data.get('recommended_steps', []),
                severity=comp_data.get('severity', 'low'),
                compliance_status=comp_data.get('compliance_status', 'pending_review')
            )
            comparisons.append(comparison)
        
        # Generate email templates for each resource
        templates = []
        for comparison in comparisons:
            template = await llm_email_service.generate_email_template(comparison)
            templates.append({
                'resource_name': template.resource_name,
                'policy_short_name': template.policy_short_name,
                'policy_name': template.policy_name,
                'severity': template.severity,
                'native_type': template.native_type,
                'subject': template.subject,
                'ai_recommendations': template.ai_recommendations,
                'remediation_steps': template.remediation_steps,
                'business_impact': template.business_impact,
                'azure_commands': template.azure_commands,
                'html_preview': template.html_content[:500] + '...' if len(template.html_content) > 500 else template.html_content
            })
        
        return {
            "success": True,
            "templates": templates,
            "total_templates": len(templates),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template generation failed: {str(e)}")

@app.post("/api/v1/validation/llm-email/send")
async def send_llm_email_notifications(request_data: dict):
    """Send LLM-powered email notifications"""
    try:
        recipients = request_data.get('recipients', [])
        send_mode = request_data.get('send_mode', 'bulk')  # 'bulk', 'individual', 'selected'
        selected_items = request_data.get('selected_items', [])
        report_data = request_data.get('report_data')
        
        if not recipients:
            raise HTTPException(status_code=400, detail="At least one recipient email is required")
        
        if not report_data:
            raise HTTPException(status_code=400, detail="Validation report data is required")
        
        # Convert report data to ResourceComparison objects
        from validation_service import ResourceComparison
        
        comparisons = []
        for comp_data in report_data.get('comparisons', []):
            comparison = ResourceComparison(
                resource_name=comp_data.get('resource_name', ''),
                resource_group=comp_data.get('resource_group', ''),
                subscription_id=comp_data.get('subscription_id', ''),
                subscription_name=comp_data.get('subscription_name', ''),
                owner_name=comp_data.get('owner_name', ''),
                tags=comp_data.get('tags', {}),
                status=comp_data.get('status', 'unchanged'),
                changes=comp_data.get('changes', []),
                remediation_details=comp_data.get('remediation_details', ''),
                recommended_steps=comp_data.get('recommended_steps', []),
                severity=comp_data.get('severity', 'low'),
                compliance_status=comp_data.get('compliance_status', 'pending_review')
            )
            comparisons.append(comparison)
        
        # Create email notification request
        email_request = EmailNotificationRequest(
            recipients=recipients,
            resource_comparisons=comparisons,
            send_mode=send_mode,
            selected_items=selected_items if send_mode == 'selected' else None
        )
        
        # Send emails based on mode
        if send_mode == 'individual':
            result = await llm_email_service.send_individual_emails(email_request)
        else:  # bulk or selected
            result = await llm_email_service.send_bulk_emails(email_request)
        
        return {
            "success": result['success'],
            "message": f"Emails sent successfully in {send_mode} mode",
            "results": result.get('results', []),
            "total_emails_sent": result.get('total_emails_sent', 0),
            "total_resources": result.get('total_resources', 0),
            "send_mode": send_mode,
            "sent_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")

@app.post("/api/v1/validation/llm-email/preview")
async def preview_llm_email_template(request_data: dict):
    """Preview LLM-generated email template for a specific resource"""
    try:
        resource_data = request_data.get('resource_data')
        if not resource_data:
            raise HTTPException(status_code=400, detail="Resource data is required")
        
        # Convert to ResourceComparison object
        from validation_service import ResourceComparison
        
        comparison = ResourceComparison(
            resource_name=resource_data.get('resource_name', ''),
            resource_group=resource_data.get('resource_group', ''),
            subscription_id=resource_data.get('subscription_id', ''),
            subscription_name=resource_data.get('subscription_name', ''),
            owner_name=resource_data.get('owner_name', ''),
            tags=resource_data.get('tags', {}),
            status=resource_data.get('status', 'unchanged'),
            changes=resource_data.get('changes', []),
            remediation_details=resource_data.get('remediation_details', ''),
            recommended_steps=resource_data.get('recommended_steps', []),
            severity=resource_data.get('severity', 'low'),
            compliance_status=resource_data.get('compliance_status', 'pending_review')
        )
        
        # Generate email template
        template = await llm_email_service.generate_email_template(comparison)
        
        return {
            "success": True,
            "template": {
                "subject": template.subject,
                "html_content": template.html_content,
                "text_content": template.text_content,
                "resource_name": template.resource_name,
                "policy_short_name": template.policy_short_name,
                "policy_name": template.policy_name,
                "severity": template.severity,
                "native_type": template.native_type,
                "ai_recommendations": template.ai_recommendations,
                "remediation_steps": template.remediation_steps,
                "business_impact": template.business_impact,
                "azure_commands": template.azure_commands
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template preview failed: {str(e)}")

@app.get("/api/v1/validation/status/{validation_id}")
async def get_validation_status(validation_id: str):
    """Get status of a validation process"""
    try:
        # In a real implementation, you would track validation processes
        # For now, we'll return a mock status
        return {
            "validation_id": validation_id,
            "status": "completed",
            "progress": 100,
            "message": "Validation completed successfully",
            "started_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get validation status: {str(e)}")

@app.get("/api/v1/monitoring/status")
async def get_monitoring_status():
    """Get comprehensive monitoring status including scans, agents, activity, and email notifications"""
    try:
        # Get current scan status
        scan_status = 'idle'
        if SECURITY_SCANS:
            latest_scan = max(SECURITY_SCANS, key=lambda x: x.get('created_at', ''))
            scan_status = latest_scan.get('status', 'idle')
        
        # Get agent performance metrics
        total_agents = len(AGENTS)
        active_agents = len([agent for agent in AGENTS if agent.get('status') == 'running'])
        success_rate = 85 if total_agents > 0 else 0  # Mock success rate
        avg_response_time = 1.2  # Mock average response time in seconds
        
        # Generate activity logs
        activity_logs = []
        
        # Add scan activities
        for scan in SECURITY_SCANS[-10:]:  # Last 10 scans
            activity_logs.append({
                "id": f"scan_{scan.get('scan_id', 'unknown')}",
                "timestamp": scan.get('created_at', datetime.now().isoformat()),
                "type": "scan",
                "message": f"Security scan {scan.get('status', 'unknown')} for {scan.get('framework', 'unknown')} framework",
                "status": "success" if scan.get('status') == 'completed' else "warning" if scan.get('status') == 'running' else "error"
            })
        
        # Add agent activities
        for agent in AGENTS[-5:]:  # Last 5 agents
            activity_logs.append({
                "id": f"agent_{agent.get('id', 'unknown')}",
                "timestamp": agent.get('created_at', datetime.now().isoformat()),
                "type": "agent",
                "message": f"Agent '{agent.get('name', 'Unknown')}' {agent.get('status', 'unknown')}",
                "status": "success" if agent.get('status') == 'completed' else "warning" if agent.get('status') == 'running' else "error"
            })
        
        # Add mock notification activities
        activity_logs.extend([
            {
                "id": "notif_001",
                "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat(),
                "type": "notification",
                "message": "Email notification sent successfully to 3 recipients",
                "status": "success"
            },
            {
                "id": "notif_002",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "type": "notification",
                "message": "Failed to send email notification - SMTP server unreachable",
                "status": "error"
            }
        ])
        
        # Add mock error logs
        activity_logs.extend([
            {
                "id": "error_001",
                "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
                "type": "error",
                "message": "Azure API rate limit exceeded during resource enumeration",
                "status": "error"
            },
            {
                "id": "error_002",
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "type": "error",
                "message": "LLM service timeout while generating recommendations",
                "status": "error"
            }
        ])
        
        # Sort activity logs by timestamp (newest first)
        activity_logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Email notification status
        email_status = {
            "totalSent": 25,
            "successful": 22,
            "failed": 3,
            "lastSent": (datetime.now() - timedelta(minutes=15)).isoformat(),
            "failureReasons": [
                "SMTP server connection timeout",
                "Invalid recipient email address: invalid@domain",
                "Email quota exceeded for current billing period"
            ]
        }
        
        monitoring_data = {
            "scanStatus": scan_status,
            "agentPerformance": {
                "totalAgents": total_agents,
                "activeAgents": active_agents,
                "successRate": success_rate,
                "avgResponseTime": avg_response_time
            },
            "activityLogs": activity_logs[:20],  # Return last 20 activities
            "emailNotificationStatus": email_status
        }
        
        return {
            "success": True,
            "monitoring": monitoring_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to fetch monitoring status: {str(e)}",
            "monitoring": {
                "scanStatus": "unknown",
                "agentPerformance": {
                    "totalAgents": 0,
                    "activeAgents": 0,
                    "successRate": 0,
                    "avgResponseTime": 0
                },
                "activityLogs": [],
                "emailNotificationStatus": {
                    "totalSent": 0,
                    "successful": 0,
                    "failed": 0,
                    "lastSent": "",
                    "failureReasons": []
                }
            }
         }

@app.post("/api/v1/monitoring/ai-analyze")
async def analyze_monitoring_item_with_ai(request_data: dict):
    """Generate AI recommendations for monitoring items (activity logs, failure reasons)"""
    try:
        item_type = request_data.get('type', 'unknown')
        item_message = request_data.get('message', '')
        item_context = request_data.get('context', {})
        
        # Create appropriate prompt based on item type
        if item_type == 'error':
            prompt = f"""
Analyze the following system error and provide recommendations:

Error Message: {item_message}
Context: {json.dumps(item_context, indent=2)}

Please provide:
1. Root Cause Analysis
2. Immediate Actions
3. Long-term Prevention
4. Risk Assessment
5. Monitoring Recommendations

Format your response in a structured manner.
"""
        elif item_type == 'notification':
            prompt = f"""
Analyze the following email notification issue and provide recommendations:

Notification Issue: {item_message}
Context: {json.dumps(item_context, indent=2)}

Please provide:
1. Issue Analysis
2. Troubleshooting Steps
3. Configuration Recommendations
4. Alternative Solutions
5. Prevention Measures

Format your response in a structured manner.
"""
        elif item_type == 'scan':
            prompt = f"""
Analyze the following security scan issue and provide recommendations:

Scan Issue: {item_message}
Context: {json.dumps(item_context, indent=2)}

Please provide:
1. Scan Analysis
2. Performance Optimization
3. Configuration Tuning
4. Resource Recommendations
5. Best Practices

Format your response in a structured manner.
"""
        elif item_type == 'agent':
            prompt = f"""
Analyze the following agent performance issue and provide recommendations:

Agent Issue: {item_message}
Context: {json.dumps(item_context, indent=2)}

Please provide:
1. Performance Analysis
2. Optimization Strategies
3. Resource Allocation
4. Configuration Improvements
5. Monitoring Enhancements

Format your response in a structured manner.
"""
        else:
            prompt = f"""
Analyze the following system monitoring item and provide recommendations:

Item: {item_message}
Type: {item_type}
Context: {json.dumps(item_context, indent=2)}

Please provide:
1. Analysis
2. Recommendations
3. Action Items
4. Best Practices
5. Prevention Measures

Format your response in a structured manner.
"""
        
        # Generate AI recommendations
        if OPENAI_API_KEY and OPENAI_API_KEY != "your-openai-api-key":
            try:
                response = await openai.ChatCompletion.acreate(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a cybersecurity expert specializing in system monitoring, troubleshooting, and operational excellence. Provide detailed, actionable recommendations."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=OPENAI_MAX_TOKENS,
                    temperature=OPENAI_TEMPERATURE
                )
                
                ai_analysis = response.choices[0].message.content.strip()
                
                return {
                    "success": True,
                    "analysis": {
                        "type": item_type,
                        "message": item_message,
                        "aiRecommendations": ai_analysis,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
            except Exception as openai_error:
                # Fallback to mock analysis
                mock_analysis = _generate_mock_monitoring_analysis(item_type, item_message)
                return {
                    "success": True,
                    "analysis": {
                        "type": item_type,
                        "message": item_message,
                        "aiRecommendations": mock_analysis,
                        "timestamp": datetime.now().isoformat(),
                        "note": "Generated using fallback analysis due to AI service unavailability"
                    }
                }
        else:
            # Use mock analysis when OpenAI is not configured
            mock_analysis = _generate_mock_monitoring_analysis(item_type, item_message)
            return {
                "success": True,
                "analysis": {
                    "type": item_type,
                    "message": item_message,
                    "aiRecommendations": mock_analysis,
                    "timestamp": datetime.now().isoformat(),
                    "note": "Generated using mock analysis - configure OpenAI for enhanced recommendations"
                }
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to analyze monitoring item: {str(e)}"
        }

def _generate_mock_monitoring_analysis(item_type: str, message: str) -> str:
    """Generate mock analysis for monitoring items"""
    
    if item_type == 'error':
        return f"""
## Root Cause Analysis
The error "{message}" indicates a system-level issue that requires immediate attention.

## Immediate Actions
1. Check system logs for additional context
2. Verify service connectivity and dependencies
3. Monitor resource utilization (CPU, memory, network)
4. Implement temporary workarounds if available

## Long-term Prevention
1. Implement proper error handling and retry mechanisms
2. Set up proactive monitoring and alerting
3. Regular system health checks and maintenance
4. Capacity planning and resource optimization

## Risk Assessment
- **Impact**: Medium to High
- **Probability**: Depends on system stability
- **Mitigation**: Implement monitoring and automated recovery

## Monitoring Recommendations
1. Set up real-time alerts for similar errors
2. Implement health check endpoints
3. Monitor key performance indicators
4. Regular system audits and reviews
"""
    
    elif item_type == 'notification':
        return f"""
## Issue Analysis
The notification issue "{message}" suggests problems with email delivery infrastructure.

## Troubleshooting Steps
1. Verify SMTP server configuration and connectivity
2. Check email authentication settings (SPF, DKIM, DMARC)
3. Review email content for spam triggers
4. Validate recipient email addresses

## Configuration Recommendations
1. Implement email queue management
2. Set up backup SMTP providers
3. Configure proper retry mechanisms
4. Implement email delivery tracking

## Alternative Solutions
1. Use multiple email service providers
2. Implement webhook notifications as backup
3. Set up SMS notifications for critical alerts
4. Use push notifications for real-time updates

## Prevention Measures
1. Regular testing of email delivery
2. Monitor email reputation and deliverability
3. Implement proper error handling
4. Set up monitoring for email service health
"""
    
    elif item_type == 'scan':
        return f"""
## Scan Analysis
The scan issue "{message}" indicates potential performance or configuration problems.

## Performance Optimization
1. Optimize scan scheduling to avoid peak hours
2. Implement parallel processing where possible
3. Use incremental scanning for large datasets
4. Configure appropriate timeout values

## Configuration Tuning
1. Adjust scan parameters based on environment
2. Implement proper resource allocation
3. Configure scan priorities and queuing
4. Set up scan result caching

## Resource Recommendations
1. Monitor CPU and memory usage during scans
2. Implement resource throttling
3. Use dedicated scanning infrastructure
4. Scale resources based on scan volume

## Best Practices
1. Regular scan schedule optimization
2. Implement scan result validation
3. Set up scan performance monitoring
4. Regular review of scan configurations
"""
    
    elif item_type == 'agent':
        return f"""
## Performance Analysis
The agent issue "{message}" suggests performance or operational challenges.

## Optimization Strategies
1. Review agent workload distribution
2. Implement proper task queuing
3. Optimize agent resource allocation
4. Configure appropriate timeout settings

## Resource Allocation
1. Monitor agent resource consumption
2. Implement dynamic scaling
3. Set up resource limits and quotas
4. Use load balancing for agent tasks

## Configuration Improvements
1. Optimize agent parameters
2. Implement proper error handling
3. Configure retry mechanisms
4. Set up agent health monitoring

## Monitoring Enhancements
1. Real-time agent performance tracking
2. Set up alerts for agent failures
3. Implement agent lifecycle management
4. Regular performance reviews and tuning
"""
    
    else:
        return f"""
## Analysis
The monitoring item "{message}" of type "{item_type}" requires attention.

## Recommendations
1. Investigate the root cause of the issue
2. Implement appropriate monitoring and alerting
3. Set up preventive measures
4. Regular review and optimization

## Action Items
1. Immediate investigation and resolution
2. Document findings and solutions
3. Update monitoring configurations
4. Implement process improvements

## Best Practices
1. Proactive monitoring and alerting
2. Regular system health checks
3. Proper documentation and knowledge sharing
4. Continuous improvement processes

## Prevention Measures
1. Implement robust error handling
2. Set up comprehensive monitoring
3. Regular system maintenance
4. Capacity planning and optimization
"""

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Securra Enhanced Backend with Agentic System")
    print("📍 URL: http://127.0.0.1:9099")
    print("📋 Features: Subscription Management, CIS/SOC Reports, AI Assistant, User Management, Agentic System")
    print("🔐 Test Credentials:")
    print("   Admin: admin@securra.com / admin123")
    print("   Analyst: analyst@securra.com / analyst123")
    print("   Demo: demo@securra.com / demo123")
    uvicorn.run("enhanced_backend:app", host="127.0.0.1", port=9099, reload=True)
