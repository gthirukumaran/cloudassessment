import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Card,
  CardContent,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  CircularProgress,
  Alert,
  Button,
  Divider
} from '@mui/material';
import {
  Security as SecurityIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import { useParams } from 'react-router-dom';

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

interface ScanDetail {
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

const ScanDetailPage: React.FC = () => {
  const { scanId } = useParams<{ scanId: string }>();
  const [scanDetail, setScanDetail] = useState<ScanDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchScanDetail();
  }, [scanId]);

  const fetchScanDetail = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://127.0.0.1:9099/api/v1/scans/${scanId}/status`);
      if (response.ok) {
        const data = await response.json();
        setScanDetail(data.scan);
      } else {
        setError('Failed to fetch scan details');
      }
    } catch (err) {
      setError('Error fetching scan details');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <ErrorIcon color="error" />;
      case 'high': return <WarningIcon color="warning" />;
      case 'medium': return <InfoIcon color="info" />;
      case 'low': return <CheckCircleIcon color="success" />;
      default: return <InfoIcon />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error || !scanDetail) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          Scan Details
        </Typography>
        <Alert severity="error">
          {error || 'Scan not found'}
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Scan Details
        </Typography>
        {scanDetail.status === 'completed' && (
          <Button variant="contained" startIcon={<DownloadIcon />}>
            Download Report
          </Button>
        )}
      </Box>

      <Grid container spacing={3}>
        {/* Scan Overview */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Scan Information
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">Scan ID</Typography>
                  <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>{scanDetail.scan_id}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">Framework</Typography>
                  <Chip label={scanDetail.framework} variant="outlined" size="small" />
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">Status</Typography>
                  <Chip 
                    label={scanDetail.status} 
                    color={scanDetail.status === 'completed' ? 'success' : scanDetail.status === 'failed' ? 'error' : 'primary'}
                    size="small"
                  />
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">Progress</Typography>
                  <Typography variant="body1">{scanDetail.progress}%</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">Start Time</Typography>
                  <Typography variant="body1">{new Date(scanDetail.start_time).toLocaleString()}</Typography>
                </Grid>
                {scanDetail.end_time && (
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">End Time</Typography>
                    <Typography variant="body1">{new Date(scanDetail.end_time).toLocaleString()}</Typography>
                  </Grid>
                )}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Results Summary */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Results Summary
              </Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">Total Checks</Typography>
                  <Typography variant="h6">{scanDetail.total_checks}</Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="success.main">Passed</Typography>
                  <Typography variant="h6" color="success.main">{scanDetail.passed_checks}</Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="error.main">Failed</Typography>
                  <Typography variant="h6" color="error.main">{scanDetail.failed_checks}</Typography>
                </Box>
                {scanDetail.compliance_score && (
                  <>
                    <Divider />
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="body2">Compliance Score</Typography>
                      <Typography 
                        variant="h6" 
                        color={scanDetail.compliance_score >= 80 ? 'success.main' : 'warning.main'}
                      >
                        {scanDetail.compliance_score}%
                      </Typography>
                    </Box>
                  </>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Findings */}
        {scanDetail.findings && scanDetail.findings.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Security Findings ({scanDetail.findings.length})
                </Typography>
                <List>
                  {scanDetail.findings.map((finding, index) => (
                    <ListItem key={index} divider>
                      <ListItemIcon>
                        {getSeverityIcon(finding.severity)}
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography variant="subtitle1">{finding.title}</Typography>
                            <Chip 
                              label={finding.severity} 
                              color={getSeverityColor(finding.severity) as any}
                              size="small"
                            />
                            <Chip 
                              label={finding.status} 
                              color={finding.status === 'passed' ? 'success' : finding.status === 'failed' ? 'error' : 'warning'}
                              size="small"
                            />
                          </Box>
                        }
                        secondary={
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="body2" paragraph>
                              {finding.description}
                            </Typography>
                            {finding.resource_name && (
                              <Typography variant="body2" sx={{ mb: 1 }}>
                                <strong>Resource:</strong> {finding.resource_name}
                              </Typography>
                            )}
                            {finding.resource_id && (
                              <Typography 
                                variant="caption" 
                                sx={{ 
                                  fontFamily: 'monospace', 
                                  display: 'block', 
                                  mb: 1, 
                                  color: 'text.secondary',
                                  wordBreak: 'break-all'
                                }}
                              >
                                <strong>Resource ID:</strong> {finding.resource_id}
                              </Typography>
                            )}
                            <Typography variant="caption" color="text.secondary">
                              <strong>Category:</strong> {finding.category}
                            </Typography>
                            <Typography variant="body2" sx={{ mt: 1, p: 1, bgcolor: 'action.hover', borderRadius: 1 }}>
                              <strong>Recommendation:</strong> {finding.recommendation}
                            </Typography>
                          </Box>
                        }
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
  );
};

export default ScanDetailPage;
