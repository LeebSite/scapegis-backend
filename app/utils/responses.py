"""
Response utilities for consistent API responses
"""
import math
from typing import Any, List, Dict, Optional
from fastapi import HTTPException


def success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
    """
    Create a successful API response
    
    Args:
        data: The response data
        message: Success message
        
    Returns:
        Formatted success response
    """
    return {
        "status": "success",
        "data": data,
        "message": message
    }


def error_response(message: str, status_code: int = 400, details: Optional[Dict] = None) -> HTTPException:
    """
    Create an error response
    
    Args:
        message: Error message
        status_code: HTTP status code
        details: Additional error details
        
    Returns:
        HTTPException with formatted error
    """
    error_data = {
        "status": "error",
        "message": message
    }
    
    if details:
        error_data["details"] = details
        
    return HTTPException(status_code=status_code, detail=error_data)


def paginated_response(
    items: List[Any], 
    total: int, 
    page: int, 
    size: int,
    message: str = "Data retrieved successfully"
) -> Dict[str, Any]:
    """
    Create a paginated API response
    
    Args:
        items: List of items for current page
        total: Total number of items
        page: Current page number
        size: Page size
        message: Success message
        
    Returns:
        Formatted paginated response
    """
    pages = math.ceil(total / size) if size > 0 else 0
    
    return {
        "status": "success",
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        },
        "message": message
    }


def not_found_response(resource: str, resource_id: str = None) -> HTTPException:
    """
    Create a not found error response
    
    Args:
        resource: Name of the resource (e.g., "Project", "Layer")
        resource_id: ID of the resource if available
        
    Returns:
        HTTPException with 404 status
    """
    if resource_id:
        message = f"{resource} with ID '{resource_id}' not found"
    else:
        message = f"{resource} not found"
        
    return error_response(message, status_code=404)


def validation_error_response(errors: List[Dict]) -> HTTPException:
    """
    Create a validation error response
    
    Args:
        errors: List of validation errors
        
    Returns:
        HTTPException with 422 status
    """
    return error_response(
        message="Validation failed",
        status_code=422,
        details={"validation_errors": errors}
    )


def unauthorized_response(message: str = "Unauthorized access") -> HTTPException:
    """
    Create an unauthorized error response
    
    Args:
        message: Error message
        
    Returns:
        HTTPException with 401 status
    """
    return error_response(message, status_code=401)


def forbidden_response(message: str = "Access forbidden") -> HTTPException:
    """
    Create a forbidden error response
    
    Args:
        message: Error message
        
    Returns:
        HTTPException with 403 status
    """
    return error_response(message, status_code=403)


def server_error_response(message: str = "Internal server error") -> HTTPException:
    """
    Create a server error response
    
    Args:
        message: Error message
        
    Returns:
        HTTPException with 500 status
    """
    return error_response(message, status_code=500)
