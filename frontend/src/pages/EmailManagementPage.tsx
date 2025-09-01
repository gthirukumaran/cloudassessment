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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Tabs,
  Tab,
  Badge,
  LinearProgress,
  Alert,
  Tooltip,
  Divider,
  Stack,
  CircularProgress,
} from '@mui/material';
import {
  Email as EmailIcon,
  Send as SendIcon,
  Schedule as ScheduleIcon,
  Policy as PolicyIcon,
  SmartToy as AIIcon,
  Refresh as RefreshIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useSnackbar } from '../contexts/SnackbarContext';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`email-tabpanel-${index}`}
      aria-labelledby={`email-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `email-tab-${index}`,
    'aria-controls': `email-tabpanel-${index}`,
  };
}

interface EmailRecord {
  id: string;
  recipient_email: string;
  subject: string;
  status: string;
  bucket: string;
  created_at: string;
  sent_at?: string;
  response_received?: boolean;
  resource_name?: string;
  severity?: string;
}

interface BucketStats {
  total: number;
  pending: number;
  sent: number;
  responded: number;
}

const EmailManagementPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [emailRecords, setEmailRecords] = useState<EmailRecord[]>([]);
  const [bucketStats, setBucketStats] = useState<Record<string, BucketStats>>({});
  const [loading, setLoading] = useState(false);
  const [selectedBucket, setSelectedBucket] = useState('all');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState<EmailRecord | null>(null);
  const [llmStats, setLlmStats] = useState<any>(null);
  
  const { user } = useAuth();
  const { showSnackbar } = useSnackbar();

  const buckets = [
    { key: 'wrong-owner', label: 'Wrong Owner', color: 'warning', icon: <WarningIcon /> },
    { key: 'reminder', label: 'Reminders', color: 'info', icon: <ScheduleIcon /> },
    { key: 'exception-policy', label: 'Exception Policy', color: 'success', icon: <PolicyIcon /> },
    { key: 'llm-response', label: 'LLM Responses', color: 'secondary', icon: <AIIcon /> },
  ];

  useEffect(() => {
    fetchEmailData();
    fetchBucketStats();
    fetchLlmStats();
  }, [selectedBucket]);

  const fetchEmailData = async () => {
    setLoading(true);
    try {
      const endpoint = selectedBucket === 'all' 
        ? '/api/v1/email-management/records'
        : `/api/v1/email-management/${selectedBucket}/records`;
      
      const response = await fetch(`http://127.0.0.1:9099${endpoint}`);
      const data = await response.json();
      
      if (data.success) {
        setEmailRecords(data.data || []);
      }
    } catch (error) {
      console.error('Error fetching email data:', error);
      showSnackbar('Error fetching email data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchBucketStats = async () => {
    try {
      const stats: Record<string, BucketStats> = {};
      
      for (const bucket of buckets) {
        const response = await fetch(`http://127.0.0.1:9099/api/v1/email-management/${bucket.key}/statistics`);
        const data = await response.json();
        
        if (data.success) {
          stats[bucket.key] = data.data;
        }
      }
      
      setBucketStats(stats);
    } catch (error) {
      console.error('Error fetching bucket stats:', error);
    }
  };

  const fetchLlmStats = async () => {
    try {
      const response = await fetch('http://127.0.0.1:9099/api/v1/email-management/llm-response/statistics');
      const data = await response.json();
      
      if (data.success) {
        setLlmStats(data.data);
      }
    } catch (error) {
      console.error('Error fetching LLM stats:', error);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleBucketChange = (bucket: string) => {
    setSelectedBucket(bucket);
  };

  const handleViewEmail = (email: EmailRecord) => {
    setSelectedEmail(email);
    setDialogOpen(true);
  };

  const handleProcessBatch = async (bucketType: string) => {
    setLoading(true);
    try {
      const response = await fetch(`http://127.0.0.1:9099/api/v1/email-management/${bucketType}/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          batch_size: 10,
          filters: {}
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        showSnackbar(`Batch processing initiated for ${bucketType}`, 'success');
        fetchEmailData();
        fetchBucketStats();
      }
    } catch (error) {
      console.error('Error processing batch:', error);
      showSnackbar('Error processing batch', 'error');
    } finally {
      setLoading(false);
    }
  };

  const renderBucketOverview = () => (
    <Grid container spacing={3}>
      {buckets.map((bucket) => {
        const stats = bucketStats[bucket.key] || { total: 0, pending: 0, sent: 0, responded: 0 };
        const responseRate = stats.sent > 0 ? ((stats.responded / stats.sent) * 100).toFixed(1) : '0';
        
        return (
          <Grid item xs={12} sm={6} md={3} key={bucket.key}>
            <Card 
              sx={{ 
                cursor: 'pointer',
                '&:hover': { elevation: 4 },
                border: selectedBucket === bucket.key ? 2 : 0,
                borderColor: 'primary.main'
              }}
              onClick={() => handleBucketChange(bucket.key)}
            >
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <Badge badgeContent={stats.pending} color="error">
                    {bucket.icon}
                  </Badge>
                  <Typography variant="h6" ml={2}>
                    {bucket.label}
                  </Typography>
                </Box>
                
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Total
                    </Typography>
                    <Typography variant="h4">
                      {stats.total}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Response Rate
                    </Typography>
                    <Typography variant="h4" color={parseFloat(responseRate) > 50 ? 'success.main' : 'warning.main'}>
                      {responseRate}%
                    </Typography>
                  </Grid>
                </Grid>
                
                <Box mt={2}>
                  <LinearProgress 
                    variant="determinate" 
                    value={stats.total > 0 ? (stats.sent / stats.total) * 100 : 0}
                    sx={{ mb: 1 }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    {stats.sent} of {stats.total} sent
                  </Typography>
                </Box>
                
                <Button
                  variant="outlined"
                  size="small"
                  fullWidth
                  sx={{ mt: 2 }}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleProcessBatch(bucket.key);
                  }}
                >
                  Process Batch
                </Button>
              </CardContent>
            </Card>
          </Grid>
        );
      })}
    </Grid>
  );

  const renderEmailTable = () => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Recipient</TableCell>
            <TableCell>Subject</TableCell>
            <TableCell>Resource</TableCell>
            <TableCell>Bucket</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Severity</TableCell>
            <TableCell>Created</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {emailRecords.map((email) => (
            <TableRow key={email.id}>
              <TableCell>{email.recipient_email}</TableCell>
              <TableCell>
                <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                  {email.subject}
                </Typography>
              </TableCell>
              <TableCell>{email.resource_name || 'N/A'}</TableCell>
              <TableCell>
                <Chip 
                  label={email.bucket} 
                  size="small"
                  color={buckets.find(b => b.key === email.bucket)?.color as any || 'default'}
                />
              </TableCell>
              <TableCell>
                <Chip 
                  label={email.status}
                  size="small"
                  color={email.status === 'sent' ? 'success' : email.status === 'pending' ? 'warning' : 'default'}
                />
              </TableCell>
              <TableCell>
                {email.severity && (
                  <Chip 
                    label={email.severity}
                    size="small"
                    color={email.severity === 'high' ? 'error' : email.severity === 'medium' ? 'warning' : 'info'}
                  />
                )}
              </TableCell>
              <TableCell>
                <Typography variant="caption">
                  {new Date(email.created_at).toLocaleDateString()}
                </Typography>
              </TableCell>
              <TableCell>
                <Tooltip title="View Details">
                  <IconButton size="small" onClick={() => handleViewEmail(email)}>
                    <ViewIcon />
                  </IconButton>
                </Tooltip>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  const renderLlmAnalytics = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              LLM Response Statistics
            </Typography>
            {llmStats && (
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Total Records
                  </Typography>
                  <Typography variant="h4">
                    {llmStats.total_records || 0}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Responses Sent
                  </Typography>
                  <Typography variant="h4">
                    {llmStats.responses_sent || 0}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary">
                    Response Rate
                  </Typography>
                  <Typography variant="h4" color="success.main">
                    {llmStats.response_rate || 0}%
                  </Typography>
                </Grid>
              </Grid>
            )}
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Response Types Breakdown
            </Typography>
            {llmStats?.response_types && (
              <Stack spacing={1}>
                {Object.entries(llmStats.response_types).map(([type, count]) => (
                  <Box key={type} display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                      {type.replace('_', ' ')}
                    </Typography>
                    <Chip label={count} size="small" />
                  </Box>
                ))}
              </Stack>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" gutterBottom>
          Email Management Dashboard
        </Typography>
        <Button
          variant="contained"
          startIcon={<RefreshIcon />}
          onClick={() => {
            fetchEmailData();
            fetchBucketStats();
            fetchLlmStats();
          }}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      <Paper sx={{ width: '100%', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="email management tabs">
          <Tab label="Overview" {...a11yProps(0)} />
          <Tab label="Email Records" {...a11yProps(1)} />
          <Tab label="LLM Analytics" {...a11yProps(2)} />
        </Tabs>
      </Paper>

      <TabPanel value={tabValue} index={0}>
        {renderBucketOverview()}
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Box mb={2}>
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Filter by Bucket</InputLabel>
            <Select
              value={selectedBucket}
              label="Filter by Bucket"
              onChange={(e) => handleBucketChange(e.target.value)}
            >
              <MenuItem value="all">All Buckets</MenuItem>
              {buckets.map((bucket) => (
                <MenuItem key={bucket.key} value={bucket.key}>
                  {bucket.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
        
        {loading ? (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        ) : (
          renderEmailTable()
        )}
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        {renderLlmAnalytics()}
      </TabPanel>

      {/* Email Detail Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Email Details
        </DialogTitle>
        <DialogContent>
          {selectedEmail && (
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Recipient"
                  value={selectedEmail.recipient_email}
                  fullWidth
                  InputProps={{ readOnly: true }}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Status"
                  value={selectedEmail.status}
                  fullWidth
                  InputProps={{ readOnly: true }}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Subject"
                  value={selectedEmail.subject}
                  fullWidth
                  InputProps={{ readOnly: true }}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Bucket"
                  value={selectedEmail.bucket}
                  fullWidth
                  InputProps={{ readOnly: true }}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Created At"
                  value={new Date(selectedEmail.created_at).toLocaleString()}
                  fullWidth
                  InputProps={{ readOnly: true }}
                  margin="normal"
                />
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default EmailManagementPage;