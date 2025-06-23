"""
Project Service - Business logic for project operations
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import desc, func, and_
from app.models.project import Project
from app.models.layer import Layer
from app.schemas.project import CreateProjectRequest, UpdateProjectRequest, DuplicateProjectRequest
from app.utils.responses import not_found_response, error_response
from datetime import datetime, timezone
import uuid


class ProjectService:
    """Service class for project operations"""
    
    @staticmethod
    async def get_recent_projects(db: Session, limit: int = 10, owner_id: Optional[str] = None) -> List[Project]:
        """
        Get recent projects
        
        Args:
            db: Database session
            limit: Number of projects to return
            owner_id: Filter by owner ID (optional)
            
        Returns:
            List of recent projects
        """
        query = db.query(Project)
        
        if owner_id:
            query = query.filter(Project.owner_id == owner_id)
        
        projects = query.order_by(desc(Project.updated_at)).limit(limit).all()
        return projects
    
    @staticmethod
    async def get_projects_paginated(
        db: Session, 
        page: int = 1, 
        size: int = 20, 
        search: Optional[str] = None,
        owner_id: Optional[str] = None
    ) -> tuple[List[Project], int]:
        """
        Get paginated projects with optional search
        
        Args:
            db: Database session
            page: Page number (1-based)
            size: Page size
            search: Search query (optional)
            owner_id: Filter by owner ID (optional)
            
        Returns:
            Tuple of (projects, total_count)
        """
        query = db.query(Project)
        
        if owner_id:
            query = query.filter(Project.owner_id == owner_id)
        
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                Project.name.ilike(search_filter) | 
                Project.description.ilike(search_filter)
            )
        
        total = query.count()
        
        offset = (page - 1) * size
        projects = query.order_by(desc(Project.updated_at)).offset(offset).limit(size).all()
        
        return projects, total
    
    @staticmethod
    async def create_project(db: Session, project_data: CreateProjectRequest, owner_id: Optional[str] = None) -> Project:
        """
        Create a new project
        
        Args:
            db: Database session
            project_data: Project creation data
            owner_id: Owner ID (optional)
            
        Returns:
            Created project
        """
        # Prepare settings
        settings = {
            "mapCenter": project_data.mapCenter or [0, 0],
            "mapZoom": project_data.mapZoom or 2,
        }
        
        if project_data.bounds:
            settings["bounds"] = project_data.bounds
        
        # Create project
        project = Project(
            name=project_data.name,
            description=project_data.description,
            workspace_id=project_data.workspace_id,
            owner_id=owner_id,
            settings=settings,
            zoom_level=project_data.mapZoom or 2,
            is_public=project_data.is_public or False,
            layer_count=0
        )
        
        db.add(project)
        db.commit()
        db.refresh(project)
        
        # Create default base layer
        from app.services.layer_service import LayerService
        await LayerService.create_default_base_layer(db, str(project.id))
        
        # Update layer count
        project.layer_count = 1
        db.commit()
        db.refresh(project)
        
        return project
    
    @staticmethod
    async def get_project_by_id(db: Session, project_id: str, include_layers: bool = True) -> Optional[Project]:
        """
        Get project by ID
        
        Args:
            db: Database session
            project_id: Project ID
            include_layers: Whether to include layers
            
        Returns:
            Project or None if not found
        """
        query = db.query(Project).filter(Project.id == project_id)
        
        if include_layers:
            query = query.options(selectinload(Project.layers))
        
        project = query.first()
        
        if project:
            # Update last accessed
            project.last_accessed = datetime.now(timezone.utc)
            db.commit()
        
        return project
    
    @staticmethod
    async def update_project(db: Session, project_id: str, updates: UpdateProjectRequest) -> Optional[Project]:
        """
        Update project
        
        Args:
            db: Database session
            project_id: Project ID
            updates: Update data
            
        Returns:
            Updated project or None if not found
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            return None
        
        # Update fields
        update_data = updates.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if field in ["mapCenter", "mapZoom", "bounds"]:
                # Update settings
                if not project.settings:
                    project.settings = {}
                project.settings[field] = value
                
                # Also update zoom_level if mapZoom is provided
                if field == "mapZoom":
                    project.zoom_level = value
            else:
                setattr(project, field, value)
        
        project.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(project)
        
        return project
    
    @staticmethod
    async def delete_project(db: Session, project_id: str) -> bool:
        """
        Delete project
        
        Args:
            db: Database session
            project_id: Project ID
            
        Returns:
            True if deleted, False if not found
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            return False
        
        db.delete(project)
        db.commit()
        
        return True
    
    @staticmethod
    async def duplicate_project(
        db: Session, 
        project_id: str, 
        duplicate_data: DuplicateProjectRequest,
        owner_id: Optional[str] = None
    ) -> Optional[Project]:
        """
        Duplicate project
        
        Args:
            db: Database session
            project_id: Original project ID
            duplicate_data: Duplication data
            owner_id: Owner ID (optional)
            
        Returns:
            Duplicated project or None if original not found
        """
        original = db.query(Project).options(selectinload(Project.layers)).filter(Project.id == project_id).first()
        
        if not original:
            return None
        
        # Create new project
        new_project = Project(
            name=duplicate_data.name,
            description=duplicate_data.description or original.description,
            workspace_id=original.workspace_id,
            owner_id=owner_id or original.owner_id,
            settings=original.settings.copy() if original.settings else {},
            zoom_level=original.zoom_level,
            is_public=original.is_public,
            layer_count=0
        )
        
        db.add(new_project)
        db.commit()
        db.refresh(new_project)
        
        # Copy layers if requested
        if duplicate_data.copy_layers and original.layers:
            from app.services.layer_service import LayerService
            
            for layer in original.layers:
                await LayerService.duplicate_layer(db, layer, str(new_project.id))
            
            # Update layer count
            new_project.layer_count = len(original.layers)
            db.commit()
            db.refresh(new_project)
        
        return new_project


# LayerService will be imported when needed to avoid circular imports
