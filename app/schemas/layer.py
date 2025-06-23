"""
Layer Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum


class LayerType(str, Enum):
    """Layer type enumeration"""
    BASE = "base"
    VECTOR = "vector"
    RASTER = "raster"
    POINT = "point"


class CreateLayerRequest(BaseModel):
    """Schema for creating a new layer"""
    name: str = Field(..., min_length=1, max_length=100, description="Layer name")
    description: Optional[str] = Field(None, description="Layer description")
    project_id: str = Field(..., description="Project ID this layer belongs to")
    layer_type: LayerType = Field(..., description="Layer type")
    data_source: Optional[str] = Field(None, description="Data source URL or path")
    style_config: Optional[Dict[str, Any]] = Field({}, description="Layer style configuration")
    is_visible: Optional[bool] = Field(True, description="Whether layer is visible")
    opacity: Optional[float] = Field(1.0, ge=0.0, le=1.0, description="Layer opacity")
    z_index: Optional[int] = Field(0, description="Layer z-index for ordering")


class UpdateLayerRequest(BaseModel):
    """Schema for updating a layer"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Layer name")
    description: Optional[str] = Field(None, description="Layer description")
    layer_type: Optional[LayerType] = Field(None, description="Layer type")
    data_source: Optional[str] = Field(None, description="Data source URL or path")
    style_config: Optional[Dict[str, Any]] = Field(None, description="Layer style configuration")
    is_visible: Optional[bool] = Field(None, description="Whether layer is visible")
    opacity: Optional[float] = Field(None, ge=0.0, le=1.0, description="Layer opacity")
    z_index: Optional[int] = Field(None, description="Layer z-index for ordering")


class LayerResponse(BaseModel):
    """Schema for layer response"""
    id: str
    name: str
    description: Optional[str]
    project_id: str
    layer_type: str
    data_source: Optional[str]
    style_config: Dict[str, Any]
    is_visible: bool
    opacity: float
    z_index: int
    feature_count: int
    created_at: Optional[str]
    updated_at: Optional[str]


class LayerFrontendResponse(BaseModel):
    """Schema for frontend layer response"""
    id: str
    name: str
    type: str
    visible: bool
    opacity: float
    source: Optional[str]
    style: Dict[str, Any]
