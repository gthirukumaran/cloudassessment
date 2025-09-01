import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  Avatar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  LinearProgress,
  Divider,
  IconButton,
} from '@mui/material';
import {
  Description as ReportIcon,
  Download as DownloadIcon,
  Add as AddIcon,
  Security as SecurityIcon,
  Assessment as AssessmentIcon,
  CheckCircle as CheckIcon,
  Schedule as ScheduleIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

interface Report {
  report_id: string;
  scan_id: string;
  subscription_id: string;
  framework: string;
  generated_at: string;
  compliance_score: number;
  status: string;
  executive_summary: string;
  file_size: string;
}

const ReportsPage: React.FC = () => {
  const { user, token } = useAuth();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [newReport, setNewReport] = useState({
    type: 'CIS',
    environment: 'production',
    scan_id: ''
  });
  
  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const response = await fetch('http://127.0.0.1:9099/api/v1/reports');
      const data = await response.json();
      setReports(data.reports);
    } catch (error) {
      console.error('Error fetching reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    try {
      const response = await fetch('http://127.0.0.1:9099/api/v1/reports', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newReport),
      });
      
      if (response.ok) {
        fetchReports();
        setOpenDialog(false);
        setNewReport({ type: 'CIS', environment: 'production', scan_id: '' });
      }
    } catch (error) {
      console.error('Error generating report:', error);
    }
  };

  const downloadReport = async (reportId: string) => {
    try {
      console.log(`🔄 Downloading report ${reportId}...`);
      const response = await fetch(`http://127.0.0.1:9099/api/v1/reports/${reportId}/download`);
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `securra-report-${reportId}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        console.log(`✅ Report ${reportId} downloaded successfully`);
      } else {
        console.error(`❌ Failed to download report: ${response.status}`);
        alert('Failed to download report. Please try again.');
      }
    } catch (error) {
      console.error('❌ Error downloading report:', error);
      alert('Error downloading report. Please check if the backend is running.');
    }
  };

  const viewReport = async (reportId: string) => {
    try {
      console.log(`👁️ Viewing report ${reportId}...`);
      const response = await fetch(`http://127.0.0.1:9099/api/v1/reports/${reportId}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const report = await response.json();
      const msg = [
        `Report: ${report.framework} Compliance Report`,
        `Score: ${report.compliance_score ?? 'N/A'}%`,
        `Generated: ${report.generated_at}`,
        `Status: ${report.status}`,
        report.executive_summary ? `\nSummary: ${report.executive_summary}` : ''
      ].join('\n');
      alert(msg);
    } catch (err) {
      console.error('❌ Error viewing report:', err);
      alert('Error viewing report.');
    }
  };

  const deleteReport = async (reportId: string) => {
    if (!isAdmin) {
      alert('Admin access required to delete reports.');
      return;
    }

    if (!confirm('Are you sure you want to delete this report? This action cannot be undone.')) {
      return;
    }

    try {
      console.log(`🗑️ Deleting report ${reportId}...`);
      const response = await fetch(`http://127.0.0.1:9099/api/v1/reports/${reportId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        console.log(`✅ Report ${reportId} deleted successfully`);
        fetchReports(); // Refresh the reports list
        alert('Report deleted successfully.');
      } else {
        const errorData = await response.json();
        console.error(`❌ Failed to delete report: ${response.status}`, errorData);
        alert(`Failed to delete report: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('❌ Error deleting report:', error);
      alert('Error deleting report. Please check if the backend is running.');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'generated': return 'success';
      case 'generating': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const getComplianceColor = (score?: number) => {
    if (!score) return 'text.secondary';
    if (score >= 90) return 'success.main';
    if (score >= 70) return 'warning.main';
    return 'error.main';
  };

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2 }}>Loading reports...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Compliance Reports
          </Typography>
          <Typography variant="body1" color="text.secondary">
            CIS, SOC, and NIST compliance reports for executive review
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpenDialog(true)}
          sx={{ height: 'fit-content' }}
        >
          Generate Report
        </Button>
      </Box>

      {/* Report Types Overview */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ textAlign: 'center', backgroundColor: 'primary.light' }}>
            <CardContent>
              <Avatar sx={{ bgcolor: 'primary.main', mx: 'auto', mb: 2 }}>
                <SecurityIcon />
              </Avatar>
              <Typography variant="h6" gutterBottom>
                CIS Benchmarks
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Center for Internet Security configuration standards
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ textAlign: 'center', backgroundColor: 'secondary.light' }}>
            <CardContent>
              <Avatar sx={{ bgcolor: 'secondary.main', mx: 'auto', mb: 2 }}>
                <AssessmentIcon />
              </Avatar>
              <Typography variant="h6" gutterBottom>
                SOC 2 Type II
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Service Organization Control reports for compliance
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ textAlign: 'center', backgroundColor: 'info.light' }}>
            <CardContent>
              <Avatar sx={{ bgcolor: 'info.main', mx: 'auto', mb: 2 }}>
                <ReportIcon />
              </Avatar>
              <Typography variant="h6" gutterBottom>
                NIST Framework
              </Typography>
              <Typography variant="body2" color="text.secondary">
                National Institute of Standards cybersecurity framework
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Reports List */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Generated Reports
        </Typography>
        
        {reports.length === 0 ? (
          <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
            No reports generated yet. Click "Generate Report" to create your first compliance report.
          </Typography>
        ) : (
          <Grid container spacing={3}>
            {reports.map((report) => (
              <Grid item xs={12} key={report.report_id}>
                <Card sx={{ '&:hover': { boxShadow: 4 } }}>
                  <CardContent>
                    <Grid container spacing={3} alignItems="center">
                      <Grid item xs={12} md={6}>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                            <ReportIcon />
                          </Avatar>
                          <Box>
                            <Typography variant="h6">{report.framework} Compliance Report</Typography>
                            <Typography variant="body2" color="text.secondary">
                              {report.subscription_id} • {new Date(report.generated_at).toLocaleDateString()}
                            </Typography>
                          </Box>
                        </Box>
                      </Grid>
                      
                      <Grid item xs={12} md={3}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Chip
                            label={report.framework}
                            color="primary"
                            variant="outlined"
                            sx={{ mb: 1 }}
                          />
                          <br />
                          <Chip
                            label={report.status}
                            color={getStatusColor(report.status) as any}
                            icon={report.status === 'generated' ? <CheckIcon /> : <ScheduleIcon />}
                          />
                        </Box>
                      </Grid>
                      
                      <Grid item xs={12} md={1}>
                        {report.compliance_score && (
                          <Box sx={{ textAlign: 'center' }}>
                            <Typography 
                              variant="h4" 
                              sx={{ color: getComplianceColor(report.compliance_score) }}
                            >
                              {report.compliance_score}%
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Compliance Score
                            </Typography>
                          </Box>
                        )}
                      </Grid>
                      
                      <Grid item xs={12} md={2}>
                        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                          {report.status === 'generated' && (
                            <Button
                              variant="outlined"
                              startIcon={<DownloadIcon />}
                              onClick={() => downloadReport(report.report_id)}
                              size="small"
                            >
                              Download
                            </Button>
                          )}
                          {isAdmin && (
                            <IconButton
                              color="error"
                              onClick={() => deleteReport(report.report_id)}
                              size="small"
                              title="Delete Report (Admin Only)"
                            >
                              <DeleteIcon />
                            </IconButton>
                          )}
                        </Box>
                      </Grid>
                    </Grid>
                    
                    <Divider sx={{ my: 2 }} />
                    
                    <Typography variant="body2" color="text.secondary">
                      <strong>Executive Summary:</strong> {report.executive_summary}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Paper>

      {/* Generate Report Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Generate Compliance Report</DialogTitle>
        <DialogContent>
          <TextField
            select
            label="Report Type"
            value={newReport.type}
            onChange={(e) => setNewReport({ ...newReport, type: e.target.value })}
            fullWidth
            margin="normal"
          >
            <MenuItem value="CIS">CIS Benchmark</MenuItem>
            <MenuItem value="SOC">SOC 2 Type II</MenuItem>
            <MenuItem value="NIST">NIST Framework</MenuItem>
            <MenuItem value="ISO27001">ISO 27001</MenuItem>
          </TextField>
          
          <TextField
            select
            label="Environment"
            value={newReport.environment}
            onChange={(e) => setNewReport({ ...newReport, environment: e.target.value })}
            fullWidth
            margin="normal"
          >
            <MenuItem value="production">Production</MenuItem>
            <MenuItem value="staging">Staging</MenuItem>
            <MenuItem value="development">Development</MenuItem>
          </TextField>
          
          <TextField
            label="Scan ID (optional)"
            value={newReport.scan_id}
            onChange={(e) => setNewReport({ ...newReport, scan_id: e.target.value })}
            fullWidth
            margin="normal"
            placeholder="Leave empty to use latest scan"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={generateReport} variant="contained">
            Generate Report
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ReportsPage;
