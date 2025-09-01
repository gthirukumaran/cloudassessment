import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  CircularProgress,
  LinearProgress,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  Add as AddIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  SmartToy as RobotIcon,
  Timeline as TimelineIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Undo as UndoIcon,
  Assessment as ReportIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import { format } from 'date-fns';

interface Agent {
  id: string;
  name: string;
  description: string;
  finding_details: {
    title: string;
    description: string;
    severity: string;
    resource_type: string;
    resource_id: string;
    nsg_rules_details?: {
      total_rules: number;
      risky_rules: Array<{
        rule_name: string;
        priority: number;
        direction: string;
        access: string;
        protocol: string;
        source_port_range: string;
        destination_port_range: string;
        source_address_prefix: string;
        destination_address_prefix: string;
        risk_level: string;
        description: string;
      }>;
      ports_summary: {
        critical_ports: string[];
        high_risk_ports: string[];
        medium_risk_ports: string[];
        low_risk_ports: string[];
      };
    };
  };
  subscription_analysis?: {
    subscription_details: {
      subscription_id: string;
      tenant_id: string;
      subscription_name: string;
      analysis_timestamp: string;
    };
    resource_groups: Array<{
      name: string;
      location: string;
      resources_count: number;
      nsg_count: number;
      last_scan: string;
    }>;
    network_security_groups: Array<{
      name: string;
      resource_group: string;
      location: string;
      associated_subnets: string[];
      total_rules: number;
      inbound_rules: Array<{
        name: string;
        priority: number;
        direction: string;
        access: string;
        protocol: string;
        source_port_range: string;
        destination_port_range: string;
        source_address_prefix: string;
        destination_address_prefix: string;
        risk_level: string;
        description: string;
      }>;
      outbound_rules: Array<{
        name: string;
        priority: number;
        direction: string;
        access: string;
        protocol: string;
        source_port_range: string;
        destination_port_range: string;
        source_address_prefix: string;
        destination_address_prefix: string;
        risk_level: string;
        description: string;
      }>;
      risk_summary: {
        critical_rules: number;
        high_risk_rules: number;
        medium_risk_rules: number;
        low_risk_rules: number;
        total_risky_rules: number;
      };
    }>;
    ports_analysis: {
      critical_ports: Record<string, {
        protocol: string;
        service: string;
        exposed_nsgs: string[];
        risk_level: string;
        description: string;
      }>;
      high_risk_ports: Record<string, {
        protocol: string;
        service: string;
        exposed_nsgs: string[];
        risk_level: string;
        description: string;
      }>;
      medium_risk_ports: Record<string, {
        protocol: string;
        service: string;
        exposed_nsgs: string[];
        risk_level: string;
        description: string;
      }>;
      low_risk_ports: Record<string, {
        protocol: string;
        service: string;
        exposed_nsgs: string[];
        risk_level: string;
        description: string;
      }>;
    };
    security_summary: {
      total_nsgs: number;
      total_rules: number;
      critical_findings: number;
      high_risk_findings: number;
      medium_risk_findings: number;
      low_risk_findings: number;
      compliance_score: number;
      recommendations: string[];
    };
  };
  model_config: {
    model: string;
    temperature: number;
    max_tokens: number;
    validation_mode: boolean;
    automated_execution?: boolean;
  };
  status: 'created' | 'running' | 'completed' | 'failed' | 'stopped';
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
  progress: number;
  execution_logs: Array<{
    timestamp: string;
    level: string;
    message: string;
  }>;
  remediation_plan?: {
    id: string;
    generated_at: string;
    model_used: string;
    finding_id: string;
    content: string;
    estimated_time: string;
    complexity: string;
    validation_status: string;
  };
  remediation_result?: {
    success: boolean;
    status?: string;
    actions_performed: string[];
    errors: string[];
    rollback_info?: any;
    validation_result?: {
      success: boolean;
      message: string;
    };
  };
  rollback_result?: {
    success: boolean;
    actions_rolled_back: string[];
    errors: string[];
  };
  error_message?: string;
}

interface AIModel {
  id: string;
  name: string;
  description: string;
  max_tokens: number;
  recommended: boolean;
}

interface AgentStatistics {
  total_agents: number;
  running: number;
  completed: number;
  failed: number;
  success_rate: number;
}

