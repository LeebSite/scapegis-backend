"""
Layer Service - Business logic for layer operations
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.layer import Layer
from app.models.project import Project
from app.schemas.layer import CreateLayerRequest, UpdateLayerRequest
from datetime import datetime, timezone


class LayerService:
    """Service class for layer operations"""
    
    @staticmethod
    async def get_layers_by_project(db: Session, project_id: str) -> List[Layer]:
        """
        Get all layers for a project
        
        Args:
            db: Database session
            project_id: Project ID
            
        Returns:
            List of layers
        """
        layers = db.query(Layer).filter(Layer.project_id == project_id).order_by(Layer.z_index, Layer.created_at).all()
        return layers
    
    @staticmethod
    async def get_layer_by_id(db: Session, layer_id: str) -> Optional[Layer]:
        """
        Get layer by ID
        
        Args:
            db: Database session
            layer_id: Layer ID
            
        Returns:
            Layer or None if not found
        """
        layer = db.query(Layer).filter(Layer.id == layer_id).first()
        return layer
    
    @staticmethod
    async def create_layer(db: Session, layer_data: CreateLayerRequest) -> Layer:
        """
        Create a new layer
        
        Args:
            db: Database session
            layer_data: Layer creation data
            
        Returns:
            Created layer
        """
        # Create layer
        layer = Layer(
            name=layer_data.name,
            description=layer_data.description,
            project_id=layer_data.project_id,
            layer_type=layer_data.layer_type.value,
            data_source=layer_data.data_source,
            style_config=layer_data.style_config or {},
            is_visible=layer_data.is_visible,
            opacity=layer_data.opacity,
            z_index=layer_data.z_index,
            feature_count=0
        )
        
        db.add(layer)
        db.commit()
        db.refresh(layer)
        
        # Update project layer count
        await LayerService._update_project_layer_count(db, layer_data.project_id)
        
        return layer
    
    @staticmethod
    async def create_default_base_layer(db: Session, project_id: str) -> Layer:
        """
        Create default base layer for a project
        
        Args:
            db: Database session
            project_id: Project ID
            
        Returns:
            Created base layer
        """
        layer = Layer(
            name="OpenStreetMap",
            description="Default OpenStreetMap base layer",
            project_id=project_id,
            layer_type="base",
            data_source="openstreetmap",
            style_config={
                "type": "raster",
                "source": {
                    "type": "raster",
                    "tiles": ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
                    "tileSize": 256,
                    "attribution": "© OpenStreetMap contributors"
                }
            },
            is_visible=True,
            opacity=1.0,
            z_index=0,
            feature_count=0
        )
        
        db.add(layer)
        db.commit()
        db.refresh(layer)
        
        return layer
    
    @staticmethod
    async def update_layer(db: Session, layer_id: str, updates: UpdateLayerRequest) -> Optional[Layer]:
        """
        Update layer
        
        Args:
            db: Database session
            layer_id: Layer ID
            updates: Update data
            
        Returns:
            Updated layer or None if not found
        """
        layer = db.query(Layer).filter(Layer.id == layer_id).first()
        
        if not layer:
            return None
        
        # Update fields
        update_data = updates.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "layer_type" and hasattr(value, "value"):
                setattr(layer, field, value.value)
            else:
                setattr(layer, field, value)
        
        layer.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(layer)
        
        return layer
    
    @staticmethod
    async def delete_layer(db: Session, layer_id: str) -> bool:
        """
        Delete layer
        
        Args:
            db: Database session
            layer_id: Layer ID
            
        Returns:
            True if deleted, False if not found
        """
        layer = db.query(Layer).filter(Layer.id == layer_id).first()
        
        if not layer:
            return False
        
        project_id = layer.project_id
        
        db.delete(layer)
        db.commit()
        
        # Update project layer count
        await LayerService._update_project_layer_count(db, project_id)
        
        return True
    
    @staticmethod
    async def duplicate_layer(db: Session, original_layer: Layer, new_project_id: str) -> Layer:
        """
        Duplicate a layer to another project
        
        Args:
            db: Database session
            original_layer: Original layer to duplicate
            new_project_id: Target project ID
            
        Returns:
            Duplicated layer
        """
        new_layer = Layer(
            name=f"{original_layer.name} (Copy)",
            description=original_layer.description,
            project_id=new_project_id,
            layer_type=original_layer.layer_type,
            data_source=original_layer.data_source,
            style_config=original_layer.style_config.copy() if original_layer.style_config else {},
            is_visible=original_layer.is_visible,
            opacity=original_layer.opacity,
            z_index=original_layer.z_index,
            feature_count=original_layer.feature_count
        )
        
        db.add(new_layer)
        db.commit()
        db.refresh(new_layer)
        
        return new_layer
    
    @staticmethod
    async def _update_project_layer_count(db: Session, project_id: str):
        """
        Update project layer count
        
        Args:
            db: Database session
            project_id: Project ID
        """
        count = db.query(func.count(Layer.id)).filter(Layer.project_id == project_id).scalar()
        
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.layer_count = count
            project.updated_at = datetime.now(timezone.utc)
            db.commit()
