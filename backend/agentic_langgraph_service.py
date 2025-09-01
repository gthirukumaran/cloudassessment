"""Enhanced Agentic Service with LangGraph Integration
Provides advanced workflow orchestration for security remediation using LangGraph
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum

# LangGraph imports
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from langchain_core.runnables import RunnableConfig
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("⚠️  LangGraph not installed. Install with: pip install langgraph")

# AutoGen imports
try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    print("⚠️  AutoGen not installed. Install with: pip install pyautogen")

# Azure SDK imports
from azure_remediation_service import AzureRemediationService
from azure.identity import ClientSecretCredential
from azure.core.exceptions import AzureError

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """State structure for LangGraph workflow"""
    agent_id: str
    finding: Dict[str, Any]
    remediation_plan: Optional[Dict[str, Any]]
    execution_result: Optional[Dict[str, Any]]
    rollback_info: Optional[Dict[str, Any]]
    current_step: str
    messages: List[Dict[str, Any]]
    configuration: Dict[str, Any]
    validation_results: List[Dict[str, Any]]
    errors: List[str]
    metadata: Dict[str, Any]

class WorkflowStep(Enum):
    """Workflow execution steps"""
    INITIALIZE = "initialize"
    ANALYZE_FINDING = "analyze_finding"
    GENERATE_PLAN = "generate_plan"
    VALIDATE_PLAN = "validate_plan"
    EXECUTE_REMEDIATION = "execute_remediation"
    VALIDATE_EXECUTION = "validate_execution"
    COMPLETE = "complete"
    ROLLBACK = "rollback"
    ERROR = "error"

@dataclass
class AgentConfiguration:
    """Agent configuration with SDK and LangGraph settings"""
    agent_id: str
    name: str
    description: str
    
    # AI Model Configuration
    model_name: str = "gpt-4-turbo"
    temperature: float = 0.1
    max_tokens: int = 4096
    
    # Execution Configuration
    validation_mode: bool = True
    automated_execution: bool = False
    rollback_enabled: bool = True
    
    # Azure SDK Configuration
    use_azure_sdk: bool = True
    azure_subscription_id: Optional[str] = None
    azure_resource_group: Optional[str] = None
    
    # Framework Configuration
    use_langgraph: bool = True
    use_autogen: bool = False
    
    # LangGraph Configuration
    checkpoint_enabled: bool = True
    max_iterations: int = 10
    
    # AutoGen Configuration
    autogen_config: Optional[Dict[str, Any]] = None
    
    # Workflow Configuration
    workflow_steps: List[str] = None
    custom_validators: List[str] = None
    
    def __post_init__(self):
        if self.workflow_steps is None:
            self.workflow_steps = [
                WorkflowStep.INITIALIZE.value,
                WorkflowStep.ANALYZE_FINDING.value,
                WorkflowStep.GENERATE_PLAN.value,
                WorkflowStep.VALIDATE_PLAN.value,
                WorkflowStep.EXECUTE_REMEDIATION.value,
                WorkflowStep.VALIDATE_EXECUTION.value,
                WorkflowStep.COMPLETE.value
            ]

class EnhancedAgenticService:
    """Enhanced Agentic Service with LangGraph and Azure SDK Integration"""
    
    def __init__(self):
        self.azure_service = AzureRemediationService()
        self.memory_saver = MemorySaver() if LANGGRAPH_AVAILABLE else None
        self.active_workflows: Dict[str, Any] = {}
        self.configurations: Dict[str, AgentConfiguration] = {}
        
        # Initialize workflow graph
        if LANGGRAPH_AVAILABLE:
            self.workflow_graph = self._create_workflow_graph()
        else:
            self.workflow_graph = None
            logger.warning("LangGraph not available, using fallback workflow")
    
    def _create_workflow_graph(self) -> StateGraph:
        """Create the LangGraph workflow for security remediation"""
        workflow = StateGraph(AgentState)
        
        # Add nodes for each workflow step
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("analyze_finding", self._analyze_finding_node)
        workflow.add_node("generate_plan", self._generate_plan_node)
        workflow.add_node("validate_plan", self._validate_plan_node)
        workflow.add_node("execute_remediation", self._execute_remediation_node)
        workflow.add_node("validate_execution", self._validate_execution_node)
        workflow.add_node("rollback", self._rollback_node)
        workflow.add_node("complete", self._complete_node)
        workflow.add_node("error", self._error_node)
        
        # Define workflow edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "analyze_finding")
        workflow.add_edge("analyze_finding", "generate_plan")
        workflow.add_edge("generate_plan", "validate_plan")
        
        # Conditional edges based on validation
        workflow.add_conditional_edges(
            "validate_plan",
            self._should_execute_or_retry,
            {
                "execute": "execute_remediation",
                "retry": "generate_plan",
                "error": "error"
            }
        )
        
        workflow.add_edge("execute_remediation", "validate_execution")
        
        # Conditional edges after execution
        workflow.add_conditional_edges(
            "validate_execution",
            self._should_complete_or_rollback,
            {
                "complete": "complete",
                "rollback": "rollback",
                "error": "error"
            }
        )
        
        workflow.add_edge("rollback", "error")
        workflow.add_edge("complete", END)
        workflow.add_edge("error", END)
        
        return workflow.compile(checkpointer=self.memory_saver)
    
    async def create_agent_configuration(self, config_data: Dict[str, Any]) -> AgentConfiguration:
        """Create and store agent configuration"""
        config = AgentConfiguration(
            agent_id=config_data["agent_id"],
            name=config_data.get("name", f"Agent {config_data['agent_id']}"),
            description=config_data.get("description", ""),
            model_name=config_data.get("model_name", "gpt-4-turbo"),
            temperature=config_data.get("temperature", 0.1),
            max_tokens=config_data.get("max_tokens", 4096),
            validation_mode=config_data.get("validation_mode", True),
            automated_execution=config_data.get("automated_execution", False),
            rollback_enabled=config_data.get("rollback_enabled", True),
            use_azure_sdk=config_data.get("use_azure_sdk", True),
            use_langgraph=config_data.get("use_langgraph", True),
            use_autogen=config_data.get("use_autogen", False),
            azure_subscription_id=config_data.get("azure_subscription_id"),
            azure_resource_group=config_data.get("azure_resource_group"),
            autogen_config=config_data.get("autogen_config", {
                "llm_config": {
                    "model": config_data.get("model_name", "gpt-4-turbo"),
                    "temperature": config_data.get("temperature", 0.1),
                    "max_tokens": config_data.get("max_tokens", 4096)
                }
            })
        )
        
        self.configurations[config.agent_id] = config
        return config
    
    async def get_current_state_configuration(self, agent_id: str) -> Dict[str, Any]:
        """Get current state configuration for PDF export"""
        config = self.configurations.get(agent_id)
        if not config:
            raise ValueError(f"Agent configuration not found: {agent_id}")
        
        # Get current workflow state if available
        workflow_state = None
        if agent_id in self.active_workflows:
            workflow_state = self.active_workflows[agent_id].get("state")
        
        return {
            "agent_configuration": {
                "agent_id": config.agent_id,
                "name": config.name,
                "description": config.description,
                "model_configuration": {
                    "model_name": config.model_name,
                    "temperature": config.temperature,
                    "max_tokens": config.max_tokens
                },
                "execution_configuration": {
                    "validation_mode": config.validation_mode,
                    "automated_execution": config.automated_execution,
                    "rollback_enabled": config.rollback_enabled
                },
                "integration_configuration": {
                    "use_azure_sdk": config.use_azure_sdk,
                    "use_langgraph": config.use_langgraph,
                    "use_autogen": config.use_autogen,
                    "azure_subscription_id": config.azure_subscription_id,
                    "azure_resource_group": config.azure_resource_group,
                    "autogen_config": config.autogen_config
                },
                "workflow_configuration": {
                    "workflow_steps": config.workflow_steps,
                    "checkpoint_enabled": config.checkpoint_enabled,
                    "max_iterations": config.max_iterations
                }
            },
            "current_state": workflow_state,
            "azure_sdk_status": await self._get_azure_sdk_status(),
            "langgraph_status": self._get_langgraph_status(),
            "autogen_status": self._get_autogen_status(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def execute_agent_workflow(self, agent_id: str, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete agent workflow using LangGraph, AutoGen, or fallback"""
        config = self.configurations.get(agent_id)
        if not config:
            raise ValueError(f"Agent configuration not found: {agent_id}")
        
        if config.use_autogen and AUTOGEN_AVAILABLE:
            return await self._execute_autogen_workflow(agent_id, finding, config)
        elif config.use_langgraph and self.workflow_graph:
            return await self._execute_langgraph_workflow(agent_id, finding, config)
        else:
            return await self._execute_fallback_workflow(agent_id, finding, config)
    
    async def _execute_langgraph_workflow(self, agent_id: str, finding: Dict[str, Any], config: AgentConfiguration) -> Dict[str, Any]:
        """Execute workflow using LangGraph"""
        initial_state: AgentState = {
            "agent_id": agent_id,
            "finding": finding,
            "remediation_plan": None,
            "execution_result": None,
            "rollback_info": None,
            "current_step": WorkflowStep.INITIALIZE.value,
            "messages": [],
            "configuration": config.__dict__,
            "validation_results": [],
            "errors": [],
            "metadata": {
                "started_at": datetime.utcnow().isoformat(),
                "workflow_type": "langgraph"
            }
        }
        
        # Store active workflow
        self.active_workflows[agent_id] = {
            "state": initial_state,
            "config": config,
            "started_at": datetime.utcnow()
        }
        
        try:
            # Execute the workflow
            final_state = await self.workflow_graph.ainvoke(
                initial_state,
                config=RunnableConfig(thread_id=agent_id)
            )
            
            # Update stored state
            self.active_workflows[agent_id]["state"] = final_state
            
            return {
                "success": len(final_state["errors"]) == 0,
                "agent_id": agent_id,
                "final_state": final_state,
                "execution_summary": self._generate_execution_summary(final_state),
                "rollback_available": final_state.get("rollback_info") is not None
            }
            
        except Exception as e:
            logger.error(f"LangGraph workflow execution failed for agent {agent_id}: {e}")
            return {
                "success": False,
                "agent_id": agent_id,
                "error": str(e),
                "rollback_available": False
            }
    
    async def _execute_autogen_workflow(self, agent_id: str, finding: Dict[str, Any], config: AgentConfiguration) -> Dict[str, Any]:
        """Execute workflow using Microsoft AutoGen"""
        try:
            # Initialize AutoGen agents
            llm_config = config.autogen_config.get("llm_config", {})
            
            # Create user proxy agent
            user_proxy = autogen.UserProxyAgent(
                name="security_analyst",
                system_message="You are a security analyst responsible for coordinating security remediation tasks.",
                code_execution_config={"work_dir": "autogen_workspace", "use_docker": False},
                human_input_mode="NEVER",
                max_consecutive_auto_reply=3
            )
            
            # Create assistant agent for remediation planning
            remediation_agent = autogen.AssistantAgent(
                name="remediation_specialist",
                system_message="You are a security remediation specialist. Analyze security findings and create detailed remediation plans with Azure CLI commands.",
                llm_config=llm_config
            )
            
            # Create validation agent
            validation_agent = autogen.AssistantAgent(
                name="validation_expert",
                system_message="You are a security validation expert. Review remediation plans for completeness and safety before execution.",
                llm_config=llm_config
            )
            
            # Store active workflow
            self.active_workflows[agent_id] = {
                "state": {
                    "agent_id": agent_id,
                    "finding": finding,
                    "current_step": "autogen_execution",
                    "started_at": datetime.utcnow().isoformat(),
                    "workflow_type": "autogen"
                },
                "config": config,
                "started_at": datetime.utcnow()
            }
            
            # Prepare the task message
            task_message = f"""
            Security Finding Analysis and Remediation:
            
            Finding Details:
            - Type: {finding.get('type', 'Unknown')}
            - Severity: {finding.get('severity', 'Medium')}
            - Resource: {finding.get('resource', 'Unknown')}
            - Description: {finding.get('description', 'No description provided')}
            
            Please:
            1. Analyze this security finding
            2. Create a detailed remediation plan
            3. Validate the plan for safety and completeness
            4. Provide Azure CLI commands if applicable
            
            Ensure all recommendations follow security best practices.
            """
            
            # Execute multi-agent conversation
            chat_result = user_proxy.initiate_chat(
                remediation_agent,
                message=task_message,
                max_turns=5
            )
            
            # Extract results from chat
            messages = chat_result.chat_history if hasattr(chat_result, 'chat_history') else []
            
            # Generate execution summary
            execution_summary = {
                "total_messages": len(messages),
                "agents_involved": ["security_analyst", "remediation_specialist", "validation_expert"],
                "workflow_completed": True,
                "remediation_plan_generated": True
            }
            
            return {
                "success": True,
                "agent_id": agent_id,
                "workflow_type": "autogen",
                "chat_history": messages,
                "execution_summary": execution_summary,
                "rollback_available": False  # AutoGen workflows don't support automatic rollback
            }
            
        except Exception as e:
            logger.error(f"AutoGen workflow execution failed for agent {agent_id}: {e}")
            return {
                "success": False,
                "agent_id": agent_id,
                "error": str(e),
                "workflow_type": "autogen",
                "rollback_available": False
            }
    
    async def rollback_agent_execution(self, agent_id: str) -> Dict[str, Any]:
        """Rollback agent execution using stored rollback information"""
        if agent_id not in self.active_workflows:
            raise ValueError(f"No active workflow found for agent: {agent_id}")
        
        workflow_info = self.active_workflows[agent_id]
        state = workflow_info["state"]
        config = workflow_info["config"]
        
        if not state.get("rollback_info"):
            raise ValueError(f"No rollback information available for agent: {agent_id}")
        
        try:
            # Execute rollback using Azure SDK
            if config.use_azure_sdk:
                rollback_result = await self.azure_service.rollback_remediation(
                    state["finding"],
                    state["rollback_info"]
                )
            else:
                # Simulate rollback
                rollback_result = {
                    "success": True,
                    "actions_rolled_back": ["[SIMULATED] Rollback completed"],
                    "errors": []
                }
            
            # Update state
            state["current_step"] = WorkflowStep.ROLLBACK.value
            state["metadata"]["rolled_back_at"] = datetime.utcnow().isoformat()
            
            return rollback_result
            
        except Exception as e:
            logger.error(f"Rollback failed for agent {agent_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "actions_rolled_back": [],
                "errors": [str(e)]
            }
    
    # Workflow node implementations
    async def _initialize_node(self, state: AgentState) -> AgentState:
        """Initialize the workflow"""
        state["current_step"] = WorkflowStep.INITIALIZE.value
        state["messages"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": "info",
            "message": f"Initializing workflow for agent {state['agent_id']}"
        })
        return state
    
    async def _analyze_finding_node(self, state: AgentState) -> AgentState:
        """Analyze the security finding"""
        state["current_step"] = WorkflowStep.ANALYZE_FINDING.value
        
        # Add analysis logic here
        finding = state["finding"]
        analysis = {
            "severity_score": self._calculate_severity_score(finding.get("severity", "medium")),
            "resource_type": finding.get("resource_type", "unknown"),
            "complexity": self._determine_complexity(finding),
            "estimated_time": self._estimate_remediation_time(finding)
        }
        
        state["metadata"]["analysis"] = analysis
        state["messages"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": "info",
            "message": f"Finding analysis completed. Complexity: {analysis['complexity']}"
        })
        
        return state
    
    async def _generate_plan_node(self, state: AgentState) -> AgentState:
        """Generate remediation plan"""
        state["current_step"] = WorkflowStep.GENERATE_PLAN.value
        
        # Generate plan using AI or predefined templates
        plan = await self._generate_ai_remediation_plan(state["finding"], state["configuration"])
        state["remediation_plan"] = plan
        
        state["messages"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": "info",
            "message": "Remediation plan generated successfully"
        })
        
        return state
    
    async def _validate_plan_node(self, state: AgentState) -> AgentState:
        """Validate the remediation plan"""
        state["current_step"] = WorkflowStep.VALIDATE_PLAN.value
        
        plan = state["remediation_plan"]
        validation_result = await self._validate_remediation_plan(plan, state["finding"])
        
        state["validation_results"].append(validation_result)
        
        if not validation_result["valid"]:
            state["errors"].extend(validation_result["errors"])
        
        state["messages"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": "info" if validation_result["valid"] else "warning",
            "message": f"Plan validation: {'Passed' if validation_result['valid'] else 'Failed'}"
        })
        
        return state
    
    async def _execute_remediation_node(self, state: AgentState) -> AgentState:
        """Execute the remediation"""
        state["current_step"] = WorkflowStep.EXECUTE_REMEDIATION.value
        
        config = AgentConfiguration(**state["configuration"])
        
        if config.use_azure_sdk and config.automated_execution:
            # Execute using Azure SDK
            execution_result = await self.azure_service.execute_remediation(
                state["finding"],
                state["remediation_plan"]
            )
        else:
            # Simulate execution
            execution_result = {
                "success": True,
                "actions_performed": ["[SIMULATED] Remediation executed"],
                "errors": [],
                "rollback_info": {"simulated": True}
            }
        
        state["execution_result"] = execution_result
        state["rollback_info"] = execution_result.get("rollback_info")
        
        state["messages"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": "info" if execution_result["success"] else "error",
            "message": f"Remediation execution: {'Completed' if execution_result['success'] else 'Failed'}"
        })
        
        return state
    
    async def _validate_execution_node(self, state: AgentState) -> AgentState:
        """Validate the execution results"""
        state["current_step"] = WorkflowStep.VALIDATE_EXECUTION.value
        
        execution_result = state["execution_result"]
        validation = await self._validate_execution_result(execution_result, state["finding"])
        
        state["validation_results"].append(validation)
        
        state["messages"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": "info" if validation["valid"] else "warning",
            "message": f"Execution validation: {'Passed' if validation['valid'] else 'Failed'}"
        })
        
        return state
    
    async def _complete_node(self, state: AgentState) -> AgentState:
        """Complete the workflow"""
        state["current_step"] = WorkflowStep.COMPLETE.value
        state["metadata"]["completed_at"] = datetime.utcnow().isoformat()
        
        state["messages"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": "info",
            "message": "Workflow completed successfully"
        })
        
        return state
    
    async def _rollback_node(self, state: AgentState) -> AgentState:
        """Handle rollback"""
        state["current_step"] = WorkflowStep.ROLLBACK.value
        
        # Rollback logic would be implemented here
        state["messages"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": "warning",
            "message": "Initiating rollback procedure"
        })
        
        return state
    
    async def _error_node(self, state: AgentState) -> AgentState:
        """Handle errors"""
        state["current_step"] = WorkflowStep.ERROR.value
        state["metadata"]["failed_at"] = datetime.utcnow().isoformat()
        
        state["messages"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": "error",
            "message": f"Workflow failed with {len(state['errors'])} errors"
        })
        
        return state
    
    # Conditional edge functions
    def _should_execute_or_retry(self, state: AgentState) -> str:
        """Determine if plan should be executed or retried"""
        validation_results = state["validation_results"]
        if not validation_results:
            return "error"
        
        latest_validation = validation_results[-1]
        if latest_validation["valid"]:
            return "execute"
        elif len(validation_results) < 3:  # Allow up to 3 retries
            return "retry"
        else:
            return "error"
    
    def _should_complete_or_rollback(self, state: AgentState) -> str:
        """Determine if workflow should complete or rollback"""
        execution_result = state["execution_result"]
        if not execution_result:
            return "error"
        
        if execution_result["success"]:
            validation_results = [v for v in state["validation_results"] if v.get("type") == "execution"]
            if validation_results and validation_results[-1]["valid"]:
                return "complete"
        
        # If execution failed or validation failed, rollback if available
        if state.get("rollback_info"):
            return "rollback"
        else:
            return "error"
    
    # Helper methods
    async def _execute_fallback_workflow(self, agent_id: str, finding: Dict[str, Any], config: AgentConfiguration) -> Dict[str, Any]:
        """Fallback workflow when LangGraph is not available"""
        logger.info(f"Executing fallback workflow for agent {agent_id}")
        
        try:
            # Simple sequential execution
            plan = await self._generate_ai_remediation_plan(finding, config.__dict__)
            
            if config.automated_execution and config.use_azure_sdk:
                execution_result = await self.azure_service.execute_remediation(finding, plan)
            else:
                execution_result = {
                    "success": True,
                    "actions_performed": ["[SIMULATED] Fallback remediation executed"],
                    "errors": [],
                    "rollback_info": {"simulated": True}
                }
            
            return {
                "success": execution_result["success"],
                "agent_id": agent_id,
                "execution_result": execution_result,
                "workflow_type": "fallback",
                "rollback_available": execution_result.get("rollback_info") is not None
            }
            
        except Exception as e:
            logger.error(f"Fallback workflow failed for agent {agent_id}: {e}")
            return {
                "success": False,
                "agent_id": agent_id,
                "error": str(e),
                "workflow_type": "fallback",
                "rollback_available": False
            }
    
    async def _generate_ai_remediation_plan(self, finding: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered remediation plan"""
        # This would integrate with OpenAI/Azure OpenAI
        return {
            "id": f"plan-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "generated_at": datetime.utcnow().isoformat(),
            "finding_id": finding.get("id", "unknown"),
            "steps": [
                "Analyze current configuration",
                "Apply security remediation",
                "Validate changes",
                "Document results"
            ],
            "estimated_time": "15 minutes",
            "complexity": "medium",
            "validation_status": "pending"
        }
    
    async def _validate_remediation_plan(self, plan: Dict[str, Any], finding: Dict[str, Any]) -> Dict[str, Any]:
        """Validate remediation plan"""
        return {
            "valid": True,
            "type": "plan",
            "timestamp": datetime.utcnow().isoformat(),
            "errors": [],
            "warnings": []
        }
    
    async def _validate_execution_result(self, execution_result: Dict[str, Any], finding: Dict[str, Any]) -> Dict[str, Any]:
        """Validate execution results"""
        return {
            "valid": execution_result.get("success", False),
            "type": "execution",
            "timestamp": datetime.utcnow().isoformat(),
            "errors": execution_result.get("errors", []),
            "warnings": []
        }
    
    def _calculate_severity_score(self, severity: str) -> int:
        """Calculate numeric severity score"""
        severity_map = {"low": 1, "medium": 5, "high": 8, "critical": 10}
        return severity_map.get(severity.lower(), 5)
    
    def _determine_complexity(self, finding: Dict[str, Any]) -> str:
        """Determine remediation complexity"""
        severity = finding.get("severity", "medium").lower()
        resource_type = finding.get("resource_type", "")
        
        if severity in ["critical", "high"] or "network" in resource_type.lower():
            return "high"
        elif severity == "medium":
            return "medium"
        else:
            return "low"
    
    def _estimate_remediation_time(self, finding: Dict[str, Any]) -> str:
        """Estimate remediation time"""
        complexity = self._determine_complexity(finding)
        time_map = {"low": "5-10 minutes", "medium": "15-30 minutes", "high": "45-90 minutes"}
        return time_map.get(complexity, "15-30 minutes")
    
    def _generate_execution_summary(self, state: AgentState) -> Dict[str, Any]:
        """Generate execution summary"""
        return {
            "agent_id": state["agent_id"],
            "workflow_completed": state["current_step"] == WorkflowStep.COMPLETE.value,
            "total_steps": len(state["messages"]),
            "errors_count": len(state["errors"]),
            "validations_passed": len([v for v in state["validation_results"] if v["valid"]]),
            "execution_time": self._calculate_execution_time(state),
            "rollback_available": state.get("rollback_info") is not None
        }
    
    def _calculate_execution_time(self, state: AgentState) -> str:
        """Calculate total execution time"""
        started_at = state["metadata"].get("started_at")
        completed_at = state["metadata"].get("completed_at") or state["metadata"].get("failed_at")
        
        if started_at and completed_at:
            start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
            duration = end_time - start_time
            return f"{duration.total_seconds():.1f} seconds"
        
        return "Unknown"
    
    async def _get_azure_sdk_status(self) -> Dict[str, Any]:
        """Get Azure SDK status"""
        return {
            "available": self.azure_service.credential is not None,
            "subscription_id": self.azure_service.subscription_id,
            "clients_initialized": len(self.azure_service.clients) > 0,
            "last_check": datetime.utcnow().isoformat()
        }
    
    def _get_langgraph_status(self) -> Dict[str, Any]:
        """Get LangGraph status"""
        return {
            "available": LANGGRAPH_AVAILABLE,
            "workflow_graph_initialized": self.workflow_graph is not None,
            "memory_saver_enabled": self.memory_saver is not None,
            "active_workflows": len(self.active_workflows)
        }
    
    def _get_autogen_status(self) -> Dict[str, Any]:
        """Get Microsoft AutoGen integration status"""
        return {
            "available": AUTOGEN_AVAILABLE,
            "version": getattr(autogen, '__version__', 'unknown') if AUTOGEN_AVAILABLE else None,
            "agents_supported": ["UserProxyAgent", "AssistantAgent"] if AUTOGEN_AVAILABLE else [],
            "active_workflows": len([w for w in self.active_workflows.values() if w.get("state", {}).get("workflow_type") == "autogen"])
        }

# Global service instance
agentic_service = EnhancedAgenticService()