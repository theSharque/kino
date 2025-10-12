"""
Project data models
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ProjectBase(BaseModel):
    """Base project model with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    width: int = Field(..., gt=0, le=7680, description="Video width in pixels")
    height: int = Field(..., gt=0, le=4320, description="Video height in pixels")
    fps: int = Field(..., gt=0, le=120, description="Frames per second")

    @field_validator('width', 'height')
    @classmethod
    def validate_dimensions(cls, v: int) -> int:
        """Ensure dimensions are positive"""
        if v <= 0:
            raise ValueError('Dimension must be positive')
        return v

    @field_validator('fps')
    @classmethod
    def validate_fps(cls, v: int) -> int:
        """Ensure FPS is reasonable"""
        if v <= 0:
            raise ValueError('FPS must be positive')
        if v > 120:
            raise ValueError('FPS must be 120 or less')
        return v


class ProjectCreate(ProjectBase):
    """Model for creating a new project"""
    pass


class ProjectUpdate(BaseModel):
    """Model for updating an existing project"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    width: Optional[int] = Field(None, gt=0, le=7680)
    height: Optional[int] = Field(None, gt=0, le=4320)
    fps: Optional[int] = Field(None, gt=0, le=120)


class ProjectResponse(ProjectBase):
    """Model for project response"""
    id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Model for list of projects response"""
    total: int
    projects: list[ProjectResponse]

