"""
Layers API endpoints
"""
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.services.layer_service import LayerService
from app.schemas.layer import (
    CreateLayerRequest,
    UpdateLayerRequest,
    LayerResponse,
    LayerFrontendResponse
)
from app.utils.responses import (
    success_response,
    not_found_response,
    error_response
)

router = APIRouter(prefix="/layers", tags=["Layers"])


@router.get("/")
async def get_layers(
    project_id: str = Query(..., description="Project ID to get layers for"),
    db: Session = Depends(get_db)
):
    """
    Get all layers for a project
    
    Args:
        project_id: Project ID
        db: Database session
        
    Returns:
        List of layers for the project
    """
    try:
        layers = await LayerService.get_layers_by_project(db, project_id)
        
        # Convert to response format
        layer_data = [layer.to_dict() for layer in layers]
        
        return success_response(
            data=layer_data,
            message="Layers retrieved successfully"
        )
        
    except Exception as e:
        raise error_response(f"Failed to retrieve layers: {str(e)}", status_code=500)


@router.get("/{layer_id}")
async def get_layer(
    layer_id: str = Path(..., description="Layer ID"),
    db: Session = Depends(get_db)
):
    """
    Get layer by ID
    
    Args:
        layer_id: Layer ID
        db: Database session
        
    Returns:
        Layer details
    """
    try:
        layer = await LayerService.get_layer_by_id(db, layer_id)
        
        if not layer:
            raise not_found_response("Layer", layer_id)
        
        return success_response(
            data=layer.to_dict(),
            message="Layer retrieved successfully"
        )
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise not_found_response("Layer", layer_id)
        raise error_response(f"Failed to retrieve layer: {str(e)}", status_code=500)


@router.post("/")
async def create_layer(
    layer_data: CreateLayerRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new layer
    
    Args:
        layer_data: Layer creation data
        db: Database session
        
    Returns:
        Created layer
    """
    try:
        layer = await LayerService.create_layer(db, layer_data)
        
        return success_response(
            data=layer.to_dict(),
            message="Layer created successfully"
        )
        
    except Exception as e:
        raise error_response(f"Failed to create layer: {str(e)}", status_code=500)


@router.put("/{layer_id}")
async def update_layer(
    layer_id: str = Path(..., description="Layer ID"),
    updates: UpdateLayerRequest = ...,
    db: Session = Depends(get_db)
):
    """
    Update layer
    
    Args:
        layer_id: Layer ID
        updates: Update data
        db: Database session
        
    Returns:
        Updated layer
    """
    try:
        layer = await LayerService.update_layer(db, layer_id, updates)
        
        if not layer:
            raise not_found_response("Layer", layer_id)
        
        return success_response(
            data=layer.to_dict(),
            message="Layer updated successfully"
        )
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise not_found_response("Layer", layer_id)
        raise error_response(f"Failed to update layer: {str(e)}", status_code=500)


@router.delete("/{layer_id}")
async def delete_layer(
    layer_id: str = Path(..., description="Layer ID"),
    db: Session = Depends(get_db)
):
    """
    Delete layer
    
    Args:
        layer_id: Layer ID
        db: Database session
        
    Returns:
        Success confirmation
    """
    try:
        deleted = await LayerService.delete_layer(db, layer_id)
        
        if not deleted:
            raise not_found_response("Layer", layer_id)
        
        return success_response(
            data={"deleted": True, "layer_id": layer_id},
            message="Layer deleted successfully"
        )
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise not_found_response("Layer", layer_id)
        raise error_response(f"Failed to delete layer: {str(e)}", status_code=500)


@router.post("/{layer_id}/upload")
async def upload_layer_data(
    layer_id: str = Path(..., description="Layer ID"),
    db: Session = Depends(get_db)
):
    """
    Upload data to layer (placeholder for future implementation)
    
    Args:
        layer_id: Layer ID
        db: Database session
        
    Returns:
        Upload status
    """
    try:
        layer = await LayerService.get_layer_by_id(db, layer_id)
        
        if not layer:
            raise not_found_response("Layer", layer_id)
        
        # TODO: Implement file upload logic
        # This is a placeholder for future file upload functionality
        
        return success_response(
            data={
                "layer_id": layer_id,
                "upload_status": "not_implemented",
                "message": "File upload functionality will be implemented in future version"
            },
            message="Upload endpoint ready (not implemented yet)"
        )
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise not_found_response("Layer", layer_id)
        raise error_response(f"Failed to upload layer data: {str(e)}", status_code=500)
