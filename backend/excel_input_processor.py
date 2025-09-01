import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComparisonStatus(Enum):
    MATCHED = "matched"
    MISSING_IN_SOURCE = "missing_in_source"
    MISSING_IN_REFERENCE = "missing_in_reference"
    OWNER_MISMATCH = "owner_mismatch"
    METADATA_MISMATCH = "metadata_mismatch"

@dataclass
class ResourceRecord:
    """Represents a resource record from Excel/CSV input"""
    resource_name: str
    resource_group: str
    subscription_id: str
    subscription_name: str
    owner_name: str
    resource_tags: str
    region: str
    resource_type: str
    comparison_status: Optional[ComparisonStatus] = None
    policy_short_name: Optional[str] = None
    security_findings: Optional[List[str]] = None
    remediation_required: bool = False
    
@dataclass
class ComparisonResult:
    """Represents the result of comparing two datasets"""
    matched_resources: List[ResourceRecord]
    missing_in_source: List[ResourceRecord]
    missing_in_reference: List[ResourceRecord]
    owner_mismatches: List[Tuple[ResourceRecord, ResourceRecord]]  # (source, reference)
    metadata_mismatches: List[Tuple[ResourceRecord, ResourceRecord]]
    total_resources: int
    comparison_timestamp: datetime

