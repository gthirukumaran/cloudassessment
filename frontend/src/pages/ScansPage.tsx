import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  IconButton,
  Tooltip,
  Grid,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Checkbox,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Radio,
  RadioGroup,
  FormLabel
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Visibility as ViewIcon,
  Download as DownloadIcon,
  Security as SecurityIcon,
  Schedule as ScheduleIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  ExpandMore as ExpandMoreIcon,
  Info as InfoIcon,
  PriorityHigh as CriticalIcon,
  Warning as HighIcon,
  Info as MediumIcon,
  CheckCircle as LowIcon,
  Cancel as CancelIcon
} from '@mui/icons-material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

interface Subscription {
  id: string;
  name: string;
  status: string;
  resource_groups_count: number;
  compliance_score?: number;
}

interface Scan {
  scan_id: string;
  subscription_id: string;
  framework: string;
  status: string;
  start_time: string;
  end_time?: string;
  progress: number;
  total_checks: number;
  passed_checks: number;
  failed_checks: number;
  compliance_score?: number;
  findings?: ScanFinding[];
}

interface ScanFinding {
  id: string;
  title: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  category: string;
  recommendation: string;
  status: 'passed' | 'failed' | 'warning';
  resource_id?: string;
  resource_name?: string;
}

interface CISControl {
  id: string;
  title: string;
  description: string;
  category: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  checks: CISCheck[];
}

interface CISCheck {
  id: string;
  title: string;
  description: string;
  impact: string;
  remediation: string;
  references: string[];
}

