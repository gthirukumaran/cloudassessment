"""
AI service for OpenAI GPT-4 integration and intelligent analysis
"""
import openai
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.config import settings
from app.models.scan import Finding, Scan
from app.models.chatbot import ChatMessage, MessageType


class AIService:
    """AI service for OpenAI GPT-4 integration and intelligent analysis"""
    
    def __init__(self):
        openai.api_key = settings.openai_api_key
        self.model = settings.openai_model
    
    async def analyze_finding(self, finding: Finding, scan_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze a security finding using AI"""
        try:
            # Prepare context for AI analysis
            context = self._prepare_finding_context(finding, scan_context)
            
            # Generate AI analysis
            response = await self._generate_analysis(context)
            
            # Update finding with AI analysis
            finding.ai_analysis = response.get("analysis", "")
            finding.ai_confidence = response.get("confidence", 0)
            
            return response
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI analysis failed: {str(e)}"
            )
    
    def _prepare_finding_context(self, finding: Finding, scan_context: Optional[Dict[str, Any]] = None) -> str:
        """Prepare context for AI analysis"""
        context = f"""
        Security Finding Analysis Request:
        
        Finding Title: {finding.title}
        Finding Description: {finding.description}
        Severity: {finding.severity.value}
        Category: {finding.category}
        Resource Type: {finding.resource_type}
        Resource Name: {finding.resource_name}
        Finding Type: {finding.finding_type}
        
        Compliance Framework: {finding.compliance_framework or 'Not specified'}
        Compliance Control: {finding.compliance_control or 'Not specified'}
        
        Current Remediation Steps: {finding.remediation_steps or 'Not provided'}
        Remediation Cost: {finding.remediation_cost or 'Not specified'}
        Remediation Effort: {finding.remediation_effort or 'Not specified'}
        """
        
        if scan_context:
            context += f"\nScan Context: {scan_context}"
        
        return context
    
    async def _generate_analysis(self, context: str) -> Dict[str, Any]:
        """Generate AI analysis using OpenAI"""
        start_time = time.time()
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a cybersecurity expert specializing in cloud security assessment and remediation. 
                        Analyze the provided security finding and provide:
                        1. Detailed analysis of the security risk
                        2. Improved remediation steps with specific commands
                        3. Risk assessment and business impact
                        4. Compliance implications
                        5. Confidence score (0-100)
                        
                        Format your response as JSON with the following structure:
                        {
                            "analysis": "Detailed analysis of the finding",
                            "remediation_steps": "Step-by-step remediation instructions",
                            "risk_assessment": "Risk level and business impact",
                            "compliance_implications": "Compliance framework implications",
                            "confidence": 85,
                            "suggested_actions": ["action1", "action2", "action3"]
                        }"""
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            # Parse AI response
            ai_response = response.choices[0].message.content
            parsed_response = self._parse_ai_response(ai_response)
            
            return {
                **parsed_response,
                "response_time_ms": response_time,
                "tokens_used": response.usage.total_tokens,
                "model_used": self.model
            }
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response and extract structured data"""
        try:
            # Try to extract JSON from response
            import json
            import re
            
            # Find JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return parsed
            
            # Fallback: return as plain text
            return {
                "analysis": response,
                "remediation_steps": "",
                "risk_assessment": "",
                "compliance_implications": "",
                "confidence": 50,
                "suggested_actions": []
            }
        except Exception:
            # Return fallback response
            return {
                "analysis": response,
                "remediation_steps": "",
                "risk_assessment": "",
                "compliance_implications": "",
                "confidence": 50,
                "suggested_actions": []
            }
    
    async def generate_chat_response(
        self, 
        query: str, 
        chat_history: List[ChatMessage],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate AI chat response"""
        try:
            # Prepare conversation history
            messages = self._prepare_chat_messages(query, chat_history, context)
            
            start_time = time.time()
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            ai_response = response.choices[0].message.content
            
            return {
                "response": ai_response,
                "tokens_used": response.usage.total_tokens,
                "model_used": self.model,
                "response_time_ms": response_time,
                "confidence_score": 0.8  # Default confidence
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Chat response generation failed: {str(e)}"
            )
    
    def _prepare_chat_messages(
        self, 
        query: str, 
        chat_history: List[ChatMessage],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """Prepare messages for AI chat"""
        messages = [
            {
                "role": "system",
                "content": """You are Securra, an AI-powered cloud security assistant. 
                You help users with:
                - Cloud security assessment questions
                - Security finding analysis and remediation
                - Compliance guidance
                - Best practices for cloud security
                
                Provide clear, actionable advice with specific steps when possible.
                Always prioritize security best practices and compliance requirements."""
            }
        ]
        
        # Add context if provided
        if context:
            context_str = self._format_context(context)
            messages.append({
                "role": "system",
                "content": f"Current context: {context_str}"
            })
        
        # Add chat history (last 10 messages to avoid token limits)
        for message in chat_history[-10:]:
            role = "user" if message.message_type == MessageType.USER else "assistant"
            messages.append({
                "role": role,
                "content": message.content
            })
        
        # Add current query
        messages.append({
            "role": "user",
            "content": query
        })
        
        return messages
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for AI consumption"""
        context_parts = []
        
        if "scan_id" in context:
            context_parts.append(f"Current scan: {context['scan_id']}")
        
        if "finding_id" in context:
            context_parts.append(f"Current finding: {context['finding_id']}")
        
        if "resource_type" in context:
            context_parts.append(f"Resource type: {context['resource_type']}")
        
        if "severity" in context:
            context_parts.append(f"Severity level: {context['severity']}")
        
        return "; ".join(context_parts) if context_parts else "No specific context"
    
    async def generate_remediation_plan(self, findings: List[Finding]) -> Dict[str, Any]:
        """Generate comprehensive remediation plan for multiple findings"""
        try:
            # Prepare findings summary
            findings_summary = self._prepare_findings_summary(findings)
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a cybersecurity expert creating a comprehensive remediation plan.
                        Analyze the provided security findings and create:
                        1. Prioritized remediation steps
                        2. Resource requirements
                        3. Timeline estimates
                        4. Risk mitigation strategies
                        5. Compliance considerations
                        
                        Format as JSON with structure:
                        {
                            "executive_summary": "High-level overview",
                            "prioritized_findings": [{"finding_id": "id", "priority": "high/medium/low", "effort": "hours"}],
                            "remediation_steps": ["step1", "step2"],
                            "timeline": "Estimated timeline",
                            "resources_needed": ["resource1", "resource2"],
                            "risk_mitigation": "Risk mitigation strategies",
                            "compliance_notes": "Compliance considerations"
                        }"""
                    },
                    {
                        "role": "user",
                        "content": findings_summary
                    }
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            ai_response = response.choices[0].message.content
            return self._parse_ai_response(ai_response)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Remediation plan generation failed: {str(e)}"
            )
    
    def _prepare_findings_summary(self, findings: List[Finding]) -> str:
        """Prepare summary of findings for AI analysis"""
        summary = f"Security Findings Summary (Total: {len(findings)})\n\n"
        
        for i, finding in enumerate(findings, 1):
            summary += f"""
            Finding {i}:
            - Title: {finding.title}
            - Severity: {finding.severity.value}
            - Category: {finding.category}
            - Resource: {finding.resource_name} ({finding.resource_type})
            - Description: {finding.description}
            - Current Remediation: {finding.remediation_steps or 'Not provided'}
            """
        
        return summary
    
    async def generate_response(
        self, 
        prompt: str, 
        context: str = "", 
        max_tokens: int = 800,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """Generate AI response for generic prompts"""
        try:
            start_time = time.time()
            
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert cloud security consultant. Provide detailed, actionable responses based on the given context and requirements."
                },
                {
                    "role": "user",
                    "content": f"Context: {context}\n\nRequest: {prompt}"
                }
            ]
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            response_time = int((time.time() - start_time) * 1000)
            ai_response = response.choices[0].message.content
            
            return {
                "response": ai_response,
                "tokens_used": response.usage.total_tokens,
                "model_used": self.model,
                "response_time_ms": response_time,
                "provider": "openai"
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI response generation failed: {str(e)}"
            )
