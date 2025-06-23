"""
Project Model
"""
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import Optional, List, Dict, Any
# from geoalchemy2 import Geometry  # Will be enabled after GDAL installation
from app.core.database import Base


class Project(Base):
    """Project model for WebGIS projects"""
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(100), nullable=False)
    description = Column(Text)
    workspace_id = Column(UUID(as_uuid=True))
    owner_id = Column(UUID(as_uuid=True))  # References auth.users(id)
    settings = Column(JSONB, default={})  # stores mapCenter, mapZoom, bounds
    # bounds = Column(Geometry('POLYGON', srid=4326))  # Will be enabled with GDAL
    # center = Column(Geometry('POINT', srid=4326))    # Will be enabled with GDAL
    zoom_level = Column(Integer, default=2)
    is_public = Column(Boolean, default=False)
    layer_count = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    layers = relationship("Layer", back_populates="project", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        # Extract map settings from settings JSONB
        settings = self.settings or {}
        map_center = settings.get('mapCenter', [0, 0])
        map_zoom = settings.get('mapZoom', self.zoom_level)
        bounds = settings.get('bounds')
        
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "workspace_id": str(self.workspace_id) if self.workspace_id else None,
            "owner_id": str(self.owner_id) if self.owner_id else None,
            "settings": settings,
            "mapCenter": map_center,
            "mapZoom": map_zoom,
            "bounds": bounds,
            "zoom_level": self.zoom_level,
            "is_public": self.is_public,
            "layer_count": self.layer_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "layers": [layer.to_dict() for layer in self.layers] if hasattr(self, 'layers') and self.layers else []
        }
    
    def to_frontend_format(self) -> Dict[str, Any]:
        """Convert to frontend Project interface format"""
        settings = self.settings or {}
        map_center = settings.get('mapCenter', [0, 0])
        map_zoom = settings.get('mapZoom', self.zoom_level)
        bounds = settings.get('bounds')
        
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            "mapCenter": map_center,
            "mapZoom": map_zoom,
            "bounds": bounds,
            "layers": [layer.to_frontend_format() for layer in self.layers] if hasattr(self, 'layers') and self.layers else []
        }
