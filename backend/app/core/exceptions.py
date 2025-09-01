"""
Custom exceptions for Securra application
"""
from fastapi import HTTPException


class SecurraException(HTTPException):
    """Base exception for Securra application"""
    
    def __init__(self, detail: str, status_code: int = 400, code: str = None):
        super().__init__(status_code=status_code, detail=detail)
        self.code = code


class AuthenticationError(SecurraException):
    """Authentication related errors"""
    
    def __init__(self, detail: str = "Authentication failed", code: str = "AUTH_ERROR"):
        super().__init__(detail=detail, status_code=401, code=code)


class AuthorizationError(SecurraException):
    """Authorization related errors"""
    
    def __init__(self, detail: str = "Access denied", code: str = "AUTHZ_ERROR"):
        super().__init__(detail=detail, status_code=403, code=code)


class ValidationError(SecurraException):
    """Validation related errors"""
    
    def __init__(self, detail: str = "Validation failed", code: str = "VALIDATION_ERROR"):
        super().__init__(detail=detail, status_code=422, code=code)


class ResourceNotFoundError(SecurraException):
    """Resource not found errors"""
    
    def __init__(self, detail: str = "Resource not found", code: str = "NOT_FOUND"):
        super().__init__(detail=detail, status_code=404, code=code)


class ScanError(SecurraException):
    """Scan related errors"""
    
    def __init__(self, detail: str = "Scan operation failed", code: str = "SCAN_ERROR"):
        super().__init__(detail=detail, status_code=500, code=code)


class AIAnalysisError(SecurraException):
    """AI analysis related errors"""
    
    def __init__(self, detail: str = "AI analysis failed", code: str = "AI_ERROR"):
        super().__init__(detail=detail, status_code=500, code=code)


class ReportGenerationError(SecurraException):
    """Report generation related errors"""
    
    def __init__(self, detail: str = "Report generation failed", code: str = "REPORT_ERROR"):
        super().__init__(detail=detail, status_code=500, code=code)


class RateLimitError(SecurraException):
    """Rate limiting errors"""
    
    def __init__(self, detail: str = "Rate limit exceeded", code: str = "RATE_LIMIT"):
        super().__init__(detail=detail, status_code=429, code=code)
