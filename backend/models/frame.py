"""
Frame data models
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class FrameBase(BaseModel):
    """Base frame model with common fields"""
    path: str = Field(..., min_length=1, max_length=500, description="Path to frame file")
    generator: str = Field(..., min_length=1, max_length=255, description="Generator information")
    project_id: int = Field(..., gt=0, description="Project ID this frame belongs to")
    variant_id: int = Field(default=0, ge=0, description="Variant ID for this frame")

    @field_validator('path')
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Ensure path is not empty"""
        if not v.strip():
            raise ValueError('Path cannot be empty')
        return v.strip()

    @field_validator('generator')
    @classmethod
    def validate_generator(cls, v: str) -> str:
        """Ensure generator is not empty"""
        if not v.strip():
            raise ValueError('Generator cannot be empty')
        return v.strip()


class FrameCreate(FrameBase):
    """Model for creating a new frame"""
    pass


class FrameUpdate(BaseModel):
    """Model for updating an existing frame"""
    path: Optional[str] = Field(None, min_length=1, max_length=500)
    generator: Optional[str] = Field(None, min_length=1, max_length=255)
    project_id: Optional[int] = Field(None, gt=0)
    variant_id: Optional[int] = Field(None, ge=0)


class FrameResponse(FrameBase):
    """Model for frame response"""
    id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class FrameListResponse(BaseModel):
    """Model for list of frames response"""
    total: int
    frames: list[FrameResponse]

