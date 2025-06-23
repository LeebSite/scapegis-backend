"""
Projects API endpoints
"""
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.services.project_service import ProjectService
from app.schemas.project import (
    CreateProjectRequest, 
    UpdateProjectRequest, 
    DuplicateProjectRequest,
    ProjectResponse,
    ProjectListResponse
)
from app.utils.responses import (
    success_response, 
    paginated_response, 
    not_found_response,
    error_response
)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/recent")
async def get_recent_projects(
    limit: int = Query(6, ge=1, le=50, description="Number of recent projects to return"),
    db: Session = Depends(get_db)
):
    """
    Get recent projects for dashboard
    
    Args:
        limit: Number of projects to return (default: 6)
        db: Database session
        
    Returns:
        List of recent projects
    """
    try:
        projects = await ProjectService.get_recent_projects(db, limit=limit)
        
        # Convert to response format
        project_data = [project.to_dict() for project in projects]
        
        return success_response(
            data=project_data,
            message="Recent projects retrieved successfully"
        )
        
    except Exception as e:
        raise error_response(f"Failed to retrieve recent projects: {str(e)}", status_code=500)


@router.get("/")
async def get_projects(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search query"),
    db: Session = Depends(get_db)
):
    """
    Get paginated projects with optional search
    
    Args:
        page: Page number (1-based)
        size: Page size
        search: Search query (optional)
        db: Database session
        
    Returns:
        Paginated list of projects
    """
    try:
        projects, total = await ProjectService.get_projects_paginated(
            db, page=page, size=size, search=search
        )
        
        # Convert to response format
        project_data = [project.to_dict() for project in projects]
        
        return paginated_response(
            items=project_data,
            total=total,
            page=page,
            size=size,
            message="Projects retrieved successfully"
        )
        
    except Exception as e:
        raise error_response(f"Failed to retrieve projects: {str(e)}", status_code=500)


@router.post("/")
async def create_project(
    project_data: CreateProjectRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new project
    
    Args:
        project_data: Project creation data
        db: Database session
        
    Returns:
        Created project
    """
    try:
        project = await ProjectService.create_project(db, project_data)
        
        return success_response(
            data=project.to_dict(),
            message="Project created successfully"
        )
        
    except Exception as e:
        raise error_response(f"Failed to create project: {str(e)}", status_code=500)


@router.get("/{project_id}")
async def get_project(
    project_id: str = Path(..., description="Project ID"),
    include_layers: bool = Query(True, description="Include layers in response"),
    db: Session = Depends(get_db)
):
    """
    Get project by ID
    
    Args:
        project_id: Project ID
        include_layers: Whether to include layers
        db: Database session
        
    Returns:
        Project details
    """
    try:
        project = await ProjectService.get_project_by_id(db, project_id, include_layers)
        
        if not project:
            raise not_found_response("Project", project_id)
        
        return success_response(
            data=project.to_dict(),
            message="Project retrieved successfully"
        )
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise not_found_response("Project", project_id)
        raise error_response(f"Failed to retrieve project: {str(e)}", status_code=500)


@router.put("/{project_id}")
async def update_project(
    project_id: str = Path(..., description="Project ID"),
    updates: UpdateProjectRequest = ...,
    db: Session = Depends(get_db)
):
    """
    Update project
    
    Args:
        project_id: Project ID
        updates: Update data
        db: Database session
        
    Returns:
        Updated project
    """
    try:
        project = await ProjectService.update_project(db, project_id, updates)
        
        if not project:
            raise not_found_response("Project", project_id)
        
        return success_response(
            data=project.to_dict(),
            message="Project updated successfully"
        )
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise not_found_response("Project", project_id)
        raise error_response(f"Failed to update project: {str(e)}", status_code=500)


@router.delete("/{project_id}")
async def delete_project(
    project_id: str = Path(..., description="Project ID"),
    db: Session = Depends(get_db)
):
    """
    Delete project
    
    Args:
        project_id: Project ID
        db: Database session
        
    Returns:
        Success confirmation
    """
    try:
        deleted = await ProjectService.delete_project(db, project_id)
        
        if not deleted:
            raise not_found_response("Project", project_id)
        
        return success_response(
            data={"deleted": True, "project_id": project_id},
            message="Project deleted successfully"
        )
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise not_found_response("Project", project_id)
        raise error_response(f"Failed to delete project: {str(e)}", status_code=500)


@router.post("/{project_id}/duplicate")
async def duplicate_project(
    project_id: str = Path(..., description="Project ID to duplicate"),
    duplicate_data: DuplicateProjectRequest = ...,
    db: Session = Depends(get_db)
):
    """
    Duplicate project
    
    Args:
        project_id: Original project ID
        duplicate_data: Duplication data
        db: Database session
        
    Returns:
        Duplicated project
    """
    try:
        new_project = await ProjectService.duplicate_project(db, project_id, duplicate_data)
        
        if not new_project:
            raise not_found_response("Project", project_id)
        
        return success_response(
            data=new_project.to_dict(),
            message="Project duplicated successfully"
        )
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise not_found_response("Project", project_id)
        raise error_response(f"Failed to duplicate project: {str(e)}", status_code=500)
