import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  Divider,
  Stack,
  Badge
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Security as SecurityIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  PlayArrow as PlayIcon,
  Settings as SettingsIcon,
  Public as PublicIcon,
  Lock as PrivateIcon
} from '@mui/icons-material';

interface ComplianceFramework {
  id: string;
  name: string;
  display_name: string;
  description: string;
  version: string;
  framework_type: 'regulatory' | 'industry' | 'internal' | 'custom';
  industry?: string;
  region?: string;
  tags: string[];
  is_active: boolean;
  is_public: boolean;
  controls_count: number;
  created_at: string;
  updated_at: string;
}

interface ComplianceControl {
  id: string;
  control_id: string;
  title: string;
  description: string;
  category: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  control_type: 'preventive' | 'detective' | 'corrective' | 'compensating';
  implementation_guidance?: string;
  testing_procedures?: string;
  resource_types: string[];
  references: string[];
  tags: string[];
  order_index: number;
  is_active: boolean;
}

const ComplianceFrameworksPage: React.FC = () => {
  const navigate = useNavigate();
  const [frameworks, setFrameworks] = useState<ComplianceFramework[]>([]);
  const [selectedFramework, setSelectedFramework] = useState<ComplianceFramework | null>(null);
  const [controls, setControls] = useState<ComplianceControl[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openFrameworkDialog, setOpenFrameworkDialog] = useState(false);
  const [openControlDialog, setOpenControlDialog] = useState(false);
  const [openViewDialog, setOpenViewDialog] = useState(false);
  const [editingFramework, setEditingFramework] = useState<ComplianceFramework | null>(null);
  const [editingControl, setEditingControl] = useState<ComplianceControl | null>(null);

  // Framework form state
  const [frameworkForm, setFrameworkForm] = useState({
    name: '',
    display_name: '',
    description: '',
    version: '1.0',
    framework_type: 'custom' as const,
    industry: '',
    region: '',
    tags: [] as string[],
    is_public: false
  });

  // Control form state
  const [controlForm, setControlForm] = useState({
    control_id: '',
    title: '',
    description: '',
    category: '',
    severity: 'medium' as const,
    control_type: 'preventive' as const,
    implementation_guidance: '',
    testing_procedures: '',
    resource_types: [] as string[],
    references: [] as string[],
    tags: [] as string[]
  });

  const [tagInput, setTagInput] = useState('');
  const [resourceTypeInput, setResourceTypeInput] = useState('');
  const [referenceInput, setReferenceInput] = useState('');

  useEffect(() => {
    fetchFrameworks();
  }, []);

  const fetchFrameworks = async () => {
    try {
      setLoading(true);
      // Mock data for now - replace with actual API call
      const mockFrameworks: ComplianceFramework[] = [
        {
          id: '1',
          name: 'custom-security-framework',
          display_name: 'Custom Security Framework',
          description: 'A custom security framework tailored for our organization',
          version: '1.0',
          framework_type: 'custom',
          industry: 'Technology',
          region: 'Global',
          tags: ['security', 'custom', 'azure'],
          is_active: true,
          is_public: false,
          controls_count: 15,
          created_at: '2024-01-15T10:00:00Z',
          updated_at: '2024-01-15T10:00:00Z'
        },
        {
          id: '2',
          name: 'gdpr-compliance',
          display_name: 'GDPR Compliance Framework',
          description: 'Framework for GDPR compliance in cloud environments',
          version: '2.1',
          framework_type: 'regulatory',
          industry: 'All',
          region: 'EU',
          tags: ['gdpr', 'privacy', 'regulatory'],
          is_active: true,
          is_public: true,
          controls_count: 28,
          created_at: '2024-01-10T08:00:00Z',
          updated_at: '2024-01-12T14:30:00Z'
        }
      ];
      setFrameworks(mockFrameworks);
    } catch (err) {
      setError('Failed to fetch frameworks');
    } finally {
      setLoading(false);
    }
  };

  const fetchControls = async (frameworkId: string) => {
    try {
      // Mock data for now - replace with actual API call
      const mockControls: ComplianceControl[] = [
        {
          id: '1',
          control_id: 'CSF-001',
          title: 'Multi-Factor Authentication',
          description: 'Ensure all user accounts have multi-factor authentication enabled',
          category: 'Identity and Access Management',
          severity: 'high',
          control_type: 'preventive',
          implementation_guidance: 'Configure MFA for all Azure AD users',
          testing_procedures: 'Verify MFA is enabled for all accounts',
          resource_types: ['Microsoft.Authorization/users', 'Microsoft.AAD/users'],
          references: ['https://docs.microsoft.com/azure/active-directory/authentication/'],
          tags: ['mfa', 'authentication', 'security'],
          order_index: 1,
          is_active: true
        },
        {
          id: '2',
          control_id: 'CSF-002',
          title: 'Storage Encryption',
          description: 'Ensure all storage accounts have encryption enabled',
          category: 'Data Protection',
          severity: 'critical',
          control_type: 'preventive',
          implementation_guidance: 'Enable encryption at rest for all storage accounts',
          testing_procedures: 'Check encryption settings on storage accounts',
          resource_types: ['Microsoft.Storage/storageAccounts'],
          references: ['https://docs.microsoft.com/azure/storage/common/storage-service-encryption'],
          tags: ['encryption', 'storage', 'data-protection'],
          order_index: 2,
          is_active: true
        }
      ];
      setControls(mockControls);
    } catch (err) {
      setError('Failed to fetch controls');
    }
  };

  const handleCreateFramework = async () => {
    try {
      // Mock implementation - replace with actual API call
      const newFramework: ComplianceFramework = {
        id: Date.now().toString(),
        ...frameworkForm,
        controls_count: 0,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      setFrameworks([...frameworks, newFramework]);
      setOpenFrameworkDialog(false);
      resetFrameworkForm();
    } catch (err) {
      setError('Failed to create framework');
    }
  };

  const handleCreateControl = async () => {
    if (!selectedFramework) return;
    
    try {
      // Mock implementation - replace with actual API call
      const newControl: ComplianceControl = {
        id: Date.now().toString(),
        ...controlForm,
        order_index: controls.length + 1,
        is_active: true
      };
      setControls([...controls, newControl]);
      setOpenControlDialog(false);
      resetControlForm();
      
      // Update framework controls count
      setFrameworks(frameworks.map(f => 
        f.id === selectedFramework.id 
          ? { ...f, controls_count: f.controls_count + 1 }
          : f
      ));
    } catch (err) {
      setError('Failed to create control');
    }
  };

  const handleViewFramework = (framework: ComplianceFramework) => {
    setSelectedFramework(framework);
    fetchControls(framework.id);
    setOpenViewDialog(true);
  };

  const handleRunScan = (framework: ComplianceFramework) => {
    // Navigate to scan creation with this framework pre-selected
    navigate('/scans', { 
      state: { 
        selectedFramework: {
          id: framework.id,
          name: framework.name,
          display_name: framework.display_name,
          description: framework.description,
          controls_count: framework.controls_count
        },
        openDialog: true 
      } 
    });
  };

  const resetFrameworkForm = () => {
    setFrameworkForm({
      name: '',
      display_name: '',
      description: '',
      version: '1.0',
      framework_type: 'custom',
      industry: '',
      region: '',
      tags: [],
      is_public: false
    });
    setEditingFramework(null);
  };

  const resetControlForm = () => {
    setControlForm({
      control_id: '',
      title: '',
      description: '',
      category: '',
      severity: 'medium',
      control_type: 'preventive',
      implementation_guidance: '',
      testing_procedures: '',
      resource_types: [],
      references: [],
      tags: []
    });
    setEditingControl(null);
  };

  const addTag = () => {
    if (tagInput.trim() && !frameworkForm.tags.includes(tagInput.trim())) {
      setFrameworkForm({
        ...frameworkForm,
        tags: [...frameworkForm.tags, tagInput.trim()]
      });
      setTagInput('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    setFrameworkForm({
      ...frameworkForm,
      tags: frameworkForm.tags.filter(tag => tag !== tagToRemove)
    });
  };

  const addResourceType = () => {
    if (resourceTypeInput.trim() && !controlForm.resource_types.includes(resourceTypeInput.trim())) {
      setControlForm({
        ...controlForm,
        resource_types: [...controlForm.resource_types, resourceTypeInput.trim()]
      });
      setResourceTypeInput('');
    }
  };

  const removeResourceType = (typeToRemove: string) => {
    setControlForm({
      ...controlForm,
      resource_types: controlForm.resource_types.filter(type => type !== typeToRemove)
    });
  };

  const addReference = () => {
    if (referenceInput.trim() && !controlForm.references.includes(referenceInput.trim())) {
      setControlForm({
        ...controlForm,
        references: [...controlForm.references, referenceInput.trim()]
      });
      setReferenceInput('');
    }
  };

  const removeReference = (refToRemove: string) => {
    setControlForm({
      ...controlForm,
      references: controlForm.references.filter(ref => ref !== refToRemove)
    });
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
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Compliance Frameworks
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpenFrameworkDialog(true)}
        >
          Create Framework
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {frameworks.map((framework) => (
          <Grid item xs={12} md={6} lg={4} key={framework.id}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                  <Typography variant="h6" component="h2">
                    {framework.display_name}
                  </Typography>
                  <Box display="flex" gap={1}>
                    {framework.is_public ? (
                      <Tooltip title="Public Framework">
                        <PublicIcon color="primary" fontSize="small" />
                      </Tooltip>
                    ) : (
                      <Tooltip title="Private Framework">
                        <PrivateIcon color="action" fontSize="small" />
                      </Tooltip>
                    )}
                    <Chip
                      label={framework.framework_type}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  </Box>
                </Box>
                
                <Typography variant="body2" color="text.secondary" mb={2}>
                  {framework.description}
                </Typography>
                
                <Box display="flex" flexWrap="wrap" gap={0.5} mb={2}>
                  {framework.tags.map((tag) => (
                    <Chip key={tag} label={tag} size="small" variant="outlined" />
                  ))}
                </Box>
                
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="body2">
                    <strong>{framework.controls_count}</strong> controls
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    v{framework.version}
                  </Typography>
                </Box>
                
                <Box display="flex" gap={1}>
                  <Button
                    size="small"
                    startIcon={<ViewIcon />}
                    onClick={() => handleViewFramework(framework)}
                  >
                    View
                  </Button>
                  <Button
                    size="small"
                    startIcon={<PlayIcon />}
                    onClick={() => handleRunScan(framework)}
                    color="primary"
                  >
                    Run Scan
                  </Button>
                  <IconButton size="small">
                    <EditIcon />
                  </IconButton>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Create Framework Dialog */}
      <Dialog open={openFrameworkDialog} onClose={() => setOpenFrameworkDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create New Compliance Framework</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Framework Name"
                value={frameworkForm.name}
                onChange={(e) => setFrameworkForm({ ...frameworkForm, name: e.target.value })}
                placeholder="e.g., custom-security-framework"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Display Name"
                value={frameworkForm.display_name}
                onChange={(e) => setFrameworkForm({ ...frameworkForm, display_name: e.target.value })}
                placeholder="e.g., Custom Security Framework"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Description"
                value={frameworkForm.description}
                onChange={(e) => setFrameworkForm({ ...frameworkForm, description: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Version"
                value={frameworkForm.version}
                onChange={(e) => setFrameworkForm({ ...frameworkForm, version: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Framework Type</InputLabel>
                <Select
                  value={frameworkForm.framework_type}
                  onChange={(e) => setFrameworkForm({ ...frameworkForm, framework_type: e.target.value as any })}
                >
                  <MenuItem value="custom">Custom</MenuItem>
                  <MenuItem value="regulatory">Regulatory</MenuItem>
                  <MenuItem value="industry">Industry</MenuItem>
                  <MenuItem value="internal">Internal</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Industry"
                value={frameworkForm.industry}
                onChange={(e) => setFrameworkForm({ ...frameworkForm, industry: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Region"
                value={frameworkForm.region}
                onChange={(e) => setFrameworkForm({ ...frameworkForm, region: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={frameworkForm.is_public}
                    onChange={(e) => setFrameworkForm({ ...frameworkForm, is_public: e.target.checked })}
                  />
                }
                label="Make this framework public"
              />
            </Grid>
            <Grid item xs={12}>
              <Box display="flex" gap={1} alignItems="center" mb={1}>
                <TextField
                  size="small"
                  label="Add Tag"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addTag()}
                />
                <Button onClick={addTag} variant="outlined" size="small">
                  Add
                </Button>
              </Box>
              <Box display="flex" flexWrap="wrap" gap={0.5}>
                {frameworkForm.tags.map((tag) => (
                  <Chip
                    key={tag}
                    label={tag}
                    onDelete={() => removeTag(tag)}
                    size="small"
                  />
                ))}
              </Box>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenFrameworkDialog(false)}>Cancel</Button>
          <Button onClick={handleCreateFramework} variant="contained">
            Create Framework
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Framework Dialog */}
      <Dialog open={openViewDialog} onClose={() => setOpenViewDialog(false)} maxWidth="lg" fullWidth>
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">
              {selectedFramework?.display_name}
            </Typography>
            <Button
              startIcon={<AddIcon />}
              onClick={() => setOpenControlDialog(true)}
              variant="contained"
              size="small"
            >
              Add Control
            </Button>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedFramework && (
            <Box>
              <Typography variant="body1" paragraph>
                {selectedFramework.description}
              </Typography>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="h6" gutterBottom>
                Controls ({controls.length})
              </Typography>
              
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Control ID</TableCell>
                      <TableCell>Title</TableCell>
                      <TableCell>Category</TableCell>
                      <TableCell>Severity</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {controls.map((control) => (
                      <TableRow key={control.id}>
                        <TableCell>{control.control_id}</TableCell>
                        <TableCell>{control.title}</TableCell>
                        <TableCell>{control.category}</TableCell>
                        <TableCell>
                          <Chip
                            icon={getSeverityIcon(control.severity)}
                            label={control.severity}
                            size="small"
                            color={getSeverityColor(control.severity) as any}
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>{control.control_type}</TableCell>
                        <TableCell>
                          <IconButton size="small">
                            <EditIcon />
                          </IconButton>
                          <IconButton size="small">
                            <DeleteIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenViewDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Create Control Dialog */}
      <Dialog open={openControlDialog} onClose={() => setOpenControlDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add New Control</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Control ID"
                value={controlForm.control_id}
                onChange={(e) => setControlForm({ ...controlForm, control_id: e.target.value })}
                placeholder="e.g., CSF-001"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Title"
                value={controlForm.title}
                onChange={(e) => setControlForm({ ...controlForm, title: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Description"
                value={controlForm.description}
                onChange={(e) => setControlForm({ ...controlForm, description: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Category"
                value={controlForm.category}
                onChange={(e) => setControlForm({ ...controlForm, category: e.target.value })}
                placeholder="e.g., Identity and Access Management"
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <FormControl fullWidth>
                <InputLabel>Severity</InputLabel>
                <Select
                  value={controlForm.severity}
                  onChange={(e) => setControlForm({ ...controlForm, severity: e.target.value as any })}
                >
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="critical">Critical</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={3}>
              <FormControl fullWidth>
                <InputLabel>Control Type</InputLabel>
                <Select
                  value={controlForm.control_type}
                  onChange={(e) => setControlForm({ ...controlForm, control_type: e.target.value as any })}
                >
                  <MenuItem value="preventive">Preventive</MenuItem>
                  <MenuItem value="detective">Detective</MenuItem>
                  <MenuItem value="corrective">Corrective</MenuItem>
                  <MenuItem value="compensating">Compensating</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Implementation Guidance"
                value={controlForm.implementation_guidance}
                onChange={(e) => setControlForm({ ...controlForm, implementation_guidance: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Testing Procedures"
                value={controlForm.testing_procedures}
                onChange={(e) => setControlForm({ ...controlForm, testing_procedures: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <Box display="flex" gap={1} alignItems="center" mb={1}>
                <TextField
                  size="small"
                  label="Add Resource Type"
                  value={resourceTypeInput}
                  onChange={(e) => setResourceTypeInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addResourceType()}
                  placeholder="e.g., Microsoft.Storage/storageAccounts"
                />
                <Button onClick={addResourceType} variant="outlined" size="small">
                  Add
                </Button>
              </Box>
              <Box display="flex" flexWrap="wrap" gap={0.5}>
                {controlForm.resource_types.map((type) => (
                  <Chip
                    key={type}
                    label={type}
                    onDelete={() => removeResourceType(type)}
                    size="small"
                  />
                ))}
              </Box>
            </Grid>
            <Grid item xs={12}>
              <Box display="flex" gap={1} alignItems="center" mb={1}>
                <TextField
                  size="small"
                  label="Add Reference URL"
                  value={referenceInput}
                  onChange={(e) => setReferenceInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addReference()}
                  placeholder="https://docs.microsoft.com/..."
                />
                <Button onClick={addReference} variant="outlined" size="small">
                  Add
                </Button>
              </Box>
              <Box display="flex" flexWrap="wrap" gap={0.5}>
                {controlForm.references.map((ref) => (
                  <Chip
                    key={ref}
                    label={ref}
                    onDelete={() => removeReference(ref)}
                    size="small"
                  />
                ))}
              </Box>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenControlDialog(false)}>Cancel</Button>
          <Button onClick={handleCreateControl} variant="contained">
            Add Control
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ComplianceFrameworksPage;