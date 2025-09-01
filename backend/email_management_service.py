"""Enhanced Email Management Service with LLM Integration
Provides comprehensive email management with bucket categorization,
Excel input processing, and intelligent response handling.
"""

import asyncio
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import os
import re
from pathlib import Path
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import imaplib
import email
from email.header import decode_header

# Import existing services
from llm_email_service import LLMEmailService, EmailTemplate
from app.services.ai_service import AIService
from validation_service import ResourceComparison
from excel_input_processor import ExcelInputProcessor, ComparisonResult, ResourceRecord

logger = logging.getLogger(__name__)

class EmailBucket(Enum):
    """Email categorization buckets"""
    WRONG_OWNER = "wrong_owner"
    REMINDER = "reminder"
    EXCEPTION_APPROVAL = "exception_approval"
    REPLIED_RESPONSE = "replied_response"
    PENDING_REVIEW = "pending_review"
    RESOLVED = "resolved"

class EmailStatus(Enum):
    """Email processing status"""
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    REPLIED = "replied"
    BOUNCED = "bounced"
    FAILED = "failed"

@dataclass
class EmailRecord:
    """Email record with tracking information"""
    id: str
    resource_name: str
    policy_short_name: str
    owner_email: str
    owner_name: str
    resource_group: str
    subscription_id: str
    severity: str
    bucket: EmailBucket
    status: EmailStatus
    sent_at: Optional[datetime] = None
    last_reminder_at: Optional[datetime] = None
    reminder_count: int = 0
    response_received_at: Optional[datetime] = None
    response_content: Optional[str] = None
    llm_analysis: Optional[Dict[str, Any]] = None
    exception_reason: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

@dataclass
class ExcelInputData:
    """Data structure for Excel input processing"""
    policy_short_name: str
    resource_name: str
    resource_group: str
    owner_name: str
    owner_email: str
    subscription_id: str
    severity: str
    compliance_status: str
    last_scan_date: str
    remediation_details: Optional[str] = None
    tags: Optional[Dict[str, str]] = None
    resource_type: Optional[str] = None
    region: Optional[str] = None
    comparison_status: Optional[str] = None

