import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  CircularProgress,
  Divider,
  Grid,
  Tooltip
} from '@mui/material';
import {
  Upload as UploadIcon,
  Email as EmailIcon,
  Preview as PreviewIcon,
  Send as SendIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  CheckBox,
  CheckBoxOutlineBlank,
  SmartToy as AIIcon
} from '@mui/icons-material';
import * as XLSX from 'xlsx';

interface ResourceComparison {
  resourceName: string;
  resourceGroup: string;
  subscription: string;
  owner: string;
  status: 'new' | 'updated' | 'unchanged' | 'removed';
  severity: 'high' | 'medium' | 'low';
  remediation: string;
  recommendedSteps: string;
  azureCommand?: string;
  estimatedCost?: string;
  priority?: number;
}

interface EmailTemplate {
  subject: string;
  htmlContent: string;
  textContent: string;
}

const AIEmailNotificationPage: React.FC = () => {
  // File upload states
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [validationData, setValidationData] = useState<ResourceComparison[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Email functionality states
  const [selectedResources, setSelectedResources] = useState<Set<number>>(new Set());
  const [emailDialog, setEmailDialog] = useState(false);
  const [previewDialog, setPreviewDialog] = useState(false);
  const [emailTemplate, setEmailTemplate] = useState<EmailTemplate | null>(null);
  const [emailPreview, setEmailPreview] = useState<string>('');
  const [emailRecipients, setEmailRecipients] = useState<string>('');
  const [emailSendMode, setEmailSendMode] = useState<'bulk' | 'individual' | 'selected'>('bulk');
  const [llmEmailLoading, setLlmEmailLoading] = useState(false);

  // File upload handler
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadedFile(file);
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const fileExtension = file.name.split('.').pop()?.toLowerCase();
      let data: any[] = [];

      if (fileExtension === 'csv') {
        const text = await file.text();
        const lines = text.split('\n');
        const headers = lines[0].split(',').map(h => h.trim());
        
        for (let i = 1; i < lines.length; i++) {
          if (lines[i].trim()) {
            const values = lines[i].split(',').map(v => v.trim());
            const row: any = {};
            headers.forEach((header, index) => {
              row[header] = values[index] || '';
            });
            data.push(row);
          }
        }
      } else if (fileExtension === 'xlsx' || fileExtension === 'xls') {
        const arrayBuffer = await file.arrayBuffer();
        const workbook = XLSX.read(arrayBuffer, { type: 'array' });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        data = XLSX.utils.sheet_to_json(worksheet);
      } else {
        throw new Error('Unsupported file format. Please upload CSV or Excel files.');
      }

      // Transform data to ResourceComparison format
      const transformedData: ResourceComparison[] = data.map((row: any) => ({
        resourceName: row['Resource Name'] || row['resourceName'] || row['name'] || 'Unknown',
        resourceGroup: row['Resource Group'] || row['resourceGroup'] || row['group'] || 'Unknown',
        subscription: row['Subscription'] || row['subscription'] || row['sub'] || 'Unknown',
        owner: row['Owner'] || row['owner'] || row['contact'] || 'Unknown',
        status: (row['Status'] || row['status'] || 'new').toLowerCase() as 'new' | 'updated' | 'unchanged' | 'removed',
        severity: (row['Severity'] || row['severity'] || 'medium').toLowerCase() as 'high' | 'medium' | 'low',
        remediation: row['Remediation'] || row['remediation'] || row['fix'] || 'No remediation specified',
        recommendedSteps: row['Recommended Steps'] || row['recommendedSteps'] || row['steps'] || 'No steps specified',
        azureCommand: row['Azure Command'] || row['azureCommand'] || row['command'] || '',
        estimatedCost: row['Estimated Cost'] || row['estimatedCost'] || row['cost'] || '',
        priority: parseInt(row['Priority'] || row['priority'] || '1') || 1
      }));

      setValidationData(transformedData);
      setSuccess(`Successfully loaded ${transformedData.length} resources from ${file.name}`);
    } catch (err) {
      setError(`Failed to process file: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  // Resource selection handlers
  const handleResourceSelection = (index: number) => {
    const newSelected = new Set(selectedResources);
    if (newSelected.has(index)) {
      newSelected.delete(index);
    } else {
      newSelected.add(index);
    }
    setSelectedResources(newSelected);
  };

  const handleSelectAllResources = () => {
    if (selectedResources.size === validationData.length) {
      setSelectedResources(new Set());
    } else {
      setSelectedResources(new Set(validationData.map((_, index) => index)));
    }
  };

  // LLM Email functions
  const handleGenerateLLMEmail = async () => {
    setLlmEmailLoading(true);
    setError(null);

    try {
      let resourcesToProcess: ResourceComparison[] = [];
      
      if (emailSendMode === 'selected') {
        resourcesToProcess = Array.from(selectedResources).map(index => validationData[index]);
      } else {
        resourcesToProcess = validationData;
      }

      const response = await fetch('/api/v1/validation/llm-email/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          comparisons: resourcesToProcess,
          emailType: emailSendMode,
          recipients: emailRecipients.split(',').map(email => email.trim()).filter(email => email)
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setEmailTemplate(result.template);
      setSuccess('Email template generated successfully!');
    } catch (err) {
      setError(`Failed to generate email template: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLlmEmailLoading(false);
    }
  };

  const handlePreviewLLMEmail = async () => {
    if (!emailTemplate) {
      setError('Please generate an email template first.');
      return;
    }

    setLlmEmailLoading(true);
    try {
      let resourcesToProcess: ResourceComparison[] = [];
      
      if (emailSendMode === 'selected') {
        resourcesToProcess = Array.from(selectedResources).map(index => validationData[index]);
      } else {
        resourcesToProcess = validationData;
      }

      const response = await fetch('/api/v1/validation/llm-email/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          template: emailTemplate,
          comparisons: resourcesToProcess,
          emailType: emailSendMode
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setEmailPreview(result.preview);
      setPreviewDialog(true);
    } catch (err) {
      setError(`Failed to preview email: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLlmEmailLoading(false);
    }
  };

  const handleSendLLMEmail = async () => {
    if (!emailTemplate) {
      setError('Please generate an email template first.');
      return;
    }

    if (!emailRecipients.trim()) {
      setError('Please enter recipient email addresses.');
      return;
    }

    setLlmEmailLoading(true);
    try {
      let resourcesToProcess: ResourceComparison[] = [];
      
      if (emailSendMode === 'selected') {
        resourcesToProcess = Array.from(selectedResources).map(index => validationData[index]);
        if (resourcesToProcess.length === 0) {
          setError('Please select at least one resource for selected mode.');
          setLlmEmailLoading(false);
          return;
        }
      } else {
        resourcesToProcess = validationData;
      }

      const response = await fetch('/api/v1/validation/llm-email/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          template: emailTemplate,
          comparisons: resourcesToProcess,
          recipients: emailRecipients.split(',').map(email => email.trim()).filter(email => email),
          emailType: emailSendMode
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setSuccess(`Emails sent successfully! ${result.message || ''}`);
      setEmailDialog(false);
    } catch (err) {
      setError(`Failed to send emails: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLlmEmailLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'new': return 'primary';
      case 'updated': return 'warning';
      case 'unchanged': return 'default';
      case 'removed': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        AI Email Notification System
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Upload your exported validation data (Excel or CSV) and generate AI-powered email notifications
      </Typography>

      {/* File Upload Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Upload Validation Data
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Button
              variant="contained"
              component="label"
              startIcon={<UploadIcon />}
              disabled={loading}
            >
              Choose File
              <input
                type="file"
                hidden
                accept=".csv,.xlsx,.xls"
                onChange={handleFileUpload}
              />
            </Button>
            {uploadedFile && (
              <Typography variant="body2">
                {uploadedFile.name} ({(uploadedFile.size / 1024).toFixed(1)} KB)
              </Typography>
            )}
            {loading && <CircularProgress size={24} />}
          </Box>
          <Typography variant="body2" color="text.secondary">
            Supported formats: CSV, Excel (.xlsx, .xls)
          </Typography>
        </CardContent>
      </Card>

      {/* Status Messages */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Data Summary and Actions */}
      {validationData.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Data Summary
            </Typography>
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={12} sm={6} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {validationData.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Resources
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="error">
                    {validationData.filter(r => r.severity === 'high').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    High Severity
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="warning.main">
                    {validationData.filter(r => r.severity === 'medium').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Medium Severity
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="success.main">
                    {selectedResources.size}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Selected
                  </Typography>
                </Box>
              </Grid>
            </Grid>
            <Divider sx={{ my: 2 }} />
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Button
                variant="contained"
                startIcon={<AIIcon />}
                onClick={() => setEmailDialog(true)}
                disabled={validationData.length === 0}
              >
                AI Email Notifications
              </Button>
              <Button
                variant="outlined"
                startIcon={<DeleteIcon />}
                onClick={() => {
                  setValidationData([]);
                  setSelectedResources(new Set());
                  setUploadedFile(null);
                  setEmailTemplate(null);
                }}
              >
                Clear Data
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Validation Results Table */}
      {validationData.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Validation Results
            </Typography>
            <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
              <Table stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox">
                      <Checkbox
                        indeterminate={selectedResources.size > 0 && selectedResources.size < validationData.length}
                        checked={validationData.length > 0 && selectedResources.size === validationData.length}
                        onChange={handleSelectAllResources}
                      />
                    </TableCell>
                    <TableCell>Resource Name</TableCell>
                    <TableCell>Resource Group</TableCell>
                    <TableCell>Subscription</TableCell>
                    <TableCell>Owner</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Severity</TableCell>
                    <TableCell>Remediation</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {validationData.map((resource, index) => (
                    <TableRow key={index} hover>
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={selectedResources.has(index)}
                          onChange={() => handleResourceSelection(index)}
                        />
                      </TableCell>
                      <TableCell>{resource.resourceName}</TableCell>
                      <TableCell>{resource.resourceGroup}</TableCell>
                      <TableCell>{resource.subscription}</TableCell>
                      <TableCell>{resource.owner}</TableCell>
                      <TableCell>
                        <Chip
                          label={resource.status}
                          color={getStatusColor(resource.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={resource.severity}
                          color={getSeverityColor(resource.severity) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Tooltip title={resource.remediation}>
                          <Typography
                            variant="body2"
                            sx={{
                              maxWidth: 200,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}
                          >
                            {resource.remediation}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* LLM Email Dialog */}
      <Dialog open={emailDialog} onClose={() => setEmailDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AIIcon color="primary" />
            AI Email Notifications
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 1 }}>
            <FormControl fullWidth>
              <InputLabel>Email Send Mode</InputLabel>
              <Select
                value={emailSendMode}
                label="Email Send Mode"
                onChange={(e) => setEmailSendMode(e.target.value as 'bulk' | 'individual' | 'selected')}
              >
                <MenuItem value="bulk">Bulk Email (All resources in one email)</MenuItem>
                <MenuItem value="individual">Individual Emails (One per resource)</MenuItem>
                <MenuItem value="selected">Selected Resources Only ({selectedResources.size} selected)</MenuItem>
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="Recipient Email Addresses"
              placeholder="Enter email addresses separated by commas"
              value={emailRecipients}
              onChange={(e) => setEmailRecipients(e.target.value)}
              multiline
              rows={2}
              helperText="Separate multiple email addresses with commas"
            />

            {emailTemplate && (
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>
                    Generated Email Template Preview
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                    Subject: {emailTemplate.subject}
                  </Typography>
                  <Box
                    sx={{
                      maxHeight: 200,
                      overflow: 'auto',
                      p: 2,
                      bgcolor: 'grey.50',
                      borderRadius: 1,
                      fontSize: '0.875rem'
                    }}
                    dangerouslySetInnerHTML={{ __html: emailTemplate.htmlContent }}
                  />
                </CardContent>
              </Card>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEmailDialog(false)}>Cancel</Button>
          <Button
            onClick={handlePreviewLLMEmail}
            disabled={!emailTemplate || llmEmailLoading}
            startIcon={<PreviewIcon />}
          >
            Preview
          </Button>
          <Button
            onClick={handleGenerateLLMEmail}
            disabled={llmEmailLoading}
            startIcon={<AIIcon />}
          >
            {llmEmailLoading ? <CircularProgress size={20} /> : 'Generate Template'}
          </Button>
          <Button
            onClick={handleSendLLMEmail}
            disabled={!emailTemplate || !emailRecipients.trim() || llmEmailLoading}
            variant="contained"
            startIcon={<SendIcon />}
          >
            Send Emails
          </Button>
        </DialogActions>
      </Dialog>

      {/* Email Preview Dialog */}
      <Dialog open={previewDialog} onClose={() => setPreviewDialog(false)} maxWidth="lg" fullWidth>
        <DialogTitle>Email Preview</DialogTitle>
        <DialogContent>
          <Box
            sx={{
              minHeight: 400,
              border: '1px solid #ddd',
              borderRadius: 1,
              p: 2
            }}
            dangerouslySetInnerHTML={{ __html: emailPreview }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AIEmailNotificationPage;