"""
Layer Model
"""
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import Dict, Any
# from geoalchemy2 import Geometry  # Will be enabled after GDAL installation
from app.core.database import Base


class Layer(Base):
    """Layer model for WebGIS layers"""
    __tablename__ = "layers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(100), nullable=False)
    description = Column(Text)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    layer_type = Column(String(20), nullable=False)  # 'base', 'vector', 'raster', 'point'
    data_source = Column(Text)
    style_config = Column(JSONB, default={})
    is_visible = Column(Boolean, default=True)
    opacity = Column(Float, default=1.0)
    z_index = Column(Integer, default=0)
    # bounds = Column(Geometry('POLYGON', srid=4326))  # Will be enabled with GDAL
    feature_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="layers")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "project_id": str(self.project_id),
            "layer_type": self.layer_type,
            "data_source": self.data_source,
            "style_config": self.style_config or {},
            "is_visible": self.is_visible,
            "opacity": self.opacity,
            "z_index": self.z_index,
            "feature_count": self.feature_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def to_frontend_format(self) -> Dict[str, Any]:
        """Convert to frontend Layer interface format"""
        return {
            "id": str(self.id),
            "name": self.name,
            "type": self.layer_type,
            "visible": self.is_visible,
            "opacity": self.opacity,
            "source": self.data_source,
            "style": self.style_config or {}
        }