class EmailManagementService:
    """Enhanced Email Management Service with LLM Integration"""
    
    def __init__(self):
        self.llm_email_service = LLMEmailService()
        self.ai_service = AIService()
        self.excel_processor = ExcelInputProcessor()
        self.db_path = "email_management.db"
        self._init_database()
        
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
        self.imap_port = int(os.getenv('IMAP_PORT', '993'))
        self.email_user = os.getenv('EMAIL_USER', '')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        
        # Reminder configuration
        self.reminder_intervals = [3, 7, 14, 30]  # Days
        self.max_reminders = 4
    
    def _init_database(self):
        """Initialize SQLite database for email tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_records (
                id TEXT PRIMARY KEY,
                resource_name TEXT NOT NULL,
                policy_short_name TEXT NOT NULL,
                owner_email TEXT NOT NULL,
                owner_name TEXT NOT NULL,
                resource_group TEXT NOT NULL,
                subscription_id TEXT NOT NULL,
                severity TEXT NOT NULL,
                bucket TEXT NOT NULL,
                status TEXT NOT NULL,
                sent_at TEXT,
                last_reminder_at TEXT,
                reminder_count INTEGER DEFAULT 0,
                response_received_at TEXT,
                response_content TEXT,
                llm_analysis TEXT,
                exception_reason TEXT,
                resolved_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_responses (
                id TEXT PRIMARY KEY,
                email_record_id TEXT NOT NULL,
                sender_email TEXT NOT NULL,
                subject TEXT,
                content TEXT NOT NULL,
                received_at TEXT NOT NULL,
                llm_analysis TEXT,
                bucket_classification TEXT,
                processed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (email_record_id) REFERENCES email_records (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def process_excel_input(self, excel_file_path: str) -> Dict[str, Any]:
        """Process Excel file input and generate email records"""
        try:
            # Read Excel file
            df = pd.read_excel(excel_file_path)
            
            # Validate required columns
            required_columns = [
                'policy_short_name', 'resource_name', 'resource_group',
                'owner_name', 'owner_email', 'subscription_id', 'severity'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            processed_records = []
            failed_records = []
            
            for index, row in df.iterrows():
                try:
                    # Create ExcelInputData object
                    input_data = ExcelInputData(
                        policy_short_name=str(row['policy_short_name']),
                        resource_name=str(row['resource_name']),
                        resource_group=str(row['resource_group']),
                        owner_name=str(row['owner_name']),
                        owner_email=str(row['owner_email']),
                        subscription_id=str(row['subscription_id']),
                        severity=str(row['severity']),
                        compliance_status=str(row.get('compliance_status', 'Non-Compliant')),
                        last_scan_date=str(row.get('last_scan_date', datetime.utcnow().isoformat())),
                        remediation_details=str(row.get('remediation_details', '')) if pd.notna(row.get('remediation_details')) else None,
                        tags=json.loads(str(row.get('tags', '{}'))) if pd.notna(row.get('tags')) else None,
                        resource_type=str(row.get('resource_type', '')) if pd.notna(row.get('resource_type')) else None,
                        region=str(row.get('region', '')) if pd.notna(row.get('region')) else None,
                        comparison_status=str(row.get('comparison_status', '')) if pd.notna(row.get('comparison_status')) else None
                    )
                    
                    # Create email record
                    email_record = await self._create_email_record_from_excel(input_data)
                    processed_records.append(email_record)
                    
                except Exception as e:
                    logger.error(f"Error processing row {index}: {str(e)}")
                    failed_records.append({
                        'row_index': index,
                        'error': str(e),
                        'data': row.to_dict()
                    })
            
            return {
                'success': True,
                'processed_count': len(processed_records),
                'failed_count': len(failed_records),
                'processed_records': [asdict(record) for record in processed_records],
                'failed_records': failed_records
            }
            
        except Exception as e:
            logger.error(f"Error processing Excel file: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processed_count': 0,
                'failed_count': 0
            }
    
    async def process_excel_file_with_processor(self, file_path: str) -> Dict[str, Any]:
        """Process Excel/CSV file using Excel processor and generate email records"""
        try:
            # Process the file using Excel processor
            comparison_result = self.excel_processor.process_compare_analysis_file(file_path)
            
            # Generate email input data
            email_data = self.excel_processor.generate_email_input_data(comparison_result)
            
            email_ids_by_bucket = {
                EmailBucket.WRONG_OWNER.value: [],
                EmailBucket.REMINDER.value: [],
                EmailBucket.EXCEPTION_APPROVAL.value: [],
                EmailBucket.REPLIED_RESPONSE.value: []
            }
            
            processed_records = []
            
            # Process wrong owner emails
            for item in email_data.get('wrong_owner', []):
                email_record = await self._create_email_record_from_dict(item, EmailBucket.WRONG_OWNER)
                await self._save_email_record(email_record)
                email_ids_by_bucket[EmailBucket.WRONG_OWNER.value].append(email_record.id)
                processed_records.append(email_record)
            
            # Process reminder emails
            for item in email_data.get('reminder', []):
                email_record = await self._create_email_record_from_dict(item, EmailBucket.REMINDER)
                await self._save_email_record(email_record)
                email_ids_by_bucket[EmailBucket.REMINDER.value].append(email_record.id)
                processed_records.append(email_record)
            
            # Process general notifications
            for item in email_data.get('general_notification', []):
                email_record = await self._create_email_record_from_dict(item, EmailBucket.PENDING_REVIEW)
                await self._save_email_record(email_record)
                email_ids_by_bucket[EmailBucket.REPLIED_RESPONSE.value].append(email_record.id)
                processed_records.append(email_record)
            
            logger.info(f"Processed Excel file {file_path} and created {len(processed_records)} email records")
            
            return {
                'success': True,
                'processed_count': len(processed_records),
                'failed_count': 0,
                'email_ids_by_bucket': email_ids_by_bucket,
                'processed_records': [asdict(record) for record in processed_records]
            }
            
        except Exception as e:
            logger.error(f"Error processing Excel file {file_path}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processed_count': 0,
                'failed_count': 0
            }
    
    async def process_dual_file_comparison(self, source_file: str, reference_file: str) -> Dict[str, Any]:
        """Process two files for comparison and generate email records"""
        try:
            # Process comparison
            comparison_result = self.excel_processor.process_dual_file_comparison(source_file, reference_file)
            
            # Generate email input data
            email_data = self.excel_processor.generate_email_input_data(comparison_result)
            
            return await self._process_email_data_dict(email_data)
            
        except Exception as e:
            logger.error(f"Error processing dual file comparison: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processed_count': 0,
                'failed_count': 0
            }
    
    async def _create_email_record_from_excel(self, input_data: ExcelInputData) -> EmailRecord:
        """Create email record from Excel input data"""
        record_id = f"email_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(input_data.resource_name) % 10000}"
        
        email_record = EmailRecord(
            id=record_id,
            resource_name=input_data.resource_name,
            policy_short_name=input_data.policy_short_name,
            owner_email=input_data.owner_email,
            owner_name=input_data.owner_name,
            resource_group=input_data.resource_group,
            subscription_id=input_data.subscription_id,
            severity=input_data.severity,
            bucket=EmailBucket.PENDING_REVIEW,
            status=EmailStatus.SENT
        )
        
        # Save to database
        await self._save_email_record(email_record)
        
        return email_record
    
    async def _create_email_record_from_dict(self, data_dict: Dict[str, Any], bucket: EmailBucket) -> EmailRecord:
        """Create email record from dictionary data"""
        record_id = f"email_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(data_dict.get('resource_name', '')) % 10000}"
        
        email_record = EmailRecord(
            id=record_id,
            resource_name=data_dict.get('resource_name', ''),
            policy_short_name=data_dict.get('policy_short_name', ''),
            owner_email=data_dict.get('owner_email', ''),
            owner_name=data_dict.get('owner_name', ''),
            resource_group=data_dict.get('resource_group', ''),
            subscription_id=data_dict.get('subscription_id', ''),
            severity=data_dict.get('severity', 'medium'),
            bucket=bucket,
            status=EmailStatus.SENT
        )
        
        return email_record
    
    async def _process_email_data_dict(self, email_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Process email data dictionary and create records"""
        email_ids_by_bucket = {
            EmailBucket.WRONG_OWNER.value: [],
            EmailBucket.REMINDER.value: [],
            EmailBucket.EXCEPTION_APPROVAL.value: [],
            EmailBucket.REPLIED_RESPONSE.value: []
        }
        
        processed_records = []
        
        # Process each category
        for category, items in email_data.items():
            if category == 'wrong_owner':
                bucket = EmailBucket.WRONG_OWNER
            elif category == 'reminder':
                bucket = EmailBucket.REMINDER
            elif category == 'exception_approval':
                bucket = EmailBucket.EXCEPTION_APPROVAL
            else:
                bucket = EmailBucket.PENDING_REVIEW
            
            for item in items:
                email_record = await self._create_email_record_from_dict(item, bucket)
                await self._save_email_record(email_record)
                email_ids_by_bucket[bucket.value].append(email_record.id)
                processed_records.append(email_record)
        
        return {
            'success': True,
            'processed_count': len(processed_records),
            'failed_count': 0,
            'email_ids_by_bucket': email_ids_by_bucket,
            'processed_records': [asdict(record) for record in processed_records]
        }
    
    async def _save_email_record(self, record: EmailRecord):
        """Save email record to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO email_records (
                id, resource_name, policy_short_name, owner_email, owner_name,
                resource_group, subscription_id, severity, bucket, status,
                sent_at, last_reminder_at, reminder_count, response_received_at,
                response_content, llm_analysis, exception_reason, resolved_at,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record.id, record.resource_name, record.policy_short_name,
            record.owner_email, record.owner_name, record.resource_group,
            record.subscription_id, record.severity, record.bucket.value,
            record.status.value, 
            record.sent_at.isoformat() if record.sent_at else None,
            record.last_reminder_at.isoformat() if record.last_reminder_at else None,
            record.reminder_count,
            record.response_received_at.isoformat() if record.response_received_at else None,
            record.response_content,
            json.dumps(record.llm_analysis) if record.llm_analysis else None,
            record.exception_reason,
            record.resolved_at.isoformat() if record.resolved_at else None,
            record.created_at.isoformat(),
            record.updated_at.isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    async def analyze_email_response(self, email_content: str, sender_email: str, subject: str) -> Dict[str, Any]:
        """Analyze email response using LLM to determine bucket classification"""
        try:
            # Prepare context for LLM analysis
            analysis_prompt = f"""
            Analyze the following email response to a security notification and classify it into one of these categories:
            
            1. WRONG_OWNER: The recipient indicates they are not the right owner/responsible person
            2. EXCEPTION_APPROVAL: The recipient requests an exception or indicates no action needed
            3. REPLIED_RESPONSE: The recipient acknowledges and provides a substantive response
            4. REMINDER: This is a follow-up that needs reminder classification
            
            Email Details:
            From: {sender_email}
            Subject: {subject}
            Content: {email_content}
            
            Provide your analysis in JSON format:
            {{
                "classification": "WRONG_OWNER|EXCEPTION_APPROVAL|REPLIED_RESPONSE|REMINDER",
                "confidence": 0.0-1.0,
                "reasoning": "Explanation of classification",
                "key_phrases": ["list of key phrases that influenced decision"],
                "suggested_action": "Recommended next action",
                "owner_transfer_info": "If wrong owner, extract any mentioned correct owner info",
                "exception_justification": "If exception, extract the justification provided"
            }}
            """
            
            # Use AI service to analyze the email
            ai_response = await self.ai_service.generate_response(
                prompt=analysis_prompt,
                context="email_analysis",
                max_tokens=1000
            )
            
            # Parse the AI response
            try:
                analysis_result = json.loads(ai_response.get('response', '{}'))
            except json.JSONDecodeError:
                # Fallback analysis
                analysis_result = self._fallback_email_analysis(email_content, sender_email)
            
            return {
                'success': True,
                'analysis': analysis_result,
                'ai_provider': ai_response.get('provider'),
                'tokens_used': ai_response.get('tokens_used', 0)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing email response: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'analysis': self._fallback_email_analysis(email_content, sender_email)
            }
    
    def _fallback_email_analysis(self, email_content: str, sender_email: str) -> Dict[str, Any]:
        """Fallback email analysis using keyword matching"""
        content_lower = email_content.lower()
        
        # Define keyword patterns
        wrong_owner_keywords = [
            'not responsible', 'wrong person', 'not my resource', 'not the owner',
            'contact', 'forward to', 'not mine', 'different team', 'transferred'
        ]
        
        exception_keywords = [
            'exception', 'waiver', 'approved risk', 'business requirement',
            'no action needed', 'acceptable risk', 'compensating control'
        ]
        
        acknowledgment_keywords = [
            'will fix', 'working on', 'scheduled', 'in progress', 'thank you',
            'acknowledged', 'will address', 'remediation planned'
        ]
        
        # Classify based on keywords
        if any(keyword in content_lower for keyword in wrong_owner_keywords):
            classification = "WRONG_OWNER"
            confidence = 0.7
        elif any(keyword in content_lower for keyword in exception_keywords):
            classification = "EXCEPTION_APPROVAL"
            confidence = 0.7
        elif any(keyword in content_lower for keyword in acknowledgment_keywords):
            classification = "REPLIED_RESPONSE"
            confidence = 0.6
        else:
            classification = "REPLIED_RESPONSE"
            confidence = 0.4
        
        return {
            'classification': classification,
            'confidence': confidence,
            'reasoning': f'Keyword-based classification using fallback analysis',
            'key_phrases': [],
            'suggested_action': 'Manual review recommended',
            'owner_transfer_info': None,
            'exception_justification': None
        }
    
    async def process_email_responses(self) -> Dict[str, Any]:
        """Process incoming email responses and update buckets"""
        try:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_user, self.email_password)
            mail.select('inbox')
            
            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')
            email_ids = messages[0].split()
            
            processed_responses = []
            
            for email_id in email_ids:
                try:
                    # Fetch email
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Extract email details
                    subject = decode_header(email_message['Subject'])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    
                    sender = email_message['From']
                    
                    # Extract email content
                    content = self._extract_email_content(email_message)
                    
                    # Analyze the response
                    analysis_result = await self.analyze_email_response(content, sender, subject)
                    
                    # Find matching email record
                    email_record = await self._find_email_record_by_sender(sender)
                    
                    if email_record:
                        # Update email record based on analysis
                        await self._update_email_record_from_response(
                            email_record, analysis_result, content
                        )
                        processed_responses.append({
                            'email_id': email_id.decode(),
                            'sender': sender,
                            'subject': subject,
                            'analysis': analysis_result,
                            'record_updated': True
                        })
                    else:
                        processed_responses.append({
                            'email_id': email_id.decode(),
                            'sender': sender,
                            'subject': subject,
                            'analysis': analysis_result,
                            'record_updated': False,
                            'note': 'No matching email record found'
                        })
                    
                    # Mark email as read
                    mail.store(email_id, '+FLAGS', '\\Seen')
                    
                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {str(e)}")
                    continue
            
            mail.close()
            mail.logout()
            
            return {
                'success': True,
                'processed_count': len(processed_responses),
                'responses': processed_responses
            }
            
        except Exception as e:
            logger.error(f"Error processing email responses: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processed_count': 0
            }
    
    def _extract_email_content(self, email_message) -> str:
        """Extract text content from email message"""
        content = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    content += part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            content = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        return content
    
    async def _find_email_record_by_sender(self, sender_email: str) -> Optional[EmailRecord]:
        """Find email record by sender email address"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM email_records WHERE owner_email = ? ORDER BY created_at DESC LIMIT 1',
            (sender_email,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_email_record(row)
        return None
    
    def _row_to_email_record(self, row) -> EmailRecord:
        """Convert database row to EmailRecord object"""
        return EmailRecord(
            id=row[0],
            resource_name=row[1],
            policy_short_name=row[2],
            owner_email=row[3],
            owner_name=row[4],
            resource_group=row[5],
            subscription_id=row[6],
            severity=row[7],
            bucket=EmailBucket(row[8]),
            status=EmailStatus(row[9]),
            sent_at=datetime.fromisoformat(row[10]) if row[10] else None,
            last_reminder_at=datetime.fromisoformat(row[11]) if row[11] else None,
            reminder_count=row[12],
            response_received_at=datetime.fromisoformat(row[13]) if row[13] else None,
            response_content=row[14],
            llm_analysis=json.loads(row[15]) if row[15] else None,
            exception_reason=row[16],
            resolved_at=datetime.fromisoformat(row[17]) if row[17] else None,
            created_at=datetime.fromisoformat(row[18]),
            updated_at=datetime.fromisoformat(row[19])
        )
    
    async def _update_email_record_from_response(self, record: EmailRecord, analysis: Dict[str, Any], content: str):
        """Update email record based on response analysis"""
        # Update record based on classification
        classification = analysis.get('analysis', {}).get('classification', 'REPLIED_RESPONSE')
        
        if classification == 'WRONG_OWNER':
            record.bucket = EmailBucket.WRONG_OWNER
            # Handle wrong owner scenario
            await self._handle_wrong_owner_response(record, analysis)
        elif classification == 'EXCEPTION_APPROVAL':
            record.bucket = EmailBucket.EXCEPTION_APPROVAL
            record.exception_reason = analysis.get('analysis', {}).get('exception_justification')
        elif classification == 'REPLIED_RESPONSE':
            record.bucket = EmailBucket.REPLIED_RESPONSE
        
        record.status = EmailStatus.REPLIED
        record.response_received_at = datetime.utcnow()
        record.response_content = content
        record.llm_analysis = analysis
        record.updated_at = datetime.utcnow()
        
        # Save updated record
        await self._save_email_record(record)
    
    async def _handle_wrong_owner_response(self, record: EmailRecord, analysis: Dict[str, Any]):
        """Handle wrong owner response by extracting new owner information"""
        try:
            analysis_data = analysis.get('analysis', {})
            owner_transfer_info = analysis_data.get('owner_transfer_info')
            
            if owner_transfer_info:
                # Extract new owner information from the response
                new_owner_info = await self._extract_new_owner_info(record.response_content, owner_transfer_info)
                
                if new_owner_info:
                    # Create new email record for the correct owner
                    await self._create_transferred_email_record(record, new_owner_info)
                    
                    # Update original record with transfer information
                    record.llm_analysis['transfer_info'] = new_owner_info
                    record.llm_analysis['transfer_processed'] = True
                    
            logger.info(f"Processed wrong owner response for record {record.id}")
            
        except Exception as e:
            logger.error(f"Error handling wrong owner response for record {record.id}: {str(e)}")
    
    async def _extract_new_owner_info(self, response_content: str, transfer_info: str) -> Optional[Dict[str, str]]:
        """Extract new owner information from email response using LLM"""
        try:
            extraction_prompt = f"""
            Extract the correct owner information from this email response:
            
            Response Content: {response_content}
            Transfer Info: {transfer_info}
            
            Extract and return in JSON format:
            {{
                "new_owner_name": "Full name of the correct owner",
                "new_owner_email": "Email address of the correct owner",
                "department": "Department or team name if mentioned",
                "reason": "Reason for the transfer"
            }}
            
            If no clear owner information is found, return null.
            """
            
            ai_response = await self.ai_service.generate_response(
                prompt=extraction_prompt,
                context="owner_extraction",
                max_tokens=500
            )
            
            try:
                extracted_info = json.loads(ai_response.get('response', '{}'))
                
                # Validate extracted information
                if extracted_info and extracted_info.get('new_owner_email'):
                    return extracted_info
                    
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM response for owner extraction")
                
            return None
            
        except Exception as e:
            logger.error(f"Error extracting new owner info: {str(e)}")
            return None
    
    async def _create_transferred_email_record(self, original_record: EmailRecord, new_owner_info: Dict[str, str]):
        """Create new email record for the correct owner"""
        try:
            # Generate new record ID
            new_record_id = f"{original_record.id}_transferred_{int(datetime.utcnow().timestamp())}"
            
            # Create new email record
            new_record = EmailRecord(
                id=new_record_id,
                resource_name=original_record.resource_name,
                policy_short_name=original_record.policy_short_name,
                owner_email=new_owner_info.get('new_owner_email'),
                owner_name=new_owner_info.get('new_owner_name', 'Unknown'),
                resource_group=original_record.resource_group,
                subscription_id=original_record.subscription_id,
                severity=original_record.severity,
                bucket=EmailBucket.PENDING_REVIEW,  # Start in pending review
                status=EmailStatus.SENT,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Add transfer metadata to LLM analysis
            new_record.llm_analysis = {
                'transferred_from': original_record.id,
                'original_owner': original_record.owner_email,
                'transfer_reason': new_owner_info.get('reason', 'Wrong owner reported'),
                'transfer_date': datetime.utcnow().isoformat()
            }
            
            # Save the new record
            await self._save_email_record(new_record)
            
            # Send notification to new owner
            await self._send_transfer_notification(new_record, original_record)
            
            logger.info(f"Created transferred email record {new_record_id} for {new_record.owner_email}")
            
        except Exception as e:
            logger.error(f"Error creating transferred email record: {str(e)}")
    
    async def _send_transfer_notification(self, new_record: EmailRecord, original_record: EmailRecord):
        """Send notification email to the new owner"""
        try:
            # Generate transfer notification email
            template = await self._generate_transfer_notification_email(new_record, original_record)
            
            # Send the email
            success = await self._send_reminder_email(new_record.owner_email, template)
            
            if success:
                new_record.sent_at = datetime.utcnow()
                new_record.updated_at = datetime.utcnow()
                await self._save_email_record(new_record)
                logger.info(f"Transfer notification sent to {new_record.owner_email}")
            else:
                logger.error(f"Failed to send transfer notification to {new_record.owner_email}")
                
        except Exception as e:
            logger.error(f"Error sending transfer notification: {str(e)}")
    
    async def _generate_transfer_notification_email(self, new_record: EmailRecord, original_record: EmailRecord) -> EmailTemplate:
        """Generate email template for ownership transfer notification"""
        try:
            template_prompt = f"""
            Generate a professional email notification for a security compliance issue that has been transferred to the correct owner.
            
            Details:
            - Resource: {new_record.resource_name}
            - Policy: {new_record.policy_short_name}
            - Severity: {new_record.severity}
            - Resource Group: {new_record.resource_group}
            - Subscription: {new_record.subscription_id}
            - Original Owner: {original_record.owner_email}
            - Transfer Reason: Ownership correction
            
            The email should:
            1. Explain that this issue was transferred from another owner
            2. Provide clear details about the compliance issue
            3. Request acknowledgment and action
            4. Be professional and actionable
            
            Return in JSON format:
            {{
                "subject": "Security Compliance Issue - Ownership Transfer",
                "body": "Email body content",
                "priority": "high"
            }}
            """
            
            ai_response = await self.ai_service.generate_response(
                prompt=template_prompt,
                context="transfer_notification",
                max_tokens=1000
            )
            
            try:
                template_data = json.loads(ai_response.get('response', '{}'))
                return EmailTemplate(
                    subject=template_data.get('subject', f"Security Compliance - {new_record.policy_short_name}"),
                    body=template_data.get('body', f"Security compliance issue for {new_record.resource_name} requires your attention."),
                    priority=template_data.get('priority', 'high')
                )
            except json.JSONDecodeError:
                # Fallback template
                return EmailTemplate(
                    subject=f"Security Compliance Transfer - {new_record.policy_short_name}",
                    body=f"A security compliance issue for resource '{new_record.resource_name}' has been transferred to you for resolution. Please review and take appropriate action.",
                    priority="high"
                )
                
        except Exception as e:
            logger.error(f"Error generating transfer notification email: {str(e)}")
            return EmailTemplate(
                subject=f"Security Compliance - {new_record.policy_short_name}",
                body=f"Security compliance issue for {new_record.resource_name} requires your attention.",
                priority="high"
            )
    
    async def get_wrong_owner_records(self) -> List[EmailRecord]:
        """Get all records in the wrong owner bucket"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM email_records 
            WHERE bucket = ? 
            ORDER BY created_at DESC
        """, (EmailBucket.WRONG_OWNER.value,))
        
        records = [self._row_to_email_record(row) for row in cursor.fetchall()]
        conn.close()
        
        return records
    
    async def process_wrong_owner_bucket(self) -> Dict[str, Any]:
        """Process all records in wrong owner bucket for potential transfers"""
        try:
            wrong_owner_records = await self.get_wrong_owner_records()
            processed_transfers = []
            failed_transfers = []
            
            for record in wrong_owner_records:
                try:
                    # Check if transfer has already been processed
                    if record.llm_analysis and record.llm_analysis.get('transfer_processed'):
                        continue
                    
                    # Re-analyze for owner transfer information
                    if record.response_content:
                        analysis = await self.analyze_email_response(
                            record.response_content, 
                            record.owner_email, 
                            f"Re: {record.policy_short_name}"
                        )
                        
                        await self._handle_wrong_owner_response(record, analysis)
                        processed_transfers.append(record.id)
                        
                except Exception as e:
                    logger.error(f"Error processing wrong owner record {record.id}: {str(e)}")
                    failed_transfers.append({'record_id': record.id, 'error': str(e)})
            
            return {
                'success': True,
                'processed_count': len(processed_transfers),
                'failed_count': len(failed_transfers),
                'processed_records': processed_transfers,
                'failed_records': failed_transfers
            }
            
        except Exception as e:
            logger.error(f"Error processing wrong owner bucket: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processed_count': 0,
                'failed_count': 0
            }
    
    async def send_reminder_emails(self) -> Dict[str, Any]:
        """Send reminder emails for pending responses"""
        try:
            # Get records that need reminders
            reminder_candidates = await self._get_reminder_candidates()
            
            sent_reminders = []
            failed_reminders = []
            
            for record in reminder_candidates:
                try:
                    # Generate reminder email
                    reminder_template = await self._generate_reminder_email(record)
                    
                    # Send reminder
                    success = await self._send_reminder_email(record.owner_email, reminder_template)
                    
                    if success:
                        # Update record
                        record.last_reminder_at = datetime.utcnow()
                        record.reminder_count += 1
                        record.updated_at = datetime.utcnow()
                        await self._save_email_record(record)
                        
                        sent_reminders.append({
                            'record_id': record.id,
                            'owner_email': record.owner_email,
                            'reminder_count': record.reminder_count
                        })
                    else:
                        failed_reminders.append({
                            'record_id': record.id,
                            'owner_email': record.owner_email,
                            'error': 'Failed to send email'
                        })
                        
                except Exception as e:
                    logger.error(f"Error sending reminder for record {record.id}: {str(e)}")
                    failed_reminders.append({
                        'record_id': record.id,
                        'owner_email': record.owner_email,
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'sent_count': len(sent_reminders),
                'failed_count': len(failed_reminders),
                'sent_reminders': sent_reminders,
                'failed_reminders': failed_reminders
            }
            
        except Exception as e:
            logger.error(f"Error sending reminder emails: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'sent_count': 0,
                'failed_count': 0
            }
    
    async def _get_reminder_candidates(self) -> List[EmailRecord]:
        """Get email records that need reminder emails"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate cutoff dates for reminders
        now = datetime.utcnow()
        reminder_conditions = []
        
        for i, interval in enumerate(self.reminder_intervals):
            cutoff_date = (now - timedelta(days=interval)).isoformat()
            reminder_conditions.append(f"""
                (reminder_count = {i} AND 
                 (last_reminder_at IS NULL OR last_reminder_at < '{cutoff_date}') AND
                 sent_at < '{cutoff_date}')
            """)
        
        query = f"""
            SELECT * FROM email_records 
            WHERE bucket IN ('pending_review', 'reminder') 
            AND status NOT IN ('replied', 'resolved') 
            AND reminder_count < {self.max_reminders}
            AND ({' OR '.join(reminder_conditions)})
            ORDER BY created_at ASC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_email_record(row) for row in rows]
    
    async def _generate_reminder_email(self, record: EmailRecord) -> EmailTemplate:
        """Generate reminder email template"""
        reminder_number = record.reminder_count + 1
        
        subject = f"🔔 Reminder #{reminder_number}: Security Alert - {record.policy_short_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Security Reminder</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #ff9800; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .reminder-badge {{ background-color: #f44336; color: white; padding: 5px 10px; border-radius: 3px; }}
                .resource-info {{ background-color: #f5f5f5; padding: 15px; margin: 10px 0; border-left: 4px solid #2196f3; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔔 Security Reminder #{reminder_number}</h1>
                <span class="reminder-badge">Action Required</span>
            </div>
            <div class="content">
                <p>Dear {record.owner_name},</p>
                
                <p>This is a <strong>reminder #{reminder_number}</strong> regarding a security finding that requires your attention.</p>
                
                <div class="resource-info">
                    <h3>Resource Details:</h3>
                    <ul>
                        <li><strong>Resource:</strong> {record.resource_name}</li>
                        <li><strong>Policy:</strong> {record.policy_short_name}</li>
                        <li><strong>Resource Group:</strong> {record.resource_group}</li>
                        <li><strong>Severity:</strong> {record.severity.upper()}</li>
                        <li><strong>Original Alert Date:</strong> {record.created_at.strftime('%Y-%m-%d %H:%M')}</li>
                    </ul>
                </div>
                
                <p><strong>Please respond to this email with one of the following:</strong></p>
                <ul>
                    <li>Confirmation that you will address the security finding</li>
                    <li>If you are not the correct owner, please provide the correct contact information</li>
                    <li>If this requires an exception, please provide business justification</li>
                </ul>
                
                <p>If no response is received, this will be escalated according to our security policy.</p>
                
                <p>Thank you for your attention to this security matter.</p>
                
                <p>Best regards,<br>Security Team</p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Security Reminder #{reminder_number}
        
        Dear {record.owner_name},
        
        This is a reminder #{reminder_number} regarding a security finding that requires your attention.
        
        Resource Details:
        - Resource: {record.resource_name}
        - Policy: {record.policy_short_name}
        - Resource Group: {record.resource_group}
        - Severity: {record.severity.upper()}
        - Original Alert Date: {record.created_at.strftime('%Y-%m-%d %H:%M')}
        
        Please respond with:
        1. Confirmation that you will address the security finding
        2. If you are not the correct owner, please provide the correct contact
        3. If this requires an exception, please provide business justification
        
        Thank you,
        Security Team
        """
        
        return EmailTemplate(
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            resource_name=record.resource_name,
            policy_short_name=record.policy_short_name,
            policy_name=record.policy_short_name,
            severity=record.severity,
            native_type="reminder",
            ai_recommendations="Please respond to this reminder",
            remediation_steps="Respond to security team",
            business_impact="Delayed response may result in escalation",
            azure_commands="N/A"
        )
    
    async def _send_reminder_email(self, recipient: str, template: EmailTemplate) -> bool:
        """Send reminder email"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = template.subject
            msg['From'] = self.email_user
            msg['To'] = recipient
            
            # Create text and HTML parts
            text_part = MIMEText(template.text_content, 'plain')
            html_part = MIMEText(template.html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending reminder email to {recipient}: {str(e)}")
            return False
    
    async def schedule_reminder_notifications(self, validation_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Schedule reminder notifications based on validation data and comparison files"""
        try:
            scheduled_reminders = []
            
            # If validation data is provided, process it for reminder scheduling
            if validation_data:
                for resource in validation_data.get('resources', []):
                    # Check if resource needs follow-up
                    if self._needs_follow_up_reminder(resource):
                        reminder_record = await self._create_reminder_record(resource)
                        if reminder_record:
                            scheduled_reminders.append(reminder_record)
            
            # Process existing records for automatic reminder scheduling
            pending_records = await self._get_pending_reminder_records()
            for record in pending_records:
                if await self._should_schedule_reminder(record):
                    await self._schedule_next_reminder(record)
                    scheduled_reminders.append({
                        'record_id': record.id,
                        'owner_email': record.owner_email,
                        'next_reminder_date': record.next_reminder_date
                    })
            
            return {
                'success': True,
                'scheduled_count': len(scheduled_reminders),
                'scheduled_reminders': scheduled_reminders
            }
            
        except Exception as e:
            logger.error(f"Error scheduling reminder notifications: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'scheduled_count': 0
            }
    
    def _needs_follow_up_reminder(self, resource: Dict[str, Any]) -> bool:
        """Determine if a resource needs follow-up reminder based on validation results"""
        try:
            # Check if resource has unresolved security findings
            if resource.get('status') in ['non_compliant', 'failed', 'critical']:
                return True
            
            # Check if resource has high/critical severity issues
            severity = resource.get('severity', '').lower()
            if severity in ['high', 'critical']:
                return True
            
            # Check if resource has been pending for too long
            created_date = resource.get('created_date')
            if created_date:
                days_pending = (datetime.utcnow() - datetime.fromisoformat(created_date)).days
                if days_pending > 7:  # More than 7 days pending
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking follow-up reminder need: {str(e)}")
            return False
    
    async def _create_reminder_record(self, resource: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a reminder record from validation resource data"""
        try:
            # Generate record ID
            record_id = f"reminder_{resource.get('resource_name', 'unknown')}_{int(datetime.utcnow().timestamp())}"
            
            # Create email record for reminder
            reminder_record = EmailRecord(
                id=record_id,
                resource_name=resource.get('resource_name', 'Unknown Resource'),
                policy_short_name=resource.get('policy_name', 'Security Policy'),
                owner_email=resource.get('owner_email', 'unknown@example.com'),
                owner_name=resource.get('owner_name', 'Unknown Owner'),
                resource_group=resource.get('resource_group', 'Unknown'),
                subscription_id=resource.get('subscription_id', 'Unknown'),
                severity=resource.get('severity', 'medium'),
                bucket=EmailBucket.REMINDER,
                status=EmailStatus.PENDING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Add validation metadata
            reminder_record.llm_analysis = {
                'validation_source': True,
                'resource_status': resource.get('status'),
                'compliance_score': resource.get('compliance_score'),
                'created_from': 'validation_data'
            }
            
            # Save the record
            await self._save_email_record(reminder_record)
            
            return {
                'record_id': record_id,
                'resource_name': reminder_record.resource_name,
                'owner_email': reminder_record.owner_email,
                'severity': reminder_record.severity
            }
            
        except Exception as e:
            logger.error(f"Error creating reminder record: {str(e)}")
            return None
    
    async def _get_pending_reminder_records(self) -> List[EmailRecord]:
        """Get records that are pending reminder scheduling"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM email_records 
            WHERE bucket = 'reminder' 
            AND status IN ('pending', 'sent')
            AND (next_reminder_date IS NULL OR next_reminder_date <= ?)
            ORDER BY created_at ASC
        """
        
        cursor.execute(query, (datetime.utcnow().isoformat(),))
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_email_record(row) for row in rows]
    
    async def _should_schedule_reminder(self, record: EmailRecord) -> bool:
        """Determine if a record should have its next reminder scheduled"""
        try:
            # Don't schedule if already resolved
            if record.status in [EmailStatus.REPLIED, EmailStatus.RESOLVED]:
                return False
            
            # Don't schedule if max reminders reached
            if record.reminder_count >= self.max_reminders:
                return False
            
            # Check if enough time has passed since last reminder
            if record.last_reminder_at:
                days_since_last = (datetime.utcnow() - record.last_reminder_at).days
                next_interval = self.reminder_intervals[min(record.reminder_count, len(self.reminder_intervals) - 1)]
                if days_since_last < next_interval:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking reminder scheduling: {str(e)}")
            return False
    
    async def _schedule_next_reminder(self, record: EmailRecord):
        """Schedule the next reminder for a record"""
        try:
            # Calculate next reminder date
            next_interval = self.reminder_intervals[min(record.reminder_count, len(self.reminder_intervals) - 1)]
            next_reminder_date = datetime.utcnow() + timedelta(days=next_interval)
            
            # Update record with next reminder date
            record.next_reminder_date = next_reminder_date
            record.updated_at = datetime.utcnow()
            
            await self._save_email_record(record)
            
            logger.info(f"Scheduled next reminder for record {record.id} on {next_reminder_date}")
            
        except Exception as e:
            logger.error(f"Error scheduling next reminder: {str(e)}")
    
    async def process_comparison_for_reminders(self, comparison_result: Dict[str, Any]) -> Dict[str, Any]:
        """Process comparison file results to generate targeted reminders"""
        try:
            generated_reminders = []
            
            # Process resources that need attention based on comparison
            for resource_comparison in comparison_result.get('comparisons', []):
                if self._comparison_needs_reminder(resource_comparison):
                    reminder_data = await self._create_comparison_reminder(resource_comparison)
                    if reminder_data:
                        generated_reminders.append(reminder_data)
            
            return {
                'success': True,
                'generated_count': len(generated_reminders),
                'generated_reminders': generated_reminders
            }
            
        except Exception as e:
            logger.error(f"Error processing comparison for reminders: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'generated_count': 0
            }
    
    def _comparison_needs_reminder(self, comparison: Dict[str, Any]) -> bool:
        """Determine if a comparison result needs a reminder"""
        try:
            # Check if there are differences that need attention
            status = comparison.get('status', '').lower()
            if status in ['different', 'missing', 'non_compliant']:
                return True
            
            # Check if resource has degraded compliance
            current_score = comparison.get('current_compliance_score', 100)
            previous_score = comparison.get('previous_compliance_score', 100)
            if current_score < previous_score:
                return True
            
            # Check if new security findings were introduced
            new_findings = comparison.get('new_findings', [])
            if len(new_findings) > 0:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking comparison reminder need: {str(e)}")
            return False
    
    async def _create_comparison_reminder(self, comparison: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create reminder from comparison result"""
        try:
            # Generate record ID
            record_id = f"comparison_reminder_{comparison.get('resource_name', 'unknown')}_{int(datetime.utcnow().timestamp())}"
            
            # Create email record
            reminder_record = EmailRecord(
                id=record_id,
                resource_name=comparison.get('resource_name', 'Unknown Resource'),
                policy_short_name=comparison.get('policy_name', 'Compliance Check'),
                owner_email=comparison.get('owner_email', 'unknown@example.com'),
                owner_name=comparison.get('owner_name', 'Unknown Owner'),
                resource_group=comparison.get('resource_group', 'Unknown'),
                subscription_id=comparison.get('subscription_id', 'Unknown'),
                severity=self._determine_comparison_severity(comparison),
                bucket=EmailBucket.REMINDER,
                status=EmailStatus.PENDING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Add comparison metadata
            reminder_record.llm_analysis = {
                'comparison_source': True,
                'comparison_status': comparison.get('status'),
                'compliance_change': comparison.get('compliance_change'),
                'new_findings_count': len(comparison.get('new_findings', [])),
                'created_from': 'comparison_analysis'
            }
            
            # Save the record
            await self._save_email_record(reminder_record)
            
            return {
                'record_id': record_id,
                'resource_name': reminder_record.resource_name,
                'owner_email': reminder_record.owner_email,
                'comparison_status': comparison.get('status')
            }
            
        except Exception as e:
            logger.error(f"Error creating comparison reminder: {str(e)}")
            return None
    
    def _determine_comparison_severity(self, comparison: Dict[str, Any]) -> str:
        """Determine severity based on comparison results"""
        try:
            # Check for critical changes
            new_findings = comparison.get('new_findings', [])
            critical_findings = [f for f in new_findings if f.get('severity', '').lower() == 'critical']
            if len(critical_findings) > 0:
                return 'critical'
            
            # Check for high severity changes
            high_findings = [f for f in new_findings if f.get('severity', '').lower() == 'high']
            if len(high_findings) > 0:
                return 'high'
            
            # Check compliance score degradation
            current_score = comparison.get('current_compliance_score', 100)
            previous_score = comparison.get('previous_compliance_score', 100)
            score_drop = previous_score - current_score
            
            if score_drop > 20:
                return 'high'
            elif score_drop > 10:
                return 'medium'
            
            return 'medium'
            
        except Exception as e:
            logger.error(f"Error determining comparison severity: {str(e)}")
            return 'medium'
    
    async def create_exception_policy_record(self, resource_data: Dict[str, Any], exception_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create exception policy record for resources with approved exceptions"""
        try:
            # Generate record ID
            record_id = f"exception_{resource_data.get('resource_name', 'unknown')}_{int(datetime.utcnow().timestamp())}"
            
            # Create email record for exception policy
            exception_record = EmailRecord(
                id=record_id,
                resource_name=resource_data.get('resource_name', 'Unknown Resource'),
                policy_short_name=resource_data.get('policy_name', 'Security Policy'),
                owner_email=resource_data.get('owner_email', 'unknown@example.com'),
                owner_name=resource_data.get('owner_name', 'Unknown Owner'),
                resource_group=resource_data.get('resource_group', 'Unknown'),
                subscription_id=resource_data.get('subscription_id', 'Unknown'),
                severity=resource_data.get('severity', 'medium'),
                bucket=EmailBucket.EXCEPTION_POLICY,
                status=EmailStatus.RESOLVED,  # Exceptions are considered resolved
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Add exception metadata
            exception_record.llm_analysis = {
                'exception_approved': True,
                'exception_reason': exception_details.get('reason', 'Business exception'),
                'approved_by': exception_details.get('approved_by', 'Unknown'),
                'approval_date': exception_details.get('approval_date', datetime.utcnow().isoformat()),
                'expiry_date': exception_details.get('expiry_date'),
                'business_justification': exception_details.get('business_justification', ''),
                'created_from': 'exception_policy'
            }
            
            # Save the record
            await self._save_email_record(exception_record)
            
            return {
                'success': True,
                'record_id': record_id,
                'resource_name': exception_record.resource_name,
                'exception_reason': exception_details.get('reason')
            }
            
        except Exception as e:
            logger.error(f"Error creating exception policy record: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_exception_policy_records(self) -> List[EmailRecord]:
        """Get records from exception policy bucket"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM email_records 
            WHERE bucket = 'exception_policy'
            ORDER BY created_at DESC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_email_record(row) for row in rows]
    
    async def validate_exception_expiry(self) -> Dict[str, Any]:
        """Check for expired exceptions and move them back to pending review"""
        try:
            expired_exceptions = []
            renewed_exceptions = []
            
            # Get all exception policy records
            exception_records = await self.get_exception_policy_records()
            
            for record in exception_records:
                if await self._is_exception_expired(record):
                    # Move back to pending review
                    await self._reactivate_expired_exception(record)
                    expired_exceptions.append({
                        'record_id': record.id,
                        'resource_name': record.resource_name,
                        'owner_email': record.owner_email
                    })
                elif await self._needs_exception_renewal(record):
                    # Send renewal notification
                    await self._send_exception_renewal_notification(record)
                    renewed_exceptions.append({
                        'record_id': record.id,
                        'resource_name': record.resource_name,
                        'owner_email': record.owner_email
                    })
            
            return {
                'success': True,
                'expired_count': len(expired_exceptions),
                'renewal_notifications_sent': len(renewed_exceptions),
                'expired_exceptions': expired_exceptions,
                'renewal_notifications': renewed_exceptions
            }
            
        except Exception as e:
            logger.error(f"Error validating exception expiry: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'expired_count': 0,
                'renewal_notifications_sent': 0
            }
    
    async def _is_exception_expired(self, record: EmailRecord) -> bool:
        """Check if an exception has expired"""
        try:
            if not record.llm_analysis or not record.llm_analysis.get('expiry_date'):
                return False
            
            expiry_date = datetime.fromisoformat(record.llm_analysis['expiry_date'])
            return datetime.utcnow() > expiry_date
            
        except Exception as e:
            logger.error(f"Error checking exception expiry: {str(e)}")
            return False
    
    async def _needs_exception_renewal(self, record: EmailRecord) -> bool:
        """Check if an exception needs renewal notification (30 days before expiry)"""
        try:
            if not record.llm_analysis or not record.llm_analysis.get('expiry_date'):
                return False
            
            expiry_date = datetime.fromisoformat(record.llm_analysis['expiry_date'])
            renewal_threshold = expiry_date - timedelta(days=30)
            
            # Check if we're within renewal period and haven't sent notification yet
            return (datetime.utcnow() > renewal_threshold and 
                    not record.llm_analysis.get('renewal_notification_sent', False))
            
        except Exception as e:
            logger.error(f"Error checking exception renewal need: {str(e)}")
            return False
    
    async def _reactivate_expired_exception(self, record: EmailRecord):
        """Reactivate an expired exception by moving it back to pending review"""
        try:
            # Update record status and bucket
            record.bucket = EmailBucket.PENDING_REVIEW
            record.status = EmailStatus.PENDING
            record.updated_at = datetime.utcnow()
            
            # Update LLM analysis to indicate expiry
            if not record.llm_analysis:
                record.llm_analysis = {}
            
            record.llm_analysis.update({
                'exception_expired': True,
                'reactivated_date': datetime.utcnow().isoformat(),
                'previous_exception_reason': record.llm_analysis.get('exception_reason', '')
            })
            
            # Save updated record
            await self._save_email_record(record)
            
            # Send reactivation notification
            await self._send_exception_expiry_notification(record)
            
            logger.info(f"Reactivated expired exception for record {record.id}")
            
        except Exception as e:
            logger.error(f"Error reactivating expired exception: {str(e)}")
    
    async def _send_exception_renewal_notification(self, record: EmailRecord):
        """Send notification for exception renewal"""
        try:
            # Generate renewal notification email
            template = await self._generate_exception_renewal_email(record)
            
            # Send the email
            success = await self._send_reminder_email(record.owner_email, template)
            
            if success:
                # Mark renewal notification as sent
                if not record.llm_analysis:
                    record.llm_analysis = {}
                
                record.llm_analysis['renewal_notification_sent'] = True
                record.llm_analysis['renewal_notification_date'] = datetime.utcnow().isoformat()
                record.updated_at = datetime.utcnow()
                
                await self._save_email_record(record)
                logger.info(f"Exception renewal notification sent for record {record.id}")
            
        except Exception as e:
            logger.error(f"Error sending exception renewal notification: {str(e)}")
    
    async def _send_exception_expiry_notification(self, record: EmailRecord):
        """Send notification for expired exception"""
        try:
            # Generate expiry notification email
            template = await self._generate_exception_expiry_email(record)
            
            # Send the email
            success = await self._send_reminder_email(record.owner_email, template)
            
            if success:
                logger.info(f"Exception expiry notification sent for record {record.id}")
            
        except Exception as e:
            logger.error(f"Error sending exception expiry notification: {str(e)}")
    
    async def _generate_exception_renewal_email(self, record: EmailRecord) -> EmailTemplate:
        """Generate email template for exception renewal notification"""
        expiry_date = record.llm_analysis.get('expiry_date', 'Unknown')
        
        subject = f"🔔 Exception Renewal Required - {record.policy_short_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Exception Renewal Required</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #ff9800; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; margin: 10px 0; }}
                .resource-info {{ background-color: #f5f5f5; padding: 15px; margin: 10px 0; border-left: 4px solid #2196f3; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔔 Exception Renewal Required</h1>
            </div>
            <div class="content">
                <p>Dear {record.owner_name},</p>
                
                <div class="warning">
                    <strong>⚠️ Your security exception is expiring soon and requires renewal.</strong>
                </div>
                
                <div class="resource-info">
                    <h3>Exception Details:</h3>
                    <ul>
                        <li><strong>Resource:</strong> {record.resource_name}</li>
                        <li><strong>Policy:</strong> {record.policy_short_name}</li>
                        <li><strong>Resource Group:</strong> {record.resource_group}</li>
                        <li><strong>Current Exception Reason:</strong> {record.llm_analysis.get('exception_reason', 'N/A')}</li>
                        <li><strong>Expiry Date:</strong> {expiry_date}</li>
                    </ul>
                </div>
                
                <p><strong>Action Required:</strong></p>
                <ul>
                    <li>Review the current exception and determine if it's still valid</li>
                    <li>If renewal is needed, provide updated business justification</li>
                    <li>If no longer needed, the resource will return to compliance monitoring</li>
                </ul>
                
                <p>Please respond within 30 days to avoid automatic reactivation of security monitoring.</p>
                
                <p>Best regards,<br>Security Team</p>
            </div>
        </body>
        </html>
        """
        
        return EmailTemplate(
            subject=subject,
            html_content=html_content,
            text_content=f"Exception renewal required for {record.resource_name}. Expiry: {expiry_date}",
            resource_name=record.resource_name,
            policy_short_name=record.policy_short_name,
            policy_name=record.policy_short_name,
            severity=record.severity,
            native_type="exception_renewal",
            ai_recommendations="Review and renew exception if still valid",
            remediation_steps="Provide updated business justification",
            business_impact="Exception will expire and monitoring will resume",
            azure_commands="N/A"
        )
    
    async def _generate_exception_expiry_email(self, record: EmailRecord) -> EmailTemplate:
        """Generate email template for expired exception notification"""
        subject = f"🚨 Exception Expired - Security Monitoring Resumed - {record.policy_short_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Exception Expired</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #f44336; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .alert {{ background-color: #ffebee; border: 1px solid #f44336; padding: 10px; margin: 10px 0; }}
                .resource-info {{ background-color: #f5f5f5; padding: 15px; margin: 10px 0; border-left: 4px solid #f44336; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚨 Exception Expired</h1>
            </div>
            <div class="content">
                <p>Dear {record.owner_name},</p>
                
                <div class="alert">
                    <strong>⚠️ Your security exception has expired and monitoring has resumed.</strong>
                </div>
                
                <div class="resource-info">
                    <h3>Resource Details:</h3>
                    <ul>
                        <li><strong>Resource:</strong> {record.resource_name}</li>
                        <li><strong>Policy:</strong> {record.policy_short_name}</li>
                        <li><strong>Resource Group:</strong> {record.resource_group}</li>
                        <li><strong>Previous Exception:</strong> {record.llm_analysis.get('previous_exception_reason', 'N/A')}</li>
                    </ul>
                </div>
                
                <p>This resource is now subject to regular security compliance monitoring. Please take appropriate action to address any security findings.</p>
                
                <p>If you believe this exception should be renewed, please contact the security team with updated business justification.</p>
                
                <p>Best regards,<br>Security Team</p>
            </div>
        </body>
        </html>
        """
        
        return EmailTemplate(
            subject=subject,
            html_content=html_content,
            text_content=f"Exception expired for {record.resource_name}. Security monitoring resumed.",
            resource_name=record.resource_name,
            policy_short_name=record.policy_short_name,
            policy_name=record.policy_short_name,
            severity=record.severity,
            native_type="exception_expired",
            ai_recommendations="Address security findings or request new exception",
            remediation_steps="Review security compliance requirements",
            business_impact="Resource is now subject to security monitoring",
            azure_commands="N/A"
        )
    
    async def process_exception_requests(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process exception requests from email responses"""
        try:
            processed_requests = []
            
            for request in request_data.get('exception_requests', []):
                # Validate exception request
                if self._validate_exception_request(request):
                    # Create exception policy record
                    result = await self.create_exception_policy_record(
                        request.get('resource_data', {}),
                        request.get('exception_details', {})
                    )
                    
                    if result.get('success'):
                        processed_requests.append(result)
                        
                        # Send confirmation email
                        await self._send_exception_approval_notification(request)
            
            return {
                'success': True,
                'processed_count': len(processed_requests),
                'processed_requests': processed_requests
            }
            
        except Exception as e:
            logger.error(f"Error processing exception requests: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processed_count': 0
            }
    
    def _validate_exception_request(self, request: Dict[str, Any]) -> bool:
        """Validate exception request has required fields"""
        try:
            resource_data = request.get('resource_data', {})
            exception_details = request.get('exception_details', {})
            
            # Check required fields
            required_resource_fields = ['resource_name', 'owner_email']
            required_exception_fields = ['reason', 'business_justification']
            
            for field in required_resource_fields:
                if not resource_data.get(field):
                    return False
            
            for field in required_exception_fields:
                if not exception_details.get(field):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating exception request: {str(e)}")
            return False
    
    async def _send_exception_approval_notification(self, request: Dict[str, Any]):
        """Send notification for approved exception"""
        try:
            resource_data = request.get('resource_data', {})
            owner_email = resource_data.get('owner_email')
            
            if owner_email:
                # Generate approval notification
                template = await self._generate_exception_approval_email(request)
                
                # Send the email
                await self._send_reminder_email(owner_email, template)
                
                logger.info(f"Exception approval notification sent to {owner_email}")
            
        except Exception as e:
            logger.error(f"Error sending exception approval notification: {str(e)}")
    
    async def _generate_exception_approval_email(self, request: Dict[str, Any]) -> EmailTemplate:
        """Generate email template for exception approval notification"""
        resource_data = request.get('resource_data', {})
        exception_details = request.get('exception_details', {})
        
        resource_name = resource_data.get('resource_name', 'Unknown')
        policy_name = resource_data.get('policy_name', 'Security Policy')
        
        subject = f"✅ Exception Approved - {policy_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Exception Approved</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #4caf50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .success {{ background-color: #e8f5e8; border: 1px solid #4caf50; padding: 10px; margin: 10px 0; }}
                .resource-info {{ background-color: #f5f5f5; padding: 15px; margin: 10px 0; border-left: 4px solid #4caf50; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>✅ Exception Approved</h1>
            </div>
            <div class="content">
                <p>Dear {resource_data.get('owner_name', 'Resource Owner')},</p>
                
                <div class="success">
                    <strong>✅ Your exception request has been approved.</strong>
                </div>
                
                <div class="resource-info">
                    <h3>Exception Details:</h3>
                    <ul>
                        <li><strong>Resource:</strong> {resource_name}</li>
                        <li><strong>Policy:</strong> {policy_name}</li>
                        <li><strong>Exception Reason:</strong> {exception_details.get('reason', 'N/A')}</li>
                        <li><strong>Approved By:</strong> {exception_details.get('approved_by', 'Security Team')}</li>
                        <li><strong>Expiry Date:</strong> {exception_details.get('expiry_date', 'No expiry set')}</li>
                    </ul>
                </div>
                
                <p>This resource is now exempt from the specified security policy. Please ensure you continue to follow your organization's security best practices.</p>
                
                <p>You will receive a renewal notification 30 days before the exception expires (if applicable).</p>
                
                <p>Best regards,<br>Security Team</p>
            </div>
        </body>
        </html>
        """
        
        return EmailTemplate(
            subject=subject,
            html_content=html_content,
            text_content=f"Exception approved for {resource_name}. Policy: {policy_name}",
            resource_name=resource_name,
            policy_short_name=policy_name,
            policy_name=policy_name,
            severity="info",
            native_type="exception_approved",
            ai_recommendations="Continue following security best practices",
            remediation_steps="No action required - exception approved",
            business_impact="Resource exempt from specified policy",
            azure_commands="N/A"
        )
    
    async def generate_llm_response(self, email_content: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate LLM-powered response to incoming emails"""
        try:
            # Analyze the email content to determine response type
            response_analysis = await self._analyze_email_for_response(email_content, context_data)
            
            if not response_analysis.get('should_respond', False):
                return {
                    'success': True,
                    'should_respond': False,
                    'reason': response_analysis.get('reason', 'No response needed')
                }
            
            # Generate appropriate response based on analysis
            response_template = await self._generate_response_template(
                email_content, 
                context_data, 
                response_analysis
            )
            
            return {
                'success': True,
                'should_respond': True,
                'response_type': response_analysis.get('response_type'),
                'response_template': response_template,
                'confidence_score': response_analysis.get('confidence_score', 0.0),
                'suggested_actions': response_analysis.get('suggested_actions', [])
            }
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'should_respond': False
            }
    
    async def _analyze_email_for_response(self, email_content: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze email content to determine if and how to respond"""
        try:
            # Create analysis prompt
            prompt = f"""
            Analyze the following email to determine if an automated response is appropriate and what type of response should be sent.
            
            Email Content:
            {email_content}
            
            Context Information:
            - Resource: {context_data.get('resource_name', 'Unknown')}
            - Policy: {context_data.get('policy_name', 'Unknown')}
            - Owner: {context_data.get('owner_name', 'Unknown')}
            - Severity: {context_data.get('severity', 'Unknown')}
            
            Please analyze and provide:
            1. Should we respond? (yes/no)
            2. Response type (acknowledgment, clarification_request, information_provided, escalation_needed, resolved)
            3. Confidence score (0.0-1.0)
            4. Reason for decision
            5. Suggested actions
            
            Response format (JSON):
            {{
                "should_respond": boolean,
                "response_type": "string",
                "confidence_score": float,
                "reason": "string",
                "suggested_actions": ["action1", "action2"]
            }}
            """
            
            # Call LLM for analysis
            analysis_result = await self._call_llm_for_analysis(prompt)
            
            # Parse the response
            try:
                import json
                parsed_result = json.loads(analysis_result)
                return parsed_result
            except json.JSONDecodeError:
                # Fallback parsing
                return self._parse_analysis_fallback(analysis_result)
            
        except Exception as e:
            logger.error(f"Error analyzing email for response: {str(e)}")
            return {
                'should_respond': False,
                'response_type': 'error',
                'confidence_score': 0.0,
                'reason': f'Analysis error: {str(e)}',
                'suggested_actions': []
            }
    
    async def _generate_response_template(self, email_content: str, context_data: Dict[str, Any], analysis: Dict[str, Any]) -> EmailTemplate:
        """Generate response email template based on analysis"""
        response_type = analysis.get('response_type', 'acknowledgment')
        
        if response_type == 'acknowledgment':
            return await self._generate_acknowledgment_response(email_content, context_data)
        elif response_type == 'clarification_request':
            return await self._generate_clarification_response(email_content, context_data)
        elif response_type == 'information_provided':
            return await self._generate_information_response(email_content, context_data)
        elif response_type == 'escalation_needed':
            return await self._generate_escalation_response(email_content, context_data)
        elif response_type == 'resolved':
            return await self._generate_resolution_response(email_content, context_data)
        else:
            return await self._generate_default_response(email_content, context_data)
    
    async def _generate_acknowledgment_response(self, email_content: str, context_data: Dict[str, Any]) -> EmailTemplate:
        """Generate acknowledgment response template"""
        resource_name = context_data.get('resource_name', 'Unknown Resource')
        policy_name = context_data.get('policy_name', 'Security Policy')
        
        subject = f"✅ Received - Security Finding Acknowledgment - {policy_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Security Finding Acknowledgment</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #2196f3; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .info {{ background-color: #e3f2fd; border: 1px solid #2196f3; padding: 10px; margin: 10px 0; }}
                .resource-info {{ background-color: #f5f5f5; padding: 15px; margin: 10px 0; border-left: 4px solid #2196f3; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>✅ Security Finding Acknowledgment</h1>
            </div>
            <div class="content">
                <p>Dear {context_data.get('owner_name', 'Resource Owner')},</p>
                
                <div class="info">
                    <strong>✅ We have received your response regarding the security finding.</strong>
                </div>
                
                <div class="resource-info">
                    <h3>Finding Details:</h3>
                    <ul>
                        <li><strong>Resource:</strong> {resource_name}</li>
                        <li><strong>Policy:</strong> {policy_name}</li>
                        <li><strong>Severity:</strong> {context_data.get('severity', 'Unknown')}</li>
                    </ul>
                </div>
                
                <p>Your response has been logged and will be reviewed by our security team. We will follow up if any additional information is needed.</p>
                
                <p>If you have any questions or need immediate assistance, please contact our security team.</p>
                
                <p>Best regards,<br>Security Team</p>
            </div>
        </body>
        </html>
        """
        
        return EmailTemplate(
            subject=subject,
            html_content=html_content,
            text_content=f"Acknowledgment: Response received for {resource_name} security finding.",
            resource_name=resource_name,
            policy_short_name=policy_name,
            policy_name=policy_name,
            severity=context_data.get('severity', 'info'),
            native_type="acknowledgment",
            ai_recommendations="Response logged for security team review",
            remediation_steps="No action required - acknowledgment sent",
            business_impact="Response tracking updated",
            azure_commands="N/A"
        )
    
    async def _generate_clarification_response(self, email_content: str, context_data: Dict[str, Any]) -> EmailTemplate:
        """Generate clarification request response template"""
        resource_name = context_data.get('resource_name', 'Unknown Resource')
        policy_name = context_data.get('policy_name', 'Security Policy')
        
        subject = f"❓ Clarification Needed - {policy_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Clarification Needed</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #ff9800; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; margin: 10px 0; }}
                .resource-info {{ background-color: #f5f5f5; padding: 15px; margin: 10px 0; border-left: 4px solid #ff9800; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>❓ Clarification Needed</h1>
            </div>
            <div class="content">
                <p>Dear {context_data.get('owner_name', 'Resource Owner')},</p>
                
                <div class="warning">
                    <strong>❓ We need additional information to process your response.</strong>
                </div>
                
                <div class="resource-info">
                    <h3>Finding Details:</h3>
                    <ul>
                        <li><strong>Resource:</strong> {resource_name}</li>
                        <li><strong>Policy:</strong> {policy_name}</li>
                        <li><strong>Severity:</strong> {context_data.get('severity', 'Unknown')}</li>
                    </ul>
                </div>
                
                <p>To better assist you, please provide:</p>
                <ul>
                    <li>Specific details about your remediation approach</li>
                    <li>Timeline for implementing the fix</li>
                    <li>Any business constraints or exceptions needed</li>
                </ul>
                
                <p>Please reply with the requested information so we can properly categorize and track your response.</p>
                
                <p>Best regards,<br>Security Team</p>
            </div>
        </body>
        </html>
        """
        
        return EmailTemplate(
            subject=subject,
            html_content=html_content,
            text_content=f"Clarification needed for {resource_name} security finding response.",
            resource_name=resource_name,
            policy_short_name=policy_name,
            policy_name=policy_name,
            severity=context_data.get('severity', 'medium'),
            native_type="clarification_request",
            ai_recommendations="Provide additional details for proper categorization",
            remediation_steps="Reply with requested clarification information",
            business_impact="Response processing on hold pending clarification",
            azure_commands="N/A"
        )
    
    async def _generate_information_response(self, email_content: str, context_data: Dict[str, Any]) -> EmailTemplate:
        """Generate information provided response template"""
        resource_name = context_data.get('resource_name', 'Unknown Resource')
        policy_name = context_data.get('policy_name', 'Security Policy')
        
        subject = f"📋 Information Received - {policy_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Information Received</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #4caf50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .success {{ background-color: #e8f5e8; border: 1px solid #4caf50; padding: 10px; margin: 10px 0; }}
                .resource-info {{ background-color: #f5f5f5; padding: 15px; margin: 10px 0; border-left: 4px solid #4caf50; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📋 Information Received</h1>
            </div>
            <div class="content">
                <p>Dear {context_data.get('owner_name', 'Resource Owner')},</p>
                
                <div class="success">
                    <strong>📋 Thank you for providing the requested information.</strong>
                </div>
                
                <div class="resource-info">
                    <h3>Finding Details:</h3>
                    <ul>
                        <li><strong>Resource:</strong> {resource_name}</li>
                        <li><strong>Policy:</strong> {policy_name}</li>
                        <li><strong>Severity:</strong> {context_data.get('severity', 'Unknown')}</li>
                    </ul>
                </div>
                
                <p>We have received and logged your detailed response. Our security team will review the information and update the finding status accordingly.</p>
                
                <p>You will receive a follow-up notification once the review is complete.</p>
                
                <p>Best regards,<br>Security Team</p>
            </div>
        </body>
        </html>
        """
        
        return EmailTemplate(
            subject=subject,
            html_content=html_content,
            text_content=f"Information received for {resource_name} security finding.",
            resource_name=resource_name,
            policy_short_name=policy_name,
            policy_name=policy_name,
            severity=context_data.get('severity', 'info'),
            native_type="information_received",
            ai_recommendations="Information logged for security team review",
            remediation_steps="No action required - information received",
            business_impact="Finding status will be updated after review",
            azure_commands="N/A"
        )
    
    async def _generate_escalation_response(self, email_content: str, context_data: Dict[str, Any]) -> EmailTemplate:
        """Generate escalation needed response template"""
        resource_name = context_data.get('resource_name', 'Unknown Resource')
        policy_name = context_data.get('policy_name', 'Security Policy')
        
        subject = f"🚨 Escalation Required - {policy_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Escalation Required</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #f44336; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .alert {{ background-color: #ffebee; border: 1px solid #f44336; padding: 10px; margin: 10px 0; }}
                .resource-info {{ background-color: #f5f5f5; padding: 15px; margin: 10px 0; border-left: 4px solid #f44336; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚨 Escalation Required</h1>
            </div>
            <div class="content">
                <p>Dear {context_data.get('owner_name', 'Resource Owner')},</p>
                
                <div class="alert">
                    <strong>🚨 This security finding requires escalation to senior management.</strong>
                </div>
                
                <div class="resource-info">
                    <h3>Finding Details:</h3>
                    <ul>
                        <li><strong>Resource:</strong> {resource_name}</li>
                        <li><strong>Policy:</strong> {policy_name}</li>
                        <li><strong>Severity:</strong> {context_data.get('severity', 'Unknown')}</li>
                    </ul>
                </div>
                
                <p>Based on your response, this issue has been escalated to senior management for review and decision.</p>
                
                <p>You will be contacted by a senior security team member within 24 hours to discuss next steps.</p>
                
                <p>Best regards,<br>Security Team</p>
            </div>
        </body>
        </html>
        """
        
        return EmailTemplate(
            subject=subject,
            html_content=html_content,
            text_content=f"Escalation required for {resource_name} security finding.",
            resource_name=resource_name,
            policy_short_name=policy_name,
            policy_name=policy_name,
            severity="high",
            native_type="escalation_required",
            ai_recommendations="Senior management review required",
            remediation_steps="Await contact from senior security team",
            business_impact="Issue escalated to management level",
            azure_commands="N/A"
        )
    
    async def _generate_resolution_response(self, email_content: str, context_data: Dict[str, Any]) -> EmailTemplate:
        """Generate resolution confirmation response template"""
        resource_name = context_data.get('resource_name', 'Unknown Resource')
        policy_name = context_data.get('policy_name', 'Security Policy')
        
        subject = f"✅ Issue Resolved - {policy_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Issue Resolved</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #4caf50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .success {{ background-color: #e8f5e8; border: 1px solid #4caf50; padding: 10px; margin: 10px 0; }}
                .resource-info {{ background-color: #f5f5f5; padding: 15px; margin: 10px 0; border-left: 4px solid #4caf50; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>✅ Issue Resolved</h1>
            </div>
            <div class="content">
                <p>Dear {context_data.get('owner_name', 'Resource Owner')},</p>
                
                <div class="success">
                    <strong>✅ The security finding has been marked as resolved.</strong>
                </div>
                
                <div class="resource-info">
                    <h3>Resolution Details:</h3>
                    <ul>
                        <li><strong>Resource:</strong> {resource_name}</li>
                        <li><strong>Policy:</strong> {policy_name}</li>
                        <li><strong>Resolution Date:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</li>
                    </ul>
                </div>
                
                <p>Thank you for addressing this security finding. The issue has been closed and no further action is required at this time.</p>
                
                <p>We will continue to monitor your resources for compliance with security policies.</p>
                
                <p>Best regards,<br>Security Team</p>
            </div>
        </body>
        </html>
        """
        
        return EmailTemplate(
            subject=subject,
            html_content=html_content,
            text_content=f"Security finding resolved for {resource_name}.",
            resource_name=resource_name,
            policy_short_name=policy_name,
            policy_name=policy_name,
            severity="info",
            native_type="resolution_confirmed",
            ai_recommendations="Issue resolved - no further action needed",
            remediation_steps="No action required - issue closed",
            business_impact="Security finding successfully resolved",
            azure_commands="N/A"
        )
    
    async def _generate_default_response(self, email_content: str, context_data: Dict[str, Any]) -> EmailTemplate:
        """Generate default response template"""
        resource_name = context_data.get('resource_name', 'Unknown Resource')
        policy_name = context_data.get('policy_name', 'Security Policy')
        
        subject = f"📧 Response Received - {policy_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Response Received</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #607d8b; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .info {{ background-color: #e0f2f1; border: 1px solid #607d8b; padding: 10px; margin: 10px 0; }}
                .resource-info {{ background-color: #f5f5f5; padding: 15px; margin: 10px 0; border-left: 4px solid #607d8b; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📧 Response Received</h1>
            </div>
            <div class="content">
                <p>Dear {context_data.get('owner_name', 'Resource Owner')},</p>
                
                <div class="info">
                    <strong>📧 We have received your response.</strong>
                </div>
                
                <div class="resource-info">
                    <h3>Finding Details:</h3>
                    <ul>
                        <li><strong>Resource:</strong> {resource_name}</li>
                        <li><strong>Policy:</strong> {policy_name}</li>
                        <li><strong>Severity:</strong> {context_data.get('severity', 'Unknown')}</li>
                    </ul>
                </div>
                
                <p>Your response has been received and will be reviewed by our security team. We will follow up if any additional action is required.</p>
                
                <p>Best regards,<br>Security Team</p>
            </div>
        </body>
        </html>
        """
        
        return EmailTemplate(
            subject=subject,
            html_content=html_content,
            text_content=f"Response received for {resource_name} security finding.",
            resource_name=resource_name,
            policy_short_name=policy_name,
            policy_name=policy_name,
            severity=context_data.get('severity', 'info'),
            native_type="default_response",
            ai_recommendations="Response logged for review",
            remediation_steps="No immediate action required",
            business_impact="Response tracking updated",
            azure_commands="N/A"
        )
    
    def _parse_analysis_fallback(self, analysis_text: str) -> Dict[str, Any]:
        """Fallback parsing for LLM analysis response"""
        try:
            # Simple keyword-based parsing
            should_respond = 'yes' in analysis_text.lower() or 'true' in analysis_text.lower()
            
            response_type = 'acknowledgment'  # default
            if 'clarification' in analysis_text.lower():
                response_type = 'clarification_request'
            elif 'escalation' in analysis_text.lower():
                response_type = 'escalation_needed'
            elif 'resolved' in analysis_text.lower():
                response_type = 'resolved'
            elif 'information' in analysis_text.lower():
                response_type = 'information_provided'
            
            return {
                'should_respond': should_respond,
                'response_type': response_type,
                'confidence_score': 0.7,  # moderate confidence for fallback
                'reason': 'Fallback parsing used',
                'suggested_actions': ['Review response manually']
            }
            
        except Exception as e:
            logger.error(f"Error in fallback parsing: {str(e)}")
            return {
                'should_respond': False,
                'response_type': 'error',
                'confidence_score': 0.0,
                'reason': 'Parsing failed',
                'suggested_actions': ['Manual review required']
            }
    
    async def send_llm_response(self, record_id: str, response_template: EmailTemplate) -> Dict[str, Any]:
        """Send LLM-generated response and update record"""
        try:
            # Get the email record
            record = await self._get_email_record_by_id(record_id)
            if not record:
                return {
                    'success': False,
                    'error': 'Record not found'
                }
            
            # Send the response email
            success = await self._send_reminder_email(record.owner_email, response_template)
            
            if success:
                # Update record with response information
                if not record.llm_analysis:
                    record.llm_analysis = {}
                
                record.llm_analysis.update({
                    'llm_response_sent': True,
                    'response_type': response_template.native_type,
                    'response_date': datetime.utcnow().isoformat(),
                    'response_subject': response_template.subject
                })
                
                record.status = EmailStatus.RESPONDED
                record.updated_at = datetime.utcnow()
                
                await self._save_email_record(record)
                
                return {
                    'success': True,
                    'record_id': record_id,
                    'response_sent': True,
                    'response_type': response_template.native_type
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to send response email'
                }
            
        except Exception as e:
            logger.error(f"Error sending LLM response: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def process_llm_responses_batch(self, email_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process multiple emails for LLM responses in batch"""
        try:
            processed_responses = []
            failed_responses = []
            
            for email_data in email_batch:
                try:
                    # Generate LLM response
                    response_result = await self.generate_llm_response(
                        email_data.get('email_content', ''),
                        email_data.get('context_data', {})
                    )
                    
                    if response_result.get('success') and response_result.get('should_respond'):
                        # Send the response
                        send_result = await self.send_llm_response(
                            email_data.get('record_id'),
                            response_result.get('response_template')
                        )
                        
                        if send_result.get('success'):
                            processed_responses.append({
                                'record_id': email_data.get('record_id'),
                                'response_type': response_result.get('response_type'),
                                'status': 'sent'
                            })
                        else:
                            failed_responses.append({
                                'record_id': email_data.get('record_id'),
                                'error': send_result.get('error', 'Unknown error')
                            })
                    else:
                        processed_responses.append({
                            'record_id': email_data.get('record_id'),
                            'response_type': 'no_response_needed',
                            'status': 'skipped',
                            'reason': response_result.get('reason', 'No response needed')
                        })
                        
                except Exception as e:
                    failed_responses.append({
                        'record_id': email_data.get('record_id', 'unknown'),
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'processed_count': len(processed_responses),
                'failed_count': len(failed_responses),
                'processed_responses': processed_responses,
                'failed_responses': failed_responses
            }
            
        except Exception as e:
            logger.error(f"Error processing LLM responses batch: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processed_count': 0,
                'failed_count': len(email_batch)
            }
    
    async def get_llm_response_statistics(self) -> Dict[str, Any]:
        """Get statistics for LLM responses"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get response statistics
            stats_query = """
                SELECT 
                    COUNT(*) as total_records,
                    SUM(CASE WHEN json_extract(llm_analysis, '$.llm_response_sent') = 'true' THEN 1 ELSE 0 END) as responses_sent,
                    SUM(CASE WHEN status = 'responded' THEN 1 ELSE 0 END) as responded_records
                FROM email_records
            """
            
            cursor.execute(stats_query)
            stats = cursor.fetchone()
            
            # Get response type breakdown
            type_query = """
                SELECT 
                    json_extract(llm_analysis, '$.response_type') as response_type,
                    COUNT(*) as count
                FROM email_records 
                WHERE json_extract(llm_analysis, '$.llm_response_sent') = 'true'
                GROUP BY json_extract(llm_analysis, '$.response_type')
            """
            
            cursor.execute(type_query)
            response_types = cursor.fetchall()
            
            conn.close()
            
            return {
                'success': True,
                'total_records': stats[0] if stats else 0,
                'responses_sent': stats[1] if stats else 0,
                'responded_records': stats[2] if stats else 0,
                'response_rate': (stats[1] / stats[0] * 100) if stats and stats[0] > 0 else 0,
                'response_types': {
                    row[0]: row[1] for row in response_types if row[0]
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting LLM response statistics: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'total_records': 0,
                'responses_sent': 0,
                'responded_records': 0,
                'response_rate': 0,
                'response_types': {}
            }
    
    async def get_bucket_statistics(self) -> Dict[str, Any]:
        """Get statistics for all email buckets"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get bucket counts
        cursor.execute("""
            SELECT bucket, COUNT(*) as count
            FROM email_records
            GROUP BY bucket
        """)
        
        bucket_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get status counts
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM email_records
            GROUP BY status
        """)
        
        status_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get reminder statistics
        cursor.execute("""
            SELECT 
                AVG(reminder_count) as avg_reminders,
                MAX(reminder_count) as max_reminders,
                COUNT(CASE WHEN reminder_count > 0 THEN 1 END) as records_with_reminders
            FROM email_records
        """)
        
        reminder_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'bucket_counts': bucket_counts,
            'status_counts': status_counts,
            'reminder_statistics': {
                'average_reminders': reminder_stats[0] or 0,
                'max_reminders': reminder_stats[1] or 0,
                'records_with_reminders': reminder_stats[2] or 0
            },
            'total_records': sum(bucket_counts.values())
        }
    
    async def get_records_by_bucket(self, bucket: EmailBucket, limit: int = 100) -> List[Dict[str, Any]]:
        """Get email records by bucket"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM email_records WHERE bucket = ? ORDER BY updated_at DESC LIMIT ?',
            (bucket.value, limit)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        records = []
        for row in rows:
            record = self._row_to_email_record(row)
            records.append(asdict(record))
        
        return records
    
    async def generate_llm_response(self, email_content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate LLM-powered response to email"""
        try:
            response_prompt = f"""
            Generate a professional email response based on the following context:
            
            Original Email: {email_content}
            
            Context:
            - Resource: {context.get('resource_name', 'Unknown')}
            - Policy: {context.get('policy_short_name', 'Unknown')}
            - Severity: {context.get('severity', 'Unknown')}
            - Owner: {context.get('owner_name', 'Unknown')}
            
            Generate a response that:
            1. Acknowledges the email
            2. Provides helpful information or next steps
            3. Maintains a professional tone
            4. Includes relevant security guidance if applicable
            
            Return the response in JSON format:
            {{
                "subject": "Response subject line",
                "content": "Email response content",
                "tone": "professional|helpful|urgent",
                "next_actions": ["list of suggested next actions"]
            }}
            """
            
            ai_response = await self.ai_service.generate_response(
                prompt=response_prompt,
                context="email_response_generation",
                max_tokens=800
            )
            
            try:
                response_data = json.loads(ai_response.get('response', '{}'))
            except json.JSONDecodeError:
                response_data = {
                    "subject": "Re: Security Finding Response",
                    "content": "Thank you for your response. We have received your message and will follow up accordingly.",
                    "tone": "professional",
                    "next_actions": ["Manual review required"]
                }
            
            return {
                'success': True,
                'response': response_data,
                'ai_provider': ai_response.get('provider'),
                'tokens_used': ai_response.get('tokens_used', 0)
            }
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'response': {
                    "subject": "Re: Security Finding Response",
                    "content": "Thank you for your response. We have received your message.",
                    "tone": "professional",
                    "next_actions": ["Manual review required"]
                }
            }

# Global service instance
email_management_service = EmailManagementService()