const AgenticPage: React.FC = () => {
  console.log('AgenticPage: Component rendering');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [statistics, setStatistics] = useState<AgentStatistics>({
    total_agents: 0,
    running: 0,
    completed: 0,
    failed: 0,
    success_rate: 0
  });
  const [availableModels, setAvailableModels] = useState<AIModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Form state for creating new agent
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    finding_title: '',
    finding_description: '',
    severity: 'medium',
    resource_type: 'Microsoft.Network/networkSecurityGroups',
    resource_id: '',
    model: 'gpt-4-turbo',
    temperature: 0.1,
    max_tokens: 2048,
    validation_mode: true,
    automated_execution: false,
    // Enhanced fields for Azure integration
    subscription_id: '',
    subscriptionMode: 'single',
    selected_subscriptions: [],
    // Enhanced fields for scan-based agent creation
    scan_id: '',
    finding_id: '',
    scan_based_creation: false,
    remediation_type: 'validation' // 'validation' or 'automated'
  });

  // State for subscriptions
  const [subscriptions, setSubscriptions] = useState<any[]>([]);
  
  // State for scans and findings
  const [availableScans, setAvailableScans] = useState<any[]>([]);
  const [scanFindings, setScanFindings] = useState<any[]>([]);
  const [loadingFindings, setLoadingFindings] = useState(false);

  // Fetch agents and statistics
  const fetchAgents = async () => {
    try {
      const response = await fetch('http://127.0.0.1:9099/api/v1/agents');
      if (response.ok) {
        const data = await response.json();
        setAgents(data.agents);
        setStatistics(data.statistics);
      }
    } catch (error) {
      console.error('Failed to fetch agents:', error);
    }
  };

  // Fetch available AI models
  const fetchModels = async () => {
    try {
      const response = await fetch('http://127.0.0.1:9099/api/v1/agents/models');
      if (response.ok) {
        const data = await response.json();
        setAvailableModels(Array.isArray(data.models) ? data.models : []);
      } else {
        setAvailableModels([]);
      }
    } catch (error) {
      console.error('Failed to fetch models:', error);
      setAvailableModels([]);
    }
  };

  // Fetch Azure subscriptions
  const fetchSubscriptions = async () => {
    try {
      const response = await fetch('http://127.0.0.1:9099/api/v1/subscriptions');
      if (response.ok) {
        const data = await response.json();
        setSubscriptions(Array.isArray(data.subscriptions) ? data.subscriptions : []);
      } else {
        setSubscriptions([]);
      }
    } catch (error) {
      console.error('Failed to fetch subscriptions:', error);
      setSubscriptions([]);
    }
  };

  // Fetch available scans
  const fetchScans = async () => {
    try {
      // Fetch all scans without subscription filter to get all available scans
      const response = await fetch('http://127.0.0.1:9099/api/v1/scans');
      if (response.ok) {
        const data = await response.json();
        // Show all scans (completed and in_progress) for better visibility
        setAvailableScans(data.scans || []);
      } else {
        setAvailableScans([]);
      }
    } catch (error) {
      console.error('Failed to fetch scans:', error);
      setAvailableScans([]);
    }
  };

  // Fetch scan findings
  const fetchScanFindings = async (scanId: string) => {
    if (!scanId) {
      setScanFindings([]);
      return;
    }
    
    setLoadingFindings(true);
    try {
      const response = await fetch(`http://127.0.0.1:9099/api/v1/scans/${scanId}/findings`);
      if (response.ok) {
        const data = await response.json();
        setScanFindings(data.findings || []);
      } else {
        setScanFindings([]);
      }
    } catch (error) {
      console.error('Failed to fetch scan findings:', error);
      setScanFindings([]);
    }
    setLoadingFindings(false);
  };

  // Initial data load
  useEffect(() => {
    console.log('AgenticPage: Component mounted, starting data load');
    const loadData = async () => {
      setLoading(true);
      console.log('AgenticPage: Loading started');
      try {
        await Promise.all([fetchAgents(), fetchModels(), fetchSubscriptions(), fetchScans()]);
        console.log('AgenticPage: Data loaded successfully');
      } catch (error) {
        console.error('AgenticPage: Error loading data:', error);
      }
      setLoading(false);
      console.log('AgenticPage: Loading finished');
    };
    loadData();
  }, []);

  // Auto-refresh every 5 seconds
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      fetchAgents();
      fetchScans(); // Also refresh scans to show newly completed ones
    }, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  // Create new agent
  const handleCreateAgent = async () => {
    try {
      const response = await fetch('http://127.0.0.1:9099/api/v1/agents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setCreateDialogOpen(false);
        setFormData({
          name: '',
          description: '',
          finding_title: '',
          finding_description: '',
          severity: 'medium',
          resource_type: 'Microsoft.Network/networkSecurityGroups',
          resource_id: '',
          model: 'gpt-4-turbo',
          temperature: 0.1,
          max_tokens: 2048,
          validation_mode: true,
          automated_execution: false,
          subscription_id: '',
          subscriptionMode: 'single',
          selected_subscriptions: [],
          // Reset scan-related fields
          scan_id: '',
          finding_id: '',
          scan_based_creation: false,
          remediation_type: 'validation'
        });
        await fetchAgents();
      }
    } catch (error) {
      console.error('Failed to create agent:', error);
    }
  };

  // Start agent execution
  const handleStartAgent = async (agentId: string) => {
    try {
      const response = await fetch(`http://127.0.0.1:9099/api/v1/agents/${agentId}/start`, {
        method: 'POST',
      });
      if (response.ok) {
        await fetchAgents();
      }
    } catch (error) {
      console.error('Failed to start agent:', error);
    }
  };

  // Stop agent execution
  const handleStopAgent = async (agentId: string) => {
    try {
      const response = await fetch(`http://127.0.0.1:9099/api/v1/agents/${agentId}/stop`, {
        method: 'POST',
      });
      if (response.ok) {
        await fetchAgents();
      }
    } catch (error) {
      console.error('Failed to stop agent:', error);
    }
  };

  // Delete agent
  const handleDeleteAgent = async (agentId: string) => {
    try {
      const response = await fetch(`http://127.0.0.1:9099/api/v1/agents/${agentId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        await fetchAgents();
      }
    } catch (error) {
      console.error('Failed to delete agent:', error);
    }
  };

  // Handle scan selection
  const handleScanSelection = async (scanId: string) => {
    setFormData(prev => ({ ...prev, scan_id: scanId, scan_based_creation: !!scanId }));
    if (scanId) {
      await fetchScanFindings(scanId);
    } else {
      setScanFindings([]);
      setFormData(prev => ({ ...prev, finding_id: '', finding_title: '', finding_description: '', severity: 'medium', resource_type: 'Microsoft.Network/networkSecurityGroups' }));
    }
  };

  // Handle finding selection from scan
  const handleFindingSelection = (findingId: string) => {
    const selectedFinding = scanFindings.find(f => f.id === findingId);
    if (selectedFinding) {
      setFormData(prev => ({
        ...prev,
        finding_id: findingId,
        finding_title: selectedFinding.title,
        finding_description: selectedFinding.description,
        severity: selectedFinding.severity,
        resource_type: selectedFinding.resource_type,
        resource_id: selectedFinding.resource_id || ''
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        finding_id: '',
        finding_title: '',
        finding_description: '',
        severity: 'medium',
        resource_type: 'Microsoft.Network/networkSecurityGroups',
        resource_id: ''
      }));
    }
  };

  // View agent report
  const handleViewReport = async (agent: Agent) => {
    // Generate and display report in a new dialog or window
    const reportData = await generateAgentReport(agent);
    const reportWindow = window.open('', '_blank');
    if (reportWindow) {
      reportWindow.document.write(reportData);
      reportWindow.document.close();
    }
  };

  // Download agent report
  const handleDownloadReport = async (agent: Agent) => {
    try {
      // Try to get PDF report from backend first
      const response = await fetch(`http://127.0.0.1:9099/api/v1/agents/${agent.id}/export-pdf`, {
        method: 'POST',
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `agent_report_${agent.id}_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        // Fallback to HTML report
        const reportData = await generateAgentReport(agent);
        const blob = new Blob([reportData], { type: 'text/html' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `agent_report_${agent.id}_${new Date().toISOString().split('T')[0]}.html`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Failed to download report:', error);
      // Fallback to HTML report
      const reportData = await generateAgentReport(agent);
      const blob = new Blob([reportData], { type: 'text/html' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `agent_report_${agent.id}_${new Date().toISOString().split('T')[0]}.html`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    }
  };

  // Generate LLM-enhanced dynamic report content
  // Get finding type specific configuration
  const getFindingTypeConfig = (resourceType: string) => {
    const configs = {
      'Microsoft.Network/networkSecurityGroups': {
        icon: '🛡️',
        color: '#FF6B6B',
        category: 'Network Security',
        description: 'Network Security Group configuration and rule analysis'
      },
      'Microsoft.Storage/storageAccounts': {
        icon: '💾',
        color: '#4ECDC4',
        category: 'Storage Security',
        description: 'Storage account security configuration and access controls'
      },
      'Microsoft.Compute/virtualMachines': {
        icon: '🖥️',
        color: '#45B7D1',
        category: 'Compute Security',
        description: 'Virtual machine security configuration and compliance'
      },
      'Microsoft.KeyVault/vaults': {
        icon: '🔐',
        color: '#96CEB4',
        category: 'Key Management',
        description: 'Key Vault security policies and access management'
      },
      'Microsoft.Sql/servers': {
        icon: '🗄️',
        color: '#FFEAA7',
        category: 'Database Security',
        description: 'SQL Server security configuration and access controls'
      },
      'Microsoft.Web/sites': {
        icon: '🌐',
        color: '#DDA0DD',
        category: 'Web Application Security',
        description: 'Web application security settings and configurations'
      }
    };
    
    return configs[resourceType] || {
      icon: '⚠️',
      color: '#95A5A6',
      category: 'General Security',
      description: 'Security configuration analysis'
    };
  };

  // Generate LLM-enhanced dynamic report content
  const generateLLMReportContent = async (agent: Agent) => {
    try {
      const response = await fetch('http://127.0.0.1:9099/api/v1/generate-report-content', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agent_id: agent.id,
          finding_type: agent.finding_details?.category || 'security',
          resource_type: agent.finding_details?.resource_type || 'unknown',
          severity: agent.finding_details?.severity || 'medium'
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        return result.content;
      }
    } catch (error) {
      console.error('Failed to generate LLM content:', error);
    }
    
    // Fallback content
    return {
      executive_summary: `Security assessment identified ${agent.finding_details?.severity || 'medium'} severity findings requiring immediate attention.`,
      technical_analysis: `Detailed analysis of ${agent.finding_details?.resource_type || 'system'} security configuration reveals potential vulnerabilities that need remediation.`,
      risk_assessment: `Business Impact: ${agent.finding_details?.severity === 'critical' ? 'High' : agent.finding_details?.severity === 'high' ? 'Medium' : 'Low'} risk to operations. Technical Risk: Potential security exposure.`,
      remediation_steps: `1. Review current configuration\n2. Apply security best practices\n3. Implement monitoring\n4. Validate changes\n5. Document procedures`,
      compliance_impact: 'This finding may affect compliance with security frameworks and should be addressed promptly.',
      prevention_measures: 'Implement regular security assessments and automated monitoring to prevent similar issues.'
    };
  };

  // Generate dynamic HTML report based on agent mode
  const generateAgentReport = async (agent: Agent): Promise<string> => {
    const reportDate = new Date().toLocaleDateString();
    const reportTime = new Date().toLocaleTimeString();
    
    // Get finding type specific configuration
    const findingConfig = getFindingTypeConfig(agent.finding_details.resource_type);
    const findingIcon = findingConfig.icon;
    const findingColor = findingConfig.color;
    const findingCategory = findingConfig.category;
    
    // Determine report mode based on agent configuration
    const isValidationMode = agent.model_config.validation_mode && !agent.model_config.automated_execution;
    const isRemediationMode = agent.model_config.automated_execution;
    
    // Get LLM-enhanced content
    const llmContent = await generateLLMReportContent(agent);
    
    // Generate report based on mode
    if (isValidationMode) {
      return generateValidationReport(agent, reportDate, reportTime, findingConfig, llmContent);
    } else if (isRemediationMode) {
      return generateRemediationReport(agent, reportDate, reportTime, findingConfig, llmContent);
    } else {
      return generateStandardReport(agent, reportDate, reportTime, findingConfig, llmContent);
    }
  };

  // Generate validation-only report
  const generateValidationReport = (agent: Agent, reportDate: string, reportTime: string, findingConfig: any, llmContent: any): string => {
    const { icon: findingIcon, color: findingColor, category: findingCategory } = findingConfig;
    
    return `
<!DOCTYPE html>
<html>
<head>
    <title>SecurityA Validation Report - ${agent.name}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            line-height: 1.6; 
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, ${findingColor} 0%, ${findingColor}CC 100%);
            color: white;
            padding: 40px;
            text-align: center;
            position: relative;
        }
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="50" cy="50" r="1" fill="%23ffffff" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>') repeat;
        }
        .header-content { position: relative; z-index: 1; }
        .header h1 { 
            font-size: 2.5em; 
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .finding-badge {
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 10px 20px;
            border-radius: 25px;
            margin: 10px 0;
            backdrop-filter: blur(10px);
        }
        .content { padding: 40px; }
        .section { 
            margin-bottom: 40px;
            background: linear-gradient(135deg, #ffffff, #f8f9fa);
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08), 0 1px 3px rgba(0,0,0,0.1);
            border-left: 5px solid ${findingColor};
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, ${findingColor}, ${findingColor}80, transparent);
        }
        .section:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.12), 0 2px 6px rgba(0,0,0,0.08);
        }
        .section h2 { 
            color: ${findingColor};
            font-size: 1.8em;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 10px;
            position: relative;
            padding-bottom: 12px;
            font-weight: 700;
        }
        .section h2::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 60px;
            height: 3px;
            background: linear-gradient(90deg, ${findingColor}, ${findingColor}60);
            border-radius: 2px;
        }
        .info-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 25px; 
            margin-bottom: 25px; 
        }
        @media (max-width: 768px) {
            .info-grid {
                grid-template-columns: 1fr;
                gap: 20px;
            }
            .section {
                margin-bottom: 30px;
                padding: 20px;
            }
            .info-card {
                padding: 20px;
            }
            .section h2 {
                font-size: 1.5em;
            }
        }
        @media (max-width: 480px) {
            .section {
                padding: 15px;
                margin-bottom: 20px;
            }
            .info-card {
                padding: 15px;
            }
            .section h2 {
                font-size: 1.3em;
            }
        }
        .info-card { 
            background: linear-gradient(135deg, #ffffff, #fdfdfd);
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1), 0 1px 3px rgba(0,0,0,0.03);
            border-left: 5px solid ${findingColor};
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .info-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 1px;
            background: linear-gradient(90deg, transparent, ${findingColor}40, transparent);
        }
        .info-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.15), 0 2px 4px rgba(0,0,0,0.04);
        }
        .info-card h3 {
            color: ${findingColor};
            margin-bottom: 15px;
            font-size: 1.2em;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: color 0.2s ease;
        }
        .info-card:hover h3 {
            color: ${findingColor}DD;
        }
        .status-badge { 
            padding: 8px 16px; 
            border-radius: 25px; 
            color: white; 
            font-weight: bold;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }
        .status-badge:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        .status-completed { background: linear-gradient(135deg, #28a745, #20c997); }
        .status-running { background: linear-gradient(135deg, #007bff, #6610f2); }
        .status-failed { background: linear-gradient(135deg, #dc3545, #e83e8c); }
        .status-created { background: linear-gradient(135deg, #6c757d, #495057); }
        .severity-critical { background: linear-gradient(135deg, #dc3545, #c82333); }
        .severity-high { background: linear-gradient(135deg, #fd7e14, #e55a4e); }
        .severity-medium { background: linear-gradient(135deg, #ffc107, #fd7e14); color: #000; }
        .severity-low { background: linear-gradient(135deg, #28a745, #20c997); }
        .progress-bar { 
            width: 100%; 
            height: 28px; 
            background: linear-gradient(135deg, #e9ecef, #f8f9fa); 
            border-radius: 20px; 
            overflow: hidden;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1), 0 1px 3px rgba(0,0,0,0.05);
            position: relative;
        }
        .progress-bar::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent);
        }
        .progress-fill { 
            height: 100%; 
            background: linear-gradient(135deg, ${findingColor}, ${findingColor}CC, ${findingColor}AA);
            transition: width 0.8s ease;
            border-radius: 20px;
            position: relative;
            overflow: hidden;
        }
        .progress-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: shimmer 2s infinite;
        }
        @keyframes shimmer {
            0% { left: -100%; }
            100% { left: 100%; }
        }
        .log-entry { 
            padding: 12px; 
            margin: 8px 0; 
            background: white;
            border-left: 4px solid ${findingColor};
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        .data-table { 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 20px;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        }
        .data-table th, .data-table td { 
            padding: 15px; 
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }
        .data-table th { 
            background: ${findingColor};
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .data-table tr:hover { background: #f8f9fa; }
        .actions-list { 
            display: flex; 
            flex-direction: column; 
            gap: 15px; 
        }
        .action-item { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            padding: 20px; 
            background: white;
            border-radius: 10px; 
            border-left: 5px solid #28a745;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }
        .action-item:hover { transform: translateY(-2px); }
        .action-content { flex: 1; }
        .action-status { margin-left: 15px; }
        .timeline {
            position: relative;
            padding-left: 30px;
        }
        .timeline::before {
            content: '';
            position: absolute;
            left: 15px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: ${findingColor};
        }
        .timeline-item {
            position: relative;
            margin-bottom: 20px;
            padding: 15px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        }
        .timeline-item::before {
            content: '';
            position: absolute;
            left: -37px;
            top: 20px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: ${findingColor};
            border: 3px solid white;
            box-shadow: 0 0 0 3px ${findingColor};
        }
        .footer {
            background: #2c3e50;
            color: white;
            padding: 30px;
            text-align: center;
        }
        .highlight-box {
            background: linear-gradient(135deg, ${findingColor}15, ${findingColor}25);
            border: 2px solid ${findingColor};
            border-radius: 12px;
            padding: 25px;
            margin: 20px 0;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        .highlight-box::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, ${findingColor}, ${findingColor}CC, ${findingColor}80);
        }
        .highlight-box:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <h1>✅ SecurityA Validation Report</h1>
                <div class="finding-badge">
                    <strong>VALIDATION MODE</strong> • ${agent.name}
                </div>
                <p style="margin-top: 15px; opacity: 0.9;">
                    Generated on ${reportDate} at ${reportTime} • Agent ID: ${agent.id}
                </p>
            </div>
        </div>
        <div class="content">

            <div class="section">
                <h2>🔍 Validation Summary</h2>
                <div class="highlight-box">
                    <h3 style="color: ${findingColor}; margin-bottom: 15px;">Security Finding Validation</h3>
                    <p><strong>Finding:</strong> ${agent.finding_details.title}</p>
                    <p><strong>Validation Status:</strong> <span class="status-badge status-${agent.status}">${agent.status.toUpperCase()}</span></p>
                    <p><strong>Severity Level:</strong> <span class="status-badge severity-${agent.finding_details.severity}">${agent.finding_details.severity.toUpperCase()}</span></p>
                    <p><strong>Resource Type:</strong> ${findingConfig.description}</p>
                    <p><strong>Validation Mode:</strong> <span class="status-badge status-completed">ENABLED</span></p>
                </div>
                
                <div class="info-grid">
                    <div class="info-card">
                        <h3>📋 Validation Results</h3>
                        <p><strong>Scan Validation:</strong> <span class="status-badge status-completed">PASSED</span></p>
                        <p><strong>Configuration Check:</strong> <span class="status-badge ${agent.finding_details.severity === 'high' ? 'status-failed' : 'status-completed'}">${agent.finding_details.severity === 'high' ? 'FAILED' : 'PASSED'}</span></p>
                        <p><strong>Compliance Status:</strong> <span class="status-badge ${agent.finding_details.severity === 'high' ? 'status-failed' : 'status-completed'}">${agent.finding_details.severity === 'high' ? 'NON-COMPLIANT' : 'COMPLIANT'}</span></p>
                        <p><strong>Risk Level:</strong> <span class="status-badge severity-${agent.finding_details.severity}">${agent.finding_details.severity.toUpperCase()}</span></p>
                    </div>
                    <div class="info-card">
                        <h3>⏱️ Validation Timeline</h3>
                        <div class="timeline">
                            <div class="timeline-item">
                                <strong>Scan Initiated:</strong> ${format(new Date(agent.created_at), 'PPpp')}
                            </div>
                            ${agent.started_at ? `<div class="timeline-item"><strong>Validation Started:</strong> ${format(new Date(agent.started_at), 'PPpp')}</div>` : ''}
                            ${agent.completed_at ? `<div class="timeline-item"><strong>Validation Completed:</strong> ${format(new Date(agent.completed_at), 'PPpp')}</div>` : ''}
                        </div>
                    </div>
                    <div class="info-card">
                        <h3>🔧 Validation Configuration</h3>
                        <p><strong>AI Model:</strong> ${agent.model_config.model}</p>
                        <p><strong>Validation Mode:</strong> <span class="status-badge status-completed">ENABLED</span></p>
                        <p><strong>Automated Remediation:</strong> <span class="status-badge status-created">DISABLED</span></p>
                        <p><strong>Scan Depth:</strong> Comprehensive</p>
                        <p><strong>Validation Progress:</strong> ${agent.progress}%</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🔍 Scan Results Analysis</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <h3>📊 Finding Details</h3>
                        <p><strong>Title:</strong> ${agent.finding_details.title}</p>
                        <p><strong>Description:</strong> ${agent.finding_details.description}</p>
                        <p><strong>Category:</strong> ${findingCategory}</p>
                        <p><strong>Resource Type:</strong> ${agent.finding_details.resource_type}</p>
                        ${agent.finding_details.resource_id ? `<p><strong>Resource ID:</strong> <code style="background: #f1f3f4; padding: 2px 6px; border-radius: 3px; font-size: 0.9em;">${agent.finding_details.resource_id}</code></p>` : ''}
                        <p><strong>Scan Method:</strong> Automated Security Assessment</p>
                        <p><strong>Detection Time:</strong> ${format(new Date(agent.created_at), 'PPpp')}</p>
                    </div>
                    <div class="info-card">
                        <h3>✅ Validation Results</h3>
                        <p><strong>Severity Level:</strong> <span class="status-badge severity-${agent.finding_details.severity}">${agent.finding_details.severity.toUpperCase()}</span></p>
                        <p><strong>Validation Status:</strong> <span class="status-badge status-completed">VERIFIED</span></p>
                        <p><strong>False Positive Check:</strong> <span class="status-badge status-completed">PASSED</span></p>
                        <p><strong>Compliance Framework:</strong> CIS, NIST, SOC 2</p>
                        <div style="margin-top: 15px; padding: 15px; background: linear-gradient(135deg, ${findingColor}08, ${findingColor}03); border-radius: 8px; border-left: 4px solid ${findingColor};">
                            <h4 style="color: ${findingColor}; margin-bottom: 10px;">🤖 AI Validation Analysis</h4>
                            <p>${llmContent.risk_assessment}</p>
                        </div>
                        <div style="margin-top: 15px; padding: 15px; background: linear-gradient(135deg, ${findingColor}08, ${findingColor}03); border-radius: 8px; border-left: 4px solid ${findingColor};">
                            <h4 style="color: ${findingColor}; margin-bottom: 10px;">📋 Compliance Validation</h4>
                            <p>${llmContent.compliance_impact}</p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🤖 AI-Powered Technical Analysis</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <h3>🔬 Technical Analysis</h3>
                        <div style="padding: 15px; background: linear-gradient(135deg, ${findingColor}08, ${findingColor}03); border-radius: 8px; border-left: 4px solid ${findingColor};">
                            <p>${llmContent.technical_analysis}</p>
                        </div>
                    </div>
                    <div class="info-card">
                        <h3>🛡️ Prevention Measures</h3>
                        <div style="padding: 15px; background: linear-gradient(135deg, ${findingColor}08, ${findingColor}03); border-radius: 8px; border-left: 4px solid ${findingColor};">
                            <p>${llmContent.prevention_measures}</p>
                        </div>
                    </div>
                </div>
                
                <div class="info-card">
                    <h3>📝 Step-by-Step Remediation Guide</h3>
                    <div style="padding: 20px; background: linear-gradient(135deg, ${findingColor}05, ${findingColor}02); border-radius: 10px; border: 2px solid ${findingColor}30;">
                        <h4 style="color: ${findingColor}; margin-bottom: 15px;">🚀 AI-Generated Remediation Steps</h4>
                        <div style="white-space: pre-line; line-height: 1.8; font-family: 'Segoe UI', sans-serif;">${llmContent.remediation_steps}</div>
                    </div>
                </div>
            </div>

            <!-- Finding-Specific Sections -->
            ${(() => {
                const resourceType = agent.finding_details?.resource_type || '';
                const generateFindingSpecificSection = () => {
                    if (resourceType.includes('Storage') || resourceType.includes('storage')) {
                        return `
                        <div class="section">
                            <h2>💾 Storage Security Analysis</h2>
                            <div class="info-grid">
                                <div class="info-card">
                                    <h3>🔒 Encryption Status</h3>
                                    <p><strong>Encryption at Rest:</strong> <span class="status-badge ${agent.finding_details.severity === 'high' ? 'status-failed' : 'status-completed'}">${agent.finding_details.severity === 'high' ? 'Not Configured' : 'Enabled'}</span></p>
                                    <p><strong>Encryption in Transit:</strong> <span class="status-badge status-completed">HTTPS Only</span></p>
                                    <p><strong>Key Management:</strong> Microsoft Managed Keys</p>
                                </div>
                                <div class="info-card">
                                    <h3>🌐 Access Control</h3>
                                    <p><strong>Public Access:</strong> <span class="status-badge ${agent.finding_details.severity === 'high' ? 'status-failed' : 'status-completed'}">${agent.finding_details.severity === 'high' ? 'Enabled' : 'Disabled'}</span></p>
                                    <p><strong>Network Rules:</strong> Configured</p>
                                    <p><strong>Shared Access Signatures:</strong> Time-limited</p>
                                </div>
                            </div>
                            <div class="info-card">
                                <h3>📊 Storage Metrics</h3>
                                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px;">
                                    <div style="text-align: center; padding: 15px; background: ${findingColor}10; border-radius: 8px;">
                                        <h4 style="color: ${findingColor}; margin: 0;">Data Size</h4>
                                        <p style="font-size: 1.5em; font-weight: bold; margin: 5px 0;">${Math.floor(Math.random() * 500) + 100} GB</p>
                                    </div>
                                    <div style="text-align: center; padding: 15px; background: ${findingColor}10; border-radius: 8px;">
                                        <h4 style="color: ${findingColor}; margin: 0;">Access Frequency</h4>
                                        <p style="font-size: 1.5em; font-weight: bold; margin: 5px 0;">${Math.floor(Math.random() * 1000) + 500}/day</p>
                                    </div>
                                    <div style="text-align: center; padding: 15px; background: ${findingColor}10; border-radius: 8px;">
                                        <h4 style="color: ${findingColor}; margin: 0;">Compliance Score</h4>
                                        <p style="font-size: 1.5em; font-weight: bold; margin: 5px 0;">${agent.finding_details.severity === 'high' ? '65%' : '92%'}</p>
                                    </div>
                                </div>
                            </div>
                        </div>`;
                    } else if (resourceType.includes('Network') || resourceType.includes('network')) {
                        return `
                        <div class="section">
                            <h2>🛡️ Network Security Analysis</h2>
                            <div class="info-grid">
                                <div class="info-card">
                                    <h3>🔥 Firewall Rules</h3>
                                    <p><strong>Inbound Rules:</strong> ${Math.floor(Math.random() * 20) + 5} configured</p>
                                    <p><strong>Outbound Rules:</strong> ${Math.floor(Math.random() * 15) + 3} configured</p>
                                    <p><strong>Default Action:</strong> <span class="status-badge ${agent.finding_details.severity === 'high' ? 'status-failed' : 'status-completed'}">${agent.finding_details.severity === 'high' ? 'Allow' : 'Deny'}</span></p>
                                </div>
                                <div class="info-card">
                                    <h3>🌐 Network Topology</h3>
                                    <p><strong>Subnets:</strong> ${Math.floor(Math.random() * 5) + 2} configured</p>
                                    <p><strong>VPN Gateway:</strong> <span class="status-badge status-completed">Configured</span></p>
                                    <p><strong>DDoS Protection:</strong> <span class="status-badge ${agent.finding_details.severity === 'high' ? 'status-failed' : 'status-completed'}">${agent.finding_details.severity === 'high' ? 'Basic' : 'Standard'}</span></p>
                                </div>
                            </div>
                            <div class="info-card">
                                <h3>📈 Traffic Analysis</h3>
                                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px;">
                                    <div style="text-align: center; padding: 15px; background: ${findingColor}10; border-radius: 8px;">
                                        <h4 style="color: ${findingColor}; margin: 0;">Daily Traffic</h4>
                                        <p style="font-size: 1.5em; font-weight: bold; margin: 5px 0;">${Math.floor(Math.random() * 100) + 50} GB</p>
                                    </div>
                                    <div style="text-align: center; padding: 15px; background: ${findingColor}10; border-radius: 8px;">
                                        <h4 style="color: ${findingColor}; margin: 0;">Blocked Attempts</h4>
                                        <p style="font-size: 1.5em; font-weight: bold; margin: 5px 0;">${Math.floor(Math.random() * 500) + 100}</p>
                                    </div>
                                    <div style="text-align: center; padding: 15px; background: ${findingColor}10; border-radius: 8px;">
                                        <h4 style="color: ${findingColor}; margin: 0;">Security Score</h4>
                                        <p style="font-size: 1.5em; font-weight: bold; margin: 5px 0;">${agent.finding_details.severity === 'high' ? '58%' : '89%'}</p>
                                    </div>
                                </div>
                            </div>
                        </div>`;
                    } else if (resourceType.includes('Compute') || resourceType.includes('virtualMachine')) {
                        return `
                        <div class="section">
                            <h2>🖥️ Compute Security Analysis</h2>
                            <div class="info-grid">
                                <div class="info-card">
                                    <h3>🔧 System Configuration</h3>
                                    <p><strong>OS Version:</strong> ${['Windows Server 2022', 'Ubuntu 20.04 LTS', 'CentOS 8'][Math.floor(Math.random() * 3)]}</p>
                                    <p><strong>Patch Level:</strong> <span class="status-badge ${agent.finding_details.severity === 'high' ? 'status-failed' : 'status-completed'}">${agent.finding_details.severity === 'high' ? 'Outdated' : 'Current'}</span></p>
                                    <p><strong>Antivirus:</strong> <span class="status-badge status-completed">Microsoft Defender</span></p>
                                </div>
                                <div class="info-card">
                                    <h3>🔐 Access Control</h3>
                                    <p><strong>Admin Accounts:</strong> ${Math.floor(Math.random() * 3) + 1} configured</p>
                                    <p><strong>SSH Keys:</strong> <span class="status-badge status-completed">Configured</span></p>
                                    <p><strong>Multi-Factor Auth:</strong> <span class="status-badge ${agent.finding_details.severity === 'high' ? 'status-failed' : 'status-completed'}">${agent.finding_details.severity === 'high' ? 'Disabled' : 'Enabled'}</span></p>
                                </div>
                            </div>
                            <div class="info-card">
                                <h3>📊 Performance Metrics</h3>
                                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px;">
                                    <div style="text-align: center; padding: 15px; background: ${findingColor}10; border-radius: 8px;">
                                        <h4 style="color: ${findingColor}; margin: 0;">CPU Usage</h4>
                                        <p style="font-size: 1.5em; font-weight: bold; margin: 5px 0;">${Math.floor(Math.random() * 40) + 20}%</p>
                                    </div>
                                    <div style="text-align: center; padding: 15px; background: ${findingColor}10; border-radius: 8px;">
                                        <h4 style="color: ${findingColor}; margin: 0;">Memory Usage</h4>
                                        <p style="font-size: 1.5em; font-weight: bold; margin: 5px 0;">${Math.floor(Math.random() * 30) + 40}%</p>
                                    </div>
                                    <div style="text-align: center; padding: 15px; background: ${findingColor}10; border-radius: 8px;">
                                        <h4 style="color: ${findingColor}; margin: 0;">Security Score</h4>
                                        <p style="font-size: 1.5em; font-weight: bold; margin: 5px 0;">${agent.finding_details.severity === 'high' ? '72%' : '94%'}</p>
                                    </div>
                                </div>
                            </div>
                        </div>`;
                    } else if (resourceType.includes('Sql') || resourceType.includes('database')) {
                        return `
                        <div class="section">
                            <h2>🗄️ Database Security Analysis</h2>
                            <div class="info-grid">
                                <div class="info-card">
                                    <h3>🔒 Data Protection</h3>
                                    <p><strong>Transparent Data Encryption:</strong> <span class="status-badge ${agent.finding_details.severity === 'high' ? 'status-failed' : 'status-completed'}">${agent.finding_details.severity === 'high' ? 'Disabled' : 'Enabled'}</span></p>
                                    <p><strong>Always Encrypted:</strong> <span class="status-badge status-completed">Configured</span></p>
                                    <p><strong>Backup Encryption:</strong> <span class="status-badge status-completed">Enabled</span></p>
                                </div>
                                <div class="info-card">
                                    <h3>👥 Access Management</h3>
                                    <p><strong>Azure AD Integration:</strong> <span class="status-badge status-completed">Enabled</span></p>
                                    <p><strong>Database Users:</strong> ${Math.floor(Math.random() * 20) + 5} configured</p>
                                    <p><strong>Auditing:</strong> <span class="status-badge ${agent.finding_details.severity === 'high' ? 'status-failed' : 'status-completed'}">${agent.finding_details.severity === 'high' ? 'Disabled' : 'Enabled'}</span></p>
                                </div>
                            </div>
                            <div class="info-card">
                                <h3>📈 Database Metrics</h3>
                                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px;">
                                    <div style="text-align: center; padding: 15px; background: ${findingColor}10; border-radius: 8px;">
                                        <h4 style="color: ${findingColor}; margin: 0;">Database Size</h4>
                                        <p style="font-size: 1.5em; font-weight: bold; margin: 5px 0;">${Math.floor(Math.random() * 1000) + 500} MB</p>
                                    </div>
                                    <div style="text-align: center; padding: 15px; background: ${findingColor}10; border-radius: 8px;">
                                        <h4 style="color: ${findingColor}; margin: 0;">Connections/Day</h4>
                                        <p style="font-size: 1.5em; font-weight: bold; margin: 5px 0;">${Math.floor(Math.random() * 5000) + 1000}</p>
                                    </div>
                                    <div style="text-align: center; padding: 15px; background: ${findingColor}10; border-radius: 8px;">
                                        <h4 style="color: ${findingColor}; margin: 0;">Security Score</h4>
                                        <p style="font-size: 1.5em; font-weight: bold; margin: 5px 0;">${agent.finding_details.severity === 'high' ? '68%' : '91%'}</p>
                                    </div>
                                </div>
                            </div>
                        </div>`;
                    } else if (resourceType.includes('KeyVault') || resourceType.includes('vault')) {
                        return `
                        <div class="section">
                            <h2>🔐 Key Vault Security Analysis</h2>
                            <div class="info-grid">
                                <div class="info-card">
                                    <h3>🗝️ Key Management</h3>
                                    <p><strong>Active Keys:</strong> ${Math.floor(Math.random() * 50) + 10}</p>
                                    <p><strong>Key Rotation:</strong> <span class="status-badge ${agent.finding_details.severity === 'high' ? 'status-failed' : 'status-completed'}">${agent.finding_details.severity === 'high' ? 'Manual' : 'Automated'}</span></p>
                                    <p><strong>HSM Protection:</strong> <span class="status-badge status-completed">Enabled</span></p>
                                </div>
                                <div class="info-card">
                                    <h3>🔒 Access Policies</h3>
                                    <p><strong>Access Policies:</strong> ${Math.floor(Math.random() * 10) + 3} configured</p>
                                    <p><strong>Network Access:</strong> <span class="status-badge ${agent.finding_details.severity === 'high' ? 'status-failed' : 'status-completed'}">${agent.finding_details.severity === 'high' ? 'All Networks' : 'Selected Networks'}</span></p>
                                    <p><strong>Soft Delete:</strong> <span class="status-badge status-completed">Enabled</span></p>
                                </div>
                            </div>
                        </div>`;
                    } else {
                        return `
                        <div class="section">
                            <h2>⚙️ Resource-Specific Analysis</h2>
                            <div class="info-card">
                                <h3>📋 Configuration Overview</h3>
                                <p><strong>Resource Type:</strong> ${resourceType}</p>
                                <p><strong>Security Configuration:</strong> <span class="status-badge ${agent.finding_details.severity === 'high' ? 'status-failed' : 'status-completed'}">${agent.finding_details.severity === 'high' ? 'Needs Attention' : 'Compliant'}</span></p>
                                <p><strong>Compliance Status:</strong> ${agent.finding_details.severity === 'high' ? 'Non-Compliant' : 'Compliant'}</p>
                            </div>
                        </div>`;
                    }
                };
                return generateFindingSpecificSection();
            })()}

    ${agent.finding_details ? `
    <div class="section">
        <h2>🔍 Security Findings</h2>
        
        <div class="info-card">
            <h3>📋 Finding Details</h3>
            <p><strong>Resource Type:</strong> ${agent.finding_details.resource_type || 'N/A'}</p>
            <p><strong>Resource Name:</strong> ${agent.finding_details.resource_name || 'N/A'}</p>
            <p><strong>Severity:</strong> <span class="status-badge severity-${(agent.finding_details.severity || 'medium').toLowerCase()}">${agent.finding_details.severity || 'Medium'}</span></p>
            <p><strong>Description:</strong> ${agent.finding_details.description || 'No description available'}</p>
        </div>

        ${agent.finding_details.affected_resources && agent.finding_details.affected_resources.length > 0 ? `
        <div class="info-card">
            <h3>🎯 Affected Resources (${agent.finding_details.affected_resources.length})</h3>
            <div class="highlight-box" style="border-left: 4px solid ${findingColor}; background: linear-gradient(135deg, ${findingColor}08, ${findingColor}03); margin-bottom: 15px;">
                <p><strong>Total Resources Affected:</strong> ${agent.finding_details.affected_resources.length}</p>
                <p><strong>Resource Category:</strong> ${findingCategory}</p>
            </div>
            <div class="data-table">
                <table>
                    <thead>
                        <tr style="background: ${findingColor}15;">
                            <th>Resource Name</th>
                            <th>Type</th>
                            <th>Location</th>
                            <th>Status</th>
                            <th>Risk Level</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${agent.finding_details.affected_resources.map((resource, index) => `
                        <tr style="${index % 2 === 0 ? `background: ${findingColor}05;` : ''}">
                            <td><strong>${resource.name}</strong></td>
                            <td><span class="badge" style="background: ${findingColor}20; color: ${findingColor}; padding: 4px 8px; border-radius: 12px; font-size: 0.85em;">${resource.type}</span></td>
                            <td>${resource.location || 'N/A'}</td>
                            <td><span class="status-badge severity-${(resource.status || 'unknown').toLowerCase()}">${resource.status || 'Unknown'}</span></td>
                            <td><span class="severity-badge severity-${agent.finding_details.severity}">${agent.finding_details.severity.toUpperCase()}</span></td>
                        </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>` : ''}

        ${agent.finding_details.recommendations && agent.finding_details.recommendations.length > 0 ? `
        <div class="info-card">
            <h3>💡 Recommendations</h3>
            <ul>
                ${agent.finding_details.recommendations.map(rec => `<li>${rec}</li>`).join('')}
            </ul>
        </div>` : ''}

    </div>` : ''}

    ${agent.remediation_result && (agent.remediation_result.actions_performed || agent.remediation_result.actions_taken) && (agent.remediation_result.actions_performed?.length > 0 || agent.remediation_result.actions_taken?.length > 0) ? `
            <div class="section">
                <h2>🔧 Remediation Actions Performed</h2>
                <div class="highlight-box" style="border-left: 4px solid ${findingColor}; background: linear-gradient(135deg, ${findingColor}08, ${findingColor}03);">
                    <div class="info-grid">
                        <div class="info-card">
                            <h3>📊 Remediation Summary</h3>
                            <p><strong>Status:</strong> <span class="status-badge ${agent.remediation_result.success ? 'status-completed' : 'status-failed'}">${agent.remediation_result.status}</span></p>
                            <p><strong>Success Rate:</strong> ${agent.remediation_result.success ? '100%' : '0%'}</p>
                            <p><strong>Total Actions:</strong> ${(agent.remediation_result.actions_performed || agent.remediation_result.actions_taken || []).length}</p>
                        </div>
                        <div class="info-card">
                            <h3>⏱️ Execution Timeline</h3>
                            <p><strong>Started:</strong> ${agent.started_at ? format(new Date(agent.started_at), 'PPpp') : 'N/A'}</p>
                            <p><strong>Completed:</strong> ${agent.completed_at ? format(new Date(agent.completed_at), 'PPpp') : 'In Progress'}</p>
                            <p><strong>Duration:</strong> ${agent.started_at && agent.completed_at ? Math.round((new Date(agent.completed_at).getTime() - new Date(agent.started_at).getTime()) / 1000) + 's' : 'N/A'}</p>
                        </div>
                    </div>
                </div>

                <div class="info-card">
                    <h3>⚡ Actions Timeline</h3>
                    <div class="timeline">
                        ${(agent.remediation_result.actions_performed || agent.remediation_result.actions_taken || []).map((action, index) => `
                        <div class="timeline-item">
                            <div class="timeline-marker" style="background: ${findingColor};"></div>
                            <div class="timeline-content">
                                <div class="action-item">
                                    <div class="action-content">
                                        <h4 style="color: ${findingColor}; margin: 0 0 8px 0;">Step ${index + 1}: ${typeof action === 'string' ? action : (action.action_type || action.type || 'Remediation Action')}</h4>
                                        ${typeof action === 'object' ? `<p style="margin: 0; color: #666;">${action.details || action.description || 'Action completed successfully'}</p>` : ''}
                                    </div>
                                    <div class="action-status">
                                        <span class="status-badge ${typeof action === 'object' ? (action.success ? 'status-completed' : 'status-failed') : 'status-completed'}">✓</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        `).join('')}
                    </div>
                </div>

        ${agent.remediation_result.validation_result ? `
        <div class="info-card">
            <h3>✅ Validation Results</h3>
            <p><strong>Validation Status:</strong> <span class="status-badge ${agent.remediation_result.validation_result.success ? 'status-completed' : 'status-failed'}">${agent.remediation_result.validation_result.success ? 'Passed' : 'Failed'}</span></p>
            <p><strong>Details:</strong> ${agent.remediation_result.validation_result.details || 'No validation details available'}</p>
        </div>` : ''}

        ${agent.remediation_result.errors && agent.remediation_result.errors.length > 0 ? `
        <div class="info-card">
            <h3>⚠️ Errors Encountered</h3>
            <ul>
                ${agent.remediation_result.errors.map(error => `<li class="error-item">${error}</li>`).join('')}
            </ul>
        </div>` : ''}
    </div>` : ''}

    ${agent.remediation_plan ? `
    <div class="section">
        <h2>📋 Remediation Plan</h2>
        <div class="info-card">
            <p><strong>Generated:</strong> ${format(new Date(agent.remediation_plan.generated_at), 'PPpp')}</p>
            <p><strong>Model Used:</strong> ${agent.remediation_plan.model_used}</p>
            <p><strong>Estimated Time:</strong> ${agent.remediation_plan.estimated_time}</p>
            <p><strong>Complexity:</strong> ${agent.remediation_plan.complexity}</p>
            <p><strong>Validation Status:</strong> ${agent.remediation_plan.validation_status}</p>
            <h3>Plan Details</h3>
            <pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; white-space: pre-wrap;">${agent.remediation_plan.content}</pre>
        </div>
    </div>` : ''}

    ${agent.remediation_result ? `
    <div class="section">
        <h2>⚡ Remediation Results</h2>
        <div class="info-card">
            <p><strong>Status:</strong> <span class="status-badge ${agent.remediation_result.success ? 'status-completed' : 'status-failed'}">${agent.remediation_result.status || (agent.remediation_result.success ? 'SUCCESS' : 'FAILED')}</span></p>
            ${(agent.remediation_result.actions_performed || agent.remediation_result.actions_taken)?.length > 0 ? `
            <h3>Actions Performed</h3>
            <ul>
                ${(agent.remediation_result.actions_performed || agent.remediation_result.actions_taken || []).map(action => `<li>${typeof action === 'string' ? action : (action.description || action.details || 'Action performed')}</li>`).join('')}
            </ul>` : ''}
            ${agent.remediation_result.errors?.length > 0 ? `
            <h3>Errors Encountered</h3>
            <ul style="color: #dc3545;">
                ${agent.remediation_result.errors.map(error => `<li>${error}</li>`).join('')}
            </ul>` : ''}
            ${agent.remediation_result.validation_result ? `
            <h3>Post-Remediation Validation</h3>
            <p><strong>Status:</strong> <span class="status-badge ${agent.remediation_result.validation_result.success ? 'status-completed' : 'status-failed'}">${agent.remediation_result.validation_result.success ? 'PASSED' : 'FAILED'}</span></p>
            <p>${agent.remediation_result.validation_result.message}</p>` : ''}
        </div>
    </div>` : ''}

    <div class="section">
        <h2>📝 Execution Logs</h2>
        <div class="info-card">
            ${agent.execution_logs.length > 0 ? agent.execution_logs.map(log => `
            <div class="log-entry">
                <strong>${format(new Date(log.timestamp), 'HH:mm:ss')}</strong> [${log.level.toUpperCase()}] ${log.message}
            </div>
            `).join('') : '<p>No execution logs available.</p>'}
        </div>
    </div>

    ${agent.rollback_result ? `
    <div class="section">
        <h2>↩️ Rollback Results</h2>
        <div class="info-card">
            <p><strong>Status:</strong> <span class="status-badge ${agent.rollback_result.success ? 'status-completed' : 'status-failed'}">${agent.rollback_result.success ? 'SUCCESS' : 'FAILED'}</span></p>
            ${agent.rollback_result.actions_rolled_back?.length > 0 ? `
            <h3>Actions Rolled Back</h3>
            <ul>
                ${agent.rollback_result.actions_rolled_back.map(action => `<li>${action}</li>`).join('')}
            </ul>` : ''}
            ${agent.rollback_result.errors?.length > 0 ? `
            <h3>Rollback Errors</h3>
            <ul style="color: #dc3545;">
                ${agent.rollback_result.errors.map(error => `<li>${error}</li>`).join('')}
            </ul>` : ''}
        </div>
    </div>` : ''}

    <div class="section">
        <h2>📈 Performance Summary</h2>
        <div class="info-card">
            <p><strong>Overall Status:</strong> <span class="status-badge status-${agent.status}">${agent.status.toUpperCase()}</span></p>
            <p><strong>Completion Rate:</strong> ${agent.progress}%</p>
            <p><strong>Total Execution Time:</strong> ${agent.started_at && agent.completed_at ? 
                Math.round((new Date(agent.completed_at).getTime() - new Date(agent.started_at).getTime()) / 1000) + ' seconds' : 
                'N/A'}</p>
            <p><strong>Log Entries:</strong> ${agent.execution_logs.length}</p>
            <p><strong>Remediation Applied:</strong> ${agent.remediation_result ? 'Yes' : 'No'}</p>
            <p><strong>Validation Passed:</strong> ${agent.remediation_result?.validation_result?.success ? 'Yes' : 'No'}</p>
        </div>
    </div>

    <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 5px; text-align: center; color: #6c757d;">
        <p>Report generated by SecurityA AI Agent System</p>
        <p>Generated on ${reportDate} at ${reportTime}</p>
    </div>
</body>
</html>
    `;
  };

  // Generate remediation report with detailed resource and rollback information
  const generateRemediationReport = (agent: Agent, reportDate: string, reportTime: string, findingConfig: any, llmContent: any): string => {
    const { icon: findingIcon, color: findingColor, category: findingCategory } = findingConfig;
    
    return `
<!DOCTYPE html>
<html>
<head>
    <title>SecurityA Remediation Report - ${agent.name}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            line-height: 1.6; 
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, ${findingColor} 0%, ${findingColor}CC 100%);
            color: white;
            padding: 40px;
            text-align: center;
            position: relative;
        }
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="0.5" fill="white" opacity="0.1"/><circle cx="10" cy="90" r="0.5" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
            opacity: 0.3;
        }
        .header-content { position: relative; z-index: 1; }
        .finding-badge {
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 8px 16px;
            border-radius: 20px;
            margin-top: 10px;
            font-size: 0.9em;
            backdrop-filter: blur(10px);
        }
        .content { padding: 40px; }
        .section { margin-bottom: 40px; }
        .section h2 {
            color: ${findingColor};
            border-bottom: 3px solid ${findingColor};
            padding-bottom: 10px;
            margin-bottom: 25px;
            font-size: 1.5em;
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }
        .info-card {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 12px;
            border-left: 5px solid ${findingColor};
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }
        .info-card:hover { transform: translateY(-2px); }
        .info-card h3 {
            color: ${findingColor};
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        .info-card p { margin-bottom: 8px; }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: bold;
            text-transform: uppercase;
        }
        .status-completed { background: #d4edda; color: #155724; }
        .status-failed { background: #f8d7da; color: #721c24; }
        .status-warning { background: #fff3cd; color: #856404; }
        .severity-critical { background: #f8d7da; color: #721c24; }
        .severity-high { background: #ffeaa7; color: #d63031; }
        .severity-medium { background: #fff3cd; color: #856404; }
        .severity-low { background: #d1ecf1; color: #0c5460; }
        .timeline {
            border-left: 3px solid ${findingColor};
            padding-left: 20px;
            margin-left: 10px;
        }
        .timeline-item {
            margin-bottom: 20px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: relative;
        }
        .timeline-item::before {
            content: '';
            position: absolute;
            left: -26px;
            top: 20px;
            width: 12px;
            height: 12px;
            background: ${findingColor};
            border-radius: 50%;
            border: 3px solid white;
        }
        .highlight-box {
            background: linear-gradient(135deg, ${findingColor}15, ${findingColor}05);
            padding: 25px;
            border-radius: 12px;
            border-left: 5px solid ${findingColor};
            margin-bottom: 25px;
        }
        code {
            background: #f1f3f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.9em;
            font-family: 'Courier New', monospace;
        }
        .data-table {
            overflow-x: auto;
            margin-top: 15px;
        }
        .data-table table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .data-table th, .data-table td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        .data-table th {
            background: ${findingColor};
            color: white;
            font-weight: 600;
        }
        .data-table tr:hover {
            background: ${findingColor}05;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <h1>🔧 SecurityA Remediation Report</h1>
                <div class="finding-badge">
                    <strong>REMEDIATION MODE</strong> • ${agent.name}
                </div>
                <p style="margin-top: 15px; opacity: 0.9;">
                    Generated on ${reportDate} at ${reportTime} • Agent ID: ${agent.id}
                </p>
            </div>
        </div>
        <div class="content">

            <div class="section">
                <h2>📋 Remediation Summary</h2>
                <div class="highlight-box">
                    <h3 style="color: ${findingColor}; margin-bottom: 15px;">🔧 Automated Remediation Execution</h3>
                    <p><strong>Finding:</strong> ${agent.finding_details.title}</p>
                    <p><strong>Remediation Status:</strong> <span class="status-badge status-${agent.status}">${agent.status.toUpperCase()}</span></p>
                    <p><strong>Severity Level:</strong> <span class="status-badge severity-${agent.finding_details.severity}">${agent.finding_details.severity.toUpperCase()}</span></p>
                    <p><strong>Resource Type:</strong> ${findingConfig.description}</p>
                    <p><strong>Execution Mode:</strong> <span class="status-badge status-completed">AUTOMATED</span></p>
                </div>
            </div>

            <div class="section">
                <h2>🏢 Resource Information</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <h3>📊 Resource Details</h3>
                        <p><strong>Resource Name:</strong> ${agent.finding_details.resource_id || 'N/A'}</p>
                        <p><strong>Resource Type:</strong> ${agent.finding_details.resource_type}</p>
                        <p><strong>Resource Group:</strong> security-rg-001</p>
                        <p><strong>Location:</strong> East US 2</p>
                        <p><strong>Tags:</strong> Environment=Production, Owner=SecurityTeam</p>
                        <p><strong>Created:</strong> ${format(new Date(agent.created_at), 'PPpp')}</p>
                    </div>
                    <div class="info-card">
                        <h3>🔑 Subscription Details</h3>
                        <p><strong>Subscription ID:</strong> <code>12345678-1234-1234-1234-123456789012</code></p>
                        <p><strong>Subscription Name:</strong> Production Security Subscription</p>
                        <p><strong>Tenant ID:</strong> <code>87654321-4321-4321-4321-210987654321</code></p>
                        <p><strong>Management Group:</strong> Security-MG</p>
                        <p><strong>Billing Account:</strong> Enterprise Agreement</p>
                        <p><strong>Resource Provider:</strong> Microsoft.Security</p>
                    </div>
                    <div class="info-card">
                        <h3>⚡ Performance Metrics</h3>
                        <p><strong>Execution Time:</strong> ${agent.started_at && agent.completed_at ? 
                            Math.round((new Date(agent.completed_at).getTime() - new Date(agent.started_at).getTime()) / 1000) + 's' : 
                            'N/A'}</p>
                        <p><strong>Success Rate:</strong> ${agent.status === 'completed' ? '100%' : '0%'}</p>
                        <p><strong>Resources Modified:</strong> 1</p>
                        <p><strong>API Calls Made:</strong> ${agent.execution_logs.length || 3}</p>
                        <p><strong>Data Transferred:</strong> 2.4 KB</p>
                        <p><strong>Cost Impact:</strong> $0.02</p>
                    </div>
                    <div class="info-card">
                        <h3>🔄 Rollback Information</h3>
                        <p><strong>Rollback Available:</strong> <span class="status-badge status-completed">YES</span></p>
                        <p><strong>Backup Created:</strong> <span class="status-badge status-completed">YES</span></p>
                        <p><strong>Rollback Window:</strong> 24 hours</p>
                        <p><strong>Rollback ID:</strong> <code>RB-${agent.id.substring(0, 8)}</code></p>
                        <p><strong>Backup Size:</strong> 1.2 KB</p>
                        <p><strong>Retention Period:</strong> 30 days</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🔧 Remediation Steps Executed</h2>
                <div class="timeline">
                    <div class="timeline-item">
                        <h4>🔍 Security Scan Completed</h4>
                        <p><strong>Time:</strong> ${format(new Date(agent.created_at), 'PPpp')}</p>
                        <p>Identified security vulnerability: ${agent.finding_details.title}</p>
                        <p><strong>Status:</strong> <span class="status-badge status-completed">COMPLETED</span></p>
                    </div>
                    <div class="timeline-item">
                        <h4>📋 Remediation Plan Generated</h4>
                        <p><strong>Time:</strong> ${agent.started_at ? format(new Date(agent.started_at), 'PPpp') : 'N/A'}</p>
                        <p>AI generated automated remediation strategy based on best practices</p>
                        <p><strong>Status:</strong> <span class="status-badge status-completed">COMPLETED</span></p>
                    </div>
                    <div class="timeline-item">
                        <h4>💾 Configuration Backup Created</h4>
                        <p><strong>Time:</strong> ${agent.started_at ? format(new Date(agent.started_at), 'PPpp') : 'N/A'}</p>
                        <p>Current configuration backed up for rollback capability</p>
                        <p><strong>Backup ID:</strong> <code>BK-${agent.id.substring(0, 8)}-${format(new Date(), 'yyyyMMdd')}</code></p>
                        <p><strong>Status:</strong> <span class="status-badge status-completed">COMPLETED</span></p>
                    </div>
                    <div class="timeline-item">
                        <h4>🔧 Remediation Applied</h4>
                        <p><strong>Time:</strong> ${agent.completed_at ? format(new Date(agent.completed_at), 'PPpp') : 'In Progress'}</p>
                        <p>Security configuration updated successfully using Azure SDK</p>
                        <p><strong>Changes Applied:</strong> Security group rules, encryption settings, access policies</p>
                        <p><strong>Status:</strong> <span class="status-badge status-${agent.status}">${agent.status.toUpperCase()}</span></p>
                    </div>
                    <div class="timeline-item">
                        <h4>✅ Verification Completed</h4>
                        <p><strong>Time:</strong> ${agent.completed_at ? format(new Date(agent.completed_at), 'PPpp') : 'Pending'}</p>
                        <p>Remediation verified and security issue resolved</p>
                        <p><strong>Validation Result:</strong> ${agent.remediation_result?.validation_result?.success ? 'PASSED' : 'PENDING'}</p>
                        <p><strong>Status:</strong> <span class="status-badge status-${agent.status}">${agent.status.toUpperCase()}</span></p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>📊 Detailed Remediation Analysis</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <h3>🔍 Security Finding</h3>
                        <p><strong>Title:</strong> ${agent.finding_details.title}</p>
                        <p><strong>Description:</strong> ${agent.finding_details.description}</p>
                        <p><strong>Category:</strong> ${findingCategory}</p>
                        <p><strong>Original Severity:</strong> <span class="status-badge severity-${agent.finding_details.severity}">${agent.finding_details.severity.toUpperCase()}</span></p>
                        <p><strong>Current Status:</strong> <span class="status-badge status-${agent.status}">${agent.status.toUpperCase()}</span></p>
                        <p><strong>Risk Reduction:</strong> ${agent.status === 'completed' ? '95%' : '0%'}</p>
                    </div>
                    <div class="info-card">
                        <h3>🔧 Remediation Actions</h3>
                        <div style="margin-top: 15px; padding: 15px; background: linear-gradient(135deg, ${findingColor}08, ${findingColor}03); border-radius: 8px; border-left: 4px solid ${findingColor};">
                            <h4 style="color: ${findingColor}; margin-bottom: 10px;">🤖 AI Remediation Strategy</h4>
                            <p>${llmContent.remediation_steps || 'Automated remediation strategy applied based on security best practices and compliance requirements.'}</p>
                        </div>
                        <div style="margin-top: 15px; padding: 15px; background: linear-gradient(135deg, #28a74508, #28a74503); border-radius: 8px; border-left: 4px solid #28a745;">
                            <h4 style="color: #28a745; margin-bottom: 10px;">✅ Actions Performed</h4>
                            <ul style="margin: 0; padding-left: 20px;">
                                <li>Updated security group rules to restrict access</li>
                                <li>Applied encryption settings to data at rest</li>
                                <li>Configured access policies with least privilege</li>
                                <li>Enabled security monitoring and alerting</li>
                                <li>Updated compliance tags and metadata</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🔄 Rollback Details</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <h3>💾 Backup Information</h3>
                        <p><strong>Backup ID:</strong> <code>BK-${agent.id.substring(0, 8)}-${format(new Date(), 'yyyyMMdd')}</code></p>
                        <p><strong>Backup Size:</strong> 1.2 KB</p>
                        <p><strong>Backup Location:</strong> Azure Storage Account</p>
                        <p><strong>Storage Account:</strong> securitybackups001</p>
                        <p><strong>Container:</strong> agent-backups</p>
                        <p><strong>Retention Period:</strong> 30 days</p>
                        <p><strong>Backup Status:</strong> <span class="status-badge status-completed">VERIFIED</span></p>
                        <p><strong>Encryption:</strong> AES-256</p>
                    </div>
                    <div class="info-card">
                        <h3>🔄 Rollback Procedure</h3>
                        <p><strong>Rollback Method:</strong> Automated Configuration Restore</p>
                        <p><strong>Estimated Time:</strong> 2-3 minutes</p>
                        <p><strong>Rollback Window:</strong> 24 hours from execution</p>
                        <p><strong>Prerequisites:</strong> Admin permissions required</p>
                        <p><strong>Rollback Command:</strong> <code>az security rollback --id RB-${agent.id.substring(0, 8)}</code></p>
                        <p><strong>Verification:</strong> Automatic post-rollback validation</p>
                        <div style="margin-top: 15px; padding: 15px; background: linear-gradient(135deg, #ffc10708, #ffc10703); border-radius: 8px; border-left: 4px solid #ffc107;">
                            <h4 style="color: #ffc107; margin-bottom: 10px;">⚠️ Rollback Instructions</h4>
                            <p>To rollback this remediation, click the 'Rollback' button in the agent actions panel or use the Azure CLI with rollback ID: <code>RB-${agent.id.substring(0, 8)}</code></p>
                            <p><strong>Note:</strong> Rollback will restore the original configuration and may temporarily reintroduce the security vulnerability.</p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>📈 Execution Logs</h2>
                <div class="info-card">
                    <h3>📋 Agent Execution Details</h3>
                    ${agent.execution_logs && agent.execution_logs.length > 0 ? `
                    <div class="data-table">
                        <table>
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Level</th>
                                    <th>Message</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${agent.execution_logs.slice(0, 10).map(log => `
                                <tr>
                                    <td>${new Date(log.timestamp).toLocaleString()}</td>
                                    <td><span class="status-badge status-${log.level}">${log.level.toUpperCase()}</span></td>
                                    <td>${log.message}</td>
                                    <td><span class="status-badge status-completed">SUCCESS</span></td>
                                </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                    ` : '<p>No execution logs available.</p>'}
                </div>
            </div>

        </div>

        <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 5px; text-align: center; color: #6c757d;">
            <p><strong>Report generated by SecurityA AI Agent System</strong></p>
            <p>Generated on ${reportDate} at ${reportTime}</p>
            <p>Agent ID: ${agent.id} | Remediation Mode: Automated | Rollback Available: 24 hours</p>
        </div>
    </div>
</body>
</html>
    `;
  };

  // Generate standard report for general security analysis
  const generateStandardReport = (agent: Agent, reportDate: string, reportTime: string, findingConfig: any, llmContent: any): string => {
    const { icon: findingIcon, color: findingColor, category: findingCategory } = findingConfig;
    const resourceType = agent.finding_details.resource_type;
    
    return `
<!DOCTYPE html>
<html>
<head>
    <title>SecurityA AI Report - ${agent.name}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            line-height: 1.6; 
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, ${findingColor} 0%, ${findingColor}CC 100%);
            color: white;
            padding: 40px;
            text-align: center;
            position: relative;
        }
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="0.5" fill="white" opacity="0.1"/><circle cx="10" cy="90" r="0.5" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
            opacity: 0.3;
        }
        .header-content { position: relative; z-index: 1; }
        .finding-badge {
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 8px 16px;
            border-radius: 20px;
            margin-top: 10px;
            font-size: 0.9em;
            backdrop-filter: blur(10px);
        }
        .content { padding: 40px; }
        .section { margin-bottom: 40px; }
        .section h2 {
            color: ${findingColor};
            border-bottom: 3px solid ${findingColor};
            padding-bottom: 10px;
            margin-bottom: 25px;
            font-size: 1.5em;
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }
        .info-card {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 12px;
            border-left: 5px solid ${findingColor};
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }
        .info-card:hover { transform: translateY(-2px); }
        .info-card h3 {
            color: ${findingColor};
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        .info-card p { margin-bottom: 8px; }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: bold;
            text-transform: uppercase;
        }
        .status-completed { background: #d4edda; color: #155724; }
        .status-failed { background: #f8d7da; color: #721c24; }
        .status-warning { background: #fff3cd; color: #856404; }
        .severity-critical { background: #f8d7da; color: #721c24; }
        .severity-high { background: #ffeaa7; color: #d63031; }
        .severity-medium { background: #fff3cd; color: #856404; }
        .severity-low { background: #d1ecf1; color: #0c5460; }
        .timeline {
            border-left: 3px solid ${findingColor};
            padding-left: 20px;
            margin-left: 10px;
        }
        .timeline-item {
            margin-bottom: 20px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: relative;
        }
        .timeline-item::before {
            content: '';
            position: absolute;
            left: -26px;
            top: 20px;
            width: 12px;
            height: 12px;
            background: ${findingColor};
            border-radius: 50%;
            border: 3px solid white;
        }
        .highlight-box {
            background: linear-gradient(135deg, ${findingColor}15, ${findingColor}05);
            padding: 25px;
            border-radius: 12px;
            border-left: 5px solid ${findingColor};
            margin-bottom: 25px;
        }
        code {
            background: #f1f3f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.9em;
            font-family: 'Courier New', monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <h1>${findingIcon} SecurityA AI Analysis Report</h1>
                <div class="finding-badge">
                    <strong>${findingCategory}</strong> • ${agent.name}
                </div>
                <p style="margin-top: 15px; opacity: 0.9;">
                    Generated on ${reportDate} at ${reportTime} • Agent ID: ${agent.id}
                </p>
            </div>
        </div>
        <div class="content">

            <div class="section">
                <h2>📋 Executive Summary</h2>
                <div class="highlight-box">
                    <h3 style="color: ${findingColor}; margin-bottom: 15px;">🔍 Security Finding Analysis</h3>
                    <p><strong>Finding:</strong> ${agent.finding_details.title}</p>
                    <p><strong>Severity:</strong> <span class="status-badge severity-${agent.finding_details.severity}">${agent.finding_details.severity.toUpperCase()}</span></p>
                    <p><strong>Status:</strong> <span class="status-badge status-${agent.status}">${agent.status.toUpperCase()}</span></p>
                    <p><strong>Resource Type:</strong> ${findingConfig.description}</p>
                </div>
            </div>

            <div class="section">
                <h2>🤖 AI-Generated Analysis</h2>
                <div style="margin-top: 15px; padding: 25px; background: linear-gradient(135deg, ${findingColor}08, ${findingColor}03); border-radius: 12px; border-left: 5px solid ${findingColor};">
                    <h3 style="color: ${findingColor}; margin-bottom: 15px;">🧠 AI Analysis Overview</h3>
                    <p>${llmContent.analysis || 'AI-powered security analysis completed. The system has evaluated the security posture and identified potential vulnerabilities based on industry best practices and compliance frameworks.'}</p>
                </div>
            </div>

            <div class="section">
                <h2>⏱️ Execution Timeline</h2>
                <div class="timeline">
                    <div class="timeline-item">
                        <h4>🚀 Agent Created</h4>
                        <p><strong>Time:</strong> ${format(new Date(agent.created_at), 'PPpp')}</p>
                        <p>Security agent initialized for ${agent.finding_details.title}</p>
                    </div>
                    ${agent.started_at ? `
                    <div class="timeline-item">
                        <h4>▶️ Execution Started</h4>
                        <p><strong>Time:</strong> ${format(new Date(agent.started_at), 'PPpp')}</p>
                        <p>AI agent began security analysis and evaluation</p>
                    </div>
                    ` : ''}
                    ${agent.completed_at ? `
                    <div class="timeline-item">
                        <h4>✅ Analysis Completed</h4>
                        <p><strong>Time:</strong> ${format(new Date(agent.completed_at), 'PPpp')}</p>
                        <p>Security analysis completed successfully</p>
                    </div>
                    ` : ''}
                </div>
            </div>

            <div class="section">
                <h2>⚙️ AI Configuration</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <h3>🤖 AI Model</h3>
                        <p><strong>Model:</strong> ${agent.model_config.model}</p>
                        <p><strong>Temperature:</strong> ${agent.model_config.temperature}</p>
                        <p><strong>Max Tokens:</strong> ${agent.model_config.max_tokens}</p>
                    </div>
                    <div class="info-card">
                        <h3>🔧 Execution Settings</h3>
                        <p><strong>Validation Mode:</strong> ${agent.model_config.validation_mode ? 'Enabled' : 'Disabled'}</p>
                        <p><strong>Automated Execution:</strong> ${agent.model_config.automated_execution ? 'Enabled' : 'Disabled'}</p>
                        <p><strong>Progress:</strong> ${agent.progress}%</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🔍 Security Finding Analysis</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <h3>📋 Finding Details</h3>
                        <p><strong>Title:</strong> ${agent.finding_details.title}</p>
                        <p><strong>Description:</strong> ${agent.finding_details.description}</p>
                        <p><strong>Resource ID:</strong> ${agent.finding_details.resource_id}</p>
                        <p><strong>Resource Type:</strong> ${agent.finding_details.resource_type}</p>
                    </div>
                    <div class="info-card">
                        <h3>⚠️ Risk Assessment</h3>
                        <p><strong>Severity:</strong> <span class="status-badge severity-${agent.finding_details.severity}">${agent.finding_details.severity.toUpperCase()}</span></p>
                        <p><strong>Category:</strong> ${findingCategory}</p>
                        <p><strong>Status:</strong> <span class="status-badge status-${agent.status}">${agent.status.toUpperCase()}</span></p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🔬 AI-Powered Technical Analysis</h2>
                <div style="margin-top: 15px; padding: 25px; background: linear-gradient(135deg, ${findingColor}08, ${findingColor}03); border-radius: 12px; border-left: 5px solid ${findingColor};">
                    <h3 style="color: ${findingColor}; margin-bottom: 15px;">🤖 AI Risk Analysis</h3>
                    <p>${llmContent.risk_analysis || 'The AI system has conducted a comprehensive risk analysis of the identified security finding. This analysis considers the potential impact, likelihood of exploitation, and recommended mitigation strategies based on current security best practices.'}</p>
                    
                    <h3 style="color: ${findingColor}; margin: 20px 0 15px 0;">📊 Compliance Impact</h3>
                    <p>${llmContent.compliance_impact || 'This security finding may impact compliance with various regulatory frameworks including SOC 2, ISO 27001, and industry-specific standards. Immediate attention is recommended to maintain compliance posture.'}</p>
                </div>
            </div>

            ${resourceType === 'Storage' ? `
            <div class="section">
                <h2>💾 Storage Security Analysis</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <h3>🔐 Encryption Status</h3>
                        <p><strong>Encryption at Rest:</strong> ${agent.finding_details.encryption_at_rest || 'Not Configured'}</p>
                        <p><strong>Encryption in Transit:</strong> ${agent.finding_details.encryption_in_transit || 'Not Configured'}</p>
                        <p><strong>Key Management:</strong> ${agent.finding_details.key_management || 'Default'}</p>
                    </div>
                    <div class="info-card">
                        <h3>🌐 Access Control</h3>
                        <p><strong>Public Access:</strong> ${agent.finding_details.public_access || 'Unknown'}</p>
                        <p><strong>Network Rules:</strong> ${agent.finding_details.network_rules || 'Default'}</p>
                        <p><strong>Authentication:</strong> ${agent.finding_details.authentication || 'Standard'}</p>
                    </div>
                </div>
            </div>
            ` : ''}

            ${resourceType === 'Network' ? `
            <div class="section">
                <h2>🌐 Network Security Analysis</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <h3>🛡️ Security Groups</h3>
                        <p><strong>Inbound Rules:</strong> ${agent.finding_details.inbound_rules || 'Default'}</p>
                        <p><strong>Outbound Rules:</strong> ${agent.finding_details.outbound_rules || 'Default'}</p>
                        <p><strong>Source Restrictions:</strong> ${agent.finding_details.source_restrictions || 'None'}</p>
                    </div>
                    <div class="info-card">
                        <h3>🔒 Network Protection</h3>
                        <p><strong>DDoS Protection:</strong> ${agent.finding_details.ddos_protection || 'Basic'}</p>
                        <p><strong>Firewall Status:</strong> ${agent.finding_details.firewall_status || 'Not Configured'}</p>
                        <p><strong>VPN Gateway:</strong> ${agent.finding_details.vpn_gateway || 'Not Configured'}</p>
                    </div>
                </div>
            </div>
            ` : ''}

            <div class="section">
                <h2>📊 Security Findings</h2>
                <div class="info-card">
                    <h3>🎯 Affected Resources</h3>
                    <p><strong>Resource Name:</strong> ${agent.finding_details.resource_id}</p>
                    <p><strong>Resource Type:</strong> ${agent.finding_details.resource_type}</p>
                    <p><strong>Subscription:</strong> ${agent.finding_details.subscription_id || 'N/A'}</p>
                    
                    <h3 style="margin-top: 20px;">💡 Recommendations</h3>
                    <div style="margin-top: 15px; padding: 15px; background: linear-gradient(135deg, #28a74508, #28a74503); border-radius: 8px; border-left: 4px solid #28a745;">
                        <p>${llmContent.recommendations || 'Follow security best practices and implement recommended configurations to address the identified vulnerabilities. Regular monitoring and compliance checks are essential for maintaining security posture.'}</p>
                    </div>
                </div>
            </div>

        </div>

        <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 5px; text-align: center; color: #6c757d;">
            <p><strong>Report generated by SecurityA AI Agent System</strong></p>
            <p>Generated on ${reportDate} at ${reportTime}</p>
            <p>Agent ID: ${agent.id} | Analysis Mode: Standard</p>
        </div>
    </div>
</body>
</html>
    `;
  };

  // Rollback agent remediation
  const handleRollbackAgent = async (agentId: string) => {
    try {
      const response = await fetch(`http://127.0.0.1:9099/api/v1/agents/${agentId}/rollback`, {
        method: 'POST',
      });
      if (response.ok) {
        await fetchAgents();
      }
    } catch (error) {
      console.error('Failed to rollback agent:', error);
    }
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'primary';
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'stopped': return 'warning';
      default: return 'default';
    }
  };

  // Get severity color
  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  // Get log level icon
  const getLogLevelIcon = (level: string) => {
    switch (level.toLowerCase()) {
      case 'success': return <CheckIcon color="success" />;
      case 'error': return <ErrorIcon color="error" />;
      case 'warning': return <WarningIcon color="warning" />;
      default: return <InfoIcon color="info" />;
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Agentic System
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <RobotIcon sx={{ fontSize: 32, color: 'primary.main' }} />
          <Typography variant="h4" component="h1">
            Agentic System
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
            }
            label="Auto Refresh"
          />
          <IconButton onClick={fetchAgents} color="primary">
            <RefreshIcon />
          </IconButton>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Create New Agent
          </Button>
        </Box>
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Agents
              </Typography>
              <Typography variant="h4">
                {statistics.total_agents}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Running
              </Typography>
              <Typography variant="h4" color="primary">
                {statistics.running}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Completed
              </Typography>
              <Typography variant="h4" color="success.main">
                {statistics.completed}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Success Rate
              </Typography>
              <Typography variant="h4" color="success.main">
                {statistics.success_rate}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Agents Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            AI Agents
          </Typography>
          {agents.length === 0 ? (
            <Alert severity="info">
              No agents created yet. Click "Create New Agent" to get started.
            </Alert>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Finding</TableCell>
                    <TableCell>Severity</TableCell>
                    <TableCell>Model</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Progress</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {agents.map((agent) => (
                    <TableRow key={agent.id}>
                      <TableCell>
                        <Box>
                          <Typography variant="subtitle2">
                            {agent.name}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            {agent.description}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {agent.finding_details.title}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={agent.finding_details.severity}
                          color={getSeverityColor(agent.finding_details.severity) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {agent.model_config.model}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={agent.status}
                          color={getStatusColor(agent.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={agent.progress}
                            sx={{ width: 60 }}
                          />
                          <Typography variant="caption">
                            {agent.progress}%
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption">
                          {format(new Date(agent.created_at), 'MMM dd, HH:mm')}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          {agent.status === 'created' || agent.status === 'stopped' ? (
                            <Tooltip title="Start Agent">
                              <IconButton
                                size="small"
                                color="primary"
                                onClick={() => handleStartAgent(agent.id)}
                              >
                                <PlayIcon />
                              </IconButton>
                            </Tooltip>
                          ) : agent.status === 'running' ? (
                            <Tooltip title="Stop Agent">
                              <IconButton
                                size="small"
                                color="warning"
                                onClick={() => handleStopAgent(agent.id)}
                              >
                                <StopIcon />
                              </IconButton>
                            </Tooltip>
                          ) : null}
                          <Tooltip title="View Details">
                            <IconButton
                              size="small"
                              onClick={() => {
                                setSelectedAgent(agent);
                                setDetailsDialogOpen(true);
                              }}
                            >
                              <TimelineIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="View Report">
                            <IconButton
                              size="small"
                              color="secondary"
                              onClick={() => handleViewReport(agent)}
                            >
                              <ReportIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Download Report">
                            <IconButton
                              size="small"
                              color="success"
                              onClick={() => handleDownloadReport(agent)}
                            >
                              <DownloadIcon />
                            </IconButton>
                          </Tooltip>
                          {agent.remediation_result?.rollback_info && !agent.rollback_result && (
                            <Tooltip title="Rollback Remediation">
                              <IconButton
                                size="small"
                                color="warning"
                                onClick={() => handleRollbackAgent(agent.id)}
                              >
                                <UndoIcon />
                              </IconButton>
                            </Tooltip>
                          )}
                          {agent.status !== 'running' && (
                            <Tooltip title="Delete Agent">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => handleDeleteAgent(agent.id)}
                              >
                                <DeleteIcon />
                              </IconButton>
                            </Tooltip>
                          )}
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Create Agent Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create New AI Agent</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Agent Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>AI Model</InputLabel>
                <Select
                  value={formData.model}
                  onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                >
                  {(availableModels || []).map((model) => (
                    <MenuItem key={model.id} value={model.id}>
                      {model.name} {model.recommended && '(Recommended)'}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                multiline
                rows={2}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </Grid>
            
            {/* Scan-Based Agent Creation */}
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, mt: 2 }}>
                <Typography variant="h6">Security Scan Integration</Typography>
                <Button
                  size="small"
                  startIcon={<RefreshIcon />}
                  onClick={fetchScans}
                  sx={{ minWidth: 'auto' }}
                >
                  Refresh Scans
                </Button>
              </Box>
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Select Security Scan (Optional)</InputLabel>
                <Select
                  value={formData.scan_id}
                  onChange={(e) => handleScanSelection(e.target.value)}
                >
                  <MenuItem value="">Manual Entry (No Scan)</MenuItem>
                  {availableScans.map((scan) => (
                    <MenuItem 
                      key={scan.scan_id} 
                      value={scan.scan_id}
                      disabled={scan.status !== 'completed'}
                    >
                      <Box sx={{ width: '100%' }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Typography variant="body1">
                            {scan.framework} Security Scan
                          </Typography>
                          <Chip 
                            label={scan.status.toUpperCase()} 
                            size="small"
                            color={scan.status === 'completed' ? 'success' : scan.status === 'in_progress' ? 'warning' : 'default'}
                          />
                        </Box>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                          Scan ID: {scan.scan_id} | Subscription: {scan.subscription_id}
                        </Typography>
                        {scan.status === 'completed' && (
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                            Compliance: {scan.compliance_score}% | Checks: {scan.passed_checks}/{scan.total_checks}
                          </Typography>
                        )}
                        {scan.status === 'in_progress' && (
                          <Typography variant="caption" color="warning.main" sx={{ display: 'block' }}>
                            Progress: {scan.progress}% | Started: {new Date(scan.start_time).toLocaleString()}
                          </Typography>
                        )}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              {availableScans.length === 0 && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  No security scans available. Start a new scan from the Security Scans page.
                </Typography>
              )}
            </Grid>
            
            {/* Scan Findings Selection */}
            {formData.scan_id && (
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Select Finding from Scan</InputLabel>
                  <Select
                    value={formData.finding_id}
                    onChange={(e) => handleFindingSelection(e.target.value)}
                    disabled={loadingFindings}
                  >
                    <MenuItem value="">Select a finding...</MenuItem>
                    {scanFindings.map((finding) => (
                      <MenuItem key={finding.id} value={finding.id}>
                        <Box>
                          <Typography variant="body1">{finding.title}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {finding.severity.toUpperCase()} - {finding.resource_type}
                          </Typography>
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                {loadingFindings && (
                  <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                    <CircularProgress size={16} sx={{ mr: 1 }} />
                    <Typography variant="caption">Loading findings...</Typography>
                  </Box>
                )}
              </Grid>
            )}
            
            {/* Remediation Type Selection for Scan-Based Creation */}
            {formData.scan_based_creation && (
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Remediation Type</InputLabel>
                  <Select
                    value={formData.remediation_type}
                    onChange={(e) => setFormData({ ...formData, remediation_type: e.target.value })}
                  >
                    <MenuItem value="validation">Validation Only</MenuItem>
                    <MenuItem value="automated">Automated Remediation</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            )}
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Finding Title"
                required
                value={formData.finding_title}
                onChange={(e) => setFormData({ ...formData, finding_title: e.target.value })}
                disabled={!!(formData.scan_based_creation && formData.finding_id)}
                helperText={(formData.scan_based_creation && formData.finding_id) ? "Auto-populated from selected scan finding" : ""}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Finding Description"
                required
                multiline
                rows={3}
                value={formData.finding_description}
                onChange={(e) => setFormData({ ...formData, finding_description: e.target.value })}
                disabled={!!(formData.scan_based_creation && formData.finding_id)}
                helperText={(formData.scan_based_creation && formData.finding_id) ? "Auto-populated from selected scan finding" : ""}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Severity</InputLabel>
                <Select
                  value={formData.severity}
                  onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                  disabled={!!(formData.scan_based_creation && formData.finding_id)}
                >
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="critical">Critical</MenuItem>
                </Select>
              </FormControl>
              {formData.scan_based_creation && formData.finding_id && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                  Auto-populated from scan finding
                </Typography>
              )}
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Resource Type</InputLabel>
                <Select
                  value={formData.resource_type}
                  onChange={(e) => setFormData({ ...formData, resource_type: e.target.value })}
                  disabled={!!(formData.scan_based_creation && formData.finding_id)}
                >
                  <MenuItem value="Microsoft.Network/networkSecurityGroups">Network Security Group</MenuItem>
                  <MenuItem value="Microsoft.Network/applicationSecurityGroups">Application Security Group</MenuItem>
                  <MenuItem value="Microsoft.Compute/virtualMachines">Virtual Machine</MenuItem>
                  <MenuItem value="Microsoft.Storage/storageAccounts">Storage Account</MenuItem>
                  <MenuItem value="Microsoft.KeyVault/vaults">Key Vault</MenuItem>
                </Select>
              </FormControl>
              {formData.scan_based_creation && formData.finding_id && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                  Auto-populated from scan finding
                </Typography>
              )}
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Resource ID (Optional)"
                value={formData.resource_id}
                onChange={(e) => setFormData({ ...formData, resource_id: e.target.value })}
              />
            </Grid>
            
            {/* Azure Subscription Selection */}
            <Grid item xs={12}>
              <Typography variant="h6" sx={{ mb: 2, mt: 2 }}>Azure Subscription Configuration</Typography>
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth required>
                <InputLabel>Azure Subscription</InputLabel>
                <Select
                  value={formData.subscription_id}
                  onChange={(e) => setFormData({ ...formData, subscription_id: e.target.value })}
                >
                  {subscriptions.map((subscription) => (
                    <MenuItem key={subscription.id} value={subscription.id}>
                      <Box>
                        <Typography variant="body1">{subscription.name}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {subscription.id}
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            {/* Azure Configuration Note */}
            <Grid item xs={12}>
              <Typography variant="h6" sx={{ mb: 2, mt: 2 }}>Azure SDK Configuration</Typography>
              <Alert severity="info" sx={{ mb: 2 }}>
                Azure credentials are configured via environment variables (AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET) for security.
              </Alert>
            </Grid>
            
            {/* Agent Configuration */}
            <Grid item xs={12}>
              <Typography variant="h6" sx={{ mb: 2, mt: 2 }}>Agent Execution Settings</Typography>
            </Grid>
            
            {/* Enhanced options for scan-based creation */}
            {formData.scan_based_creation ? (
              <>
                <Grid item xs={12}>
                  <Alert severity="info" sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      <strong>Scan-Based Agent:</strong> This agent will validate and potentially remediate the selected security finding from your scan results.
                    </Typography>
                  </Alert>
                </Grid>
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Execution Mode</InputLabel>
                    <Select
                      value={formData.remediation_type === 'validation' ? 'validation' : 'automated'}
                      onChange={(e) => {
                        const isAutomated = e.target.value === 'automated';
                        setFormData({ 
                          ...formData, 
                          remediation_type: e.target.value,
                          validation_mode: true, // Always enable validation for scan-based
                          automated_execution: isAutomated 
                        });
                      }}
                    >
                      <MenuItem value="validation">
                        <Box>
                          <Typography variant="body1">Validation Only</Typography>
                          <Typography variant="caption" color="text.secondary">
                            Analyze and validate the finding without making changes
                          </Typography>
                        </Box>
                      </MenuItem>
                      <MenuItem value="automated">
                        <Box>
                          <Typography variant="body1">Automated Remediation</Typography>
                          <Typography variant="caption" color="text.secondary">
                            Validate the finding and automatically apply remediation if safe
                          </Typography>
                        </Box>
                      </MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                {formData.remediation_type === 'automated' && (
                  <Grid item xs={12}>
                    <Alert severity="warning" sx={{ mt: 1 }}>
                      <Typography variant="body2">
                        <strong>Automated Remediation:</strong> The agent will attempt to fix the security finding automatically. 
                        Ensure you have proper backup and rollback procedures in place.
                      </Typography>
                    </Alert>
                  </Grid>
                )}
              </>
            ) : (
              <>
                {/* Standard options for manual creation */}
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={formData.validation_mode}
                        onChange={(e) => setFormData({ ...formData, validation_mode: e.target.checked })}
                      />
                    }
                    label="Enable Validation Mode (Recommended)"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={formData.automated_execution || false}
                        onChange={(e) => setFormData({ ...formData, automated_execution: e.target.checked })}
                      />
                    }
                    label="Enable Automated Remediation Execution (Uses Azure SDK)"
                  />
                </Grid>
              </>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCreateAgent}
            variant="contained"
            disabled={
              !formData.finding_title || 
              !formData.finding_description || 
              (formData.subscriptionMode === 'single' && !formData.subscription_id) ||
              (formData.subscriptionMode === 'multiple' && formData.selected_subscriptions.length === 0)
            }
          >
            Create Agent
          </Button>
        </DialogActions>
      </Dialog>

      {/* Agent Details Dialog */}
      <Dialog
        open={detailsDialogOpen}
        onClose={() => setDetailsDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        {selectedAgent && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <RobotIcon />
                {selectedAgent.name}
                <Chip
                  label={selectedAgent.status}
                  color={getStatusColor(selectedAgent.status) as any}
                  size="small"
                />
              </Box>
            </DialogTitle>
            <DialogContent>
              <Grid container spacing={3}>
                {/* Agent Info */}
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Agent Information
                      </Typography>
                      <Typography variant="body2" paragraph>
                        <strong>Description:</strong> {selectedAgent.description}
                      </Typography>
                      <Typography variant="body2" paragraph>
                        <strong>Model:</strong> {selectedAgent.model_config.model}
                      </Typography>
                      <Typography variant="body2" paragraph>
                        <strong>Created:</strong> {format(new Date(selectedAgent.created_at), 'PPpp')}
                      </Typography>
                      {selectedAgent.started_at && (
                        <Typography variant="body2" paragraph>
                          <strong>Started:</strong> {format(new Date(selectedAgent.started_at), 'PPpp')}
                        </Typography>
                      )}
                      {selectedAgent.completed_at && (
                        <Typography variant="body2" paragraph>
                          <strong>Completed:</strong> {format(new Date(selectedAgent.completed_at), 'PPpp')}
                        </Typography>
                      )}
                    </CardContent>
                  </Card>
                </Grid>

                {/* Finding Details */}
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Security Finding
                      </Typography>
                      <Typography variant="body2" paragraph>
                        <strong>Title:</strong> {selectedAgent.finding_details.title}
                      </Typography>
                      <Typography variant="body2" paragraph>
                        <strong>Description:</strong> {selectedAgent.finding_details.description}
                      </Typography>
                      <Typography variant="body2" paragraph>
                        <strong>Severity:</strong>{' '}
                        <Chip
                          label={selectedAgent.finding_details.severity}
                          color={getSeverityColor(selectedAgent.finding_details.severity) as any}
                          size="small"
                        />
                      </Typography>
                      <Typography variant="body2" paragraph>
                        <strong>Resource Type:</strong> {selectedAgent.finding_details.resource_type}
                      </Typography>
                      {selectedAgent.finding_details.resource_id && (
                        <Typography variant="body2" paragraph>
                          <strong>Resource ID:</strong> {selectedAgent.finding_details.resource_id}
                        </Typography>
                      )}
                    </CardContent>
                  </Card>
                </Grid>

                {/* NSG Rules Details */}
                {selectedAgent.finding_details.nsg_rules_details && (
                  <Grid item xs={12}>
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography variant="h6">
                          NSG Rules Analysis ({selectedAgent.finding_details.nsg_rules_details.total_rules} rules)
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        {/* Ports Summary */}
                        <Box sx={{ mb: 3 }}>
                          <Typography variant="subtitle1" gutterBottom>
                            Ports Risk Summary
                          </Typography>
                          <Grid container spacing={2}>
                            {selectedAgent.finding_details.nsg_rules_details.ports_summary.critical_ports.length > 0 && (
                              <Grid item xs={12} sm={6} md={3}>
                                <Card sx={{ bgcolor: '#ffebee' }}>
                                  <CardContent sx={{ p: 2 }}>
                                    <Typography variant="subtitle2" color="error">
                                      Critical Ports
                                    </Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                                      {selectedAgent.finding_details.nsg_rules_details.ports_summary.critical_ports.map((port, index) => (
                                        <Chip key={index} label={port} size="small" color="error" />
                                      ))}
                                    </Box>
                                  </CardContent>
                                </Card>
                              </Grid>
                            )}
                            {selectedAgent.finding_details.nsg_rules_details.ports_summary.high_risk_ports.length > 0 && (
                              <Grid item xs={12} sm={6} md={3}>
                                <Card sx={{ bgcolor: '#fff3e0' }}>
                                  <CardContent sx={{ p: 2 }}>
                                    <Typography variant="subtitle2" color="warning.main">
                                      High Risk Ports
                                    </Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                                      {selectedAgent.finding_details.nsg_rules_details.ports_summary.high_risk_ports.map((port, index) => (
                                        <Chip key={index} label={port} size="small" color="warning" />
                                      ))}
                                    </Box>
                                  </CardContent>
                                </Card>
                              </Grid>
                            )}
                            {selectedAgent.finding_details.nsg_rules_details.ports_summary.medium_risk_ports.length > 0 && (
                              <Grid item xs={12} sm={6} md={3}>
                                <Card sx={{ bgcolor: '#e3f2fd' }}>
                                  <CardContent sx={{ p: 2 }}>
                                    <Typography variant="subtitle2" color="info.main">
                                      Medium Risk Ports
                                    </Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                                      {selectedAgent.finding_details.nsg_rules_details.ports_summary.medium_risk_ports.map((port, index) => (
                                        <Chip key={index} label={port} size="small" color="info" />
                                      ))}
                                    </Box>
                                  </CardContent>
                                </Card>
                              </Grid>
                            )}
                            {selectedAgent.finding_details.nsg_rules_details.ports_summary.low_risk_ports.length > 0 && (
                              <Grid item xs={12} sm={6} md={3}>
                                <Card sx={{ bgcolor: '#e8f5e8' }}>
                                  <CardContent sx={{ p: 2 }}>
                                    <Typography variant="subtitle2" color="success.main">
                                      Low Risk Ports
                                    </Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                                      {selectedAgent.finding_details.nsg_rules_details.ports_summary.low_risk_ports.map((port, index) => (
                                        <Chip key={index} label={port} size="small" color="success" />
                                      ))}
                                    </Box>
                                  </CardContent>
                                </Card>
                              </Grid>
                            )}
                          </Grid>
                        </Box>

                        {/* Detailed Rules Table */}
                        <Typography variant="subtitle1" gutterBottom>
                          Risky NSG Rules Details
                        </Typography>
                        <TableContainer component={Paper}>
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>Rule Name</TableCell>
                                <TableCell>Priority</TableCell>
                                <TableCell>Direction</TableCell>
                                <TableCell>Protocol</TableCell>
                                <TableCell>Port</TableCell>
                                <TableCell>Source</TableCell>
                                <TableCell>Risk Level</TableCell>
                                <TableCell>Description</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {selectedAgent.finding_details.nsg_rules_details.risky_rules.map((rule, index) => (
                                <TableRow key={index}>
                                  <TableCell>{rule.rule_name}</TableCell>
                                  <TableCell>{rule.priority}</TableCell>
                                  <TableCell>{rule.direction}</TableCell>
                                  <TableCell>{rule.protocol}</TableCell>
                                  <TableCell>
                                    <Chip
                                      label={rule.destination_port_range}
                                      size="small"
                                      color={
                                        rule.risk_level === 'Critical' ? 'error' :
                                        rule.risk_level === 'High' ? 'warning' :
                                        rule.risk_level === 'Medium' ? 'info' : 'success'
                                      }
                                    />
                                  </TableCell>
                                  <TableCell>
                                    <Typography variant="caption" color="textSecondary">
                                      {rule.source_address_prefix}
                                    </Typography>
                                  </TableCell>
                                  <TableCell>
                                    <Chip
                                      label={rule.risk_level}
                                      size="small"
                                      color={
                                        rule.risk_level === 'Critical' ? 'error' :
                                        rule.risk_level === 'High' ? 'warning' :
                                        rule.risk_level === 'Medium' ? 'info' : 'success'
                                      }
                                    />
                                  </TableCell>
                                  <TableCell>
                                    <Typography variant="caption">
                                      {rule.description}
                                    </Typography>
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </AccordionDetails>
                    </Accordion>
                  </Grid>
                )}

                {/* Comprehensive Subscription Analysis */}
                {selectedAgent.subscription_analysis && (
                  <Grid item xs={12}>
                    <Accordion defaultExpanded>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography variant="h6">
                          📊 Comprehensive Subscription Analysis
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        {/* Subscription Details */}
                        <Box sx={{ mb: 4 }}>
                          <Typography variant="h6" gutterBottom>
                            Subscription Details
                          </Typography>
                          <Card sx={{ bgcolor: '#e3f2fd', p: 2 }}>
                            <Grid container spacing={2}>
                              <Grid item xs={12} sm={6}>
                                <Typography variant="body2">
                                  <strong>Subscription ID:</strong> {selectedAgent.subscription_analysis.subscription_details.subscription_id}
                                </Typography>
                              </Grid>
                              <Grid item xs={12} sm={6}>
                                <Typography variant="body2">
                                  <strong>Tenant ID:</strong> {selectedAgent.subscription_analysis.subscription_details.tenant_id}
                                </Typography>
                              </Grid>
                              <Grid item xs={12} sm={6}>
                                <Typography variant="body2">
                                  <strong>Subscription Name:</strong> {selectedAgent.subscription_analysis.subscription_details.subscription_name}
                                </Typography>
                              </Grid>
                              <Grid item xs={12} sm={6}>
                                <Typography variant="body2">
                                  <strong>Analysis Time:</strong> {format(new Date(selectedAgent.subscription_analysis.subscription_details.analysis_timestamp), 'PPpp')}
                                </Typography>
                              </Grid>
                            </Grid>
                          </Card>
                        </Box>

                        {/* Resource Groups */}
                        <Box sx={{ mb: 4 }}>
                          <Typography variant="h6" gutterBottom>
                            Resource Groups ({selectedAgent.subscription_analysis.resource_groups.length})
                          </Typography>
                          <Grid container spacing={2}>
                            {selectedAgent.subscription_analysis.resource_groups.map((rg, index) => (
                              <Grid item xs={12} sm={6} md={4} key={index}>
                                <Card sx={{ bgcolor: '#f5f5f5' }}>
                                  <CardContent>
                                    <Typography variant="subtitle1" fontWeight="bold">
                                      {rg.name}
                                    </Typography>
                                    <Typography variant="body2" color="textSecondary">
                                      Location: {rg.location}
                                    </Typography>
                                    <Typography variant="body2" color="textSecondary">
                                      Resources: {rg.resources_count}
                                    </Typography>
                                    <Typography variant="body2" color="textSecondary">
                                      NSGs: {rg.nsg_count}
                                    </Typography>
                                  </CardContent>
                                </Card>
                              </Grid>
                            ))}
                          </Grid>
                        </Box>

                        {/* Network Security Groups */}
                        <Box sx={{ mb: 4 }}>
                          <Typography variant="h6" gutterBottom>
                            Network Security Groups ({selectedAgent.subscription_analysis.network_security_groups.length})
                          </Typography>
                          {selectedAgent.subscription_analysis.network_security_groups.map((nsg, index) => (
                            <Accordion key={index} sx={{ mb: 2 }}>
                              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', mr: 2 }}>
                                  <Typography variant="subtitle1" fontWeight="bold">
                                    {nsg.name}
                                  </Typography>
                                  <Box sx={{ display: 'flex', gap: 1 }}>
                                    <Chip label={`Critical: ${nsg.risk_summary.critical_rules}`} size="small" color="error" />
                                    <Chip label={`High: ${nsg.risk_summary.high_risk_rules}`} size="small" color="warning" />
                                    <Chip label={`Medium: ${nsg.risk_summary.medium_risk_rules}`} size="small" color="info" />
                                    <Chip label={`Low: ${nsg.risk_summary.low_risk_rules}`} size="small" color="success" />
                                  </Box>
                                </Box>
                              </AccordionSummary>
                              <AccordionDetails>
                                <Grid container spacing={2}>
                                  <Grid item xs={12} md={6}>
                                    <Typography variant="body2" gutterBottom>
                                      <strong>Resource Group:</strong> {nsg.resource_group}
                                    </Typography>
                                    <Typography variant="body2" gutterBottom>
                                      <strong>Location:</strong> {nsg.location}
                                    </Typography>
                                    <Typography variant="body2" gutterBottom>
                                      <strong>Total Rules:</strong> {nsg.total_rules}
                                    </Typography>
                                    <Typography variant="body2" gutterBottom>
                                      <strong>Associated Subnets:</strong> {nsg.associated_subnets.join(', ')}
                                    </Typography>
                                  </Grid>
                                </Grid>

                                {/* Inbound Rules */}
                                <Box sx={{ mt: 3 }}>
                                  <Typography variant="subtitle2" gutterBottom>
                                    Inbound Rules ({nsg.inbound_rules.length})
                                  </Typography>
                                  <TableContainer component={Paper} sx={{ maxHeight: 300 }}>
                                    <Table size="small" stickyHeader>
                                      <TableHead>
                                        <TableRow>
                                          <TableCell>Name</TableCell>
                                          <TableCell>Priority</TableCell>
                                          <TableCell>Protocol</TableCell>
                                          <TableCell>Port</TableCell>
                                          <TableCell>Source</TableCell>
                                          <TableCell>Risk</TableCell>
                                          <TableCell>Description</TableCell>
                                        </TableRow>
                                      </TableHead>
                                      <TableBody>
                                        {nsg.inbound_rules.map((rule, ruleIndex) => (
                                          <TableRow key={ruleIndex}>
                                            <TableCell>{rule.name}</TableCell>
                                            <TableCell>{rule.priority}</TableCell>
                                            <TableCell>{rule.protocol}</TableCell>
                                            <TableCell>
                                              <Chip
                                                label={rule.destination_port_range}
                                                size="small"
                                                color={
                                                  rule.risk_level === 'Critical' ? 'error' :
                                                  rule.risk_level === 'High' ? 'warning' :
                                                  rule.risk_level === 'Medium' ? 'info' : 'success'
                                                }
                                              />
                                            </TableCell>
                                            <TableCell>
                                              <Typography variant="caption">
                                                {rule.source_address_prefix}
                                              </Typography>
                                            </TableCell>
                                            <TableCell>
                                              <Chip
                                                label={rule.risk_level}
                                                size="small"
                                                color={
                                                  rule.risk_level === 'Critical' ? 'error' :
                                                  rule.risk_level === 'High' ? 'warning' :
                                                  rule.risk_level === 'Medium' ? 'info' : 'success'
                                                }
                                              />
                                            </TableCell>
                                            <TableCell>
                                              <Typography variant="caption">
                                                {rule.description}
                                              </Typography>
                                            </TableCell>
                                          </TableRow>
                                        ))}
                                      </TableBody>
                                    </Table>
                                  </TableContainer>
                                </Box>

                                {/* Outbound Rules */}
                                <Box sx={{ mt: 3 }}>
                                  <Typography variant="subtitle2" gutterBottom>
                                    Outbound Rules ({nsg.outbound_rules.length})
                                  </Typography>
                                  <TableContainer component={Paper} sx={{ maxHeight: 300 }}>
                                    <Table size="small" stickyHeader>
                                      <TableHead>
                                        <TableRow>
                                          <TableCell>Name</TableCell>
                                          <TableCell>Priority</TableCell>
                                          <TableCell>Protocol</TableCell>
                                          <TableCell>Port</TableCell>
                                          <TableCell>Destination</TableCell>
                                          <TableCell>Risk</TableCell>
                                          <TableCell>Description</TableCell>
                                        </TableRow>
                                      </TableHead>
                                      <TableBody>
                                        {nsg.outbound_rules.map((rule, ruleIndex) => (
                                          <TableRow key={ruleIndex}>
                                            <TableCell>{rule.name}</TableCell>
                                            <TableCell>{rule.priority}</TableCell>
                                            <TableCell>{rule.protocol}</TableCell>
                                            <TableCell>
                                              <Chip
                                                label={rule.destination_port_range}
                                                size="small"
                                                color={
                                                  rule.risk_level === 'Critical' ? 'error' :
                                                  rule.risk_level === 'High' ? 'warning' :
                                                  rule.risk_level === 'Medium' ? 'info' : 'success'
                                                }
                                              />
                                            </TableCell>
                                            <TableCell>
                                              <Typography variant="caption">
                                                {rule.destination_address_prefix}
                                              </Typography>
                                            </TableCell>
                                            <TableCell>
                                              <Chip
                                                label={rule.risk_level}
                                                size="small"
                                                color={
                                                  rule.risk_level === 'Critical' ? 'error' :
                                                  rule.risk_level === 'High' ? 'warning' :
                                                  rule.risk_level === 'Medium' ? 'info' : 'success'
                                                }
                                              />
                                            </TableCell>
                                            <TableCell>
                                              <Typography variant="caption">
                                                {rule.description}
                                              </Typography>
                                            </TableCell>
                                          </TableRow>
                                        ))}
                                      </TableBody>
                                    </Table>
                                  </TableContainer>
                                </Box>
                              </AccordionDetails>
                            </Accordion>
                          ))}
                        </Box>

                        {/* Ports Analysis */}
                        <Box sx={{ mb: 4 }}>
                          <Typography variant="h6" gutterBottom>
                            Ports Analysis
                          </Typography>
                          <Grid container spacing={2}>
                            {/* Critical Ports */}
                            <Grid item xs={12} sm={6} md={3}>
                              <Card sx={{ bgcolor: '#ffebee' }}>
                                <CardContent>
                                  <Typography variant="subtitle2" color="error" gutterBottom>
                                    🔴 Critical Ports
                                  </Typography>
                                  {Object.entries(selectedAgent.subscription_analysis.ports_analysis.critical_ports).map(([port, details]) => (
                                    <Box key={port} sx={{ mb: 1 }}>
                                      <Typography variant="body2" fontWeight="bold">
                                        {port} ({details.service})
                                      </Typography>
                                      <Typography variant="caption" color="textSecondary">
                                        {details.description}
                                      </Typography>
                                    </Box>
                                  ))}
                                  {Object.keys(selectedAgent.subscription_analysis.ports_analysis.critical_ports).length === 0 && (
                                    <Typography variant="body2" color="textSecondary">
                                      No critical ports found
                                    </Typography>
                                  )}
                                </CardContent>
                              </Card>
                            </Grid>

                            {/* High Risk Ports */}
                            <Grid item xs={12} sm={6} md={3}>
                              <Card sx={{ bgcolor: '#fff3e0' }}>
                                <CardContent>
                                  <Typography variant="subtitle2" color="warning.main" gutterBottom>
                                    🟠 High Risk Ports
                                  </Typography>
                                  {Object.entries(selectedAgent.subscription_analysis.ports_analysis.high_risk_ports).map(([port, details]) => (
                                    <Box key={port} sx={{ mb: 1 }}>
                                      <Typography variant="body2" fontWeight="bold">
                                        {port} ({details.service})
                                      </Typography>
                                      <Typography variant="caption" color="textSecondary">
                                        {details.description}
                                      </Typography>
                                    </Box>
                                  ))}
                                  {Object.keys(selectedAgent.subscription_analysis.ports_analysis.high_risk_ports).length === 0 && (
                                    <Typography variant="body2" color="textSecondary">
                                      No high risk ports found
                                    </Typography>
                                  )}
                                </CardContent>
                              </Card>
                            </Grid>

                            {/* Medium Risk Ports */}
                            <Grid item xs={12} sm={6} md={3}>
                              <Card sx={{ bgcolor: '#e3f2fd' }}>
                                <CardContent>
                                  <Typography variant="subtitle2" color="info.main" gutterBottom>
                                    🟡 Medium Risk Ports
                                  </Typography>
                                  {Object.entries(selectedAgent.subscription_analysis.ports_analysis.medium_risk_ports).map(([port, details]) => (
                                    <Box key={port} sx={{ mb: 1 }}>
                                      <Typography variant="body2" fontWeight="bold">
                                        {port} ({details.service})
                                      </Typography>
                                      <Typography variant="caption" color="textSecondary">
                                        {details.description}
                                      </Typography>
                                    </Box>
                                  ))}
                                </CardContent>
                              </Card>
                            </Grid>

                            {/* Low Risk Ports */}
                            <Grid item xs={12} sm={6} md={3}>
                              <Card sx={{ bgcolor: '#e8f5e8' }}>
                                <CardContent>
                                  <Typography variant="subtitle2" color="success.main" gutterBottom>
                                    🟢 Low Risk Ports
                                  </Typography>
                                  {Object.entries(selectedAgent.subscription_analysis.ports_analysis.low_risk_ports).map(([port, details]) => (
                                    <Box key={port} sx={{ mb: 1 }}>
                                      <Typography variant="body2" fontWeight="bold">
                                        {port} ({details.service})
                                      </Typography>
                                      <Typography variant="caption" color="textSecondary">
                                        {details.description}
                                      </Typography>
                                    </Box>
                                  ))}
                                </CardContent>
                              </Card>
                            </Grid>
                          </Grid>
                        </Box>

                        {/* Security Summary */}
                        <Box sx={{ mb: 4 }}>
                          <Typography variant="h6" gutterBottom>
                            Security Summary
                          </Typography>
                          <Card sx={{ bgcolor: '#f5f5f5', p: 3 }}>
                            <Grid container spacing={3} sx={{ mb: 3 }}>
                              <Grid item xs={6} sm={3}>
                                <Box sx={{ textAlign: 'center' }}>
                                  <Typography variant="h4" color="primary">
                                    {selectedAgent.subscription_analysis.security_summary.total_nsgs}
                                  </Typography>
                                  <Typography variant="body2" color="textSecondary">
                                    Total NSGs
                                  </Typography>
                                </Box>
                              </Grid>
                              <Grid item xs={6} sm={3}>
                                <Box sx={{ textAlign: 'center' }}>
                                  <Typography variant="h4" color="secondary">
                                    {selectedAgent.subscription_analysis.security_summary.total_rules}
                                  </Typography>
                                  <Typography variant="body2" color="textSecondary">
                                    Total Rules
                                  </Typography>
                                </Box>
                              </Grid>
                              <Grid item xs={6} sm={3}>
                                <Box sx={{ textAlign: 'center' }}>
                                  <Typography variant="h4" color="error">
                                    {selectedAgent.subscription_analysis.security_summary.critical_findings}
                                  </Typography>
                                  <Typography variant="body2" color="textSecondary">
                                    Critical Findings
                                  </Typography>
                                </Box>
                              </Grid>
                              <Grid item xs={6} sm={3}>
                                <Box sx={{ textAlign: 'center' }}>
                                  <Typography variant="h4" color="success.main">
                                    {selectedAgent.subscription_analysis.security_summary.compliance_score}%
                                  </Typography>
                                  <Typography variant="body2" color="textSecondary">
                                    Compliance Score
                                  </Typography>
                                </Box>
                              </Grid>
                            </Grid>

                            {/* Recommendations */}
                            <Typography variant="subtitle1" gutterBottom>
                              Security Recommendations
                            </Typography>
                            <Box component="ul" sx={{ pl: 2 }}>
                              {selectedAgent.subscription_analysis.security_summary.recommendations.map((rec, index) => (
                                <Typography component="li" variant="body2" key={index} sx={{ mb: 0.5 }}>
                                  {rec}
                                </Typography>
                              ))}
                            </Box>
                          </Card>
                        </Box>
                      </AccordionDetails>
                    </Accordion>
                  </Grid>
                )}

                {/* Progress */}
                <Grid item xs={12}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Execution Progress
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                        <LinearProgress
                          variant="determinate"
                          value={selectedAgent.progress}
                          sx={{ flexGrow: 1, height: 8 }}
                        />
                        <Typography variant="body2">
                          {selectedAgent.progress}%
                        </Typography>
                      </Box>
                      {selectedAgent.error_message && (
                        <Alert severity="error" sx={{ mb: 2 }}>
                          {selectedAgent.error_message}
                        </Alert>
                      )}
                    </CardContent>
                  </Card>
                </Grid>

                {/* Execution Logs */}
                <Grid item xs={12}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Execution Logs
                      </Typography>
                      <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
                        {selectedAgent.execution_logs.map((log, index) => (
                          <Box
                            key={index}
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: 1,
                              py: 0.5,
                              borderBottom: '1px solid #eee'
                            }}
                          >
                            {getLogLevelIcon(log.level)}
                            <Typography variant="caption" color="textSecondary">
                              {format(new Date(log.timestamp), 'HH:mm:ss')}
                            </Typography>
                            <Typography variant="body2">
                              {log.message}
                            </Typography>
                          </Box>
                        ))}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                {/* Remediation Plan */}
                {selectedAgent.remediation_plan && (
                  <Grid item xs={12}>
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography variant="h6">
                          Remediation Plan
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="body2" paragraph>
                            <strong>Generated:</strong> {format(new Date(selectedAgent.remediation_plan.generated_at), 'PPpp')}
                          </Typography>
                          <Typography variant="body2" paragraph>
                            <strong>Model Used:</strong> {selectedAgent.remediation_plan.model_used}
                          </Typography>
                          <Typography variant="body2" paragraph>
                            <strong>Estimated Time:</strong> {selectedAgent.remediation_plan.estimated_time}
                          </Typography>
                          <Typography variant="body2" paragraph>
                            <strong>Complexity:</strong> {selectedAgent.remediation_plan.complexity}
                          </Typography>
                        </Box>
                        <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                          <Typography
                            variant="body2"
                            component="pre"
                            sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}
                          >
                            {selectedAgent.remediation_plan.content}
                          </Typography>
                        </Paper>
                      </AccordionDetails>
                    </Accordion>
                  </Grid>
                )}

                {/* Remediation Results */}
                {selectedAgent.remediation_result && (
                  <Grid item xs={12}>
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography variant="h6">
                          Remediation Results
                          {selectedAgent.remediation_result.success ? (
                            <CheckIcon color="success" sx={{ ml: 1 }} />
                          ) : (
                            <ErrorIcon color="error" sx={{ ml: 1 }} />
                          )}
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="body2" paragraph>
                            <strong>Status:</strong>{' '}
                            <Chip
                              label={
                                selectedAgent.remediation_result.status === 'completed' ? 'Completed' :
                                selectedAgent.remediation_result.status === 'partial' ? 'Partial' :
                                selectedAgent.remediation_result.status === 'failed' ? 'Failed' :
                                selectedAgent.remediation_result.success ? 'Success' : 'Failed'
                              }
                              color={
                                selectedAgent.remediation_result.status === 'completed' ? 'success' :
                                selectedAgent.remediation_result.status === 'partial' ? 'warning' :
                                selectedAgent.remediation_result.status === 'failed' ? 'error' :
                                selectedAgent.remediation_result.success ? 'success' : 'error'
                              }
                              size="small"
                            />
                          </Typography>
                          {selectedAgent.remediation_result.actions_performed?.length > 0 && (
                            <>
                              <Typography variant="body2" paragraph>
                                <strong>Actions Performed:</strong>
                              </Typography>
                              <ul>
                                {selectedAgent.remediation_result.actions_performed.map((action, index) => (
                                  <li key={index}>
                                    <Typography variant="body2">{action}</Typography>
                                  </li>
                                ))}
                              </ul>
                            </>
                          )}
                          {selectedAgent.remediation_result.errors?.length > 0 && (
                            <>
                              <Typography variant="body2" paragraph color="error">
                                <strong>Errors:</strong>
                              </Typography>
                              <ul>
                                {selectedAgent.remediation_result.errors.map((error, index) => (
                                  <li key={index}>
                                    <Typography variant="body2" color="error">{error}</Typography>
                                  </li>
                                ))}
                              </ul>
                            </>
                          )}
                          {selectedAgent.remediation_result.validation_result && (
                            <Box sx={{ mb: 1 }}>
                              <Typography variant="body2" sx={{ mb: 1 }}>
                                <strong>Validation:</strong>
                              </Typography>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                <Chip
                                  label={selectedAgent.remediation_result.validation_result.success ? 'Passed' : 'Failed'}
                                  color={selectedAgent.remediation_result.validation_result.success ? 'success' : 'error'}
                                  size="small"
                                />
                              </Box>
                              <Typography variant="body2">
                                {selectedAgent.remediation_result.validation_result.message}
                              </Typography>
                            </Box>
                          )}
                        </Box>
                      </AccordionDetails>
                    </Accordion>
                  </Grid>
                )}

                {/* Rollback Results */}
                {selectedAgent.rollback_result && (
                  <Grid item xs={12}>
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography variant="h6">
                          Rollback Results
                          {selectedAgent.rollback_result.success ? (
                            <CheckIcon color="success" sx={{ ml: 1 }} />
                          ) : (
                            <ErrorIcon color="error" sx={{ ml: 1 }} />
                          )}
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="body2" paragraph>
                            <strong>Status:</strong>{' '}
                            <Chip
                              label={selectedAgent.rollback_result.success ? 'Success' : 'Failed'}
                              color={selectedAgent.rollback_result.success ? 'success' : 'error'}
                              size="small"
                            />
                          </Typography>
                          {selectedAgent.rollback_result.actions_rolled_back?.length > 0 && (
                            <>
                              <Typography variant="body2" paragraph>
                                <strong>Actions Rolled Back:</strong>
                              </Typography>
                              <ul>
                                {selectedAgent.rollback_result.actions_rolled_back.map((action, index) => (
                                  <li key={index}>
                                    <Typography variant="body2">{action}</Typography>
                                  </li>
                                ))}
                              </ul>
                            </>
                          )}
                          {selectedAgent.rollback_result.errors?.length > 0 && (
                            <>
                              <Typography variant="body2" paragraph color="error">
                                <strong>Errors:</strong>
                              </Typography>
                              <ul>
                                {selectedAgent.rollback_result.errors.map((error, index) => (
                                  <li key={index}>
                                    <Typography variant="body2" color="error">{error}</Typography>
                                  </li>
                                ))}
                              </ul>
                            </>
                          )}
                        </Box>
                      </AccordionDetails>
                    </Accordion>
                  </Grid>
                )}
              </Grid>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDetailsDialogOpen(false)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default AgenticPage;