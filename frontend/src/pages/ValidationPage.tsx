import React, { useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  TextField,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Checkbox,
  Divider,
  InputAdornment,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material'
import {
  CloudUpload as UploadIcon,
  Compare as CompareIcon,
  GetApp as ExportIcon,
  Email as EmailIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  FolderOpen as BrowseIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Clear as ClearIcon,
  AutoAwesome as AIIcon,
  Send as SendIcon,
  Preview as PreviewIcon,
  Visibility as VisibilityIcon,
  EmailOutlined as EmailTemplateIcon,
  Close as CloseIcon,
  Edit as EditIcon,
  Monitor as MonitorIcon,
  Assessment as AssessmentIcon,
  Speed as PerformanceIcon,
  NotificationsActive as NotificationIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material'

interface ValidationComparison {
  resource_name: string
  resource_group: string
  subscription_id: string
  subscription_name: string
  owner_name: string
  tags: Record<string, string>
  status: 'new' | 'updated' | 'unchanged' | 'removed'
  changes: string[]
  remediation_details: string
  recommended_steps: string[]
  severity: 'low' | 'medium' | 'high' | 'critical'
  compliance_status: string
  source_values?: Record<string, string>
  reference_values?: Record<string, string>
}

interface ValidationReport {
  validation_id: string
  total_resources: number
  new_resources: number
  updated_resources: number
  unchanged_resources: number
  removed_resources: number
  generated_at: string
  source_file: string
  reference_file: string
  comparisons: ValidationComparison[]
}

const ValidationPage: React.FC = () => {
  const [sourceFile, setSourceFile] = useState<string>('')
  const [referenceFile, setReferenceFile] = useState<string>('')
  const [sourceFileInput, setSourceFileInput] = useState<HTMLInputElement | null>(null)
  const [referenceFileInput, setReferenceFileInput] = useState<HTMLInputElement | null>(null)
  const [validationReport, setValidationReport] = useState<ValidationReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [emailDialog, setEmailDialog] = useState(false)
  const [emailRecipients, setEmailRecipients] = useState<string>('')
  const [includeAttachment, setIncludeAttachment] = useState(true)
  const [columnMappingDialog, setColumnMappingDialog] = useState(false)
  const [sourceColumns, setSourceColumns] = useState<string[]>([])
  const [referenceColumns, setReferenceColumns] = useState<string[]>([])
  const [columnMapping, setColumnMapping] = useState<Array<{ id: string; source: string; reference: string }>>([])  
  const [columnMappingConfigured, setColumnMappingConfigured] = useState(false)
  
  // LLM Email states
  const [llmEmailDialog, setLlmEmailDialog] = useState(false)
  const [selectedResources, setSelectedResources] = useState<Set<string>>(new Set())
  const [emailTemplate, setEmailTemplate] = useState<string>('')
  const [emailPreview, setEmailPreview] = useState<string>('')
  const [emailRecipientsList, setEmailRecipientsList] = useState<string>('')
  const [emailSendMode, setEmailSendMode] = useState<'bulk' | 'individual' | 'selected'>('bulk')
  const [llmEmailLoading, setLlmEmailLoading] = useState(false)
  const [previewDialog, setPreviewDialog] = useState(false)
  const [detailsDialog, setDetailsDialog] = useState(false)
  const [selectedItem, setSelectedItem] = useState<ValidationComparison | null>(null)
  const [emailTemplateDialog, setEmailTemplateDialog] = useState(false)
  const [selectedItemsForEmail, setSelectedItemsForEmail] = useState<Set<string>>(new Set())
  const [isEditingEmail, setIsEditingEmail] = useState(false)
  const [editableEmailContent, setEditableEmailContent] = useState<{
    subject: string
    resourceName: string
    resourceGroup: string
    subscription: string
    status: string
    severity: string
    changes: string
    remediationDetails: string
    recommendedSteps: string
    complianceStatus: string
    customMessage: string
  }>({
    subject: 'Security Validation Alert',
    resourceName: '',
    resourceGroup: '',
    subscription: '',
    status: '',
    severity: '',
    changes: '',
    remediationDetails: '',
    recommendedSteps: '',
    complianceStatus: '',
    customMessage: 'Please review and take appropriate action as needed.'
  })
  const [emailRecipientsList2, setEmailRecipientsList2] = useState<string>('')
  
  // Monitor states
  const [monitorDialog, setMonitorDialog] = useState(false)
  const [monitoringData, setMonitoringData] = useState<{
    scanStatus: 'idle' | 'running' | 'completed' | 'failed'
    agentPerformance: {
      totalAgents: number
      activeAgents: number
      successRate: number
      avgResponseTime: number
    }
    activityLogs: Array<{
      id: string
      timestamp: string
      type: 'scan' | 'agent' | 'notification' | 'error'
      message: string
      status: 'success' | 'warning' | 'error'
    }>
    emailNotificationStatus: {
      totalSent: number
      successful: number
      failed: number
      lastSent: string
      failureReasons: string[]
    }
  }>({
    scanStatus: 'idle',
    agentPerformance: {
      totalAgents: 0,
      activeAgents: 0,
      successRate: 0,
      avgResponseTime: 0
    },
    activityLogs: [],
    emailNotificationStatus: {
      totalSent: 0,
      successful: 0,
      failed: 0,
      lastSent: '',
      failureReasons: []
    }
  })
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [refreshInterval, setRefreshInterval] = useState(30) // seconds

  // Fetch monitoring data from backend
  const fetchMonitoringData = async () => {
    try {
      const response = await fetch('http://127.0.0.1:9099/api/v1/monitoring/status')
      const data = await response.json()
      
      if (data.success && data.monitoring) {
        setMonitoringData(data.monitoring)
      } else {
        console.error('Failed to fetch monitoring data:', data.error)
      }
    } catch (error) {
      console.error('Error fetching monitoring data:', error)
    }
  }

  // Handle AI analysis for activity logs and failure reasons
  const handleAIAnalysis = async (item: { type: string; message: string; context?: any }) => {
    try {
      const response = await fetch('http://127.0.0.1:9099/api/v1/monitoring/ai-analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          type: item.type,
          message: item.message,
          context: item.context || {}
        })
      })
      
      const data = await response.json()
      
      if (data.success && data.analysis) {
        // Show AI analysis in a dialog or alert
        alert(`AI Analysis for ${item.type}:\n\n${data.analysis.aiRecommendations}`)
      } else {
        alert('Failed to get AI analysis: ' + (data.error || 'Unknown error'))
      }
    } catch (error) {
      console.error('Error getting AI analysis:', error)
      alert('Error getting AI analysis: ' + error)
    }
  }

  // Auto-refresh monitoring data
  React.useEffect(() => {
    // Initial fetch
    fetchMonitoringData()
    
    // Set up auto-refresh if enabled
    let intervalId: NodeJS.Timeout | null = null
    if (autoRefresh && refreshInterval > 0) {
      intervalId = setInterval(fetchMonitoringData, refreshInterval * 1000)
    }
    
    return () => {
      if (intervalId) {
        clearInterval(intervalId)
      }
    }
  }, [autoRefresh, refreshInterval])

  const handleSourceFileBrowse = () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.csv,.xlsx,.xls'
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (file) {
        setSourceFile(file.name)
        setSourceFileInput(input)
      }
    }
    input.click()
  }

  const handleAnalyzeFiles = async () => {
    if (!sourceFile || !referenceFile || !sourceFileInput || !referenceFileInput) {
      setError('Please select both source and reference files')
      return
    }

    const sourceFileObj = sourceFileInput.files?.[0]
    const referenceFileObj = referenceFileInput.files?.[0]

    if (!sourceFileObj || !referenceFileObj) {
      setError('Please select both source and reference files')
      return
    }

    try {
      setLoading(true)
      setError(null)

      // Create FormData for file upload
      const formData = new FormData()
      formData.append('source_file', sourceFileObj)
      formData.append('reference_file', referenceFileObj)

      // Call the analyze API endpoint
      const response = await fetch('/api/v1/validation/analyze', {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (data.success) {
        setSourceColumns(data.source_columns)
        setReferenceColumns(data.reference_columns)
        // Initialize with one empty mapping row
        setColumnMapping([{
          id: Date.now().toString(),
          source: '',
          reference: ''
        }])
        setColumnMappingDialog(true)
      } else {
        setError(data.error || 'Failed to analyze files')
      }
    } catch (err) {
      setError('Error analyzing file columns')
      console.error('Column analysis error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRefreshValidation = async () => {
    if (!sourceFile || !referenceFile || !sourceFileInput || !referenceFileInput) {
      setError('No files available to refresh. Please upload files first.')
      return
    }

    const sourceFileObj = sourceFileInput.files?.[0]
    const referenceFileObj = referenceFileInput.files?.[0]

    if (!sourceFileObj || !referenceFileObj) {
      setError('Files are no longer available. Please re-upload files.')
      return
    }

    try {
      setLoading(true)
      setError(null)

      // Create FormData for file upload
      const formData = new FormData()
      formData.append('source_file', sourceFileObj)
      formData.append('reference_file', referenceFileObj)
      
      // Add column mapping if available
      if (columnMapping.length > 0) {
        const mappingData = columnMapping.reduce((acc, mapping) => {
          if (mapping.source) {
            acc[mapping.source] = {
              source: mapping.source,
              reference: mapping.reference || 'AS_IS'
            }
          }
          return acc
        }, {} as Record<string, { source: string; reference: string }>)
        
        formData.append('column_mapping', JSON.stringify(mappingData))
      }

      // Call the compare API endpoint to refresh data
      const response = await fetch('/api/v1/validation/compare', {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (data.success) {
        setValidationReport(data.report)
        setError(null)
      } else {
        setError(data.error || 'Failed to refresh validation data')
      }
    } catch (err) {
      setError('Error refreshing validation data')
      console.error('Refresh error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleReferenceFileBrowse = () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.csv,.xlsx,.xls'
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (file) {
        setReferenceFile(file.name)
        setReferenceFileInput(input)
      }
    }
    input.click()
  }

  const handleCompareFiles = async () => {
    if (!sourceFile || !referenceFile || !sourceFileInput || !referenceFileInput) {
      setError('Please select both source and reference files')
      return
    }

    const sourceFileObj = sourceFileInput.files?.[0]
    const referenceFileObj = referenceFileInput.files?.[0]

    if (!sourceFileObj || !referenceFileObj) {
      setError('Please select both source and reference files')
      return
    }

    // Column mapping validation is handled by button state

    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      // Convert column mapping array to the nested format expected by backend
      // Backend expects: { field: { source: 'source_col', reference: 'ref_col' } }
      const mappingObject: Record<string, Record<string, string>> = {}
      
      columnMapping.forEach((mapping, index) => {
        if (mapping.source && mapping.reference) {
          // Use a generic field name since we're doing direct column mapping
          const fieldKey = `field_${index}`
          mappingObject[fieldKey] = {
            source: mapping.source,
            reference: mapping.reference
          }
        }
      })

      // Create FormData for file upload
      const formData = new FormData()
      formData.append('source_file', sourceFileObj)
      formData.append('reference_file', referenceFileObj)
      formData.append('column_mapping', JSON.stringify(mappingObject))

      const response = await fetch('/api/v1/validation/compare', {
        method: 'POST',
        body: formData
      })

      const data = await response.json()

      if (data.success) {
        setValidationReport(data.report)
        setSuccess('Validation comparison completed successfully')
      } else {
        setError('Failed to compare files')
      }
    } catch (err) {
      setError('Error occurred during validation comparison')
      console.error('Validation error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSaveColumnMapping = () => {
    setColumnMappingDialog(false)
    setColumnMappingConfigured(true)
    setSuccess('Column mapping configured successfully. You can now compare files.')
  }

  const addColumnMapping = () => {
    const newMapping = {
      id: Date.now().toString(),
      source: '',
      reference: 'AS_IS'  // Default to AS_IS as per user requirement
    }
    setColumnMapping(prev => [...prev, newMapping])
  }

  const removeColumnMapping = (id: string) => {
    setColumnMapping(prev => prev.filter(mapping => mapping.id !== id))
  }

  const updateColumnMapping = (id: string, field: 'source' | 'reference', value: string) => {
    setColumnMapping(prev => prev.map(mapping => 
      mapping.id === id ? { ...mapping, [field]: value } : mapping
    ))
  }

  const handleExportReport = async (format: 'excel' | 'csv') => {
    if (!validationReport) return

    try {
      const response = await fetch('/api/v1/validation/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          report_data: validationReport,
          format: format
        })
      })

      const data = await response.json()

      if (data.success && data.file_content) {
        // Create and download the file
        const byteCharacters = atob(data.file_content)
        const byteNumbers = new Array(byteCharacters.length)
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i)
        }
        const byteArray = new Uint8Array(byteNumbers)
        const blob = new Blob([byteArray], {
          type: format === 'excel' ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' : 'text/csv'
        })
        
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = data.filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        setSuccess(`Report exported successfully as ${format.toUpperCase()}`)
      } else {
        setError('Failed to export report')
      }
    } catch (err) {
      setError('Error occurred during export')
      console.error('Export error:', err)
    }
  }

  const handleSendEmail = async () => {
    if (!validationReport || !emailRecipients) return

    const recipients = emailRecipients.split(',').map(email => email.trim())

    try {
      const response = await fetch('/api/v1/validation/notify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          report_data: validationReport,
          recipients: recipients,
          include_attachment: includeAttachment
        })
      })

      const data = await response.json()

      if (data.success) {
        setSuccess(`Email sent to ${recipients.length} recipients`)
        setEmailDialog(false)
        setEmailRecipients('')
      } else {
        setError('Failed to send email notification')
      }
    } catch (err) {
      setError('Error occurred while sending email')
      console.error('Email error:', err)
    }
  }

  // LLM Email Functions
  const handleResourceSelection = (resourceName: string, checked: boolean) => {
    setSelectedResources(prev => {
      const newSet = new Set(prev)
      if (checked) {
        newSet.add(resourceName)
      } else {
        newSet.delete(resourceName)
      }
      return newSet
    })
  }

  const handleSelectAllResources = (checked: boolean) => {
    if (checked && validationReport) {
      setSelectedResources(new Set(validationReport.comparisons.map(comp => comp.resource_name)))
    } else {
      setSelectedResources(new Set())
    }
  }

  const handleViewDetails = (item: ValidationComparison) => {
    setSelectedItem(item)
    setDetailsDialog(true)
  }

  const handleEmailTemplate = (item: ValidationComparison) => {
    setSelectedItem(item)
    // Populate editable content with item data
    setEditableEmailContent({
      subject: 'Security Validation Alert',
      resourceName: item.resource_name,
      resourceGroup: item.resource_group,
      subscription: item.subscription_name,
      status: item.status,
      severity: item.severity,
      changes: item.changes.length > 0 ? item.changes.join(', ') : 'No changes detected',
      remediationDetails: item.remediation_details,
      recommendedSteps: item.recommended_steps.join(', '),
      complianceStatus: item.compliance_status,
      customMessage: 'Please review and take appropriate action as needed.'
    })
    setEmailRecipientsList2('')
    setIsEditingEmail(false)
    setEmailTemplateDialog(true)
  }

  const handleEditEmail = () => {
    setIsEditingEmail(true)
  }

  const handleSaveEmailEdit = () => {
    setIsEditingEmail(false)
  }

  const handleCancelEmailEdit = () => {
    if (selectedItem) {
      // Reset to original values
      setEditableEmailContent({
        subject: 'Security Validation Alert',
        resourceName: selectedItem.resource_name,
        resourceGroup: selectedItem.resource_group,
        subscription: selectedItem.subscription_name,
        status: selectedItem.status,
        severity: selectedItem.severity,
        changes: selectedItem.changes.length > 0 ? selectedItem.changes.join(', ') : 'No changes detected',
        remediationDetails: selectedItem.remediation_details,
        recommendedSteps: selectedItem.recommended_steps.join(', '),
        complianceStatus: selectedItem.compliance_status,
        customMessage: 'Please review and take appropriate action as needed.'
      })
    }
    setIsEditingEmail(false)
  }

  const handleSendTemplateEmail = async () => {
    if (!emailRecipientsList2.trim()) {
      setError('Please enter email recipients')
      return
    }

    try {
      setLlmEmailLoading(true)
      // Here you would implement the actual email sending logic
      console.log('Sending template email:', {
        recipients: emailRecipientsList2,
        content: editableEmailContent
      })
      setSuccess('Email sent successfully')
      setEmailTemplateDialog(false)
    } catch (err) {
      setError('Failed to send email')
    } finally {
      setLlmEmailLoading(false)
    }
  }

  const handleEmailItemSelection = (resourceName: string, checked: boolean) => {
    const newSelected = new Set(selectedItemsForEmail)
    if (checked) {
      newSelected.add(resourceName)
    } else {
      newSelected.delete(resourceName)
    }
    setSelectedItemsForEmail(newSelected)
  }

  const handleSendSelectedEmails = async () => {
    if (selectedItemsForEmail.size === 0) {
      setError('Please select items to send emails for')
      return
    }
    
    try {
      setLlmEmailLoading(true)
      const selectedItems = validationReport?.comparisons.filter(item => 
        selectedItemsForEmail.has(item.resource_name)
      ) || []
      
      // Here you would implement the actual email sending logic
      console.log('Sending emails for selected items:', selectedItems)
      setSuccess(`Email notifications sent for ${selectedItems.length} items`)
      setSelectedItemsForEmail(new Set())
    } catch (err) {
      setError('Failed to send email notifications')
    } finally {
      setLlmEmailLoading(false)
    }
  }

  const handleGenerateLLMEmail = async () => {
    if (!validationReport) return

    let resourcesToProcess = validationReport.comparisons
    
    if (emailSendMode === 'selected') {
      resourcesToProcess = validationReport.comparisons.filter(comp => 
        selectedResources.has(comp.resource_name)
      )
      if (resourcesToProcess.length === 0) {
        setError('Please select at least one resource for email generation')
        return
      }
    }

    try {
      setLlmEmailLoading(true)
      setError(null)

      const response = await fetch('/api/v1/validation/llm-email/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          resources: resourcesToProcess,
          send_mode: emailSendMode
        })
      })

      const data = await response.json()

      if (data.success) {
        setEmailTemplate(data.template)
        setSuccess('LLM email template generated successfully')
      } else {
        setError(data.error || 'Failed to generate LLM email template')
      }
    } catch (err) {
      setError('Error occurred while generating LLM email template')
      console.error('LLM Email generation error:', err)
    } finally {
      setLlmEmailLoading(false)
    }
  }

  const handlePreviewLLMEmail = async () => {
    if (!validationReport) return

    let resourcesToProcess = validationReport.comparisons
    
    if (emailSendMode === 'selected') {
      resourcesToProcess = validationReport.comparisons.filter(comp => 
        selectedResources.has(comp.resource_name)
      )
    }

    try {
      setLlmEmailLoading(true)

      const response = await fetch('/api/v1/validation/llm-email/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          resources: resourcesToProcess,
          send_mode: emailSendMode
        })
      })

      const data = await response.json()

      if (data.success) {
        setEmailPreview(data.preview)
        setPreviewDialog(true)
      } else {
        setError(data.error || 'Failed to generate email preview')
      }
    } catch (err) {
      setError('Error occurred while generating email preview')
      console.error('Email preview error:', err)
    } finally {
      setLlmEmailLoading(false)
    }
  }

  const handleSendLLMEmail = async () => {
    if (!validationReport || !emailRecipientsList.trim()) {
      setError('Please enter recipient email addresses')
      return
    }

    let resourcesToProcess = validationReport.comparisons
    
    if (emailSendMode === 'selected') {
      resourcesToProcess = validationReport.comparisons.filter(comp => 
        selectedResources.has(comp.resource_name)
      )
      if (resourcesToProcess.length === 0) {
        setError('Please select at least one resource for email sending')
        return
      }
    }

    const recipients = emailRecipientsList.split(',').map(email => email.trim())

    try {
      setLlmEmailLoading(true)
      setError(null)

      const response = await fetch('/api/v1/validation/llm-email/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          resources: resourcesToProcess,
          recipients: recipients,
          send_mode: emailSendMode
        })
      })

      const data = await response.json()

      if (data.success) {
        setSuccess(`LLM-powered emails sent successfully to ${recipients.length} recipients`)
        setLlmEmailDialog(false)
        setEmailRecipientsList('')
        setSelectedResources(new Set())
      } else {
        setError(data.error || 'Failed to send LLM emails')
      }
    } catch (err) {
      setError('Error occurred while sending LLM emails')
      console.error('LLM Email sending error:', err)
    } finally {
      setLlmEmailLoading(false)
    }
  }

  const handleClearAll = () => {
    // Reset all state variables to initial values
    setSourceFile('')
    setReferenceFile('')
    setSourceFileInput(null)
    setReferenceFileInput(null)
    setValidationReport(null)
    setLoading(false)
    setError(null)
    setSuccess(null)
    setEmailDialog(false)
    setEmailRecipients('')
    setIncludeAttachment(true)
    setColumnMappingDialog(false)
    setSourceColumns([])
    setReferenceColumns([])
    setColumnMapping([])
    setColumnMappingConfigured(false)
    setLlmEmailDialog(false)
    setSelectedResources(new Set())
    setEmailTemplate('')
    setEmailPreview('')
    setEmailRecipientsList('')
    setEmailSendMode('bulk')
    setLlmEmailLoading(false)
    setPreviewDialog(false)
  }

  const handleRefreshMonitoring = () => {
    fetchMonitoringData()
  }

  // Auto-refresh effect
  React.useEffect(() => {
    if (autoRefresh && monitorDialog) {
      const interval = setInterval(() => {
        fetchMonitoringData()
      }, refreshInterval * 1000)
      
      return () => clearInterval(interval)
    }
  }, [autoRefresh, refreshInterval, monitorDialog])

  // Initial fetch when dialog opens
  React.useEffect(() => {
    if (monitorDialog) {
      fetchMonitoringData()
    }
  }, [monitorDialog])

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'error'
      case 'high': return 'warning'
      case 'medium': return 'info'
      case 'low': return 'success'
      default: return 'default'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'new': return 'success'
      case 'updated': return 'warning'
      case 'unchanged': return 'default'
      case 'removed': return 'error'
      default: return 'default'
    }
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Resource Validation
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Compare CSV/Excel reports to validate resource configurations and generate update lists with remediation details.
      </Typography>

      {/* File Input Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <UploadIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            File Configuration
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Source File Path"
                value={sourceFile}
                onChange={(e) => setSourceFile(e.target.value)}
                placeholder="e.g., /path/to/source_report.xlsx"
                helperText="Path to the source CSV/Excel file or browse to select"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={handleSourceFileBrowse}
                        edge="end"
                        title="Browse for file"
                      >
                        <BrowseIcon />
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Reference File Path"
                value={referenceFile}
                onChange={(e) => setReferenceFile(e.target.value)}
                placeholder="e.g., /path/to/reference_report.xlsx"
                helperText="Path to the reference CSV/Excel file or browse to select"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={handleReferenceFileBrowse}
                        edge="end"
                        title="Browse for file"
                      >
                        <BrowseIcon />
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
          </Grid>
          <Box sx={{ mt: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button
              variant="outlined"
              onClick={handleAnalyzeFiles}
              disabled={!sourceFile || !referenceFile}
              startIcon={<UploadIcon />}
            >
              Analyze & Map Columns
            </Button>
            <Button
              variant="contained"
              onClick={handleCompareFiles}
              disabled={loading || !sourceFile || !referenceFile || !columnMappingConfigured}
              startIcon={loading ? <CircularProgress size={20} /> : <CompareIcon />}
            >
              {loading ? 'Comparing...' : 'Compare Files'}
            </Button>
            <Button
              variant="outlined"
              color="secondary"
              onClick={handleClearAll}
              disabled={loading}
              startIcon={<ClearIcon />}
            >
              Clear All
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Alerts */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Validation Report */}
      {validationReport && (
        <>
          {/* Summary Cards */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {validationReport.total_resources}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Resources
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="success.main">
                    {validationReport.new_resources}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    New Resources
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="warning.main">
                    {validationReport.updated_resources}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Updated Resources
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="text.secondary">
                    {validationReport.unchanged_resources}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Unchanged Resources
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="error.main">
                    {validationReport.removed_resources}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Removed Resources
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Action Buttons */}
          <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button
              variant="outlined"
              startIcon={<ExportIcon />}
              onClick={() => handleExportReport('excel')}
            >
              Export to Excel
            </Button>
            <Button
              variant="outlined"
              startIcon={<ExportIcon />}
              onClick={() => handleExportReport('csv')}
            >
              Export to CSV
            </Button>
            <Button
              variant="outlined"
              startIcon={<EmailIcon />}
              onClick={() => setEmailDialog(true)}
            >
              Send Email
            </Button>
            <Button
              variant="contained"
              startIcon={<MonitorIcon />}
              onClick={() => setMonitorDialog(true)}
              sx={{ bgcolor: 'success.main', '&:hover': { bgcolor: 'success.dark' } }}
            >
              Monitor
            </Button>
            <Button
              variant="contained"
              startIcon={<SendIcon />}
              onClick={handleSendSelectedEmails}
              disabled={selectedItemsForEmail.size === 0 || llmEmailLoading}
              sx={{ bgcolor: 'success.main', '&:hover': { bgcolor: 'success.dark' } }}
            >
              Send Selected Emails ({selectedItemsForEmail.size})
            </Button>
          </Box>

          {/* Detailed Results Table */}
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">
                  Validation Results
                </Typography>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<RefreshIcon />}
                  onClick={handleRefreshValidation}
                  disabled={loading || !validationReport}
                >
                  Refresh
                </Button>
              </Box>
              <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
                <Table stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell padding="checkbox">
                        <Checkbox
                          indeterminate={selectedResources.size > 0 && selectedResources.size < validationReport.comparisons.length}
                          checked={validationReport.comparisons.length > 0 && selectedResources.size === validationReport.comparisons.length}
                          onChange={(e) => handleSelectAllResources(e.target.checked)}
                        />
                      </TableCell>
                      {columnMapping.length > 0 ? (
                        columnMapping.map((mapping, index) => (
                          <TableCell key={index}>{mapping.source || `Column ${index + 1}`}</TableCell>
                        ))
                      ) : (
                        <>
                          <TableCell>Source Column Selection</TableCell>
                          <TableCell>Resource Group</TableCell>
                          <TableCell>Subscription</TableCell>
                          <TableCell>Owner</TableCell>
                        </>
                      )}
                      <TableCell>Status</TableCell>
                      <TableCell>Changes (Source vs Reference)</TableCell>
                      <TableCell>Severity</TableCell>
                      <TableCell>Remediation</TableCell>
                      <TableCell>Recommended Steps</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {validationReport.comparisons.map((comparison, index) => (
                      <TableRow key={index}>
                        <TableCell padding="checkbox">
                          <Checkbox
                            checked={selectedResources.has(comparison.resource_name)}
                            onChange={(e) => handleResourceSelection(comparison.resource_name, e.target.checked)}
                          />
                        </TableCell>
                        {columnMapping.length > 0 ? (
                          columnMapping.map((mapping, colIndex) => {
                            // Display actual source vs reference values from the comparison data
                            const sourceCol = mapping.source;
                            const referenceCol = mapping.reference;
                            
                            // Get actual values from the comparison data
                            let sourceValue = 'N/A';
                            let referenceValue = 'N/A';
                            
                            // Debug: Log available data
                            console.log('Column mapping:', { sourceCol, referenceCol });
                            console.log('Available source_values:', comparison.source_values);
                            console.log('Available reference_values:', comparison.reference_values);
                            
                            // Try to get source value from source_values
                            if (comparison.source_values && sourceCol) {
                              // Try exact match first
                              if (comparison.source_values[sourceCol]) {
                                sourceValue = comparison.source_values[sourceCol];
                              } else {
                                // Try to find any matching column (case insensitive, partial match)
                                const sourceKeys = Object.keys(comparison.source_values);
                                const matchingKey = sourceKeys.find(key => 
                                  key.toLowerCase() === sourceCol.toLowerCase() ||
                                  key.toLowerCase().includes(sourceCol.toLowerCase()) ||
                                  sourceCol.toLowerCase().includes(key.toLowerCase())
                                );
                                if (matchingKey) {
                                  sourceValue = comparison.source_values[matchingKey];
                                } else if (sourceKeys.length > 0) {
                                  // If no match found, use the first available value as fallback
                                  sourceValue = comparison.source_values[sourceKeys[0]];
                                }
                              }
                            }
                            
                            // Get reference value
                            if (referenceCol === 'AS_IS') {
                              referenceValue = sourceValue;
                            } else if (comparison.reference_values && referenceCol) {
                              // Try exact match first
                              if (comparison.reference_values[referenceCol]) {
                                referenceValue = comparison.reference_values[referenceCol];
                              } else {
                                // Try to find any matching column (case insensitive, partial match)
                                const refKeys = Object.keys(comparison.reference_values);
                                const matchingKey = refKeys.find(key => 
                                  key.toLowerCase() === referenceCol.toLowerCase() ||
                                  key.toLowerCase().includes(referenceCol.toLowerCase()) ||
                                  referenceCol.toLowerCase().includes(key.toLowerCase())
                                );
                                if (matchingKey) {
                                  referenceValue = comparison.reference_values[matchingKey];
                                } else if (refKeys.length > 0) {
                                  // If no match found, use the first available value as fallback
                                  referenceValue = comparison.reference_values[refKeys[0]];
                                }
                              }
                            }
                            
                            // Show if values are different
                            const isDifferent = sourceValue !== referenceValue && referenceValue !== 'N/A';
                            
                            return (
                              <TableCell key={colIndex}>
                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                                  <Typography 
                                    variant="body2" 
                                    sx={{ 
                                      fontWeight: 'bold', 
                                      color: isDifferent ? 'warning.main' : 'primary.main' 
                                    }}
                                  >
                                    Source: {sourceValue}
                                  </Typography>
                                  <Typography 
                                    variant="caption" 
                                    sx={{ 
                                      color: isDifferent ? 'error.main' : 'text.secondary',
                                      fontWeight: isDifferent ? 'bold' : 'normal'
                                    }}
                                  >
                                    Reference: {referenceValue}
                                  </Typography>
                                  {isDifferent && (
                                    <Typography variant="caption" sx={{ color: 'warning.main', fontStyle: 'italic' }}>
                                      ⚠️ Values differ
                                    </Typography>
                                  )}
                                </Box>
                              </TableCell>
                            );
                          })
                        ) : (
                          <>
                            <TableCell>
                              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                                <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                                  Source: {comparison.resource_name}
                                </Typography>
                                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                                  Reference: {comparison.resource_name}
                                </Typography>
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                                <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                                  Source: {comparison.resource_group}
                                </Typography>
                                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                                  Reference: {comparison.resource_group}
                                </Typography>
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                                <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                                  Source: {comparison.subscription_name}
                                </Typography>
                                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                                  Reference: {comparison.subscription_name}
                                </Typography>
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                                <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                                  Source: {comparison.owner_name}
                                </Typography>
                                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                                  Reference: {comparison.owner_name}
                                </Typography>
                              </Box>
                            </TableCell>
                          </>
                        )}
                        <TableCell>
                          <Chip
                            label={comparison.status}
                            color={getSeverityColor(comparison.status) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell sx={{ maxWidth: 300 }}>
                          {comparison.changes.length > 0 ? (
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                              {comparison.changes.slice(0, 3).map((change, changeIndex) => {
                                const isAddition = change.includes('added:');
                                const isRemoval = change.includes('removed:');
                                const isModification = change.includes('changed from');
                                
                                return (
                                  <Typography 
                                    key={changeIndex} 
                                    variant="caption" 
                                    sx={{ 
                                      fontSize: '0.75rem',
                                      color: isAddition ? 'success.main' : isRemoval ? 'error.main' : isModification ? 'warning.main' : 'text.secondary',
                                      fontWeight: isAddition || isRemoval || isModification ? 'bold' : 'normal'
                                    }}
                                  >
                                    {isAddition && '+ '}{isRemoval && '- '}{isModification && '~ '}
                                    {change.length > 50 ? `${change.substring(0, 50)}...` : change}
                                  </Typography>
                                );
                              })}
                              {comparison.changes.length > 3 && (
                                <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                                  +{comparison.changes.length - 3} more changes
                                </Typography>
                              )}
                            </Box>
                          ) : (
                            <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                              No changes detected
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={comparison.severity}
                            color={getSeverityColor(comparison.severity) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell sx={{ maxWidth: 200 }}>
                          <Typography variant="body2" noWrap>
                            {comparison.remediation_details}
                          </Typography>
                        </TableCell>
                        <TableCell sx={{ maxWidth: 200 }}>
                          <Typography variant="body2" noWrap>
                            {comparison.recommended_steps.join(', ')}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <IconButton
                              size="small"
                              onClick={() => handleViewDetails(comparison)}
                              title="View Details"
                              color="primary"
                            >
                              <VisibilityIcon fontSize="small" />
                            </IconButton>
                            <IconButton
                              size="small"
                              onClick={() => handleEmailTemplate(comparison)}
                              title="Email Template"
                              color="secondary"
                            >
                              <EmailTemplateIcon fontSize="small" />
                            </IconButton>
                            <Checkbox
                              size="small"
                              checked={selectedItemsForEmail.has(comparison.resource_name)}
                              onChange={(e) => handleEmailItemSelection(comparison.resource_name, e.target.checked)}
                              title="Select for Email"
                            />
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </>
      )}

      {/* Email Dialog */}
      <Dialog open={emailDialog} onClose={() => setEmailDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Send Email Notification</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Recipients"
            value={emailRecipients}
            onChange={(e) => setEmailRecipients(e.target.value)}
            placeholder="email1@example.com, email2@example.com"
            helperText="Enter email addresses separated by commas"
            sx={{ mt: 2, mb: 2 }}
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={includeAttachment}
                onChange={(e) => setIncludeAttachment(e.target.checked)}
              />
            }
            label="Include report as attachment"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEmailDialog(false)}>Cancel</Button>
          <Button
            onClick={handleSendEmail}
            variant="contained"
            disabled={!emailRecipients.trim()}
          >
            Send Email
          </Button>
        </DialogActions>
      </Dialog>

      {/* Column Mapping Dialog */}
      <Dialog open={columnMappingDialog} onClose={() => setColumnMappingDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Configure Column Mapping</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Map columns from your source and reference files. By default, reference columns use "AS IS" (same value from source). 
            The system will automatically search for matching values and handle empty reference columns intelligently.
          </Typography>
          
          <Box sx={{ mb: 3 }}>
            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={addColumnMapping}
              sx={{ mb: 2 }}
            >
              Add Column Mapping
            </Button>
          </Box>
          
          {columnMapping.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
              No column mappings configured. Click "Add Column Mapping" to get started.
            </Typography>
          ) : (
            <Grid container spacing={2}>
              {columnMapping.map((mapping, index) => (
                <Grid item xs={12} key={mapping.id}>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Grid container spacing={2} alignItems="center">
                      <Grid item xs={5}>
                        <FormControl fullWidth size="small">
                          <InputLabel>Source Column</InputLabel>
                          <Select
                            value={mapping.source}
                            label="Source Column"
                            onChange={(e) => updateColumnMapping(mapping.id, 'source', e.target.value)}
                          >
                            <MenuItem value="">
                              <em>-- Select from available columns --</em>
                            </MenuItem>
                            {sourceColumns.map((col) => (
                              <MenuItem key={col} value={col}>{col}</MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      </Grid>
                      <Grid item xs={1} sx={{ textAlign: 'center' }}>
                        <Typography variant="h6" color="primary" sx={{ fontWeight: 'bold' }}>
                          ↔
                        </Typography>
                      </Grid>
                      <Grid item xs={5}>
                        <FormControl fullWidth size="small">
                          <InputLabel>Reference Column</InputLabel>
                          <Select
                            value={mapping.reference}
                            label="Reference Column"
                            onChange={(e) => updateColumnMapping(mapping.id, 'reference', e.target.value)}
                          >
                            <MenuItem value="">
                              <em>-- Select from available columns --</em>
                            </MenuItem>
                            <MenuItem value="AS_IS" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                              🔄 AS IS (Use same value from source)
                            </MenuItem>
                            <Divider />
                            {referenceColumns.map((col) => (
                              <MenuItem key={col} value={col}>{col}</MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                        {mapping.reference === 'AS_IS' && (
                          <Typography variant="caption" color="primary" sx={{ mt: 0.5, display: 'block', fontStyle: 'italic' }}>
                            ✓ Will use the same column value from source file: {mapping.source || 'Select source column first'}
                          </Typography>
                        )}
                      </Grid>
                      <Grid item xs={1}>
                        <IconButton
                          onClick={() => removeColumnMapping(mapping.id)}
                          color="error"
                          size="small"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Grid>
                    </Grid>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setColumnMappingDialog(false)}>Cancel</Button>
          <Button
            onClick={handleSaveColumnMapping}
            variant="contained"
            disabled={columnMapping.length === 0 || !columnMapping.some(mapping => mapping.source || mapping.reference)}
          >
            Save Mapping
          </Button>
        </DialogActions>
      </Dialog>

      {/* LLM Email Dialog */}
      <Dialog open={llmEmailDialog} onClose={() => setLlmEmailDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AIIcon color="primary" />
            AI-Powered Email Notifications
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Generate personalized email notifications with AI-powered recommendations, remediation steps, business impact analysis, and Azure commands for each resource.
          </Typography>
          
          {/* Send Mode Selection */}
          <FormControl fullWidth sx={{ mb: 3 }}>
            <InputLabel>Email Send Mode</InputLabel>
            <Select
              value={emailSendMode}
              label="Email Send Mode"
              onChange={(e) => setEmailSendMode(e.target.value as 'bulk' | 'individual' | 'selected')}
            >
              <MenuItem value="bulk">Bulk Email (All resources in one email)</MenuItem>
              <MenuItem value="individual">Individual Emails (One email per resource)</MenuItem>
              <MenuItem value="selected">Selected Resources Only</MenuItem>
            </Select>
          </FormControl>

          {emailSendMode === 'selected' && (
            <Alert severity="info" sx={{ mb: 3 }}>
              You have selected {selectedResources.size} resource(s) for email generation. 
              {selectedResources.size === 0 && 'Please select at least one resource from the table above.'}
            </Alert>
          )}

          {/* Recipients */}
          <TextField
            fullWidth
            label="Recipients"
            value={emailRecipientsList}
            onChange={(e) => setEmailRecipientsList(e.target.value)}
            placeholder="email1@example.com, email2@example.com"
            helperText="Enter email addresses separated by commas"
            sx={{ mb: 3 }}
          />

          {/* Email Template Preview */}
          {emailTemplate && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Generated Email Template Preview
              </Typography>
              <Paper sx={{ p: 2, bgcolor: 'grey.50', maxHeight: 200, overflow: 'auto' }}>
                <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                  {emailTemplate.substring(0, 500)}...
                </Typography>
              </Paper>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLlmEmailDialog(false)}>Cancel</Button>
          <Button
            onClick={handlePreviewLLMEmail}
            startIcon={<PreviewIcon />}
            disabled={llmEmailLoading || (emailSendMode === 'selected' && selectedResources.size === 0)}
          >
            Preview
          </Button>
          <Button
            onClick={handleGenerateLLMEmail}
            startIcon={<AIIcon />}
            disabled={llmEmailLoading || (emailSendMode === 'selected' && selectedResources.size === 0)}
          >
            {llmEmailLoading ? <CircularProgress size={20} /> : 'Generate Template'}
          </Button>
          <Button
            onClick={handleSendLLMEmail}
            variant="contained"
            startIcon={<SendIcon />}
            disabled={llmEmailLoading || !emailRecipientsList.trim() || (emailSendMode === 'selected' && selectedResources.size === 0)}
          >
            {llmEmailLoading ? <CircularProgress size={20} /> : 'Send Emails'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Email Preview Dialog */}
      <Dialog open={previewDialog} onClose={() => setPreviewDialog(false)} maxWidth="lg" fullWidth>
        <DialogTitle>Email Preview</DialogTitle>
        <DialogContent>
          <Paper sx={{ p: 3, bgcolor: 'grey.50' }}>
            <div dangerouslySetInnerHTML={{ __html: emailPreview }} />
          </Paper>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Item Details Dialog */}
      <Dialog open={detailsDialog} onClose={() => setDetailsDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <VisibilityIcon color="primary" />
              Item Details
            </Box>
            <IconButton onClick={() => setDetailsDialog(false)}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedItem && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">Resource Name</Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>{selectedItem.resource_name}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">Resource Group</Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>{selectedItem.resource_group}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">Subscription</Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>{selectedItem.subscription_name}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">Owner</Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>{selectedItem.owner_name}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">Status</Typography>
                  <Chip
                    label={selectedItem.status}
                    color={getSeverityColor(selectedItem.status) as any}
                    size="small"
                    sx={{ mb: 2 }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">Severity</Typography>
                  <Chip
                    label={selectedItem.severity}
                    color={getSeverityColor(selectedItem.severity) as any}
                    size="small"
                    sx={{ mb: 2 }}
                  />
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">Tags</Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>
                    {Object.keys(selectedItem.tags).length > 0 
                      ? JSON.stringify(selectedItem.tags, null, 2)
                      : 'No tags available'
                    }
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">Changes</Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>
                    {selectedItem.changes.length > 0 
                      ? selectedItem.changes.join(', ')
                      : 'No changes detected'
                    }
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">Remediation Details</Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>{selectedItem.remediation_details}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">Recommended Steps</Typography>
                  <Box component="ul" sx={{ pl: 2, mb: 2 }}>
                    {selectedItem.recommended_steps.map((step, index) => (
                      <li key={index}>
                        <Typography variant="body2">{step}</Typography>
                      </li>
                    ))}
                  </Box>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">Compliance Status</Typography>
                  <Typography variant="body1">{selectedItem.compliance_status}</Typography>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Email Template Dialog */}
      <Dialog open={emailTemplateDialog} onClose={() => setEmailTemplateDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <EmailTemplateIcon color="secondary" />
              Email Template {isEditingEmail ? 'Editor' : 'Preview'}
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {!isEditingEmail && (
                <Button
                  startIcon={<EditIcon />}
                  onClick={handleEditEmail}
                  size="small"
                  variant="outlined"
                >
                  Edit
                </Button>
              )}
              <IconButton onClick={() => setEmailTemplateDialog(false)}>
                <CloseIcon />
              </IconButton>
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedItem && (
            <Box sx={{ mt: 2 }}>
              {isEditingEmail ? (
                // Edit Mode
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <TextField
                    fullWidth
                    label="Email Subject"
                    value={editableEmailContent.subject}
                    onChange={(e) => setEditableEmailContent(prev => ({ ...prev, subject: e.target.value }))}
                  />
                  <TextField
                    fullWidth
                    label="Resource Name"
                    value={editableEmailContent.resourceName}
                    onChange={(e) => setEditableEmailContent(prev => ({ ...prev, resourceName: e.target.value }))}
                  />
                  <TextField
                    fullWidth
                    label="Resource Group"
                    value={editableEmailContent.resourceGroup}
                    onChange={(e) => setEditableEmailContent(prev => ({ ...prev, resourceGroup: e.target.value }))}
                  />
                  <TextField
                    fullWidth
                    label="Subscription"
                    value={editableEmailContent.subscription}
                    onChange={(e) => setEditableEmailContent(prev => ({ ...prev, subscription: e.target.value }))}
                  />
                  <TextField
                    fullWidth
                    label="Status"
                    value={editableEmailContent.status}
                    onChange={(e) => setEditableEmailContent(prev => ({ ...prev, status: e.target.value }))}
                  />
                  <TextField
                    fullWidth
                    label="Severity"
                    value={editableEmailContent.severity}
                    onChange={(e) => setEditableEmailContent(prev => ({ ...prev, severity: e.target.value }))}
                  />
                  <TextField
                    fullWidth
                    label="Changes Detected"
                    multiline
                    rows={2}
                    value={editableEmailContent.changes}
                    onChange={(e) => setEditableEmailContent(prev => ({ ...prev, changes: e.target.value }))}
                  />
                  <TextField
                    fullWidth
                    label="Remediation Details"
                    multiline
                    rows={3}
                    value={editableEmailContent.remediationDetails}
                    onChange={(e) => setEditableEmailContent(prev => ({ ...prev, remediationDetails: e.target.value }))}
                  />
                  <TextField
                    fullWidth
                    label="Recommended Steps"
                    multiline
                    rows={3}
                    value={editableEmailContent.recommendedSteps}
                    onChange={(e) => setEditableEmailContent(prev => ({ ...prev, recommendedSteps: e.target.value }))}
                  />
                  <TextField
                    fullWidth
                    label="Compliance Status"
                    value={editableEmailContent.complianceStatus}
                    onChange={(e) => setEditableEmailContent(prev => ({ ...prev, complianceStatus: e.target.value }))}
                  />
                  <TextField
                    fullWidth
                    label="Custom Message"
                    multiline
                    rows={2}
                    value={editableEmailContent.customMessage}
                    onChange={(e) => setEditableEmailContent(prev => ({ ...prev, customMessage: e.target.value }))}
                  />
                </Box>
              ) : (
                // Preview Mode
                <Paper sx={{ p: 3, bgcolor: 'grey.50' }}>
                  <Typography variant="h6" gutterBottom>{editableEmailContent.subject}</Typography>
                  <Typography variant="body1" paragraph>
                    <strong>Resource:</strong> {editableEmailContent.resourceName}
                  </Typography>
                  <Typography variant="body1" paragraph>
                    <strong>Resource Group:</strong> {editableEmailContent.resourceGroup}
                  </Typography>
                  <Typography variant="body1" paragraph>
                    <strong>Subscription:</strong> {editableEmailContent.subscription}
                  </Typography>
                  <Typography variant="body1" paragraph>
                    <strong>Status:</strong> {editableEmailContent.status}
                  </Typography>
                  <Typography variant="body1" paragraph>
                    <strong>Severity:</strong> {editableEmailContent.severity}
                  </Typography>
                  <Typography variant="body1" paragraph>
                    <strong>Changes Detected:</strong><br />
                    {editableEmailContent.changes}
                  </Typography>
                  <Typography variant="body1" paragraph>
                    <strong>Remediation Details:</strong><br />
                    {editableEmailContent.remediationDetails}
                  </Typography>
                  <Typography variant="body1" paragraph>
                    <strong>Recommended Actions:</strong><br />
                    {editableEmailContent.recommendedSteps}
                  </Typography>
                  <Typography variant="body1" paragraph>
                    <strong>Compliance Status:</strong> {editableEmailContent.complianceStatus}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {editableEmailContent.customMessage}
                  </Typography>
                </Paper>
              )}
              <TextField
                fullWidth
                label="Email Recipients"
                placeholder="email1@example.com, email2@example.com"
                value={emailRecipientsList2}
                onChange={(e) => setEmailRecipientsList2(e.target.value)}
                sx={{ mt: 2 }}
                helperText="Enter email addresses separated by commas"
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          {isEditingEmail ? (
            <>
              <Button onClick={handleCancelEmailEdit}>Cancel</Button>
              <Button onClick={handleSaveEmailEdit} variant="contained">
                Save Changes
              </Button>
            </>
          ) : (
            <>
              <Button onClick={() => setEmailTemplateDialog(false)}>Close</Button>
              <Button 
                variant="contained" 
                startIcon={<SendIcon />}
                onClick={handleSendTemplateEmail}
                disabled={llmEmailLoading}
              >
                {llmEmailLoading ? 'Sending...' : 'Send Email'}
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>

      {/* Monitor Dialog */}
      <Dialog open={monitorDialog} onClose={() => setMonitorDialog(false)} maxWidth="lg" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <MonitorIcon color="success" />
              System Monitor & Tracking
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={autoRefresh}
                    onChange={(e) => setAutoRefresh(e.target.checked)}
                    size="small"
                  />
                }
                label="Auto Refresh"
              />
              <TextField
                size="small"
                type="number"
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
                inputProps={{ min: 5, max: 300 }}
                sx={{ width: 80 }}
                disabled={!autoRefresh}
              />
              <Typography variant="body2" color="text.secondary">sec</Typography>
              <Button
                size="small"
                onClick={handleRefreshMonitoring}
                startIcon={<VisibilityIcon />}
              >
                Refresh
              </Button>
              <IconButton onClick={() => setMonitorDialog(false)}>
                <CloseIcon />
              </IconButton>
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent>
          {/* Status Overview Cards */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <AssessmentIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                  <Typography variant="h6" color="primary">
                    {monitoringData.scanStatus.toUpperCase()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Scan Status
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <PerformanceIcon sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                  <Typography variant="h6" color="success.main">
                    {monitoringData.agentPerformance.activeAgents}/{monitoringData.agentPerformance.totalAgents}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active Agents
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <NotificationIcon sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
                  <Typography variant="h6" color="info.main">
                    {monitoringData.emailNotificationStatus.successful}/{monitoringData.emailNotificationStatus.totalSent}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Email Success Rate
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <CheckIcon sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
                  <Typography variant="h6" color="warning.main">
                    {monitoringData.agentPerformance.successRate}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Success Rate
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Activity Logs */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Activity Logs
              </Typography>
              <TableContainer component={Paper} sx={{ maxHeight: 300 }}>
                <Table stickyHeader size="small">
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
                      monitoringData.activityLogs.map((log) => (
                        <TableRow key={log.id}>
                          <TableCell>
                            <Typography variant="body2">
                              {new Date(log.timestamp).toLocaleString()}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={log.type}
                              size="small"
                              color={log.type === 'error' ? 'error' : log.type === 'scan' ? 'primary' : 'default'}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ maxWidth: 300 }}>
                              {log.message}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={log.status}
                              size="small"
                              color={log.status === 'success' ? 'success' : log.status === 'error' ? 'error' : 'warning'}
                            />
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
                          <Typography variant="body2" color="text.secondary">
                            No activity logs available
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>

          {/* Email Notification Status */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Email Notification Status
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Total Sent: <strong>{monitoringData.emailNotificationStatus.totalSent}</strong>
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Successful: <strong style={{ color: 'green' }}>{monitoringData.emailNotificationStatus.successful}</strong>
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Failed: <strong style={{ color: 'red' }}>{monitoringData.emailNotificationStatus.failed}</strong>
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Last Sent: <strong>{monitoringData.emailNotificationStatus.lastSent || 'Never'}</strong>
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  {monitoringData.emailNotificationStatus.failureReasons.length > 0 && (
                    <>
                      <Typography variant="body2" color="error" gutterBottom>
                        <strong>Failure Reasons:</strong>
                      </Typography>
                      {monitoringData.emailNotificationStatus.failureReasons.map((reason, index) => (
                        <Alert key={index} severity="error" sx={{ mb: 1 }}>
                          <Typography variant="body2">{reason}</Typography>
                          <Button
                            size="small"
                            startIcon={<AIIcon />}
                            onClick={() => handleAIAnalysis({ error: reason, type: 'email_failure' }, 'failure_reason')}
                            sx={{ mt: 1 }}
                          >
                            Get AI Recommendations
                          </Button>
                        </Alert>
                      ))}
                    </>
                  )}
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMonitorDialog(false)}>Close</Button>
          <Button
            variant="contained"
            startIcon={<VisibilityIcon />}
            onClick={handleRefreshMonitoring}
          >
            Refresh Data
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default ValidationPage