const ScansPage: React.FC = () => {
  const location = useLocation();
  const [scans, setScans] = useState<Scan[]>([]);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [frameworks, setFrameworks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [openDetailsDialog, setOpenDetailsDialog] = useState(false);
  const [selectedScan, setSelectedScan] = useState<Scan | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  
  // New scan form state
  const [newScan, setNewScan] = useState({
    subscription_id: '',
    framework: '',
    resource_groups: [] as string[],
    exclude_resources: [] as string[],
    severity_filter: 'all',
    notify_email: '',
    scan_mode: 'immediate' as 'immediate' | 'scheduled'
  });
  const [scheduledDateTime, setScheduledDateTime] = useState<Date | null>(null);
  const [selectedCISControls, setSelectedCISControls] = useState<string[]>([]);

  // CIS Standards Data
  const cisControls: CISControl[] = [
    {
      id: "CIS-1.1",
      title: "Ensure multi-factor authentication is enabled for all privileged users",
      description: "Multi-factor authentication adds an extra layer of protection on top of username and password. When enabled, users must provide additional verification when signing in.",
      category: "Identity and Access Management",
      severity: "critical",
      checks: [
        {
          id: "CIS-1.1.1",
          title: "MFA for Global Administrators",
          description: "Ensure that multi-factor authentication is enabled for all users with Global Administrator role",
          impact: "Critical - Global Administrators have full access to all resources and can bypass all security controls",
          remediation: "Enable MFA for all Global Administrator accounts through Azure Active Directory > Users > Multi-factor authentication",
          references: ["https://docs.microsoft.com/en-us/azure/active-directory/authentication/tutorial-enable-azure-mfa"]
        },
        {
          id: "CIS-1.1.2", 
          title: "MFA for Subscription Owners",
          description: "Ensure that multi-factor authentication is enabled for all users with Owner role on subscriptions",
          impact: "High - Subscription Owners can manage all resources and billing within the subscription",
          remediation: "Enable MFA for all Owner accounts through Azure Active Directory > Users > Multi-factor authentication",
          references: ["https://docs.microsoft.com/en-us/azure/active-directory/authentication/tutorial-enable-azure-mfa"]
        }
      ]
    },
    {
      id: "CIS-1.2",
      title: "Ensure standard security practices are implemented",
      description: "Implement security best practices including secure password policies, account lockout policies, and session management.",
      category: "Identity and Access Management", 
      severity: "high",
      checks: [
        {
          id: "CIS-1.2.1",
          title: "Password Policy Compliance",
          description: "Ensure password policy meets minimum requirements: 8+ characters, complexity, expiration",
          impact: "High - Weak passwords increase risk of unauthorized access",
          remediation: "Configure password policy in Azure AD > Authentication methods > Password protection",
          references: ["https://docs.microsoft.com/en-us/azure/active-directory/authentication/concept-password-ban-bad"]
        }
      ]
    },
    {
      id: "CIS-2.1", 
      title: "Ensure security monitoring is enabled",
      description: "Enable Azure Security Center and configure security monitoring for all resources.",
      category: "Security Monitoring",
      severity: "critical",
      checks: [
        {
          id: "CIS-2.1.1",
          title: "Security Center Standard Tier",
          description: "Ensure Azure Security Center is set to Standard tier for enhanced security monitoring",
          impact: "Critical - Standard tier provides advanced threat protection and security recommendations",
          remediation: "Upgrade to Security Center Standard tier in Azure Portal > Security Center > Pricing & settings",
          references: ["https://docs.microsoft.com/en-us/azure/security-center/security-center-pricing"]
        },
        {
          id: "CIS-2.1.2",
          title: "Auto Provisioning Enabled",
          description: "Ensure auto provisioning of monitoring agents is enabled for all supported resource types",
          impact: "High - Auto provisioning ensures security monitoring is active on all resources",
          remediation: "Enable auto provisioning in Security Center > Management > Security policy",
          references: ["https://docs.microsoft.com/en-us/azure/security-center/security-center-enable-data-collection"]
        }
      ]
    },
    {
      id: "CIS-3.1",
      title: "Ensure network security groups are configured",
      description: "Configure network security groups to restrict network traffic and implement least privilege access.",
      category: "Network Security",
      severity: "high", 
      checks: [
        {
          id: "CIS-3.1.1",
          title: "NSG on All Subnets",
          description: "Ensure all subnets have network security groups applied",
          impact: "High - Unprotected subnets allow unrestricted network access",
          remediation: "Create and assign NSGs to all subnets in Virtual Networks",
          references: ["https://docs.microsoft.com/en-us/azure/virtual-network/network-security-groups-overview"]
        },
        {
          id: "CIS-3.1.2",
          title: "Restrict RDP Access",
          description: "Ensure RDP access is restricted to specific IP ranges",
          impact: "Critical - Open RDP access increases attack surface",
          remediation: "Configure NSG rules to restrict RDP (port 3389) to authorized IP ranges",
          references: ["https://docs.microsoft.com/en-us/azure/virtual-network/network-security-groups-overview"]
        }
      ]
    },
    {
      id: "CIS-4.1",
      title: "Ensure encryption is enabled for storage accounts",
      description: "Enable encryption at rest for all storage accounts to protect data.",
      category: "Data Protection",
      severity: "critical",
      checks: [
        {
          id: "CIS-4.1.1", 
          title: "Storage Account Encryption",
          description: "Ensure storage account encryption is enabled for all storage accounts",
          impact: "Critical - Unencrypted storage accounts expose sensitive data",
          remediation: "Enable encryption in Storage Account > Settings > Encryption",
          references: ["https://docs.microsoft.com/en-us/azure/storage/common/storage-service-encryption"]
        }
      ]
    },
    {
      id: "CIS-5.1",
      title: "Ensure logging and monitoring is configured",
      description: "Configure comprehensive logging and monitoring for all Azure resources.",
      category: "Logging and Monitoring",
      severity: "high",
      checks: [
        {
          id: "CIS-5.1.1",
          title: "Activity Log Retention",
          description: "Ensure activity logs are retained for at least 365 days",
          impact: "High - Insufficient log retention limits audit and compliance capabilities",
          remediation: "Configure log retention in Log Analytics workspace > General > Usage and estimated costs",
          references: ["https://docs.microsoft.com/en-us/azure/azure-monitor/platform/manage-cost-storage"]
        },
        {
          id: "CIS-5.1.2",
          title: "Diagnostic Settings",
          description: "Ensure diagnostic settings are enabled for all supported resources",
          impact: "Medium - Missing diagnostic settings reduce visibility into resource operations",
          remediation: "Enable diagnostic settings for all resources in Azure Monitor > Diagnostic settings",
          references: ["https://docs.microsoft.com/en-us/azure/azure-monitor/platform/diagnostic-settings"]
        }
      ]
    }
  ];

  const fetchFrameworks = async () => {
    try {
      const response = await fetch('/api/v1/compliance/frameworks/test');
      if (response.ok) {
        const data = await response.json();
        // Transform API response to match the expected format
        const transformedFrameworks = data.frameworks.map((framework: any) => ({
          value: framework.id,
          label: framework.display_name,
          description: framework.description || 'Custom compliance framework',
          controls: framework.controls_count || 0,
          estimatedTime: '15-30 minutes' // Default estimate
        }));
        setFrameworks(transformedFrameworks);
      } else {
        // Fallback to hardcoded frameworks if API fails
        setFrameworks([
          { 
            value: 'CIS', 
            label: 'CIS Benchmarks', 
            description: 'Center for Internet Security Benchmarks - Comprehensive security controls for Azure',
            controls: cisControls.length,
            estimatedTime: '15-30 minutes'
          },
          { 
            value: 'SOC2', 
            label: 'SOC 2 Type II', 
            description: 'Service Organization Control 2 - Security, availability, processing integrity, confidentiality, and privacy',
            controls: 45,
            estimatedTime: '10-20 minutes'
          },
          { 
            value: 'NIST', 
            label: 'NIST Framework', 
            description: 'National Institute of Standards and Technology Cybersecurity Framework',
            controls: 60,
            estimatedTime: '20-40 minutes'
          },
          { 
            value: 'ISO27001', 
            label: 'ISO 27001', 
            description: 'International Security Management Standard - Information security management system',
            controls: 55,
            estimatedTime: '25-35 minutes'
          }
        ]);
      }
    } catch (error) {
      console.error('Failed to fetch frameworks:', error);
      // Fallback to hardcoded frameworks
      setFrameworks([
        { 
          value: 'CIS', 
          label: 'CIS Benchmarks', 
          description: 'Center for Internet Security Benchmarks - Comprehensive security controls for Azure',
          controls: cisControls.length,
          estimatedTime: '15-30 minutes'
        },
        { 
          value: 'SOC2', 
          label: 'SOC 2 Type II', 
          description: 'Service Organization Control 2 - Security, availability, processing integrity, confidentiality, and privacy',
          controls: 45,
          estimatedTime: '10-20 minutes'
        },
        { 
          value: 'NIST', 
          label: 'NIST Framework', 
          description: 'National Institute of Standards and Technology Cybersecurity Framework',
          controls: 60,
          estimatedTime: '20-40 minutes'
        },
        { 
          value: 'ISO27001', 
          label: 'ISO 27001', 
          description: 'International Security Management Standard - Information security management system',
          controls: 55,
          estimatedTime: '25-35 minutes'
        }
      ]);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchScans, 5000); // Refresh scans every 5 seconds
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Handle navigation from ComplianceFrameworksPage
    if (location.state?.selectedFramework && location.state?.openDialog) {
      const selectedFramework = location.state.selectedFramework;
      setNewScan(prev => ({
        ...prev,
        framework: selectedFramework.id
      }));
      setOpenDialog(true);
      // Clear the state to prevent reopening on refresh
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const fetchData = async () => {
    await Promise.all([fetchSubscriptions(), fetchScans(), fetchFrameworks()]);
    setLoading(false);
  };

  const fetchSubscriptions = async () => {
    try {
      const response = await fetch('http://127.0.0.1:9099/api/v1/subscriptions');
      const data = await response.json();
      setSubscriptions(data.subscriptions || []);
    } catch (error) {
      console.error('Error fetching subscriptions:', error);
    }
  };

  const fetchScans = async () => {
    try {
      const response = await fetch('http://127.0.0.1:9099/api/v1/scans');
      const data = await response.json();
      setScans(data.scans || []);
    } catch (error) {
      console.error('Error fetching scans:', error);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchScans();
    setRefreshing(false);
  };

  const handleCreateScan = async () => {
    try {
      let endpoint = 'http://127.0.0.1:9099/api/v1/scans';
      let payload: any = {
        ...newScan,
        selected_controls: newScan.framework === 'CIS' ? selectedCISControls : []
      };

      if (newScan.scan_mode === 'scheduled' && scheduledDateTime) {
        endpoint = 'http://127.0.0.1:9099/api/v1/scans/schedule';
        payload = {
          ...payload,
          scheduled_at: scheduledDateTime.toISOString()
        };
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Scan created:', result);
        setOpenDialog(false);
        resetScanForm();
        await fetchScans();
      } else {
        console.error('Failed to create scan');
      }
    } catch (error) {
      console.error('Error creating scan:', error);
    }
  };

  const resetScanForm = () => {
    setNewScan({
      subscription_id: '',
      framework: '',
      resource_groups: [],
      exclude_resources: [],
      severity_filter: 'all',
      notify_email: '',
      scan_mode: 'immediate'
    });
    setScheduledDateTime(null);
    setSelectedCISControls([]);
  };

  const handleCancelScan = async (scanId: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:9099/api/v1/scans/${scanId}/cancel`, { method: 'POST' });
      if (res.ok) await fetchScans();
    } catch (e) { console.error('Cancel failed', e); }
  };

  const handleViewDetails = async (scan: Scan) => {
    setSelectedScan(scan);
    setOpenDetailsDialog(true);
  };

  const handleDownloadReport = async (scanId: string) => {
    try {
      const response = await fetch(`http://127.0.0.1:9099/api/v1/scans/${scanId}/download`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `scan-report-${scanId}.html`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        console.error('Failed to download report');
      }
    } catch (error) {
      console.error('Error downloading report:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'in_progress':
        return <CircularProgress size={20} />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'scheduled':
        return <ScheduleIcon color="info" />;
      case 'canceled':
        return <CancelIcon color="action" />;
      default:
        return <ScheduleIcon color="action" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'in_progress':
        return 'primary';
      case 'failed':
        return 'error';
      case 'scheduled':
        return 'info';
      case 'canceled':
        return 'default';
      default:
        return 'default';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <CriticalIcon color="error" />;
      case 'high':
        return <HighIcon color="warning" />;
      case 'medium':
        return <MediumIcon color="info" />;
      case 'low':
        return <LowIcon color="success" />;
      default:
        return <InfoIcon />;
    }
  };

  const formatDuration = (startTime: string, endTime?: string) => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = Math.round((end.getTime() - start.getTime()) / (1000 * 60)); // in minutes
    
    if (duration < 60) {
      return `${duration}m`;
    } else {
      const hours = Math.floor(duration / 60);
      const minutes = duration % 60;
      return `${hours}h ${minutes}m`;
    }
  };

  const handleCISControlToggle = (controlId: string) => {
    setSelectedCISControls(prev => 
      prev.includes(controlId) 
        ? prev.filter(id => id !== controlId)
        : [...prev, controlId]
    );
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" component="h1">
            Security Scans
          </Typography>
          <Box>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={handleRefresh}
              disabled={refreshing}
              sx={{ mr: 2 }}
            >
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setOpenDialog(true)}
            >
              New Scan
            </Button>
          </Box>
        </Box>

        {/* Summary Cards */}
        <Grid container spacing={3} mb={3}>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <SecurityIcon color="primary" sx={{ mr: 2 }} />
                  <Box>
                    <Typography variant="h6">{scans.length}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Scans
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <PlayIcon color="primary" sx={{ mr: 2 }} />
                  <Box>
                    <Typography variant="h6">
                      {scans.filter(s => s.status === 'in_progress').length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      In Progress
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <CheckCircleIcon color="success" sx={{ mr: 2 }} />
                  <Box>
                    <Typography variant="h6">
                      {scans.filter(s => s.status === 'completed').length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Completed
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <ErrorIcon color="error" sx={{ mr: 2 }} />
                  <Box>
                    <Typography variant="h6">
                      {scans.filter(s => s.status === 'failed').length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Failed
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Scans Table */}
        <Paper>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Status</TableCell>
                  <TableCell>Scan ID</TableCell>
                  <TableCell>Subscription</TableCell>
                  <TableCell>Framework</TableCell>
                  <TableCell>Progress</TableCell>
                  <TableCell>Start Time</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Compliance</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {scans.map((scan) => {
                  const subscription = subscriptions.find(s => s.id === scan.subscription_id);
                  return (
                    <TableRow key={scan.scan_id}>
                      <TableCell>
                        <Box display="flex" alignItems="center">
                          {getStatusIcon(scan.status)}
                          <Chip
                            label={scan.status}
                            color={getStatusColor(scan.status) as any}
                            size="small"
                            sx={{ ml: 1 }}
                          />
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {scan.scan_id}
                        </Typography>
                      </TableCell>
                      <TableCell>{subscription?.name || scan.subscription_id}</TableCell>
                      <TableCell>
                        <Chip label={scan.framework} variant="outlined" size="small" />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ width: '100%' }}>
                          <LinearProgress
                            variant="determinate"
                            value={scan.progress || 0}
                            sx={{ mb: 1 }}
                          />
                          <Typography variant="caption">
                            {scan.progress || 0}% ({scan.passed_checks + scan.failed_checks}/{scan.total_checks})
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {new Date(scan.start_time).toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatDuration(scan.start_time, scan.end_time)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {scan.compliance_score ? (
                          <Typography variant="body2" color={scan.compliance_score >= 80 ? 'success.main' : 'warning.main'}>
                            {scan.compliance_score}%
                          </Typography>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            N/A
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Tooltip title="View Details">
                          <IconButton size="small" onClick={() => handleViewDetails(scan)}>
                            <ViewIcon />
                          </IconButton>
                        </Tooltip>
                        {scan.status !== 'completed' && scan.status !== 'failed' && scan.status !== 'canceled' && (
                          <Tooltip title="Cancel Scan">
                            <IconButton size="small" onClick={() => handleCancelScan(scan.scan_id)}>
                              <StopIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                        {scan.status === 'completed' && (
                          <Tooltip title="Download Report">
                            <IconButton size="small" onClick={() => handleDownloadReport(scan.scan_id)}>
                              <DownloadIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
                {scans.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={9} align="center">
                      <Typography variant="body2" color="text.secondary" py={3}>
                        No scans found. Create your first security scan using the "New Scan" button.
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        {/* New Scan Dialog */}
        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="lg" fullWidth>
          <DialogTitle>Create New Security Scan</DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 2 }}>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <FormControl fullWidth required>
                    <InputLabel>Azure Subscription</InputLabel>
                    <Select
                      value={newScan.subscription_id}
                      label="Azure Subscription"
                      onChange={(e) => setNewScan({ ...newScan, subscription_id: e.target.value })}
                    >
                      {subscriptions.map((sub) => (
                        <MenuItem key={sub.id} value={sub.id}>
                          <Box>
                            <Typography variant="body1">{sub.name}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {sub.resource_groups_count} resource groups • {sub.status}
                            </Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12}>
                  <FormControl fullWidth required>
                    <InputLabel>Compliance Framework</InputLabel>
                    <Select
                      value={newScan.framework}
                      label="Compliance Framework"
                      onChange={(e) => setNewScan({ ...newScan, framework: e.target.value })}
                    >
                      {frameworks.map((framework) => (
                        <MenuItem key={framework.value} value={framework.value}>
                          <Box>
                            <Typography variant="body1">{framework.label}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {framework.description} • {framework.controls} controls • ~{framework.estimatedTime}
                            </Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                {/* CIS Controls Selection */}
                {newScan.framework === 'CIS' && (
                  <Grid item xs={12}>
                    <Alert severity="info" sx={{ mb: 2 }}>
                      <Typography variant="body2">
                        <strong>CIS Benchmarks:</strong> Select specific controls to scan. All controls are selected by default.
                      </Typography>
                    </Alert>
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography variant="h6">CIS Controls ({selectedCISControls.length}/{cisControls.length} selected)</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Grid container spacing={2}>
                          {cisControls.map((control) => (
                            <Grid item xs={12} key={control.id}>
                              <Card variant="outlined">
                                <CardContent>
                                  <Box display="flex" alignItems="flex-start">
                                    <Checkbox
                                      checked={selectedCISControls.includes(control.id)}
                                      onChange={() => handleCISControlToggle(control.id)}
                                      sx={{ mt: 0 }}
                                    />
                                    <Box sx={{ flex: 1 }}>
                                      <Box display="flex" alignItems="center" mb={1}>
                                        <Typography variant="h6" sx={{ mr: 1 }}>
                                          {control.id}
                                        </Typography>
                                        {getSeverityIcon(control.severity)}
                                        <Chip 
                                          label={control.severity} 
                                          size="small" 
                                          color={control.severity === 'critical' ? 'error' : control.severity === 'high' ? 'warning' : 'default'}
                                          sx={{ ml: 1 }}
                                        />
                                      </Box>
                                      <Typography variant="body1" gutterBottom>
                                        {control.title}
                                      </Typography>
                                      <Typography variant="body2" color="text.secondary" paragraph>
                                        {control.description}
                                      </Typography>
                                      <Typography variant="caption" color="text.secondary">
                                        Category: {control.category} • {control.checks.length} checks
                                      </Typography>
                                    </Box>
                                  </Box>
                                </CardContent>
                              </Card>
                            </Grid>
                          ))}
                        </Grid>
                      </AccordionDetails>
                    </Accordion>
                  </Grid>
                )}

                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Severity Filter</InputLabel>
                    <Select
                      value={newScan.severity_filter}
                      label="Severity Filter"
                      onChange={(e) => setNewScan({ ...newScan, severity_filter: e.target.value })}
                    >
                      <MenuItem value="all">All Severities</MenuItem>
                      <MenuItem value="critical">Critical Only</MenuItem>
                      <MenuItem value="high">High and Above</MenuItem>
                      <MenuItem value="medium">Medium and Above</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12}>
                  <FormControl component="fieldset">
                    <FormLabel component="legend">Scan Mode</FormLabel>
                    <RadioGroup
                      row
                      value={newScan.scan_mode}
                      onChange={(e) => setNewScan({ ...newScan, scan_mode: e.target.value as 'immediate' | 'scheduled' })}
                    >
                      <FormControlLabel value="immediate" control={<Radio />} label="Start Now" />
                      <FormControlLabel value="scheduled" control={<Radio />} label="Schedule Later" />
                    </RadioGroup>
                  </FormControl>
                </Grid>

                {newScan.scan_mode === 'scheduled' && (
                  <Grid item xs={12}>
                    <DateTimePicker
                      label="Scheduled Date & Time"
                      value={scheduledDateTime}
                      onChange={(newValue) => setScheduledDateTime(newValue)}
                      minDateTime={new Date()}
                      slotProps={{
                        textField: {
                          fullWidth: true
                        }
                      }}
                    />
                  </Grid>
                )}

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Notification Email"
                    type="email"
                    value={newScan.notify_email}
                    onChange={(e) => setNewScan({ ...newScan, notify_email: e.target.value })}
                    helperText="Optional: Email address to notify when scan completes"
                  />
                </Grid>

                <Grid item xs={12}>
                  <Alert severity="info">
                    <Typography variant="body2">
                      <strong>Scan Information:</strong>
                    </Typography>
                    <Typography variant="caption" component="div" sx={{ mt: 1 }}>
                      • Framework: {frameworks.find(f => f.value === newScan.framework)?.label || 'Not selected'}<br/>
                      • Estimated Duration: {frameworks.find(f => f.value === newScan.framework)?.estimatedTime || 'Varies'}<br/>
                      • Controls: {newScan.framework === 'CIS' ? selectedCISControls.length : frameworks.find(f => f.value === newScan.framework)?.controls || 0}<br/>
                      • Mode: {newScan.scan_mode === 'immediate' ? 'Immediate' : 'Scheduled'}
                    </Typography>
                  </Alert>
                </Grid>
              </Grid>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
            <Button
              onClick={handleCreateScan}
              variant="contained"
              disabled={!newScan.subscription_id || !newScan.framework || (newScan.scan_mode === 'scheduled' && !scheduledDateTime)}
            >
              {newScan.scan_mode === 'immediate' ? 'Start Scan' : 'Schedule Scan'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Scan Details Dialog */}
        <Dialog open={openDetailsDialog} onClose={() => setOpenDetailsDialog(false)} maxWidth="lg" fullWidth>
          <DialogTitle>
            Scan Details - {selectedScan?.scan_id}
          </DialogTitle>
          <DialogContent>
            {selectedScan && (
              <Box sx={{ pt: 2 }}>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>Scan Information</Typography>
                        <List dense>
                          <ListItem>
                            <ListItemText 
                              primary="Status" 
                              secondary={
                                <Chip 
                                  label={selectedScan.status} 
                                  color={getStatusColor(selectedScan.status) as any}
                                  size="small"
                                />
                              }
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemText 
                              primary="Framework" 
                              secondary={selectedScan.framework}
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemText 
                              primary="Start Time" 
                              secondary={new Date(selectedScan.start_time).toLocaleString()}
                            />
                          </ListItem>
                          {selectedScan.end_time && (
                            <ListItem>
                              <ListItemText 
                                primary="End Time" 
                                secondary={new Date(selectedScan.end_time).toLocaleString()}
                              />
                            </ListItem>
                          )}
                          <ListItem>
                            <ListItemText 
                              primary="Duration" 
                              secondary={formatDuration(selectedScan.start_time, selectedScan.end_time)}
                            />
                          </ListItem>
                          <ListItem>
                            <ListItemText 
                              primary="Progress" 
                              secondary={`${selectedScan.progress}% (${selectedScan.passed_checks + selectedScan.failed_checks}/${selectedScan.total_checks})`}
                            />
                          </ListItem>
                          {selectedScan.compliance_score && (
                            <ListItem>
                              <ListItemText 
                                primary="Compliance Score" 
                                secondary={`${selectedScan.compliance_score}%`}
                              />
                            </ListItem>
                          )}
                        </List>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>Results Summary</Typography>
                        <Box display="flex" justifyContent="space-around" textAlign="center">
                          <Box>
                            <Typography variant="h4" color="success.main">
                              {selectedScan.passed_checks}
                            </Typography>
                            <Typography variant="body2">Passed</Typography>
                          </Box>
                          <Box>
                            <Typography variant="h4" color="error.main">
                              {selectedScan.failed_checks}
                            </Typography>
                            <Typography variant="body2">Failed</Typography>
                          </Box>
                          <Box>
                            <Typography variant="h4" color="primary.main">
                              {selectedScan.total_checks - (selectedScan.passed_checks + selectedScan.failed_checks)}
                            </Typography>
                            <Typography variant="body2">Pending</Typography>
                          </Box>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>

                  {selectedScan.findings && selectedScan.findings.length > 0 && (
                    <Grid item xs={12}>
                      <Card>
                        <CardContent>
                          <Typography variant="h6" gutterBottom>Findings</Typography>
                          <List>
                            {selectedScan.findings.map((finding, index) => (
                              <ListItem key={index} divider>
                                <ListItemIcon>
                                  {getSeverityIcon(finding.severity)}
                                </ListItemIcon>
                                <ListItemText
                                  primary={finding.title}
                                  secondary={
                                    <Box>
                                      <Typography variant="body2" paragraph>
                                        {finding.description}
                                      </Typography>
                                      {finding.resource_name && (
                                        <Typography variant="body2" sx={{ mb: 1 }}>
                                          <strong>Resource:</strong> {finding.resource_name}
                                        </Typography>
                                      )}
                                      {finding.resource_id && (
                                        <Typography variant="caption" sx={{ fontFamily: 'monospace', display: 'block', mb: 1, color: 'text.secondary' }}>
                                          <strong>Resource ID:</strong> {finding.resource_id}
                                        </Typography>
                                      )}
                                      <Typography variant="caption" color="text.secondary">
                                        <strong>Category:</strong> {finding.category} | <strong>Recommendation:</strong> {finding.recommendation}
                                      </Typography>
                                    </Box>
                                  }
                                />
                                <Chip 
                                  label={finding.status} 
                                  color={finding.status === 'passed' ? 'success' : finding.status === 'failed' ? 'error' : 'warning'}
                                  size="small"
                                />
                              </ListItem>
                            ))}
                          </List>
                        </CardContent>
                      </Card>
                    </Grid>
                  )}
                </Grid>
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenDetailsDialog(false)}>Close</Button>
            {selectedScan?.status === 'completed' && (
              <Button variant="contained" startIcon={<DownloadIcon />}>
                Download Report
              </Button>
            )}
          </DialogActions>
        </Dialog>
      </Box>
    </LocalizationProvider>
  );
};

export default ScansPage;