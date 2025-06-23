"""
Project Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class CreateProjectRequest(BaseModel):
    """Schema for creating a new project"""
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    workspace_id: Optional[str] = Field(None, description="Workspace ID")
    mapCenter: Optional[List[float]] = Field([0, 0], description="Map center coordinates [lng, lat]")
    mapZoom: Optional[int] = Field(2, ge=0, le=20, description="Map zoom level")
    bounds: Optional[List[List[float]]] = Field(None, description="Map bounds [[sw_lng, sw_lat], [ne_lng, ne_lat]]")
    is_public: Optional[bool] = Field(False, description="Whether project is public")


class UpdateProjectRequest(BaseModel):
    """Schema for updating a project"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    mapCenter: Optional[List[float]] = Field(None, description="Map center coordinates [lng, lat]")
    mapZoom: Optional[int] = Field(None, ge=0, le=20, description="Map zoom level")
    bounds: Optional[List[List[float]]] = Field(None, description="Map bounds [[sw_lng, sw_lat], [ne_lng, ne_lat]]")
    is_public: Optional[bool] = Field(None, description="Whether project is public")
    settings: Optional[Dict[str, Any]] = Field(None, description="Additional project settings")


class DuplicateProjectRequest(BaseModel):
    """Schema for duplicating a project"""
    name: str = Field(..., min_length=1, max_length=100, description="New project name")
    description: Optional[str] = Field(None, description="New project description")
    copy_layers: Optional[bool] = Field(True, description="Whether to copy layers")


class ProjectResponse(BaseModel):
    """Schema for project response"""
    id: str
    name: str
    description: Optional[str]
    workspace_id: Optional[str]
    owner_id: Optional[str]
    settings: Dict[str, Any]
    mapCenter: List[float]
    mapZoom: int
    bounds: Optional[List[List[float]]]
    zoom_level: int
    is_public: bool
    layer_count: int
    last_accessed: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    layers: Optional[List[Dict[str, Any]]] = []


class ProjectListResponse(BaseModel):
    """Schema for project list response"""
    id: str
    name: str
    description: Optional[str]
    layer_count: int
    last_accessed: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    is_public: bool