class ExcelInputProcessor:
    """Processes Excel/CSV files from compare analysis for email generation"""
    
    def __init__(self):
        self.supported_formats = ['.xlsx', '.xls', '.csv']
        
    def process_compare_analysis_file(self, file_path: str) -> ComparisonResult:
        """
        Process compare analysis Excel/CSV file and return structured comparison results
        
        Args:
            file_path: Path to the Excel/CSV file containing compare analysis results
            
        Returns:
            ComparisonResult object with categorized resources
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
                
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in self.supported_formats:
                raise ValueError(f"Unsupported file format: {file_ext}")
                
            # Read the file
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
                
            logger.info(f"Processing file: {file_path} with {len(df)} records")
            
            # Normalize column names
            df = self._normalize_column_names(df)
            
            # Validate required columns
            self._validate_required_columns(df)
            
            # Convert DataFrame to ResourceRecord objects
            resources = self._convert_to_resource_records(df)
            
            # Perform comparison analysis if comparison status is available
            comparison_result = self._analyze_comparison_results(resources)
            
            logger.info(f"Processed {len(resources)} resources successfully")
            return comparison_result
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            raise
    
    def process_dual_file_comparison(self, source_file: str, reference_file: str) -> ComparisonResult:
        """
        Process two separate files (source and reference) and perform comparison
        
        Args:
            source_file: Path to source data file
            reference_file: Path to reference data file
            
        Returns:
            ComparisonResult object with comparison analysis
        """
        try:
            # Process both files
            source_df = self._read_file(source_file)
            reference_df = self._read_file(reference_file)
            
            # Normalize column names
            source_df = self._normalize_column_names(source_df)
            reference_df = self._normalize_column_names(reference_df)
            
            # Validate columns
            self._validate_required_columns(source_df)
            self._validate_required_columns(reference_df)
            
            # Convert to resource records
            source_resources = self._convert_to_resource_records(source_df)
            reference_resources = self._convert_to_resource_records(reference_df)
            
            # Perform comparison
            comparison_result = self._compare_resource_sets(source_resources, reference_resources)
            
            logger.info(f"Compared {len(source_resources)} source resources with {len(reference_resources)} reference resources")
            return comparison_result
            
        except Exception as e:
            logger.error(f"Error comparing files {source_file} and {reference_file}: {str(e)}")
            raise
    
    def _read_file(self, file_path: str) -> pd.DataFrame:
        """Read file based on extension"""
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == '.csv':
            return pd.read_csv(file_path)
        else:
            return pd.read_excel(file_path)
    
    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize column names to standard format
        """
        column_mapping = {
            'resource_name': 'resource_name',
            'resourcename': 'resource_name',
            'name': 'resource_name',
            'resource_group': 'resource_group',
            'resourcegroup': 'resource_group',
            'rg': 'resource_group',
            'subscription_id': 'subscription_id',
            'subscriptionid': 'subscription_id',
            'sub_id': 'subscription_id',
            'subscription_name': 'subscription_name',
            'subscriptionname': 'subscription_name',
            'sub_name': 'subscription_name',
            'owner_name': 'owner_name',
            'ownername': 'owner_name',
            'owner': 'owner_name',
            'resource_tags': 'resource_tags',
            'resourcetags': 'resource_tags',
            'tags': 'resource_tags',
            'region': 'region',
            'location': 'region',
            'resource_type': 'resource_type',
            'resourcetype': 'resource_type',
            'type': 'resource_type',
            'comparison_status': 'comparison_status',
            'status': 'comparison_status',
            'policy_short_name': 'policy_short_name',
            'policy': 'policy_short_name',
            'security_findings': 'security_findings',
            'findings': 'security_findings',
            'remediation_required': 'remediation_required'
        }
        
        # Create a copy and normalize column names
        df_normalized = df.copy()
        df_normalized.columns = [col.lower().replace(' ', '_') for col in df_normalized.columns]
        
        # Apply column mapping
        df_normalized = df_normalized.rename(columns=column_mapping)
        
        return df_normalized
    
    def _validate_required_columns(self, df: pd.DataFrame) -> None:
        """
        Validate that required columns are present
        """
        required_columns = [
            'resource_name', 'resource_group', 'subscription_id', 
            'subscription_name', 'owner_name', 'region', 'resource_type'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
    
    def _convert_to_resource_records(self, df: pd.DataFrame) -> List[ResourceRecord]:
        """
        Convert DataFrame to list of ResourceRecord objects
        """
        resources = []
        
        for _, row in df.iterrows():
            # Handle security findings if present
            security_findings = None
            if 'security_findings' in df.columns and pd.notna(row.get('security_findings')):
                findings_str = str(row['security_findings'])
                security_findings = [f.strip() for f in findings_str.split(',') if f.strip()]
            
            # Handle comparison status if present
            comparison_status = None
            if 'comparison_status' in df.columns and pd.notna(row.get('comparison_status')):
                try:
                    comparison_status = ComparisonStatus(row['comparison_status'].lower())
                except ValueError:
                    logger.warning(f"Unknown comparison status: {row['comparison_status']}")
            
            resource = ResourceRecord(
                resource_name=str(row['resource_name']),
                resource_group=str(row['resource_group']),
                subscription_id=str(row['subscription_id']),
                subscription_name=str(row['subscription_name']),
                owner_name=str(row['owner_name']),
                resource_tags=str(row.get('resource_tags', '')),
                region=str(row['region']),
                resource_type=str(row['resource_type']),
                comparison_status=comparison_status,
                policy_short_name=str(row.get('policy_short_name', '')) if pd.notna(row.get('policy_short_name')) else None,
                security_findings=security_findings,
                remediation_required=bool(row.get('remediation_required', False))
            )
            resources.append(resource)
        
        return resources
    
    def _analyze_comparison_results(self, resources: List[ResourceRecord]) -> ComparisonResult:
        """
        Analyze resources and categorize them based on comparison status
        """
        matched = []
        missing_in_source = []
        missing_in_reference = []
        owner_mismatches = []
        metadata_mismatches = []
        
        for resource in resources:
            if resource.comparison_status == ComparisonStatus.MATCHED:
                matched.append(resource)
            elif resource.comparison_status == ComparisonStatus.MISSING_IN_SOURCE:
                missing_in_source.append(resource)
            elif resource.comparison_status == ComparisonStatus.MISSING_IN_REFERENCE:
                missing_in_reference.append(resource)
            elif resource.comparison_status == ComparisonStatus.OWNER_MISMATCH:
                # For single file analysis, we can't provide both versions
                owner_mismatches.append((resource, resource))
            elif resource.comparison_status == ComparisonStatus.METADATA_MISMATCH:
                metadata_mismatches.append((resource, resource))
            else:
                # If no comparison status, treat as matched
                matched.append(resource)
        
        return ComparisonResult(
            matched_resources=matched,
            missing_in_source=missing_in_source,
            missing_in_reference=missing_in_reference,
            owner_mismatches=owner_mismatches,
            metadata_mismatches=metadata_mismatches,
            total_resources=len(resources),
            comparison_timestamp=datetime.now()
        )
    
    def _compare_resource_sets(self, source_resources: List[ResourceRecord], 
                              reference_resources: List[ResourceRecord]) -> ComparisonResult:
        """
        Compare two sets of resources and categorize differences
        """
        # Create lookup dictionaries
        source_lookup = {(r.resource_name, r.resource_group): r for r in source_resources}
        reference_lookup = {(r.resource_name, r.resource_group): r for r in reference_resources}
        
        matched = []
        missing_in_source = []
        missing_in_reference = []
        owner_mismatches = []
        metadata_mismatches = []
        
        # Find matches and mismatches
        for key, source_resource in source_lookup.items():
            if key in reference_lookup:
                reference_resource = reference_lookup[key]
                
                # Check for owner mismatch
                if source_resource.owner_name != reference_resource.owner_name:
                    source_resource.comparison_status = ComparisonStatus.OWNER_MISMATCH
                    reference_resource.comparison_status = ComparisonStatus.OWNER_MISMATCH
                    owner_mismatches.append((source_resource, reference_resource))
                # Check for metadata mismatch
                elif (source_resource.resource_tags != reference_resource.resource_tags or
                      source_resource.region != reference_resource.region or
                      source_resource.resource_type != reference_resource.resource_type):
                    source_resource.comparison_status = ComparisonStatus.METADATA_MISMATCH
                    reference_resource.comparison_status = ComparisonStatus.METADATA_MISMATCH
                    metadata_mismatches.append((source_resource, reference_resource))
                else:
                    # Perfect match
                    source_resource.comparison_status = ComparisonStatus.MATCHED
                    reference_resource.comparison_status = ComparisonStatus.MATCHED
                    matched.append(source_resource)
            else:
                # Missing in reference
                source_resource.comparison_status = ComparisonStatus.MISSING_IN_REFERENCE
                missing_in_reference.append(source_resource)
        
        # Find resources missing in source
        for key, reference_resource in reference_lookup.items():
            if key not in source_lookup:
                reference_resource.comparison_status = ComparisonStatus.MISSING_IN_SOURCE
                missing_in_source.append(reference_resource)
        
        return ComparisonResult(
            matched_resources=matched,
            missing_in_source=missing_in_source,
            missing_in_reference=missing_in_reference,
            owner_mismatches=owner_mismatches,
            metadata_mismatches=metadata_mismatches,
            total_resources=len(source_resources) + len(reference_resources),
            comparison_timestamp=datetime.now()
        )
    
    def generate_email_input_data(self, comparison_result: ComparisonResult) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate structured data for email generation based on comparison results
        
        Returns:
            Dictionary with email categories and their respective data
        """
        email_data = {
            'wrong_owner': [],
            'reminder': [],
            'exception_policy': [],
            'general_notification': []
        }
        
        # Process owner mismatches for wrong owner emails
        for source_resource, reference_resource in comparison_result.owner_mismatches:
            email_data['wrong_owner'].append({
                'resource_name': source_resource.resource_name,
                'resource_group': source_resource.resource_group,
                'current_owner': source_resource.owner_name,
                'expected_owner': reference_resource.owner_name,
                'subscription_name': source_resource.subscription_name,
                'resource_type': source_resource.resource_type,
                'region': source_resource.region
            })
        
        # Process resources needing reminders
        reminder_resources = (
            comparison_result.missing_in_source + 
            comparison_result.missing_in_reference +
            [r for r, _ in comparison_result.metadata_mismatches]
        )
        
        for resource in reminder_resources:
            if resource.security_findings or resource.remediation_required:
                email_data['reminder'].append({
                    'resource_name': resource.resource_name,
                    'resource_group': resource.resource_group,
                    'owner_name': resource.owner_name,
                    'policy_short_name': resource.policy_short_name,
                    'security_findings': resource.security_findings,
                    'remediation_required': resource.remediation_required,
                    'subscription_name': resource.subscription_name,
                    'resource_type': resource.resource_type
                })
        
        # Process matched resources for general notifications
        for resource in comparison_result.matched_resources:
            if resource.security_findings:
                email_data['general_notification'].append({
                    'resource_name': resource.resource_name,
                    'resource_group': resource.resource_group,
                    'owner_name': resource.owner_name,
                    'security_findings': resource.security_findings,
                    'subscription_name': resource.subscription_name
                })
        
        return email_data
    
    def export_comparison_summary(self, comparison_result: ComparisonResult, output_path: str) -> None:
        """
        Export comparison summary to Excel file
        """
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = {
                    'Category': ['Matched Resources', 'Missing in Source', 'Missing in Reference', 
                               'Owner Mismatches', 'Metadata Mismatches', 'Total Resources'],
                    'Count': [len(comparison_result.matched_resources),
                             len(comparison_result.missing_in_source),
                             len(comparison_result.missing_in_reference),
                             len(comparison_result.owner_mismatches),
                             len(comparison_result.metadata_mismatches),
                             comparison_result.total_resources]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                
                # Detailed sheets for each category
                if comparison_result.owner_mismatches:
                    mismatch_data = []
                    for source, reference in comparison_result.owner_mismatches:
                        mismatch_data.append({
                            'Resource Name': source.resource_name,
                            'Resource Group': source.resource_group,
                            'Source Owner': source.owner_name,
                            'Reference Owner': reference.owner_name,
                            'Subscription': source.subscription_name
                        })
                    pd.DataFrame(mismatch_data).to_excel(writer, sheet_name='Owner Mismatches', index=False)
                
            logger.info(f"Comparison summary exported to: {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting summary: {str(e)}")
            raise

# Example usage and testing
if __name__ == "__main__":
    processor = ExcelInputProcessor()
    
    # Test with sample CSV files
    try:
        result = processor.process_dual_file_comparison(
            "sample_source.csv",
            "sample_reference.csv"
        )
        
        print(f"Comparison completed:")
        print(f"- Matched: {len(result.matched_resources)}")
        print(f"- Missing in source: {len(result.missing_in_source)}")
        print(f"- Missing in reference: {len(result.missing_in_reference)}")
        print(f"- Owner mismatches: {len(result.owner_mismatches)}")
        print(f"- Metadata mismatches: {len(result.metadata_mismatches)}")
        
        # Generate email input data
        email_data = processor.generate_email_input_data(result)
        print(f"\nEmail categories generated:")
        for category, items in email_data.items():
            print(f"- {category}: {len(items)} items")
            
    except Exception as e:
        print(f"Error: {e}")