"""PDF Configuration Export Service
Generates PDF reports for agent configurations and current state
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from io import BytesIO

# PDF generation imports
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor, black, blue, red, green
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.platypus.tableofcontents import TableOfContents
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️  ReportLab not installed. Install with: pip install reportlab")

logger = logging.getLogger(__name__)

class PDFConfigurationService:
    """Service for generating PDF configuration reports"""
    
    def __init__(self):
        self.styles = None
        self.custom_styles = {}
        if REPORTLAB_AVAILABLE:
            self._initialize_styles()
    
    def _initialize_styles(self):
        """Initialize PDF styles"""
        self.styles = getSampleStyleSheet()
        
        # Custom styles
        self.custom_styles['title'] = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=HexColor('#2E86AB'),
            alignment=TA_CENTER
        )
        
        self.custom_styles['heading1'] = ParagraphStyle(
            'CustomHeading1',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            spaceBefore=20,
            textColor=HexColor('#A23B72'),
            borderWidth=1,
            borderColor=HexColor('#A23B72'),
            borderPadding=5
        )
        
        self.custom_styles['heading2'] = ParagraphStyle(
            'CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12,
            textColor=HexColor('#F18F01')
        )
        
        self.custom_styles['code'] = ParagraphStyle(
            'Code',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Courier',
            backgroundColor=HexColor('#F5F5F5'),
            borderWidth=1,
            borderColor=HexColor('#CCCCCC'),
            borderPadding=5,
            leftIndent=10,
            rightIndent=10
        )
        
        self.custom_styles['status_success'] = ParagraphStyle(
            'StatusSuccess',
            parent=self.styles['Normal'],
            textColor=green,
            fontSize=12,
            fontName='Helvetica-Bold'
        )
        
        self.custom_styles['status_error'] = ParagraphStyle(
            'StatusError',
            parent=self.styles['Normal'],
            textColor=red,
            fontSize=12,
            fontName='Helvetica-Bold'
        )
        
        self.custom_styles['status_warning'] = ParagraphStyle(
            'StatusWarning',
            parent=self.styles['Normal'],
            textColor=HexColor('#FF8C00'),
            fontSize=12,
            fontName='Helvetica-Bold'
        )
    
    async def generate_configuration_pdf(self, config_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """Generate PDF configuration report"""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab")
        
        # Generate filename if not provided
        if not output_path:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            agent_id = config_data.get('agent_configuration', {}).get('agent_id', 'unknown')
            output_path = f"d:\\AI project\\security assessment\\backend\\exports\\agent_config_{agent_id}_{timestamp}.pdf"
        
        # Ensure export directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build PDF content
        story = []
        
        # Title page
        story.extend(self._create_title_page(config_data))
        story.append(PageBreak())
        
        # Table of contents
        story.extend(self._create_table_of_contents())
        story.append(PageBreak())
        
        # Executive summary
        story.extend(self._create_executive_summary(config_data))
        story.append(PageBreak())
        
        # Agent configuration section
        story.extend(self._create_agent_configuration_section(config_data))
        story.append(PageBreak())
        
        # Current state section
        story.extend(self._create_current_state_section(config_data))
        story.append(PageBreak())
        
        # Integration status section
        story.extend(self._create_integration_status_section(config_data))
        story.append(PageBreak())
        
        # Workflow configuration section
        story.extend(self._create_workflow_configuration_section(config_data))
        story.append(PageBreak())
        
        # Appendices
        story.extend(self._create_appendices(config_data))
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"PDF configuration report generated: {output_path}")
        return output_path
    
    def _create_title_page(self, config_data: Dict[str, Any]) -> List[Any]:
        """Create title page"""
        story = []
        
        # Main title
        story.append(Paragraph("Agentic Security Assessment", self.custom_styles['title']))
        story.append(Spacer(1, 0.5*inch))
        
        # Subtitle
        agent_config = config_data.get('agent_configuration', {})
        agent_name = agent_config.get('name', 'Unknown Agent')
        story.append(Paragraph(f"Configuration Report: {agent_name}", self.styles['Heading2']))
        story.append(Spacer(1, 0.3*inch))
        
        # Report details
        report_info = [
            ["Agent ID:", agent_config.get('agent_id', 'N/A')],
            ["Generated:", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')],
            ["Report Type:", "Current State Configuration"],
            ["Integration:", "Azure SDK + LangGraph"],
            ["Version:", "1.0.0"]
        ]
        
        table = Table(report_info, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#CCCCCC'))
        ]))
        
        story.append(table)
        story.append(Spacer(1, 1*inch))
        
        # Description
        description = f"""
        This report provides a comprehensive overview of the current configuration state for the 
        agentic security assessment system. It includes detailed information about agent settings, 
        integration status, workflow configuration, and execution capabilities.
        
        The system integrates both Azure SDK for direct cloud resource management and LangGraph 
        for advanced workflow orchestration, providing a robust platform for automated security 
        remediation with rollback capabilities.
        """
        
        story.append(Paragraph(description, self.styles['Normal']))
        
        return story
    
    def _create_table_of_contents(self) -> List[Any]:
        """Create table of contents"""
        story = []
        
        story.append(Paragraph("Table of Contents", self.custom_styles['heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        toc_items = [
            "1. Executive Summary",
            "2. Agent Configuration",
            "   2.1 Basic Settings",
            "   2.2 AI Model Configuration",
            "   2.3 Execution Configuration",
            "3. Current State",
            "   3.1 Workflow Status",
            "   3.2 Active Sessions",
            "4. Integration Status",
            "   4.1 Azure SDK Status",
            "   4.2 LangGraph Status",
            "5. Workflow Configuration",
            "   5.1 Workflow Steps",
            "   5.2 Validation Rules",
            "   5.3 Rollback Configuration",
            "6. Appendices",
            "   6.1 Raw Configuration Data",
            "   6.2 System Requirements",
            "   6.3 Troubleshooting Guide"
        ]
        
        for item in toc_items:
            story.append(Paragraph(item, self.styles['Normal']))
            story.append(Spacer(1, 6))
        
        return story
    
    def _create_executive_summary(self, config_data: Dict[str, Any]) -> List[Any]:
        """Create executive summary"""
        story = []
        
        story.append(Paragraph("1. Executive Summary", self.custom_styles['heading1']))
        
        agent_config = config_data.get('agent_configuration', {})
        current_state = config_data.get('current_state')
        azure_status = config_data.get('azure_sdk_status', {})
        langgraph_status = config_data.get('langgraph_status', {})
        
        # Summary table
        summary_data = [
            ["Configuration Item", "Status", "Details"],
            ["Agent Status", self._get_status_text(True), f"Agent {agent_config.get('agent_id', 'N/A')} configured"],
            ["Azure SDK", self._get_status_text(azure_status.get('available', False)), 
             f"Subscription: {azure_status.get('subscription_id', 'Not configured')}"],
            ["LangGraph", self._get_status_text(langgraph_status.get('available', False)), 
             f"Workflow: {'Initialized' if langgraph_status.get('workflow_graph_initialized') else 'Not initialized'}"],
            ["Validation Mode", self._get_status_text(agent_config.get('validation_mode', False)), 
             "Enabled" if agent_config.get('validation_mode') else "Disabled"],
            ["Rollback Capability", self._get_status_text(agent_config.get('rollback_enabled', False)), 
             "Enabled" if agent_config.get('rollback_enabled') else "Disabled"]
        ]
        
        table = Table(summary_data, colWidths=[2*inch, 1*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2E86AB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#CCCCCC'))
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
        
        # Key highlights
        story.append(Paragraph("Key Highlights:", self.custom_styles['heading2']))
        
        highlights = [
            f"• Agent configured with {agent_config.get('model_name', 'default')} AI model",
            f"• {'Automated' if agent_config.get('automated_execution') else 'Manual'} execution mode",
            f"• {len(agent_config.get('workflow_steps', []))} workflow steps configured",
            f"• Integration status: Azure SDK ({'✓' if azure_status.get('available') else '✗'}), LangGraph ({'✓' if langgraph_status.get('available') else '✗'})",
            f"• Current active workflows: {langgraph_status.get('active_workflows', 0)}"
        ]
        
        for highlight in highlights:
            story.append(Paragraph(highlight, self.styles['Normal']))
            story.append(Spacer(1, 6))
        
        return story
    
    def _create_agent_configuration_section(self, config_data: Dict[str, Any]) -> List[Any]:
        """Create agent configuration section"""
        story = []
        
        story.append(Paragraph("2. Agent Configuration", self.custom_styles['heading1']))
        
        agent_config = config_data.get('agent_configuration', {})
        
        # Basic settings
        story.append(Paragraph("2.1 Basic Settings", self.custom_styles['heading2']))
        
        basic_data = [
            ["Setting", "Value"],
            ["Agent ID", agent_config.get('agent_id', 'N/A')],
            ["Name", agent_config.get('name', 'N/A')],
            ["Description", agent_config.get('description', 'No description provided')]
        ]
        
        table = Table(basic_data, colWidths=[2*inch, 3*inch])
        table.setStyle(self._get_standard_table_style())
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
        
        # AI Model configuration
        story.append(Paragraph("2.2 AI Model Configuration", self.custom_styles['heading2']))
        
        model_config = agent_config.get('model_configuration', {})
        model_data = [
            ["Setting", "Value"],
            ["Model Name", model_config.get('model_name', agent_config.get('model_name', 'N/A'))],
            ["Temperature", str(model_config.get('temperature', agent_config.get('temperature', 'N/A')))],
            ["Max Tokens", str(model_config.get('max_tokens', agent_config.get('max_tokens', 'N/A')))]
        ]
        
        table = Table(model_data, colWidths=[2*inch, 3*inch])
        table.setStyle(self._get_standard_table_style())
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
        
        # Execution configuration
        story.append(Paragraph("2.3 Execution Configuration", self.custom_styles['heading2']))
        
        exec_config = agent_config.get('execution_configuration', {})
        exec_data = [
            ["Setting", "Value"],
            ["Validation Mode", "Enabled" if exec_config.get('validation_mode', agent_config.get('validation_mode')) else "Disabled"],
            ["Automated Execution", "Enabled" if exec_config.get('automated_execution', agent_config.get('automated_execution')) else "Disabled"],
            ["Rollback Enabled", "Enabled" if exec_config.get('rollback_enabled', agent_config.get('rollback_enabled')) else "Disabled"]
        ]
        
        table = Table(exec_data, colWidths=[2*inch, 3*inch])
        table.setStyle(self._get_standard_table_style())
        story.append(table)
        
        return story
    
    def _create_current_state_section(self, config_data: Dict[str, Any]) -> List[Any]:
        """Create current state section"""
        story = []
        
        story.append(Paragraph("3. Current State", self.custom_styles['heading1']))
        
        current_state = config_data.get('current_state')
        
        if current_state:
            # Workflow status
            story.append(Paragraph("3.1 Workflow Status", self.custom_styles['heading2']))
            
            workflow_data = [
                ["Property", "Value"],
                ["Agent ID", current_state.get('agent_id', 'N/A')],
                ["Current Step", current_state.get('current_step', 'N/A')],
                ["Messages Count", str(len(current_state.get('messages', [])))],
                ["Errors Count", str(len(current_state.get('errors', [])))],
                ["Validation Results", str(len(current_state.get('validation_results', [])))]
            ]
            
            table = Table(workflow_data, colWidths=[2*inch, 3*inch])
            table.setStyle(self._get_standard_table_style())
            story.append(table)
            story.append(Spacer(1, 0.2*inch))
            
            # Recent messages
            messages = current_state.get('messages', [])
            if messages:
                story.append(Paragraph("Recent Messages:", self.styles['Heading3']))
                for msg in messages[-5:]:  # Show last 5 messages
                    timestamp = msg.get('timestamp', 'Unknown')
                    level = msg.get('level', 'info')
                    message = msg.get('message', '')
                    
                    style = self.styles['Normal']
                    if level == 'error':
                        style = self.custom_styles['status_error']
                    elif level == 'warning':
                        style = self.custom_styles['status_warning']
                    
                    story.append(Paragraph(f"[{timestamp}] {level.upper()}: {message}", style))
                    story.append(Spacer(1, 6))
        else:
            story.append(Paragraph("No active workflow state available.", self.styles['Normal']))
        
        return story
    
    def _create_integration_status_section(self, config_data: Dict[str, Any]) -> List[Any]:
        """Create integration status section"""
        story = []
        
        story.append(Paragraph("4. Integration Status", self.custom_styles['heading1']))
        
        # Azure SDK status
        story.append(Paragraph("4.1 Azure SDK Status", self.custom_styles['heading2']))
        
        azure_status = config_data.get('azure_sdk_status', {})
        azure_data = [
            ["Property", "Status", "Details"],
            ["Available", self._get_status_text(azure_status.get('available', False)), 
             "SDK initialized" if azure_status.get('available') else "Not configured"],
            ["Subscription ID", "Configured" if azure_status.get('subscription_id') else "Not set", 
             azure_status.get('subscription_id', 'N/A')],
            ["Clients Initialized", self._get_status_text(azure_status.get('clients_initialized', False)), 
             "Ready for operations" if azure_status.get('clients_initialized') else "Not initialized"],
            ["Last Check", "Recent", azure_status.get('last_check', 'N/A')]
        ]
        
        table = Table(azure_data, colWidths=[1.5*inch, 1*inch, 2.5*inch])
        table.setStyle(self._get_standard_table_style())
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
        
        # LangGraph status
        story.append(Paragraph("4.2 LangGraph Status", self.custom_styles['heading2']))
        
        langgraph_status = config_data.get('langgraph_status', {})
        langgraph_data = [
            ["Property", "Status", "Details"],
            ["Available", self._get_status_text(langgraph_status.get('available', False)), 
             "Library installed" if langgraph_status.get('available') else "Not installed"],
            ["Workflow Graph", self._get_status_text(langgraph_status.get('workflow_graph_initialized', False)), 
             "Initialized" if langgraph_status.get('workflow_graph_initialized') else "Not initialized"],
            ["Memory Saver", self._get_status_text(langgraph_status.get('memory_saver_enabled', False)), 
             "Enabled" if langgraph_status.get('memory_saver_enabled') else "Disabled"],
            ["Active Workflows", "Info", str(langgraph_status.get('active_workflows', 0))]
        ]
        
        table = Table(langgraph_data, colWidths=[1.5*inch, 1*inch, 2.5*inch])
        table.setStyle(self._get_standard_table_style())
        story.append(table)
        
        return story
    
    def _create_workflow_configuration_section(self, config_data: Dict[str, Any]) -> List[Any]:
        """Create workflow configuration section"""
        story = []
        
        story.append(Paragraph("5. Workflow Configuration", self.custom_styles['heading1']))
        
        agent_config = config_data.get('agent_configuration', {})
        workflow_config = agent_config.get('workflow_configuration', {})
        
        # Workflow steps
        story.append(Paragraph("5.1 Workflow Steps", self.custom_styles['heading2']))
        
        workflow_steps = workflow_config.get('workflow_steps', agent_config.get('workflow_steps', []))
        if workflow_steps:
            for i, step in enumerate(workflow_steps, 1):
                story.append(Paragraph(f"{i}. {step.replace('_', ' ').title()}", self.styles['Normal']))
                story.append(Spacer(1, 6))
        else:
            story.append(Paragraph("No workflow steps configured.", self.styles['Normal']))
        
        story.append(Spacer(1, 0.2*inch))
        
        # Configuration details
        story.append(Paragraph("5.2 Configuration Details", self.custom_styles['heading2']))
        
        config_data_table = [
            ["Setting", "Value"],
            ["Checkpoint Enabled", "Yes" if workflow_config.get('checkpoint_enabled', agent_config.get('checkpoint_enabled')) else "No"],
            ["Max Iterations", str(workflow_config.get('max_iterations', agent_config.get('max_iterations', 'N/A')))],
            ["Custom Validators", str(len(workflow_config.get('custom_validators', agent_config.get('custom_validators', []))))]
        ]
        
        table = Table(config_data_table, colWidths=[2*inch, 3*inch])
        table.setStyle(self._get_standard_table_style())
        story.append(table)
        
        return story
    
    def _create_appendices(self, config_data: Dict[str, Any]) -> List[Any]:
        """Create appendices"""
        story = []
        
        story.append(Paragraph("6. Appendices", self.custom_styles['heading1']))
        
        # Raw configuration data
        story.append(Paragraph("6.1 Raw Configuration Data", self.custom_styles['heading2']))
        
        # Format JSON data for display
        json_data = json.dumps(config_data, indent=2, default=str)
        
        # Split into chunks to avoid overly long paragraphs
        lines = json_data.split('\n')
        chunk_size = 50
        
        for i in range(0, len(lines), chunk_size):
            chunk = '\n'.join(lines[i:i+chunk_size])
            story.append(Paragraph(f"<pre>{chunk}</pre>", self.custom_styles['code']))
            story.append(Spacer(1, 0.1*inch))
        
        story.append(PageBreak())
        
        # System requirements
        story.append(Paragraph("6.2 System Requirements", self.custom_styles['heading2']))
        
        requirements = [
            "• Python 3.8 or higher",
            "• Azure SDK for Python (azure-identity, azure-mgmt-*)",
            "• LangGraph (optional, for advanced workflows)",
            "• OpenAI or Azure OpenAI API access",
            "• Valid Azure credentials (Client ID, Client Secret, Tenant ID)",
            "• Network access to Azure APIs",
            "• Sufficient permissions for resource management"
        ]
        
        for req in requirements:
            story.append(Paragraph(req, self.styles['Normal']))
            story.append(Spacer(1, 6))
        
        story.append(Spacer(1, 0.2*inch))
        
        # Troubleshooting guide
        story.append(Paragraph("6.3 Troubleshooting Guide", self.custom_styles['heading2']))
        
        troubleshooting = [
            ("Azure SDK not available", "Ensure Azure credentials are properly configured in environment variables or Azure CLI"),
            ("LangGraph not working", "Install LangGraph with: pip install langgraph"),
            ("Workflow execution fails", "Check agent configuration and ensure all required parameters are set"),
            ("PDF generation fails", "Install ReportLab with: pip install reportlab"),
            ("API connection errors", "Verify network connectivity and API endpoints")
        ]
        
        for issue, solution in troubleshooting:
            story.append(Paragraph(f"<b>Issue:</b> {issue}", self.styles['Normal']))
            story.append(Paragraph(f"<b>Solution:</b> {solution}", self.styles['Normal']))
            story.append(Spacer(1, 12))
        
        return story
    
    def _get_status_text(self, status: bool) -> str:
        """Get status text with color"""
        return "✓ Active" if status else "✗ Inactive"
    
    def _get_standard_table_style(self) -> TableStyle:
        """Get standard table style"""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#F0F0F0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#CCCCCC'))
        ])

# Global service instance
pdf_service = PDFConfigurationService()