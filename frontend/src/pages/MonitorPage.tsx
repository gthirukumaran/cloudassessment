import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Switch,
  FormControlLabel,
  TextField,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Monitor as MonitorIcon,
  Refresh as RefreshIcon,
  SmartToy as AIIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';

interface MonitoringData {
  scanStatus: string;
  agentPerformance: {
    activeAgents: number;
    totalAgents: number;
    successRate: number;
  };
  activityLogs: Array<{
    timestamp: string;
    type: string;
    message: string;
    status: string;
  }>;
  emailNotificationStatus: {
    totalSent: number;
    successful: number;
    failed: number;
    lastSent: string;
    failureReasons: string[];
  };
}

const MonitorPage: React.FC = () => {
  const [monitoringData, setMonitoringData] = useState<MonitoringData>({
    scanStatus: 'idle',
    agentPerformance: {
      activeAgents: 0,
      totalAgents: 0,
      successRate: 0,
    },
    activityLogs: [],
    emailNotificationStatus: {
      totalSent: 0,
      successful: 0,
      failed: 0,
      lastSent: '',
      failureReasons: [],
    },
  });
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch monitoring data from backend
  const fetchMonitoringData = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://127.0.0.1:9099/api/v1/monitoring/status');
      const data = await response.json();
      if (data.success && data.monitoring) {
        setMonitoringData(data.monitoring);
        setError(null);
      } else {
        setError('Failed to fetch monitoring data: ' + (data.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error fetching monitoring data:', error);
      setError('Error fetching monitoring data: ' + (error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  // Handle AI analysis
  const handleAIAnalysis = async (item: any, type: string) => {
    try {
      const response = await fetch('http://127.0.0.1:9099/api/v1/monitoring/ai-analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          item,
          type,
        }),
      });
      const data = await response.json();
      if (data.success) {
        alert('AI Analysis: ' + data.analysis);
      } else {
        alert('Failed to get AI analysis: ' + data.error);
      }
    } catch (error) {
      console.error('Error getting AI analysis:', error);
      alert('Error getting AI analysis: ' + (error as Error).message);
    }
  };

  // Auto-refresh monitoring data
  useEffect(() => {
    let intervalId: NodeJS.Timeout;
    
    if (autoRefresh) {
      fetchMonitoringData();
      intervalId = setInterval(fetchMonitoringData, refreshInterval * 1000);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [autoRefresh, refreshInterval]);

  // Initial data fetch
  useEffect(() => {
    fetchMonitoringData();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'success':
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'error':
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      default:
        return <MonitorIcon color="primary" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
      case 'running':
        return 'success';
      case 'idle':
        return 'default';
      case 'error':
      case 'failed':
        return 'error';
      default:
        return 'primary';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <MonitorIcon color="primary" />
          System Monitor & Tracking
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
            }
            label="Auto Refresh"
          />
          <TextField
            label="Interval (s)"
            type="number"
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            size="small"
            sx={{ width: 120 }}
            disabled={!autoRefresh}
          />
          <IconButton
            onClick={fetchMonitoringData}
            disabled={loading}
            color="primary"
          >
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
          <CircularProgress />
        </Box>
      )}

      <Grid container spacing={3}>
        {/* System Status Cards */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Scan Status
              </Typography>
              <Chip
                label={monitoringData.scanStatus.toUpperCase()}
                color={getStatusColor(monitoringData.scanStatus) as any}
                variant="filled"
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Active Agents
              </Typography>
              <Typography variant="h4">
                {monitoringData.agentPerformance.activeAgents}/{monitoringData.agentPerformance.totalAgents}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Email Status
              </Typography>
              <Typography variant="h4">
                {monitoringData.emailNotificationStatus.successful}/{monitoringData.emailNotificationStatus.totalSent}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Success Rate
              </Typography>
              <Typography variant="h4" color="success.main">
                {monitoringData.agentPerformance.successRate}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Activity Logs */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Activity Logs
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Timestamp</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Message</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {monitoringData.activityLogs.length > 0 ? (
                      monitoringData.activityLogs.map((log, index) => (
                        <TableRow key={index}>
                          <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
                          <TableCell>
                            <Chip label={log.type} size="small" />
                          </TableCell>
                          <TableCell>{log.message}</TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              {getStatusIcon(log.status)}
                              {log.status}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Button
                              size="small"
                              startIcon={<AIIcon />}
                              onClick={() => handleAIAnalysis(log, 'activity_log')}
                            >
                              AI Analyze
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={5} align="center">
                          No activity logs available
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Email Notification Status */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Email Notification Details
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2">
                  Total Sent: <strong>{monitoringData.emailNotificationStatus.totalSent}</strong>
                </Typography>
                <Typography variant="body2">
                  Successful: <strong style={{ color: 'green' }}>{monitoringData.emailNotificationStatus.successful}</strong>
                </Typography>
                <Typography variant="body2">
                  Failed: <strong style={{ color: 'red' }}>{monitoringData.emailNotificationStatus.failed}</strong>
                </Typography>
                <Typography variant="body2">
                  Last Sent: <strong>{monitoringData.emailNotificationStatus.lastSent || 'Never'}</strong>
                </Typography>
              </Box>

              {monitoringData.emailNotificationStatus.failureReasons.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Recent Failure Reasons:
                  </Typography>
                  {monitoringData.emailNotificationStatus.failureReasons.map((reason, index) => (
                    <Box key={index} sx={{ mb: 1, p: 1, bgcolor: 'error.light', borderRadius: 1 }}>
                      <Typography variant="body2" color="error.contrastText">
                        {reason}
                      </Typography>
                      <Button
                        size="small"
                        startIcon={<AIIcon />}
                        onClick={() => handleAIAnalysis({ error: reason, type: 'email_failure' }, 'failure_reason')}
                        sx={{ mt: 1 }}
                      >
                        Get AI Recommendations
                      </Button>
                    </Box>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MonitorPage;