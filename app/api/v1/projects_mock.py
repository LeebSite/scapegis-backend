"""
Mock Projects API endpoints for testing without database
"""
from fastapi import APIRouter, Query, Path
from typing import Optional, List, Dict, Any
from app.utils.responses import success_response, paginated_response, not_found_response
from datetime import datetime
import uuid

router = APIRouter(prefix="/projects-mock", tags=["Projects (Mock)"])

# Mock data for testing
MOCK_PROJECTS = [
    {
        "id": str(uuid.uuid4()),
        "name": "Sample WebGIS Project",
        "description": "A sample project for testing the WebGIS application",
        "createdAt": "2024-01-15T10:30:00Z",
        "updatedAt": "2024-01-20T14:45:00Z",
        "mapCenter": [106.8456, -6.2088],
        "mapZoom": 10,
        "bounds": [[106.7, -6.3], [106.9, -6.1]],
        "layer_count": 1,
        "is_public": True,
        "layers": [
            {
                "id": str(uuid.uuid4()),
                "name": "OpenStreetMap Base",
                "type": "base",
                "visible": True,
                "opacity": 1.0,
                "source": "openstreetmap",
                "style": {
                    "type": "raster",
                    "source": {
                        "type": "raster",
                        "tiles": ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
                        "tileSize": 256
                    }
                }
            }
        ]
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Jakarta Map Project",
        "description": "Jakarta city mapping project with detailed layers",
        "createdAt": "2024-01-10T09:15:00Z",
        "updatedAt": "2024-01-18T16:20:00Z",
        "mapCenter": [106.8456, -6.2088],
        "mapZoom": 12,
        "bounds": [[106.7, -6.3], [106.9, -6.1]],
        "layer_count": 2,
        "is_public": False,
        "layers": [
            {
                "id": str(uuid.uuid4()),
                "name": "Jakarta Roads",
                "type": "vector",
                "visible": True,
                "opacity": 0.8,
                "source": "jakarta_roads",
                "style": {"type": "line", "paint": {"line-color": "#ff6b6b", "line-width": 2}}
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Jakarta Buildings",
                "type": "vector",
                "visible": False,
                "opacity": 0.6,
                "source": "jakarta_buildings",
                "style": {"type": "fill", "paint": {"fill-color": "#4ecdc4", "fill-opacity": 0.6}}
            }
        ]
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Indonesia Overview",
        "description": "National overview map of Indonesia",
        "createdAt": "2024-01-05T08:00:00Z",
        "updatedAt": "2024-01-15T12:30:00Z",
        "mapCenter": [118.0148, -2.5489],
        "mapZoom": 5,
        "bounds": [[95, -11], [141, 6]],
        "layer_count": 1,
        "is_public": True,
        "layers": [
            {
                "id": str(uuid.uuid4()),
                "name": "Indonesia Provinces",
                "type": "vector",
                "visible": True,
                "opacity": 0.7,
                "source": "indonesia_provinces",
                "style": {"type": "fill", "paint": {"fill-color": "#45b7d1", "fill-opacity": 0.3}}
            }
        ]
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Bandung City Map",
        "description": "Detailed map of Bandung city",
        "createdAt": "2024-01-12T11:45:00Z",
        "updatedAt": "2024-01-19T15:10:00Z",
        "mapCenter": [107.6191, -6.9175],
        "mapZoom": 11,
        "bounds": [[107.5, -7.0], [107.7, -6.8]],
        "layer_count": 3,
        "is_public": False,
        "layers": []
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Surabaya Port Area",
        "description": "Port and industrial area mapping",
        "createdAt": "2024-01-08T13:20:00Z",
        "updatedAt": "2024-01-17T10:55:00Z",
        "mapCenter": [112.7521, -7.2575],
        "mapZoom": 13,
        "bounds": [[112.7, -7.3], [112.8, -7.2]],
        "layer_count": 2,
        "is_public": True,
        "layers": []
    }
]


@router.get("/recent")
async def get_recent_projects_mock(
    limit: int = Query(6, ge=1, le=50, description="Number of recent projects to return")
):
    """
    Get recent projects (mock data)
    """
    # Sort by updatedAt and limit
    sorted_projects = sorted(MOCK_PROJECTS, key=lambda x: x["updatedAt"], reverse=True)
    recent_projects = sorted_projects[:limit]
    
    return success_response(
        data=recent_projects,
        message="Recent projects retrieved successfully"
    )


@router.get("/")
async def get_projects_mock(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search query")
):
    """
    Get paginated projects (mock data)
    """
    projects = MOCK_PROJECTS.copy()
    
    # Apply search filter
    if search:
        search_lower = search.lower()
        projects = [
            p for p in projects 
            if search_lower in p["name"].lower() or 
               search_lower in (p["description"] or "").lower()
        ]
    
    total = len(projects)
    
    # Apply pagination
    start = (page - 1) * size
    end = start + size
    paginated_projects = projects[start:end]
    
    return paginated_response(
        items=paginated_projects,
        total=total,
        page=page,
        size=size,
        message="Projects retrieved successfully"
    )


@router.post("/")
async def create_project_mock(project_data: Dict[str, Any]):
    """
    Create a new project (mock)
    """
    new_project = {
        "id": str(uuid.uuid4()),
        "name": project_data.get("name", "New Project"),
        "description": project_data.get("description", ""),
        "createdAt": datetime.now().isoformat() + "Z",
        "updatedAt": datetime.now().isoformat() + "Z",
        "mapCenter": project_data.get("mapCenter", [0, 0]),
        "mapZoom": project_data.get("mapZoom", 2),
        "bounds": project_data.get("bounds"),
        "layer_count": 1,
        "is_public": project_data.get("is_public", False),
        "layers": [
            {
                "id": str(uuid.uuid4()),
                "name": "OpenStreetMap Base",
                "type": "base",
                "visible": True,
                "opacity": 1.0,
                "source": "openstreetmap",
                "style": {
                    "type": "raster",
                    "source": {
                        "type": "raster",
                        "tiles": ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
                        "tileSize": 256
                    }
                }
            }
        ]
    }
    
    # Add to mock data (in memory only)
    MOCK_PROJECTS.append(new_project)
    
    return success_response(
        data=new_project,
        message="Project created successfully"
    )


@router.get("/{project_id}")
async def get_project_mock(
    project_id: str = Path(..., description="Project ID"),
    include_layers: bool = Query(True, description="Include layers in response")
):
    """
    Get project by ID (mock)
    """
    project = next((p for p in MOCK_PROJECTS if p["id"] == project_id), None)
    
    if not project:
        raise not_found_response("Project", project_id)
    
    if not include_layers:
        project_copy = project.copy()
        project_copy["layers"] = []
        return success_response(
            data=project_copy,
            message="Project retrieved successfully"
        )
    
    return success_response(
        data=project,
        message="Project retrieved successfully"
    )
