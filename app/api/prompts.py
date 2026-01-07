"""API routes for Prompt management with versioning."""
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import Prompt, PromptVersion, User
from app.schemas.prompt import (
    PromptCreate,
    PromptUpdate,
    PromptResponse,
    PromptListResponse,
    PromptDetailResponse,
    PromptVersionResponse,
    PromptVersionListResponse,
)
from app.services.audit import create_audit_log

router = APIRouter(prefix="/prompts", tags=["Prompts"])


@router.get("", response_model=PromptListResponse)
async def list_prompts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all prompts with pagination."""
    # Build query
    query = select(Prompt).where(Prompt.is_active == True)
    
    if search:
        query = query.where(
            Prompt.tag.ilike(f"%{search}%") | Prompt.description.ilike(f"%{search}%")
        )
    
    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # Paginate
    query = query.order_by(Prompt.updated_at.desc())
    query = query.offset((page - 1) * size).limit(size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return PromptListResponse(
        items=[PromptResponse.model_validate(p) for p in items],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 0,
    )


@router.post("", response_model=PromptResponse, status_code=201)
async def create_prompt(
    data: PromptCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new prompt."""
    # Check unique tag
    existing = await db.execute(
        select(Prompt).where(Prompt.tag == data.tag, Prompt.is_active == True)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Prompt tag already exists")
    
    # Create prompt
    prompt = Prompt(
        tag=data.tag,
        content=data.content,
        description=data.description,
        current_version=1,
        is_active=True,
    )
    db.add(prompt)
    await db.flush()
    
    # Create initial version
    version = PromptVersion(
        prompt_id=str(prompt.id),
        version=1,
        content=data.content,
        description=data.description,
        change_note="Initial version",
    )
    db.add(version)
    
    # Audit log
    await create_audit_log(
        db=db,
        module="prompts",
        action="CREATE",
        object_type="prompt",
        object_id=str(prompt.id),
        after_data={"tag": prompt.tag, "content": prompt.content[:100] + "..." if len(prompt.content) > 100 else prompt.content},
        operator_id=str(current_user.id),
    )
    
    await db.commit()
    await db.refresh(prompt)
    
    return PromptResponse.model_validate(prompt)


@router.get("/{prompt_id}", response_model=PromptDetailResponse)
async def get_prompt(
    prompt_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get prompt details with version history."""
    result = await db.execute(
        select(Prompt).where(Prompt.id == prompt_id, Prompt.is_active == True)
    )
    prompt = result.scalar_one_or_none()
    
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # Get versions
    versions_result = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.prompt_id == prompt_id)
        .order_by(PromptVersion.version.desc())
    )
    versions = versions_result.scalars().all()
    
    response = PromptDetailResponse.model_validate(prompt)
    response.versions = [PromptVersionResponse.model_validate(v) for v in versions]
    
    return response


@router.patch("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: str,
    data: PromptUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a prompt. Optionally creates a new version."""
    result = await db.execute(
        select(Prompt).where(Prompt.id == prompt_id, Prompt.is_active == True)
    )
    prompt = result.scalar_one_or_none()
    
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    before_data = {"content": prompt.content, "description": prompt.description}
    
    # Update fields
    if data.content is not None:
        prompt.content = data.content
    if data.description is not None:
        prompt.description = data.description
    
    # Create new version if requested
    if data.create_version and data.content is not None:
        prompt.current_version += 1
        
        version = PromptVersion(
            prompt_id=str(prompt.id),
            version=prompt.current_version,
            content=prompt.content,
            description=prompt.description,
            change_note=data.change_note or f"Updated to version {prompt.current_version}",
        )
        db.add(version)
    
    # Audit log
    await create_audit_log(
        db=db,
        module="prompts",
        action="UPDATE",
        object_type="prompt",
        object_id=str(prompt.id),
        before_data=before_data,
        after_data={"content": prompt.content[:100] + "..." if len(prompt.content) > 100 else prompt.content, "description": prompt.description, "version": prompt.current_version},
        operator_id=str(current_user.id),
    )
    
    await db.commit()
    await db.refresh(prompt)
    
    return PromptResponse.model_validate(prompt)


@router.delete("/{prompt_id}", status_code=204)
async def delete_prompt(
    prompt_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft delete a prompt."""
    result = await db.execute(
        select(Prompt).where(Prompt.id == prompt_id, Prompt.is_active == True)
    )
    prompt = result.scalar_one_or_none()
    
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    prompt.is_active = False
    
    # Audit log
    await create_audit_log(
        db=db,
        module="prompts",
        action="DELETE",
        object_type="prompt",
        object_id=str(prompt.id),
        before_data={"tag": prompt.tag},
        operator_id=str(current_user.id),
    )
    
    await db.commit()


@router.get("/{prompt_id}/versions", response_model=PromptVersionListResponse)
async def list_prompt_versions(
    prompt_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all versions of a prompt."""
    # Verify prompt exists
    result = await db.execute(
        select(Prompt).where(Prompt.id == prompt_id, Prompt.is_active == True)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # Get versions
    versions_result = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.prompt_id == prompt_id)
        .order_by(PromptVersion.version.desc())
    )
    versions = versions_result.scalars().all()
    
    return PromptVersionListResponse(
        items=[PromptVersionResponse.model_validate(v) for v in versions],
        total=len(versions),
    )


@router.get("/{prompt_id}/versions/{version}", response_model=PromptVersionResponse)
async def get_prompt_version(
    prompt_id: str,
    version: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific version of a prompt."""
    result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.prompt_id == prompt_id,
            PromptVersion.version == version,
        )
    )
    prompt_version = result.scalar_one_or_none()
    
    if not prompt_version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return PromptVersionResponse.model_validate(prompt_version)


@router.post("/{prompt_id}/rollback/{version}", response_model=PromptResponse)
async def rollback_to_version(
    prompt_id: str,
    version: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rollback prompt to a specific version."""
    # Get prompt
    result = await db.execute(
        select(Prompt).where(Prompt.id == prompt_id, Prompt.is_active == True)
    )
    prompt = result.scalar_one_or_none()
    
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # Get target version
    version_result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.prompt_id == prompt_id,
            PromptVersion.version == version,
        )
    )
    target_version = version_result.scalar_one_or_none()
    
    if not target_version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Update prompt to target version content
    before_data = {"content": prompt.content, "version": prompt.current_version}
    
    prompt.content = target_version.content
    prompt.description = target_version.description
    prompt.current_version += 1
    
    # Create new version for rollback
    new_version = PromptVersion(
        prompt_id=str(prompt.id),
        version=prompt.current_version,
        content=prompt.content,
        description=prompt.description,
        change_note=f"Rollback to version {version}",
    )
    db.add(new_version)
    
    # Audit log
    await create_audit_log(
        db=db,
        module="prompts",
        action="ROLLBACK",
        object_type="prompt",
        object_id=str(prompt.id),
        before_data=before_data,
        after_data={"content": prompt.content[:100] + "...", "version": prompt.current_version, "rollback_from": version},
        operator_id=str(current_user.id),
    )
    
    await db.commit()
    await db.refresh(prompt)
    
    return PromptResponse.model_validate(prompt)
