"""Validation Service for Comparing Security Reports
Provides functionality to compare CSV/Excel reports against reference data
and generate update lists with remediation details and email notifications.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import json
from pathlib import Path
import asyncio
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

@dataclass
class ResourceComparison:
    """Data class for resource comparison results"""
    resource_name: str
    resource_group: str
    subscription_id: str
    subscription_name: str
    owner_name: str
    tags: Dict[str, str]
    status: str  # 'new', 'updated', 'unchanged', 'removed'
    changes: List[str]
    remediation_details: str
    recommended_steps: List[str]
    severity: str
    compliance_status: str
    # Add source and reference values for comparison display
    source_values: Dict[str, str] = None
    reference_values: Dict[str, str] = None

@dataclass
class ValidationReport:
    """Data class for validation report results"""
    total_resources: int
    new_resources: int
    updated_resources: int
    unchanged_resources: int
    removed_resources: int
    comparisons: List[ResourceComparison]
    generated_at: datetime
    source_file: str
    reference_file: str

class ValidationService:
    """Service for validating and comparing security reports"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER', '')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        self.upload_dir = Path('uploads')
        self.upload_dir.mkdir(exist_ok=True)
        self.ai_service = AIService()
        
    def read_file(self, file_path: str) -> pd.DataFrame:
        """Read CSV or Excel file and return DataFrame"""
        try:
            # Handle relative paths by looking in the backend directory
            if not os.path.isabs(file_path):
                backend_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(backend_dir, file_path)
            
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
                
            # Standardize column names
            df.columns = df.columns.str.lower().str.replace(' ', '_')
            
            return df
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            raise
    
    def read_file_with_mapping(self, file_path: str, column_mapping: Dict[str, Dict[str, str]], file_type: str) -> pd.DataFrame:
        """Read entire file and apply enhanced column mapping with AS IS defaults and smart matching"""
        try:
            # Read the entire sheet first
            df = self.read_file(file_path)
            
            # Create a copy to preserve all original data
            full_df = df.copy()
            
            # Apply column mapping with enhanced logic
            if column_mapping:
                for field, mapping in column_mapping.items():
                    source_col = mapping.get('source', '')
                    reference_col = mapping.get('reference', '')
                    
                    if file_type == 'source' and source_col and source_col in df.columns:
                        # Keep original column and create mapped version for comparison
                        full_df[f'mapped_{field}'] = df[source_col]
                    elif file_type == 'reference':
                        if reference_col == 'AS_IS':
                            # AS IS: Use source column if it exists, otherwise try smart matching
                            if source_col and source_col in df.columns:
                                full_df[f'mapped_{field}'] = df[source_col]
                            else:
                                # Smart matching: find column with similar values
                                matched_col = self._find_matching_column(df, source_col, field)
                                if matched_col:
                                    full_df[f'mapped_{field}'] = df[matched_col]
                        elif reference_col and reference_col in df.columns:
                            # Use the mapped reference column, but handle empty values
                            ref_values = df[reference_col]
                            if source_col and source_col in df.columns:
                                source_values = df[source_col] if source_col in df.columns else None
                                # Use source values where reference is empty
                                full_df[f'mapped_{field}'] = ref_values.fillna(source_values) if source_values is not None else ref_values
                            else:
                                full_df[f'mapped_{field}'] = ref_values
            
            # Apply AS IS as default for unmapped columns when no explicit mapping provided
            if file_type == 'reference' and not column_mapping:
                # Default behavior: use AS IS for all common columns
                for col in df.columns:
                    if col in df.columns:
                        full_df[f'mapped_default_{col}'] = df[col]
            
            return full_df
            
        except Exception as e:
            logger.error(f"Error reading file with mapping {file_path}: {str(e)}")
            raise
    
    def _find_matching_column(self, df: pd.DataFrame, source_col: str, field_name: str) -> Optional[str]:
        """Find the best matching column in reference file based on content similarity"""
        if not source_col or source_col not in df.columns:
            return None
            
        # Try exact column name match first
        if source_col in df.columns:
            return source_col
            
        # Try fuzzy matching on column names
        best_match = None
        best_score = 0
        
        for col in df.columns:
            # Simple similarity scoring based on column name
            if source_col.lower() in col.lower() or col.lower() in source_col.lower():
                score = len(set(source_col.lower()) & set(col.lower())) / len(set(source_col.lower()) | set(col.lower()))
                if score > best_score and score > 0.5:  # Minimum 50% similarity
                    best_score = score
                    best_match = col
        
        return best_match
    
    def create_comparison_key(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create a comparison key from the first available columns"""
        # Use the first two columns as resource identifier if available
        columns = list(df.columns)
        if len(columns) >= 2:
            df['composite_key'] = df[columns[0]].astype(str) + '|' + df[columns[1]].astype(str)
        elif len(columns) >= 1:
            df['composite_key'] = df[columns[0]].astype(str)
        else:
            df['composite_key'] = df.index.astype(str)
        return df
    
    def normalize_resource_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize resource data for comparison"""
        # Expected columns mapping
        column_mapping = {
            'resource_name': ['resource_name', 'name', 'resource', 'vm_name'],
            'resource_group': ['resource_group', 'rg', 'resource_group_name'],
            'subscription_id': ['subscription_id', 'sub_id', 'subscription'],
            'subscription_name': ['subscription_name', 'sub_name'],
            'owner_name': ['owner_name', 'owner', 'contact', 'responsible_person'],
            'tags': ['tags', 'tag', 'labels'],
            'severity': ['severity', 'risk_level', 'priority'],
            'compliance_status': ['compliance_status', 'status', 'compliance']
        }
        
        normalized_df = pd.DataFrame()
        
        for standard_col, possible_cols in column_mapping.items():
            for col in possible_cols:
                if col in df.columns:
                    normalized_df[standard_col] = df[col]
                    break
            else:
                # Set default values if column not found
                if standard_col == 'tags':
                    normalized_df[standard_col] = '{}'
                elif standard_col == 'severity':
                    normalized_df[standard_col] = 'Medium'
                elif standard_col == 'compliance_status':
                    normalized_df[standard_col] = 'Non-Compliant'
                else:
                    normalized_df[standard_col] = 'Unknown'
        
        # Parse tags if they're in string format
        if 'tags' in normalized_df.columns:
            normalized_df['tags'] = normalized_df['tags'].apply(self._parse_tags)
        
        return normalized_df
    
    def _parse_tags(self, tags_str: str) -> Dict[str, str]:
        """Parse tags from string format to dictionary"""
        try:
            if pd.isna(tags_str) or tags_str == '':
                return {}
            
            if isinstance(tags_str, str):
                # Try to parse as JSON first
                try:
                    return json.loads(tags_str)
                except json.JSONDecodeError:
                    # Parse key=value pairs
                    tags = {}
                    for pair in tags_str.split(','):
                        if '=' in pair:
                            key, value = pair.split('=', 1)
                            tags[key.strip()] = value.strip()
                    return tags
            
            return {}
        except Exception:
            return {}
    
    def compare_resources(self, source_df: pd.DataFrame, reference_df: pd.DataFrame) -> List[ResourceComparison]:
        """Compare resources between source and reference data - entire sheet comparison"""
        comparisons = []
        
        # Create composite keys for matching - handle both normalized and direct mapping
        if 'resource_name' in source_df.columns and 'resource_group' in source_df.columns:
            source_df['composite_key'] = source_df['resource_name'] + '|' + source_df['resource_group']
            reference_df['composite_key'] = reference_df['resource_name'] + '|' + reference_df['resource_group']
        elif 'mapped_resource_name' in source_df.columns and 'mapped_resource_group' in source_df.columns:
            # Use mapped columns for key creation when available
            source_df['composite_key'] = source_df['mapped_resource_name'].astype(str) + '|' + source_df['mapped_resource_group'].astype(str)
            reference_df['composite_key'] = reference_df['mapped_resource_name'].astype(str) + '|' + reference_df['mapped_resource_group'].astype(str)
        else:
            # For direct column mapping, use the first available columns
            source_df = self.create_comparison_key(source_df)
            reference_df = self.create_comparison_key(reference_df)
        
        # Find new, updated, and unchanged resources
        source_keys = set(source_df['composite_key'])
        reference_keys = set(reference_df['composite_key'])
        
        # New resources (in source but not in reference)
        new_keys = source_keys - reference_keys
        # Removed resources (in reference but not in source)
        removed_keys = reference_keys - source_keys
        # Common resources (in both)
        common_keys = source_keys & reference_keys
        
        # Process new resources
        for key in new_keys:
            source_row = source_df[source_df['composite_key'] == key].iloc[0]
            
            # Update owner_name from reference if source has owner_name column selected
            updated_source_row = self._update_owner_from_reference(source_row, reference_df)
            
            comparison = self._create_resource_comparison(
                updated_source_row, None, 'new',
                ['New resource detected'],
                self._generate_remediation_details(updated_source_row, 'new')
            )
            comparisons.append(comparison)
        
        # Process removed resources
        for key in removed_keys:
            reference_row = reference_df[reference_df['composite_key'] == key].iloc[0]
            comparison = self._create_resource_comparison(
                reference_row, None, 'removed',
                ['Resource no longer exists'],
                self._generate_remediation_details(reference_row, 'removed')
            )
            comparisons.append(comparison)
        
        # Process common resources for changes
        for key in common_keys:
            source_row = source_df[source_df['composite_key'] == key].iloc[0]
            reference_row = reference_df[reference_df['composite_key'] == key].iloc[0]
            
            # Update owner_name from reference if source has owner_name column selected
            updated_source_row = self._update_owner_from_reference(source_row, reference_df)
            
            changes = self._detect_changes(updated_source_row, reference_row)
            status = 'updated' if changes else 'unchanged'
            
            comparison = self._create_resource_comparison(
                updated_source_row, reference_row, status, changes,
                self._generate_remediation_details(updated_source_row, status)
            )
            comparisons.append(comparison)
        
        return comparisons
    
    def _update_owner_from_reference(self, source_row: pd.Series, reference_df: pd.DataFrame) -> pd.Series:
        """Update owner_name from reference data using resource_group as primary lookup key"""
        updated_row = source_row.copy()
        
        # Check if source has owner_name column and if we should update it
        owner_columns = ['owner_name', 'mapped_owner_name', 'owner', 'contact', 'responsible_person']
        has_owner_column = any(col in source_row.index for col in owner_columns)
        
        if has_owner_column:
            # Get resource group for lookup - try multiple possible column names
            resource_group = None
            rg_columns = ['resource_group', 'mapped_resource_group', 'rg', 'resource_group_name']
            
            for rg_col in rg_columns:
                if rg_col in source_row.index and pd.notna(source_row[rg_col]):
                    resource_group = source_row[rg_col]
                    break
            
            if resource_group and pd.notna(resource_group):
                # Search reference data for matching resource group
                matching_refs = None
                
                for rg_col in rg_columns:
                    if rg_col in reference_df.columns:
                        matching_refs = reference_df[reference_df[rg_col] == resource_group]
                        if not matching_refs.empty:
                            break
                
                if matching_refs is not None and not matching_refs.empty:
                    # Get the first matching reference record
                    ref_row = matching_refs.iloc[0]
                    
                    # Update owner_name from reference - try multiple owner column names
                    ref_owner = None
                    for owner_col in owner_columns:
                        if owner_col in ref_row.index and pd.notna(ref_row[owner_col]):
                            ref_owner = ref_row[owner_col]
                            break
                    
                    if ref_owner:
                        # Update the appropriate owner field in source row
                        for owner_col in owner_columns:
                            if owner_col in updated_row.index:
                                updated_row[owner_col] = ref_owner
                                break
        
        return updated_row
    
    def _create_resource_comparison(self, source_row: pd.Series, reference_row: Optional[pd.Series], 
                                  status: str, changes: List[str], remediation: str) -> ResourceComparison:
        """Create ResourceComparison object from row data"""
        row = source_row if source_row is not None else reference_row
        
        # Handle both normalized and direct mapping data with mapped columns
        def get_field_value(row: pd.Series, field: str, default: str = 'Unknown') -> str:
            # First try the direct field name
            if field in row.index:
                return str(row[field]) if pd.notna(row[field]) else default
            # Then try the mapped version
            mapped_field = f'mapped_{field}'
            if mapped_field in row.index:
                return str(row[mapped_field]) if pd.notna(row[mapped_field]) else default
            # For direct mapping, try to get the first available column for basic fields
            if field == 'resource_name' and len(row.index) > 0:
                return str(row.iloc[0]) if pd.notna(row.iloc[0]) else default
            if field == 'resource_group' and len(row.index) > 1:
                return str(row.iloc[1]) if pd.notna(row.iloc[1]) else default
            return default
        
        # Handle missing fields with defaults
        
        # Parse tags if they're in string format
        tags_value = {}
        tags_field = get_field_value(row, 'tags', '')
        if tags_field and tags_field != 'Unknown':
            try:
                # Handle comma-separated key=value format
                if '=' in tags_field:
                    for tag_pair in tags_field.split(','):
                        if '=' in tag_pair:
                            key, value = tag_pair.split('=', 1)
                            tags_value[key.strip()] = value.strip()
                else:
                    tags_value = {'raw': tags_field}
            except Exception:
                tags_value = {'raw': tags_field}
        
        # Determine severity based on status if not provided
        severity = get_field_value(row, 'severity', self._determine_default_severity(status))
        
        # Determine compliance status if not provided
        compliance_status = get_field_value(row, 'compliance_status', self._determine_default_compliance(status))
        
        # Capture source and reference values for comparison display
        source_values = {}
        reference_values = {}
        
        if source_row is not None:
            for col in source_row.index:
                if not col.startswith('composite_key') and pd.notna(source_row[col]):
                    source_values[col] = str(source_row[col])
        
        if reference_row is not None:
            for col in reference_row.index:
                if not col.startswith('composite_key') and pd.notna(reference_row[col]):
                    reference_values[col] = str(reference_row[col])
        
        return ResourceComparison(
            resource_name=get_field_value(row, 'resource_name'),
            resource_group=get_field_value(row, 'resource_group'),
            subscription_id=get_field_value(row, 'subscription_id'),
            subscription_name=get_field_value(row, 'subscription_name'),
            owner_name=get_field_value(row, 'owner_name', get_field_value(row, 'owner')),  # Try 'owner' as fallback
            tags=tags_value,
            status=status,
            changes=changes,
            remediation_details=remediation,
            recommended_steps=self._generate_recommended_steps(row, status),
            severity=severity,
            compliance_status=compliance_status,
            source_values=source_values,
            reference_values=reference_values
        )
    
    def _detect_changes(self, source_row: pd.Series, reference_row: pd.Series) -> List[str]:
        """Detect changes between source and reference rows - compare entire row data"""
        changes = []
        
        # Compare all available columns from both source and reference
        all_columns = set(source_row.index) | set(reference_row.index)
        
        # Remove system-generated columns from comparison
        system_columns = {'composite_key'}
        # Also remove mapped_ columns as they're duplicates for comparison keys
        mapped_columns = {col for col in all_columns if col.startswith('mapped_')}
        comparison_columns = all_columns - system_columns - mapped_columns
        
        for field in comparison_columns:
            source_val = source_row.get(field, '') if field in source_row.index else ''
            reference_val = reference_row.get(field, '') if field in reference_row.index else ''
            
            # Handle NaN values
            source_val = str(source_val) if pd.notna(source_val) else ''
            reference_val = str(reference_val) if pd.notna(reference_val) else ''
            
            if source_val != reference_val:
                if reference_val == '' and source_val != '':
                    changes.append(f"{field} added: '{source_val}'")
                elif source_val == '' and reference_val != '':
                    changes.append(f"{field} removed: was '{reference_val}'")
                else:
                    changes.append(f"{field} changed from '{reference_val}' to '{source_val}'")
        
        return changes
    
    def _generate_remediation_details(self, row: pd.Series, status: str) -> str:
        """Generate remediation details based on resource status and policy using LLM"""
        resource_name = row.get('resource_name', 'Unknown Resource')
        severity = row.get('severity', self._determine_default_severity(status))
        compliance_status = row.get('compliance_status', self._determine_default_compliance(status))
        
        # Extract policy information
        policy_name = row.get('policy_name', row.get('policy_short_name', 'Unknown Policy'))
        resource_type = row.get('resource_type', 'Unknown Type')
        
        # Try to generate LLM-enhanced remediation details
        try:
            # Run async method in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                llm_details = loop.run_until_complete(self._generate_llm_remediation_details(
                    resource_name, policy_name, resource_type, status, severity, compliance_status
                ))
                return llm_details
            finally:
                loop.close()
        except Exception as e:
            logger.warning(f"Failed to generate LLM remediation details: {str(e)}")
            # Fallback to original logic
            if status == 'new':
                return f"New resource '{resource_name}' detected with {severity} severity. Requires immediate security assessment and compliance validation."
            elif status == 'removed':
                return f"Resource '{resource_name}' has been removed. Verify if removal was authorized and update documentation."
            elif status == 'updated':
                return f"Resource '{resource_name}' has been modified. Review changes for security implications and compliance impact."
            else:
                return f"Resource '{resource_name}' remains unchanged with {compliance_status} status."
    
    def _generate_recommended_steps(self, row: pd.Series, status: str) -> List[str]:
        """Generate recommended steps based on resource status, severity, and policy using LLM"""
        severity = row.get('severity', self._determine_default_severity(status))
        compliance_status = row.get('compliance_status', self._determine_default_compliance(status))
        resource_name = row.get('resource_name', 'Unknown Resource')
        policy_name = row.get('policy_name', row.get('policy_short_name', 'Unknown Policy'))
        resource_type = row.get('resource_type', 'Unknown Type')
        
        # Try to generate LLM-enhanced recommended steps
        try:
            # Run async method in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                llm_steps = loop.run_until_complete(self._generate_llm_recommended_steps(
                    resource_name, policy_name, resource_type, status, severity, compliance_status
                ))
                return llm_steps
            finally:
                loop.close()
        except Exception as e:
            logger.warning(f"Failed to generate LLM recommended steps: {str(e)}")
            # Fallback to original logic
            steps = []
            
            if status == 'new':
                steps.extend([
                    "Conduct security assessment of the new resource",
                    "Apply appropriate security policies and configurations",
                    "Update resource tags with owner and compliance information",
                    "Schedule regular compliance monitoring"
                ])
            elif status == 'removed':
                steps.extend([
                    "Verify authorization for resource removal",
                    "Update inventory and documentation",
                    "Check for any dependent resources or services",
                    "Archive relevant logs and configurations"
                ])
            elif status == 'updated':
                steps.extend([
                    "Review and validate the changes made",
                    "Assess security impact of modifications",
                    "Update compliance documentation if needed",
                    "Notify stakeholders of significant changes"
                ])
            
            # Add severity-specific steps
            if severity.lower() == 'high':
                steps.insert(0, "URGENT: Address high-severity issues immediately")
            elif severity.lower() == 'critical':
                steps.insert(0, "CRITICAL: Immediate action required - escalate to security team")
            
            return steps
    
    async def _generate_llm_remediation_details(
        self, 
        resource_name: str, 
        policy_name: str, 
        resource_type: str, 
        status: str, 
        severity: str, 
        compliance_status: str
    ) -> str:
        """Generate LLM-enhanced remediation details based on policy and resource context"""
        prompt = f"""
Generate detailed remediation guidance for a security finding with the following context:

Resource: {resource_name}
Policy: {policy_name}
Resource Type: {resource_type}
Status: {status}
Severity: {severity}
Compliance Status: {compliance_status}

Provide specific, actionable remediation details that:
1. Address the policy violation or security concern
2. Include technical steps for resolution
3. Consider the resource type and Azure best practices
4. Account for the severity level
5. Provide compliance guidance

Format the response as a clear, professional remediation description.
"""
        
        context = f"Policy-based remediation for {resource_type} resource"
        
        try:
            response = await self.ai_service.generate_response(
                prompt=prompt,
                context=context,
                max_tokens=600,
                temperature=0.3
            )
            return response.get('response', '').strip()
        except Exception as e:
            logger.error(f"LLM remediation details generation failed: {str(e)}")
            raise
    
    async def _generate_llm_recommended_steps(
        self, 
        resource_name: str, 
        policy_name: str, 
        resource_type: str, 
        status: str, 
        severity: str, 
        compliance_status: str
    ) -> List[str]:
        """Generate LLM-enhanced recommended steps based on policy and resource context"""
        prompt = f"""
Generate a prioritized list of recommended action steps for a security finding with the following context:

Resource: {resource_name}
Policy: {policy_name}
Resource Type: {resource_type}
Status: {status}
Severity: {severity}
Compliance Status: {compliance_status}

Provide 4-6 specific, actionable steps that:
1. Address the immediate security concern
2. Include technical implementation steps
3. Consider Azure best practices for {resource_type}
4. Account for the {severity} severity level
5. Include validation and monitoring steps

Format the response as a numbered list of clear, actionable steps. Each step should be concise but specific.
"""
        
        context = f"Policy-based action steps for {resource_type} resource"
        
        try:
            response = await self.ai_service.generate_response(
                prompt=prompt,
                context=context,
                max_tokens=500,
                temperature=0.3
            )
            
            # Parse the response into a list of steps
            response_text = response.get('response', '').strip()
            steps = []
            
            # Split by lines and clean up
            for line in response_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # Remove numbering and bullet points
                    clean_step = line.lstrip('0123456789.-• ').strip()
                    if clean_step:
                        steps.append(clean_step)
            
            # If parsing failed, return the whole response as a single step
            if not steps and response_text:
                steps = [response_text]
            
            return steps
        except Exception as e:
            logger.error(f"LLM recommended steps generation failed: {str(e)}")
            raise
    
    def _determine_default_severity(self, status: str) -> str:
        """Determine default severity based on resource status"""
        severity_map = {
            'new': 'medium',
            'updated': 'low',
            'removed': 'high',
            'unchanged': 'low'
        }
        return severity_map.get(status, 'medium')
    
    def _determine_default_compliance(self, status: str) -> str:
        """Determine default compliance status based on resource status"""
        compliance_map = {
            'new': 'pending_review',
            'updated': 'requires_validation',
            'removed': 'decommissioned',
            'unchanged': 'compliant'
        }
        return compliance_map.get(status, 'pending_review')
    
    def generate_validation_report(self, source_file: str, reference_file: str, column_mapping: Dict[str, Dict[str, str]] = None) -> ValidationReport:
        """Generate comprehensive validation report"""
        try:
            # Read and normalize data with optional column mapping
            if column_mapping:
                source_df = self.read_file_with_mapping(source_file, column_mapping, 'source')
                reference_df = self.read_file_with_mapping(reference_file, column_mapping, 'reference')
            else:
                source_df = self.normalize_resource_data(self.read_file(source_file))
                reference_df = self.normalize_resource_data(self.read_file(reference_file))
            
            # Compare resources
            comparisons = self.compare_resources(source_df, reference_df)
            
            # Calculate statistics
            total_resources = len(comparisons)
            new_resources = len([c for c in comparisons if c.status == 'new'])
            updated_resources = len([c for c in comparisons if c.status == 'updated'])
            unchanged_resources = len([c for c in comparisons if c.status == 'unchanged'])
            removed_resources = len([c for c in comparisons if c.status == 'removed'])
            
            return ValidationReport(
                total_resources=total_resources,
                new_resources=new_resources,
                updated_resources=updated_resources,
                unchanged_resources=unchanged_resources,
                removed_resources=removed_resources,
                comparisons=comparisons,
                generated_at=datetime.now(),
                source_file=source_file,
                reference_file=reference_file
            )
            
        except Exception as e:
            logger.error(f"Error generating validation report: {str(e)}")
            raise
    
    def export_validation_report(self, report: ValidationReport, output_format: str = 'excel') -> str:
        """Export validation report with output details only"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if output_format.lower() == 'excel':
                output_file = f"validation_report_{timestamp}.xlsx"
                
                # Create DataFrame from comparisons - output details only
                data = []
                for comp in report.comparisons:
                    data.append({
                        'Resource Name': comp.resource_name,
                        'Resource Group': comp.resource_group,
                        'Subscription ID': comp.subscription_id,
                        'Subscription Name': comp.subscription_name,
                        'Owner Name': comp.owner_name,
                        'Tags': json.dumps(comp.tags),
                        'Status': comp.status,
                        'Changes': '; '.join(comp.changes),
                        'Remediation Details': comp.remediation_details,
                        'Recommended Steps': '; '.join(comp.recommended_steps),
                        'Severity': comp.severity,
                        'Compliance Status': comp.compliance_status
                    })
                
                df = pd.DataFrame(data)
                
                with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                    # Only export detailed comparison - no summary or separate status sheets
                    df.to_excel(writer, sheet_name='Validation Results', index=False)
            
            else:  # CSV format - output details only
                output_file = f"validation_report_{timestamp}.csv"
                data = []
                for comp in report.comparisons:
                    data.append({
                        'Resource Name': comp.resource_name,
                        'Resource Group': comp.resource_group,
                        'Subscription ID': comp.subscription_id,
                        'Subscription Name': comp.subscription_name,
                        'Owner Name': comp.owner_name,
                        'Tags': json.dumps(comp.tags),
                        'Status': comp.status,
                        'Changes': '; '.join(comp.changes),
                        'Remediation Details': comp.remediation_details,
                        'Recommended Steps': '; '.join(comp.recommended_steps),
                        'Severity': comp.severity,
                        'Compliance Status': comp.compliance_status
                    })
                
                # Export only detailed results without summary
                pd.DataFrame(data).to_csv(output_file, index=False)
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error exporting validation report: {str(e)}")
            raise
    
    def send_email_notification(self, report: ValidationReport, recipients: List[str], 
                              report_file: Optional[str] = None) -> bool:
        """Send email notification with validation report"""
        try:
            if not self.email_user or not self.email_password:
                logger.warning("Email credentials not configured")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"Security Validation Report - {report.generated_at.strftime('%Y-%m-%d %H:%M')}"
            
            # Email body
            body = f"""
            Security Validation Report Summary
            
            Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
            Source File: {report.source_file}
            Reference File: {report.reference_file}
            
            Summary:
            - Total Resources: {report.total_resources}
            - New Resources: {report.new_resources}
            - Updated Resources: {report.updated_resources}
            - Unchanged Resources: {report.unchanged_resources}
            - Removed Resources: {report.removed_resources}
            
            Key Findings:
            """
            
            # Add high-priority items
            critical_items = [c for c in report.comparisons if c.severity.lower() == 'critical']
            high_items = [c for c in report.comparisons if c.severity.lower() == 'high']
            
            if critical_items:
                body += f"\n\nCRITICAL ITEMS ({len(critical_items)}):\n"
                for item in critical_items[:5]:  # Show first 5
                    body += f"- {item.resource_name} ({item.resource_group}): {item.remediation_details}\n"
            
            if high_items:
                body += f"\n\nHIGH PRIORITY ITEMS ({len(high_items)}):\n"
                for item in high_items[:5]:  # Show first 5
                    body += f"- {item.resource_name} ({item.resource_group}): {item.remediation_details}\n"
            
            body += "\n\nPlease review the attached detailed report for complete information.\n\nBest regards,\nSecurity Assessment System"
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach report file if provided
            if report_file and os.path.exists(report_file):
                with open(report_file, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(report_file)}'
                    )
                    msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email notification sent to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return False

# Global instance
validation_service = ValidationService()