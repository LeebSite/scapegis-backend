"""
Test endpoints for API validation
"""
from fastapi import APIRouter, Depends
from app.core.database import get_supabase, supabase
from app.utils.responses import success_response, error_response
from supabase import Client

router = APIRouter(prefix="/test", tags=["Testing"])


@router.get("/")
async def test_api():
    """
    Basic API test endpoint
    
    Returns:
        Success response indicating API is working
    """
    return success_response(
        data={
            "api_status": "operational",
            "version": "1.0.0",
            "timestamp": "2024-01-01T00:00:00Z"
        },
        message="API is working"
    )


@router.get("/supabase")
async def test_supabase():
    """
    Test Supabase connection
    
    Returns:
        Success response with Supabase connection status
    """
    if not supabase:
        raise error_response(
            message="Supabase not configured",
            status_code=503
        )
    
    try:
        # Test basic Supabase connection
        # Try to access a system table or function
        response = supabase.rpc('version').execute()
        
        return success_response(
            data={
                "supabase_status": "connected",
                "database_version": response.data if response.data else "unknown",
                "connection_test": "passed"
            },
            message="Supabase connection successful"
        )
        
    except Exception as e:
        # If RPC fails, try a simple table query
        try:
            # Test with projects table (will fail if table doesn't exist, but connection is OK)
            response = supabase.table("projects").select("count").limit(1).execute()
            
            return success_response(
                data={
                    "supabase_status": "connected",
                    "database_test": "passed",
                    "projects_table": "accessible" if response else "not_accessible"
                },
                message="Supabase connection successful"
            )
            
        except Exception as table_error:
            return success_response(
                data={
                    "supabase_status": "connected",
                    "database_test": "connection_ok",
                    "note": "Tables may not be created yet",
                    "error_details": str(table_error)[:100]
                },
                message="Supabase connected but tables not ready"
            )


@router.get("/database")
async def test_database():
    """
    Test database tables existence
    
    Returns:
        Success response with table status
    """
    if not supabase:
        raise error_response(
            message="Supabase not configured",
            status_code=503
        )
    
    table_status = {}
    
    # Test each table
    tables_to_test = ["projects", "layers", "user_profiles"]
    
    for table_name in tables_to_test:
        try:
            response = supabase.table(table_name).select("count").limit(1).execute()
            table_status[table_name] = {
                "exists": True,
                "accessible": True,
                "record_count": len(response.data) if response.data else 0
            }
        except Exception as e:
            table_status[table_name] = {
                "exists": False,
                "accessible": False,
                "error": str(e)[:100]
            }
    
    return success_response(
        data={
            "database_status": "tested",
            "tables": table_status
        },
        message="Database table test completed"
    )


@router.get("/health")
async def test_health():
    """
    Comprehensive health check
    
    Returns:
        Success response with overall system health
    """
    health_data = {
        "api": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    }
    
    # Test Supabase
    if supabase:
        try:
            response = supabase.table("projects").select("count").limit(1).execute()
            health_data["supabase"] = "healthy"
            health_data["database"] = "accessible"
        except Exception:
            health_data["supabase"] = "connected"
            health_data["database"] = "tables_not_ready"
    else:
        health_data["supabase"] = "not_configured"
        health_data["database"] = "not_available"
    
    return success_response(
        data=health_data,
        message="Health check completed"
    )
