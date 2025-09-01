import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Tooltip,
  Grid,
  Card,
  CardContent,
  Switch,
  FormControlLabel,
  Alert,
  Snackbar,
  CircularProgress,
  Avatar
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Person as PersonIcon,
  Security as SecurityIcon,
  Settings as SettingsIcon,
  Notifications as NotificationsIcon,
  Email as EmailIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: string;
  isActive?: boolean;
  status?: string;
  permissions?: string[];
  created_at?: string;
  createdAt?: string;
  last_login?: string;
  lastLogin?: string;
}

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
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const SettingsPage: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [tabValue, setTabValue] = useState(0);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [openUserDialog, setOpenUserDialog] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });
  // const [config, setConfig] = useState({
  //   AZURE_CLIENT_ID: '',
  //   AZURE_CLIENT_SECRET: '',
  //   AZURE_TENANT_ID: '',
  //   AZURE_STORAGE_CONNECTION_STRING: '',
  //   DATABASE_URL: '',
  //   OPENAI_API_KEY: '',
  // });
  // const [loadingConfig, setLoadingConfig] = useState(false);
  // const [savingConfig, setSavingConfig] = useState(false);
  // const [testingAzure, setTestingAzure] = useState(false);
  
  // New user form state
  const [userForm, setUserForm] = useState({
    email: '',
    password: '',
    firstName: '',
    lastName: '',
    role: 'user',
    isActive: true
  });

  // Settings state
  const [settings, setSettings] = useState({
    notifications: {
      emailNotifications: true,
      scanCompletionNotifications: true,
      securityAlerts: true,
      weeklyReports: false
    },
    security: {
      sessionTimeout: 30,
      passwordExpiry: 90,
      mfaRequired: false,
      auditLogging: true
    },
    scanning: {
      maxConcurrentScans: 5,
      scanTimeout: 30,
      retentionDays: 90,
      autoScanEnabled: false
    },
    email: {
      smtpHost: '',
      smtpPort: 587,
      smtpUsername: '',
      smtpPassword: '',
      smtpTls: true,
      fromEmail: '',
      fromName: 'SecurityA Email Management'
    }
  });

  const roles = [
    { value: 'admin', label: 'Administrator', description: 'Full system access' },
    { value: 'analyst', label: 'Security Analyst', description: 'Can run scans and generate reports' },
    { value: 'user', label: 'User', description: 'Read-only access' }
  ];

  const rolePermissions = {
    admin: ['read', 'write', 'delete', 'manage_users', 'generate_reports'],
    analyst: ['read', 'write', 'generate_reports'],
    user: ['read']
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  // const fetchConfig = async () => {
  //   try {
  //     setLoadingConfig(true);
  //     const response = await fetch('http://127.0.0.1:9099/api/v1/config');
  //     if (response.ok) {
  //       const data = await response.json();
  //       // Prefill with masked values if present
  //       setConfig({
  //         AZURE_CLIENT_ID: data.AZURE_CLIENT_ID || '',
  //         AZURE_TENANT_ID: data.AZURE_TENANT_ID || '',
  //         AZURE_CLIENT_SECRET: data.AZURE_CLIENT_SECRET === 'SET' ? '********' : '',
  //         AZURE_STORAGE_CONNECTION_STRING: data.AZURE_STORAGE_CONNECTION_STRING === 'SET' ? '********' : '',
  //         DATABASE_URL: data.DATABASE_URL || '',
  //         REDIS_URL: data.REDIS_URL || '',
  //         OPENAI_API_KEY: data.OPENAI_API_KEY === 'SET' ? '********' : '',
  //       });
  //     }
  //   } catch (e) {
  //     console.error('Error loading config', e);
  //   } finally {
   //     setLoadingConfig(false);
   //   }
   // };

  // const saveConfig = async () => {
  //   try {
  //     setSavingConfig(true);
  //     const payload: any = { ...config };
  //     // If masked values are still there, don't send them to avoid overwriting
  //     if (payload.AZURE_CLIENT_SECRET === '********') delete payload.AZURE_CLIENT_SECRET;
  //     if (payload.AZURE_STORAGE_CONNECTION_STRING === '********') delete payload.AZURE_STORAGE_CONNECTION_STRING;
  //     if (payload.OPENAI_API_KEY === '********') delete payload.OPENAI_API_KEY;
  //     // If IDs/URLs are masked (contain ...), don't overwrite
  //     if (payload.AZURE_CLIENT_ID && payload.AZURE_CLIENT_ID.includes('...')) delete payload.AZURE_CLIENT_ID;
  //     if (payload.AZURE_TENANT_ID && payload.AZURE_TENANT_ID.includes('...')) delete payload.AZURE_TENANT_ID;
  //     if (payload.DATABASE_URL && payload.DATABASE_URL.includes('...')) delete payload.DATABASE_URL;
  //     // Remove empty strings
  //     Object.keys(payload).forEach((k) => { if (payload[k] === '') delete payload[k]; });

  //     const response = await fetch('http://127.0.0.1:9099/api/v1/config', {
  //       method: 'POST',
  //       headers: { 'Content-Type': 'application/json' },
  //       body: JSON.stringify(payload),
  //     });
  //     if (response.ok) {
  //       const data = await response.json();
  //       showSnackbar('Configuration saved. Azure credentials reloaded.', 'success');
  //     } else {
  //       const err = await response.json();
  //       showSnackbar(err.detail || 'Failed to save configuration', 'error');
  //     }
  //   } catch (e) {
  //     console.error('Save config error', e);
  //     showSnackbar('Failed to save configuration', 'error');
  //   } finally {
  //     setSavingConfig(false);
  //   }
  // };

  // const testAzure = async () => {
  //   try {
  //     setTestingAzure(true);
  //     const res = await fetch('http://127.0.0.1:9099/api/v1/azure/test');
  //     const data = await res.json();
  //     if (data.ok) {
  //       showSnackbar(`Azure test OK. Subscriptions: ${data.count}. Using mock: ${data.use_mock ? 'Yes' : 'No'}`, 'success');
  //     } else {
  //       showSnackbar(`Azure test failed. ${data.error || ''}`, 'error');
  //     }
  //   } catch (e) {
  //     showSnackbar('Azure test failed. Is backend running?', 'error');
  //   } finally {
  //     setTestingAzure(false);
  //   }
  // };

  const fetchUsers = async () => {
    try {
      const response = await fetch('http://127.0.0.1:9099/api/v1/users');
      const data = await response.json();
      setUsers(data.users || []);
    } catch (error) {
      console.error('Error fetching users:', error);
      showSnackbar('Failed to fetch users', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async () => {
    try {
      const response = await fetch('http://127.0.0.1:9099/api/v1/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userForm),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('User created:', result);
        setOpenUserDialog(false);
        resetUserForm();
        await fetchUsers();
        showSnackbar('User created successfully', 'success');
      } else {
        const error = await response.json();
        showSnackbar(error.detail || 'Failed to create user', 'error');
      }
    } catch (error) {
      console.error('Error creating user:', error);
      showSnackbar('Failed to create user', 'error');
    }
  };

  const handleUpdateUser = async () => {
    if (!editingUser) return;

    try {
      const response = await fetch(`http://127.0.0.1:9099/api/v1/users/${editingUser.email}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userForm),
      });

      if (response.ok) {
        setOpenUserDialog(false);
        setEditingUser(null);
        resetUserForm();
        await fetchUsers();
        showSnackbar('User updated successfully', 'success');
      } else {
        const error = await response.json();
        showSnackbar(error.detail || 'Failed to update user', 'error');
      }
    } catch (error) {
      console.error('Error updating user:', error);
      showSnackbar('Failed to update user', 'error');
    }
  };

  const saveEmailConfiguration = async () => {
    try {
      // Here you would typically send the email configuration to your backend
      // For now, we'll just show a success message
      const emailConfig = {
        smtp_host: settings.email.smtpHost,
        smtp_port: settings.email.smtpPort,
        smtp_username: settings.email.smtpUsername,
        smtp_password: settings.email.smtpPassword,
        smtp_tls: settings.email.smtpTls,
        from_email: settings.email.fromEmail,
        from_name: settings.email.fromName
      };

      // Simulate API call
      console.log('Saving email configuration:', emailConfig);
      
      // You can uncomment and modify this when you have the backend endpoint
      // const response = await fetch('http://127.0.0.1:9099/api/v1/email-config', {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json',
      //   },
      //   body: JSON.stringify(emailConfig),
      // });
      
      // if (response.ok) {
      //   showSnackbar('Email configuration saved successfully', 'success');
      // } else {
      //   const error = await response.json();
      //   showSnackbar(error.detail || 'Failed to save email configuration', 'error');
      // }
      
      // For now, just show success
      showSnackbar('Email configuration saved successfully', 'success');
    } catch (error) {
      console.error('Error saving email configuration:', error);
      showSnackbar('Failed to save email configuration', 'error');
    }
  };

  const handleDeleteUser = async (email: string) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        const response = await fetch(`http://127.0.0.1:9099/api/v1/users/${userEmail}`, {
          method: 'DELETE',
        });

        if (response.ok) {
          await fetchUsers();
          showSnackbar('User deleted successfully', 'success');
        } else {
          const error = await response.json();
          showSnackbar(error.detail || 'Failed to delete user', 'error');
        }
      } catch (error) {
        console.error('Error deleting user:', error);
        showSnackbar('Failed to delete user', 'error');
      }
    }
  };

  const openEditDialog = (user: User) => {
    setEditingUser(user);
    setUserForm({
      email: user.email,
      password: '',
      firstName: user.firstName,
      lastName: user.lastName,
      role: user.role,
      isActive: user.isActive
    });
    setOpenUserDialog(true);
  };

  const resetUserForm = () => {
    setUserForm({
      email: '',
      password: '',
      firstName: '',
      lastName: '',
      role: 'user',
      isActive: true
    });
  };

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity });
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'error';
      case 'analyst':
        return 'warning';
      default:
        return 'default';
    }
  };

  const canManageUsers = currentUser?.role === 'admin';

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Settings
      </Typography>

      <Paper>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab icon={<PersonIcon />} label="User Management" />
          <Tab icon={<SecurityIcon />} label="Security" />
          <Tab icon={<NotificationsIcon />} label="Notifications" />
          <Tab icon={<EmailIcon />} label="Email Configuration" />
          <Tab icon={<SettingsIcon />} label="General" />
        </Tabs>

        {/* User Management Tab */}
        <TabPanel value={tabValue} index={0}>
          {!canManageUsers ? (
            <Alert severity="warning">
              You don't have permission to manage users. Contact your administrator.
            </Alert>
          ) : (
            <>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h6">User Management</Typography>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => {
                    setEditingUser(null);
                    resetUserForm();
                    setOpenUserDialog(true);
                  }}
                >
                  Add User
                </Button>
              </Box>

              {/* User Statistics */}
              <Grid container spacing={3} mb={3}>
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6">{users.length}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Users
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6">
                        {users.filter(u => u.isActive).length}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Active Users
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6">
                        {users.filter(u => u.role === 'admin').length}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Administrators
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Users Table */}
              {loading ? (
                <Box display="flex" justifyContent="center" p={3}>
                  <CircularProgress />
                </Box>
              ) : (
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>User</TableCell>
                        <TableCell>Role</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Permissions</TableCell>
                        <TableCell>Created</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {users.map((user) => (
                        <TableRow key={user.id}>
                          <TableCell>
                            <Box display="flex" alignItems="center">
                              <Avatar sx={{ mr: 2 }}>
                                {user.firstName.charAt(0) + user.lastName.charAt(0)}
                              </Avatar>
                              <Box>
                                <Typography variant="body1">
                                  {user.firstName} {user.lastName}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {user.email}
                                </Typography>
                              </Box>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={user.role}
                              color={getRoleColor(user.role) as any}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={user.isActive ? 'Active' : 'Inactive'}
                              color={user.isActive ? 'success' : 'default'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="caption">
                              {user.permissions ? user.permissions.join(', ') : 'No permissions assigned'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {new Date(user.createdAt || user.created_at).toLocaleDateString()}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Tooltip title="Edit">
                              <IconButton size="small" onClick={() => openEditDialog(user)}>
                                <EditIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete">
                              <IconButton
                                size="small"
                                onClick={() => handleDeleteUser(user.email)}
                                disabled={user.email === currentUser?.email}
                              >
                                <DeleteIcon />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </>
          )}
        </TabPanel>

        {/* Security Tab */}
        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" gutterBottom>Security Settings</Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Session Timeout (minutes)"
                type="number"
                value={settings.security.sessionTimeout}
                onChange={(e) => setSettings({
                  ...settings,
                  security: { ...settings.security, sessionTimeout: parseInt(e.target.value) }
                })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Password Expiry (days)"
                type="number"
                value={settings.security.passwordExpiry}
                onChange={(e) => setSettings({
                  ...settings,
                  security: { ...settings.security, passwordExpiry: parseInt(e.target.value) }
                })}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.security.mfaRequired}
                    onChange={(e) => setSettings({
                      ...settings,
                      security: { ...settings.security, mfaRequired: e.target.checked }
                    })}
                  />
                }
                label="Require Multi-Factor Authentication"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.security.auditLogging}
                    onChange={(e) => setSettings({
                      ...settings,
                      security: { ...settings.security, auditLogging: e.target.checked }
                    })}
                  />
                }
                label="Enable Audit Logging"
              />
            </Grid>
          </Grid>
        </TabPanel>

        {/* Notifications Tab */}
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>Notification Preferences</Typography>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifications.emailNotifications}
                    onChange={(e) => setSettings({
                      ...settings,
                      notifications: { ...settings.notifications, emailNotifications: e.target.checked }
                    })}
                  />
                }
                label="Email Notifications"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifications.scanCompletionNotifications}
                    onChange={(e) => setSettings({
                      ...settings,
                      notifications: { ...settings.notifications, scanCompletionNotifications: e.target.checked }
                    })}
                  />
                }
                label="Scan Completion Notifications"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifications.securityAlerts}
                    onChange={(e) => setSettings({
                      ...settings,
                      notifications: { ...settings.notifications, securityAlerts: e.target.checked }
                    })}
                  />
                }
                label="Security Alerts"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifications.weeklyReports}
                    onChange={(e) => setSettings({
                      ...settings,
                      notifications: { ...settings.notifications, weeklyReports: e.target.checked }
                    })}
                  />
                }
                label="Weekly Reports"
              />
            </Grid>
          </Grid>
        </TabPanel>

        {/* Email Configuration Tab */}
        <TabPanel value={tabValue} index={3}>
          <Typography variant="h6" gutterBottom>Email Configuration</Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="SMTP Host"
                value={settings.email.smtpHost}
                onChange={(e) => setSettings({
                  ...settings,
                  email: { ...settings.email, smtpHost: e.target.value }
                })}
                placeholder="smtp.gmail.com"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="SMTP Port"
                type="number"
                value={settings.email.smtpPort}
                onChange={(e) => setSettings({
                  ...settings,
                  email: { ...settings.email, smtpPort: parseInt(e.target.value) }
                })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="SMTP Username"
                value={settings.email.smtpUsername}
                onChange={(e) => setSettings({
                  ...settings,
                  email: { ...settings.email, smtpUsername: e.target.value }
                })}
                placeholder="your-email@gmail.com"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="SMTP Password"
                type="password"
                value={settings.email.smtpPassword}
                onChange={(e) => setSettings({
                  ...settings,
                  email: { ...settings.email, smtpPassword: e.target.value }
                })}
                placeholder="App password or email password"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="From Email"
                value={settings.email.fromEmail}
                onChange={(e) => setSettings({
                  ...settings,
                  email: { ...settings.email, fromEmail: e.target.value }
                })}
                placeholder="noreply@yourcompany.com"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="From Name"
                value={settings.email.fromName}
                onChange={(e) => setSettings({
                  ...settings,
                  email: { ...settings.email, fromName: e.target.value }
                })}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.email.smtpTls}
                    onChange={(e) => setSettings({
                      ...settings,
                      email: { ...settings.email, smtpTls: e.target.checked }
                    })}
                  />
                }
                label="Enable TLS/SSL"
              />
            </Grid>
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={saveEmailConfiguration}
                >
                  Save Email Configuration
                </Button>
                <Button
                  variant="outlined"
                  color="secondary"
                  onClick={() => {
                    // Test email configuration functionality
                    alert('Email configuration test functionality will be implemented');
                  }}
                >
                  Test Configuration
                </Button>
              </Box>
            </Grid>
          </Grid>
        </TabPanel>

        {/* General Tab */}
        <TabPanel value={tabValue} index={4}>
          <Typography variant="h6" gutterBottom>Scanning Configuration</Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Max Concurrent Scans"
                type="number"
                value={settings.scanning.maxConcurrentScans}
                onChange={(e) => setSettings({
                  ...settings,
                  scanning: { ...settings.scanning, maxConcurrentScans: parseInt(e.target.value) }
                })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Scan Timeout (minutes)"
                type="number"
                value={settings.scanning.scanTimeout}
                onChange={(e) => setSettings({
                  ...settings,
                  scanning: { ...settings.scanning, scanTimeout: parseInt(e.target.value) }
                })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Data Retention (days)"
                type="number"
                value={settings.scanning.retentionDays}
                onChange={(e) => setSettings({
                  ...settings,
                  scanning: { ...settings.scanning, retentionDays: parseInt(e.target.value) }
                })}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.scanning.autoScanEnabled}
                    onChange={(e) => setSettings({
                      ...settings,
                      scanning: { ...settings.scanning, autoScanEnabled: e.target.checked }
                    })}
                  />
                }
                label="Enable Automatic Scanning"
              />
            </Grid>
          </Grid>
        </TabPanel>

        {/* Configuration Tab removed for .env-only testing */}
      </Paper>

      {/* User Dialog */}
      <Dialog open={openUserDialog} onClose={() => setOpenUserDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingUser ? 'Edit User' : 'Create New User'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Email"
                  type="email"
                  value={userForm.email}
                  onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                  disabled={!!editingUser}
                  required
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="First Name"
                  value={userForm.firstName}
                  onChange={(e) => setUserForm({ ...userForm, firstName: e.target.value })}
                  required
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Last Name"
                  value={userForm.lastName}
                  onChange={(e) => setUserForm({ ...userForm, lastName: e.target.value })}
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Password"
                  type="password"
                  value={userForm.password}
                  onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                  required={!editingUser}
                  helperText={editingUser ? "Leave blank to keep current password" : ""}
                />
              </Grid>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Role</InputLabel>
                  <Select
                    value={userForm.role}
                    label="Role"
                    onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}
                  >
                    {roles.map((role) => (
                      <MenuItem key={role.value} value={role.value}>
                        <Box>
                          <Typography variant="body1">{role.label}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {role.description}
                          </Typography>
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={userForm.isActive}
                      onChange={(e) => setUserForm({ ...userForm, isActive: e.target.checked })}
                    />
                  }
                  label="Active User"
                />
              </Grid>
              <Grid item xs={12}>
                <Alert severity="info">
                  <Typography variant="body2">
                    <strong>Permissions for {userForm.role}:</strong>
                  </Typography>
                  <Typography variant="caption">
                    {rolePermissions[userForm.role as keyof typeof rolePermissions]?.join(', ') || 'No permissions'}
                  </Typography>
                </Alert>
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenUserDialog(false)}>Cancel</Button>
          <Button
            onClick={editingUser ? handleUpdateUser : handleCreateUser}
            variant="contained"
            disabled={!userForm.email || !userForm.firstName || !userForm.lastName || (!editingUser && !userForm.password)}
          >
            {editingUser ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default SettingsPage;