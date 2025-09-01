"""LLM-powered Email Service for Security Validation Reports
Generates personalized email notifications using AI for each resource/policy
with detailed recommendations, remediation steps, and Azure commands.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import os
from pathlib import Path

# Import existing services
from validation_service import ResourceComparison, ValidationReport
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

@dataclass
class EmailTemplate:
    """Data class for email template"""
    subject: str
    html_content: str
    text_content: str
    resource_name: str
    policy_short_name: str
    policy_name: str
    policy_number: str
    severity: str
    native_type: str
    ai_recommendations: str
    remediation_steps: str
    business_impact: str
    azure_commands: str

@dataclass
class EmailNotificationRequest:
    """Data class for email notification request"""
    recipients: List[str]
    resource_comparisons: List[ResourceComparison]
    send_mode: str  # 'bulk', 'individual', 'selected'
    selected_items: Optional[List[str]] = None  # resource names for selected mode
    template_customization: Optional[Dict[str, Any]] = None

class LLMEmailService:
    """Service for generating LLM-powered email notifications"""
    
    def __init__(self):
        self.ai_service = AIService()
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER', '')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        
    async def generate_email_template(self, comparison: ResourceComparison) -> EmailTemplate:
        """Generate personalized email template using LLM for a single resource"""
        try:
            # Prepare context for LLM
            context = self._prepare_resource_context(comparison)
            
            # Generate AI-powered email content
            email_content = await self._generate_ai_email_content(context)
            
            # Extract policy information with enhanced details
            policy_short_name = comparison.resource_name.split('/')[-1] if '/' in comparison.resource_name else comparison.resource_name
            
            # Generate policy number based on resource type and severity
            policy_number = self._generate_policy_number(comparison)
            
            # Enhanced policy name extraction
            policy_name = self._extract_policy_name(comparison)
            
            # Create email template with enhanced policy information
            template = EmailTemplate(
                subject=f"🔒 Security Alert: {comparison.severity.upper()} - Policy #{policy_number} - {policy_short_name}",
                html_content=email_content['html_content'],
                text_content=email_content['text_content'],
                resource_name=comparison.resource_name,
                policy_short_name=policy_short_name,
                policy_name=policy_name,
                policy_number=policy_number,
                severity=comparison.severity,
                native_type=self._extract_native_type(comparison),
                ai_recommendations=email_content['ai_recommendations'],
                remediation_steps=email_content['remediation_steps'],
                business_impact=email_content['business_impact'],
                azure_commands=email_content['azure_commands']
            )
            
            return template
            
        except Exception as e:
            logger.error(f"Error generating email template for {comparison.resource_name}: {str(e)}")
            return self._create_fallback_template(comparison)
    
    def _prepare_resource_context(self, comparison: ResourceComparison) -> str:
        """Prepare context string for LLM analysis"""
        # Generate policy information for context
        policy_number = self._generate_policy_number(comparison)
        policy_name = self._extract_policy_name(comparison)
        
        context = f"""
        Resource Security Analysis Request:
        
        Resource Details:
        - Name: {comparison.resource_name}
        - Resource Group: {comparison.resource_group}
        - Subscription: {comparison.subscription_name} ({comparison.subscription_id})
        - Owner: {comparison.owner_name}
        - Tags: {json.dumps(comparison.tags, indent=2)}
        
        Policy Information:
        - Policy Number: {policy_number}
        - Policy Name: {policy_name}
        - Policy Short Name: {comparison.resource_name.split('/')[-1] if '/' in comparison.resource_name else comparison.resource_name}
        
        Security Assessment:
        - Status: {comparison.status}
        - Severity: {comparison.severity}
        - Compliance Status: {comparison.compliance_status}
        - Changes Detected: {'; '.join(comparison.changes) if comparison.changes else 'None'}
        - Current Remediation Details: {comparison.remediation_details}
        - Current Recommended Steps: {'; '.join(comparison.recommended_steps) if comparison.recommended_steps else 'None'}
        
        Please generate a comprehensive security email notification that includes:
        1. AI-Powered Recommendations specific to this resource type and security finding
        2. Detailed Remediation Steps with step-by-step instructions
        3. Business Impact analysis explaining the risks and consequences
        4. Specific Azure CLI/PowerShell commands for remediation
        
        The email should be professional, actionable, and tailored to the specific resource and security finding.
        """
        return context
    
    async def _generate_ai_email_content(self, context: str) -> Dict[str, str]:
        """Generate AI-powered email content using OpenAI"""
        try:
            import openai
            
            # Set up OpenAI client
            openai.api_key = os.getenv('OPENAI_API_KEY')
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert Azure security consultant and technical writer. 
                        Generate professional, actionable email content for security notifications.
                        
                        IMPORTANT: Always prominently include the Resource Group name, Policy Number, and Policy Name in your email content.
                        These should be clearly visible in both HTML and text versions.
                        
                        Your response must be in JSON format with the following structure:
                        {
                            "ai_recommendations": "Detailed AI-powered recommendations",
                            "remediation_steps": "Step-by-step remediation instructions",
                            "business_impact": "Business impact analysis",
                            "azure_commands": "Specific Azure CLI/PowerShell commands",
                            "html_content": "Complete HTML email content with Resource Group, Policy Number, and Policy Name prominently displayed",
                            "text_content": "Plain text version of the email with Resource Group, Policy Number, and Policy Name clearly shown"
                        }
                        
                        Make the content professional, specific, and actionable. Include proper formatting for HTML.
                        Ensure Resource Group, Policy Number, and Policy Name are highlighted in the email body."""
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            ai_response = response.choices[0].message.content
            
            # Parse JSON response
            try:
                parsed_response = json.loads(ai_response)
                return parsed_response
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return self._create_fallback_content(context)
                
        except Exception as e:
            logger.error(f"Error generating AI email content: {str(e)}")
            return self._create_fallback_content(context)
    
    def _create_fallback_content(self, context: str) -> Dict[str, str]:
        """Create fallback email content when AI generation fails"""
        return {
            "ai_recommendations": "Please review the security finding and implement appropriate security measures based on Azure best practices.",
            "remediation_steps": "1. Review the security configuration\n2. Apply recommended security settings\n3. Monitor for compliance\n4. Document changes",
            "business_impact": "This security finding may impact your organization's security posture and compliance requirements.",
            "azure_commands": "# Please consult Azure documentation for specific commands\n# az resource show --ids <resource-id>\n# az resource update --ids <resource-id> --set properties.securitySettings=enabled",
            "html_content": self._create_fallback_html(),
            "text_content": "Security Alert: Please review the attached security finding and take appropriate action."
        }
    
    def _create_fallback_html(self) -> str:
        """Create fallback HTML email template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Security Alert</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .header { background-color: #d32f2f; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; }
                .section { margin-bottom: 20px; }
                .severity-high { color: #d32f2f; font-weight: bold; }
                .severity-medium { color: #f57c00; font-weight: bold; }
                .severity-low { color: #388e3c; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔒 Security Alert</h1>
            </div>
            <div class="content">
                <div class="section">
                    <h2>Security Finding Detected</h2>
                    <p>A security finding has been detected that requires your attention.</p>
                </div>
                <div class="section">
                    <h3>📋 Recommended Actions</h3>
                    <p>Please review the security finding and implement appropriate remediation measures.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_fallback_template(self, comparison: ResourceComparison) -> EmailTemplate:
        """Create fallback email template when AI generation fails"""
        policy_short_name = comparison.resource_name.split('/')[-1] if '/' in comparison.resource_name else comparison.resource_name
        policy_number = self._generate_policy_number(comparison)
        policy_name = self._extract_policy_name(comparison)
        
        return EmailTemplate(
            subject=f"Security Alert: {comparison.severity.upper()} - Policy #{policy_number} - {policy_short_name}",
            html_content=self._create_fallback_html(),
            text_content="Security Alert: Please review the security finding and take appropriate action.",
            resource_name=comparison.resource_name,
            policy_short_name=policy_short_name,
            policy_name=policy_name,
            policy_number=policy_number,
            severity=comparison.severity,
            native_type=self._extract_native_type(comparison),
            ai_recommendations="Please review and implement appropriate security measures.",
            remediation_steps="Review security configuration and apply recommended settings.",
            business_impact="This finding may impact security posture and compliance.",
            azure_commands="Please consult Azure documentation for specific commands."
        )
    
    def _generate_policy_number(self, comparison: ResourceComparison) -> str:
        """Generate a policy number based on resource type and severity"""
        # Extract resource type from resource name or use default
        resource_type = 'GEN'  # General
        if 'storage' in comparison.resource_name.lower():
            resource_type = 'STG'
        elif 'vm' in comparison.resource_name.lower() or 'virtual' in comparison.resource_name.lower():
            resource_type = 'VM'
        elif 'network' in comparison.resource_name.lower() or 'vnet' in comparison.resource_name.lower():
            resource_type = 'NET'
        elif 'key' in comparison.resource_name.lower() or 'vault' in comparison.resource_name.lower():
            resource_type = 'KV'
        elif 'sql' in comparison.resource_name.lower() or 'database' in comparison.resource_name.lower():
            resource_type = 'DB'
        elif 'app' in comparison.resource_name.lower() or 'web' in comparison.resource_name.lower():
            resource_type = 'APP'
        
        # Severity code
        severity_code = {
            'high': '01',
            'medium': '02', 
            'low': '03'
        }.get(comparison.severity.lower(), '02')
        
        # Generate hash from resource name for uniqueness
        import hashlib
        resource_hash = hashlib.md5(comparison.resource_name.encode()).hexdigest()[:4].upper()
        
        return f"{resource_type}-{severity_code}-{resource_hash}"
    
    def _extract_policy_name(self, comparison: ResourceComparison) -> str:
        """Extract or generate a comprehensive policy name"""
        # If remediation details contain policy information, use it
        if comparison.remediation_details and len(comparison.remediation_details) > 10:
            # Try to extract a meaningful policy name from remediation details
            remediation_lower = comparison.remediation_details.lower()
            if 'policy' in remediation_lower:
                return comparison.remediation_details[:100] + '...' if len(comparison.remediation_details) > 100 else comparison.remediation_details
        
        # Generate policy name based on resource type and findings
        resource_type = 'Resource'
        if 'storage' in comparison.resource_name.lower():
            resource_type = 'Azure Storage Account'
        elif 'vm' in comparison.resource_name.lower() or 'virtual' in comparison.resource_name.lower():
            resource_type = 'Virtual Machine'
        elif 'network' in comparison.resource_name.lower() or 'vnet' in comparison.resource_name.lower():
            resource_type = 'Network Security'
        elif 'key' in comparison.resource_name.lower() or 'vault' in comparison.resource_name.lower():
            resource_type = 'Key Vault Security'
        elif 'sql' in comparison.resource_name.lower() or 'database' in comparison.resource_name.lower():
            resource_type = 'Database Security'
        elif 'app' in comparison.resource_name.lower() or 'web' in comparison.resource_name.lower():
            resource_type = 'Application Security'
        
        # Create policy name based on status and severity
        if comparison.status == 'new':
            return f"{resource_type} - New Resource Security Compliance Policy"
        elif comparison.status == 'updated':
            return f"{resource_type} - Configuration Change Security Policy"
        elif comparison.severity == 'high':
            return f"{resource_type} - High Risk Security Policy"
        else:
            return f"{resource_type} - Security Compliance Policy"
    
    def _extract_native_type(self, comparison: ResourceComparison) -> str:
        """Extract native Azure resource type from resource name or tags"""
        # Try to extract from resource name
        if '/providers/' in comparison.resource_name:
            parts = comparison.resource_name.split('/providers/')
            if len(parts) > 1:
                provider_part = parts[1]
                if '/' in provider_part:
                    return provider_part.split('/')[1]  # Get resource type
        
        # Try to extract from tags
        if 'resourceType' in comparison.tags:
            return comparison.tags['resourceType']
        
        # Fallback
        return "Azure Resource"
    
    async def send_bulk_emails(self, request: EmailNotificationRequest) -> Dict[str, Any]:
        """Send bulk emails for all resources in a single email per recipient"""
        try:
            results = []
            
            # Generate templates for all resources
            templates = []
            for comparison in request.resource_comparisons:
                if request.send_mode == 'selected' and request.selected_items:
                    if comparison.resource_name not in request.selected_items:
                        continue
                
                template = await self.generate_email_template(comparison)
                templates.append(template)
            
            # Create consolidated email for each recipient
            for recipient in request.recipients:
                success = await self._send_consolidated_email(recipient, templates)
                results.append({
                    'recipient': recipient,
                    'success': success,
                    'resource_count': len(templates)
                })
            
            return {
                'success': True,
                'results': results,
                'total_emails_sent': len([r for r in results if r['success']]),
                'total_resources': len(templates)
            }
            
        except Exception as e:
            logger.error(f"Error sending bulk emails: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def send_individual_emails(self, request: EmailNotificationRequest) -> Dict[str, Any]:
        """Send individual emails for each resource to each recipient"""
        try:
            results = []
            
            for comparison in request.resource_comparisons:
                if request.send_mode == 'selected' and request.selected_items:
                    if comparison.resource_name not in request.selected_items:
                        continue
                
                # Generate template for this resource
                template = await self.generate_email_template(comparison)
                
                # Send to each recipient
                for recipient in request.recipients:
                    success = await self._send_individual_email(recipient, template)
                    results.append({
                        'recipient': recipient,
                        'resource_name': comparison.resource_name,
                        'success': success
                    })
            
            return {
                'success': True,
                'results': results,
                'total_emails_sent': len([r for r in results if r['success']]),
                'total_resources': len([r for r in results if r['success']]) // len(request.recipients) if request.recipients else 0
            }
            
        except Exception as e:
            logger.error(f"Error sending individual emails: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _send_consolidated_email(self, recipient: str, templates: List[EmailTemplate]) -> bool:
        """Send consolidated email with all resources to a single recipient"""
        try:
            if not self.email_user or not self.email_password:
                logger.warning("Email credentials not configured")
                return False
            
            # Create consolidated email content
            subject = f"🔒 Security Assessment Report - {len(templates)} Items Require Attention"
            
            html_content = self._create_consolidated_html(templates)
            text_content = self._create_consolidated_text(templates)
            
            # Create and send email
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Consolidated email sent to {recipient} with {len(templates)} resources")
            return True
            
        except Exception as e:
            logger.error(f"Error sending consolidated email to {recipient}: {str(e)}")
            return False
    
    async def _send_individual_email(self, recipient: str, template: EmailTemplate) -> bool:
        """Send individual email for a single resource to a recipient"""
        try:
            if not self.email_user or not self.email_password:
                logger.warning("Email credentials not configured")
                return False
            
            # Create and send email
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = recipient
            msg['Subject'] = template.subject
            
            msg.attach(MIMEText(template.text_content, 'plain'))
            msg.attach(MIMEText(template.html_content, 'html'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Individual email sent to {recipient} for resource {template.resource_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending individual email to {recipient} for {template.resource_name}: {str(e)}")
            return False
    
    def _create_consolidated_html(self, templates: List[EmailTemplate]) -> str:
        """Create consolidated HTML email content for multiple resources"""
        # Group by severity
        critical_items = [t for t in templates if t.severity.lower() == 'critical']
        high_items = [t for t in templates if t.severity.lower() == 'high']
        medium_items = [t for t in templates if t.severity.lower() == 'medium']
        low_items = [t for t in templates if t.severity.lower() == 'low']
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Security Assessment Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .header {{ background: linear-gradient(135deg, #d32f2f, #f44336); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 20px; }}
                .summary {{ background-color: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
                .severity-section {{ margin-bottom: 30px; }}
                .severity-critical {{ border-left: 5px solid #d32f2f; }}
                .severity-high {{ border-left: 5px solid #ff5722; }}
                .severity-medium {{ border-left: 5px solid #f57c00; }}
                .severity-low {{ border-left: 5px solid #388e3c; }}
                .resource-item {{ background: white; border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin-bottom: 15px; }}
                .resource-header {{ font-weight: bold; font-size: 18px; margin-bottom: 10px; }}
                .resource-details {{ margin-bottom: 15px; }}
                .section-title {{ font-weight: bold; color: #1976d2; margin-top: 15px; margin-bottom: 8px; }}
                .commands {{ background-color: #f8f8f8; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px; }}
                .footer {{ background-color: #f5f5f5; padding: 20px; text-align: center; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 Security Assessment Report</h1>
                    <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="content">
                    <div class="summary">
                        <h2>📊 Summary</h2>
                        <p><strong>Total Resources:</strong> {len(templates)}</p>
                        <p><strong>Critical:</strong> {len(critical_items)} | <strong>High:</strong> {len(high_items)} | <strong>Medium:</strong> {len(medium_items)} | <strong>Low:</strong> {len(low_items)}</p>
                    </div>
        """
        
        # Add sections for each severity level
        for severity, items, css_class in [
            ('Critical', critical_items, 'severity-critical'),
            ('High', high_items, 'severity-high'),
            ('Medium', medium_items, 'severity-medium'),
            ('Low', low_items, 'severity-low')
        ]:
            if items:
                html += f"""
                    <div class="severity-section {css_class}">
                        <h2>🚨 {severity} Priority Items ({len(items)})</h2>
                """
                
                for template in items:
                    html += f"""
                        <div class="resource-item">
                            <div class="resource-header">{template.policy_short_name}</div>
                            <div class="resource-details">
                                <strong>Resource:</strong> {template.resource_name}<br>
                                <strong>Policy:</strong> {template.policy_name}<br>
                                <strong>Native Type:</strong> {template.native_type}
                            </div>
                            
                            <div class="section-title">🤖 AI-Powered Recommendations</div>
                            <p>{template.ai_recommendations}</p>
                            
                            <div class="section-title">🔧 Remediation Steps</div>
                            <p>{template.remediation_steps}</p>
                            
                            <div class="section-title">💼 Business Impact</div>
                            <p>{template.business_impact}</p>
                            
                            <div class="section-title">⚡ Azure Commands</div>
                            <div class="commands">{template.azure_commands}</div>
                        </div>
                    """
                
                html += "</div>"
        
        html += """
                </div>
                
                <div class="footer">
                    <p>This report was generated by Securra - Cloud Security Assessment AI Tool</p>
                    <p>For support, please contact your security team.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_consolidated_text(self, templates: List[EmailTemplate]) -> str:
        """Create consolidated text email content for multiple resources"""
        text = f"""
SECURITY ASSESSMENT REPORT
Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*50}
SUMMARY
{'='*50}
Total Resources: {len(templates)}

"""
        
        # Group by severity and add to text
        critical_items = [t for t in templates if t.severity.lower() == 'critical']
        high_items = [t for t in templates if t.severity.lower() == 'high']
        medium_items = [t for t in templates if t.severity.lower() == 'medium']
        low_items = [t for t in templates if t.severity.lower() == 'low']
        
        for severity, items in [
            ('CRITICAL', critical_items),
            ('HIGH', high_items),
            ('MEDIUM', medium_items),
            ('LOW', low_items)
        ]:
            if items:
                text += f"\n{severity} PRIORITY ITEMS ({len(items)})\n{'-'*40}\n"
                
                for template in items:
                    text += f"""
Resource: {template.resource_name}
Policy: {template.policy_name}
Native Type: {template.native_type}

AI-Powered Recommendations:
{template.ai_recommendations}

Remediation Steps:
{template.remediation_steps}

Business Impact:
{template.business_impact}

Azure Commands:
{template.azure_commands}

{'-'*40}
"""
        
        text += "\nThis report was generated by Securra - Cloud Security Assessment AI Tool\n"
        return text

# Global instance
llm_email_service = LLMEmailService()