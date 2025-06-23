"""
Projects API endpoints using Supabase client directly
"""
from fastapi import APIRouter, Query, Path, HTTPException
from typing import Optional, List, Dict, Any
from app.core.database import supabase
from app.utils.responses import success_response, paginated_response, not_found_response, error_response
from datetime import datetime
import uuid

router = APIRouter(prefix="/projects-sb", tags=["Projects (Supabase)"])


@router.get("/recent")
async def get_recent_projects_supabase(
    limit: int = Query(6, ge=1, le=50, description="Number of recent projects to return")
):
    """
    Get recent projects using Supabase client directly
    """
    if not supabase:
        raise error_response("Supabase not configured", status_code=503)
    
    try:
        # Get recent projects
        response = supabase.table("projects").select("*").order("updated_at", desc=True).limit(limit).execute()
        
        projects = response.data or []
        
        # Format for frontend
        formatted_projects = []
        for project in projects:
            formatted_project = {
                "id": project["id"],
                "name": project["name"],
                "description": project.get("description"),
                "createdAt": project.get("created_at"),
                "updatedAt": project.get("updated_at"),
                "mapCenter": project.get("settings", {}).get("mapCenter", [0, 0]),
                "mapZoom": project.get("settings", {}).get("mapZoom", 2),
                "bounds": project.get("settings", {}).get("bounds"),
                "layer_count": project.get("layer_count", 0),
                "is_public": project.get("is_public", False),
                "layers": []  # Will be populated if needed
            }
            formatted_projects.append(formatted_project)
        
        return success_response(
            data=formatted_projects,
            message="Recent projects retrieved successfully"
        )
        
    except Exception as e:
        raise error_response(f"Failed to retrieve recent projects: {str(e)}", status_code=500)


@router.get("/")
async def get_projects_supabase(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search query")
):
    """
    Get paginated projects using Supabase client
    """
    if not supabase:
        raise error_response("Supabase not configured", status_code=503)
    
    try:
        # Calculate offset
        offset = (page - 1) * size
        
        # Build query
        query = supabase.table("projects").select("*")
        
        if search:
            # Simple search in name and description
            query = query.or_(f"name.ilike.%{search}%,description.ilike.%{search}%")
        
        # Get total count (simplified - in production you'd want a separate count query)
        total_response = supabase.table("projects").select("id", count="exact").execute()
        total = total_response.count or 0
        
        # Get paginated results
        response = query.order("updated_at", desc=True).range(offset, offset + size - 1).execute()
        
        projects = response.data or []
        
        # Format for frontend
        formatted_projects = []
        for project in projects:
            formatted_project = {
                "id": project["id"],
                "name": project["name"],
                "description": project.get("description"),
                "createdAt": project.get("created_at"),
                "updatedAt": project.get("updated_at"),
                "mapCenter": project.get("settings", {}).get("mapCenter", [0, 0]),
                "mapZoom": project.get("settings", {}).get("mapZoom", 2),
                "bounds": project.get("settings", {}).get("bounds"),
                "layer_count": project.get("layer_count", 0),
                "is_public": project.get("is_public", False)
            }
            formatted_projects.append(formatted_project)
        
        return paginated_response(
            items=formatted_projects,
            total=total,
            page=page,
            size=size,
            message="Projects retrieved successfully"
        )
        
    except Exception as e:
        raise error_response(f"Failed to retrieve projects: {str(e)}", status_code=500)


@router.post("/")
async def create_project_supabase(project_data: Dict[str, Any]):
    """
    Create a new project using Supabase client
    """
    if not supabase:
        raise error_response("Supabase not configured", status_code=503)
    
    try:
        # Prepare project data
        new_project = {
            "name": project_data.get("name", "New Project"),
            "description": project_data.get("description"),
            "settings": {
                "mapCenter": project_data.get("mapCenter", [0, 0]),
                "mapZoom": project_data.get("mapZoom", 2),
                "bounds": project_data.get("bounds")
            },
            "zoom_level": project_data.get("mapZoom", 2),
            "is_public": project_data.get("is_public", False),
            "layer_count": 1  # Will have default base layer
        }
        
        # Insert project
        response = supabase.table("projects").insert(new_project).execute()
        
        if not response.data:
            raise error_response("Failed to create project", status_code=500)
        
        project = response.data[0]
        project_id = project["id"]
        
        # Create default base layer
        default_layer = {
            "name": "OpenStreetMap",
            "description": "Default OpenStreetMap base layer",
            "project_id": project_id,
            "layer_type": "base",
            "data_source": "openstreetmap",
            "style_config": {
                "type": "raster",
                "source": {
                    "type": "raster",
                    "tiles": ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
                    "tileSize": 256,
                    "attribution": "© OpenStreetMap contributors"
                }
            },
            "is_visible": True,
            "opacity": 1.0,
            "z_index": 0,
            "feature_count": 0
        }
        
        # Insert default layer
        layer_response = supabase.table("layers").insert(default_layer).execute()
        
        # Format response
        formatted_project = {
            "id": project["id"],
            "name": project["name"],
            "description": project.get("description"),
            "createdAt": project.get("created_at"),
            "updatedAt": project.get("updated_at"),
            "mapCenter": project.get("settings", {}).get("mapCenter", [0, 0]),
            "mapZoom": project.get("settings", {}).get("mapZoom", 2),
            "bounds": project.get("settings", {}).get("bounds"),
            "layer_count": project.get("layer_count", 1),
            "is_public": project.get("is_public", False),
            "layers": [default_layer] if layer_response.data else []
        }
        
        return success_response(
            data=formatted_project,
            message="Project created successfully"
        )
        
    except Exception as e:
        raise error_response(f"Failed to create project: {str(e)}", status_code=500)


@router.get("/{project_id}")
async def get_project_supabase(
    project_id: str = Path(..., description="Project ID"),
    include_layers: bool = Query(True, description="Include layers in response")
):
    """
    Get project by ID using Supabase client
    """
    if not supabase:
        raise error_response("Supabase not configured", status_code=503)
    
    try:
        # Get project
        response = supabase.table("projects").select("*").eq("id", project_id).execute()
        
        if not response.data:
            raise not_found_response("Project", project_id)
        
        project = response.data[0]
        
        # Get layers if requested
        layers = []
        if include_layers:
            layers_response = supabase.table("layers").select("*").eq("project_id", project_id).order("z_index").execute()
            layers = layers_response.data or []
        
        # Update last accessed
        supabase.table("projects").update({"last_accessed": datetime.now().isoformat()}).eq("id", project_id).execute()
        
        # Format response
        formatted_project = {
            "id": project["id"],
            "name": project["name"],
            "description": project.get("description"),
            "createdAt": project.get("created_at"),
            "updatedAt": project.get("updated_at"),
            "mapCenter": project.get("settings", {}).get("mapCenter", [0, 0]),
            "mapZoom": project.get("settings", {}).get("mapZoom", 2),
            "bounds": project.get("settings", {}).get("bounds"),
            "layer_count": project.get("layer_count", 0),
            "is_public": project.get("is_public", False),
            "layers": [
                {
                    "id": layer["id"],
                    "name": layer["name"],
                    "type": layer["layer_type"],
                    "visible": layer["is_visible"],
                    "opacity": layer["opacity"],
                    "source": layer["data_source"],
                    "style": layer["style_config"]
                }
                for layer in layers
            ]
        }
        
        return success_response(
            data=formatted_project,
            message="Project retrieved successfully"
        )
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise not_found_response("Project", project_id)
        raise error_response(f"Failed to retrieve project: {str(e)}", status_code=500)
