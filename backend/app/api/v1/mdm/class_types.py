from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import User, ClassType
from app.schemas.class_type import ClassTypeCreate, ClassTypeUpdate, ClassTypeResponse
from app.utils.enums import UserRole

router = APIRouter(prefix="/mdm/class-types", tags=["mdm-global"])


@router.get("", response_model=List[ClassTypeResponse])
def get_class_types(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all class types (all roles can read)"""
    query = db.query(ClassType).filter(ClassType.is_archived == False)

    if active_only:
        query = query.filter(ClassType.active == True)

    class_types = query.order_by(ClassType.name).offset(skip).limit(limit).all()
    return class_types


@router.post("", response_model=ClassTypeResponse)
def create_class_type(
    class_type_data: ClassTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create class type (Super Admin only)"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only Super Admin can create class types")

    # Check if name already exists
    existing = db.query(ClassType).filter(
        ClassType.name == class_type_data.name,
        ClassType.is_archived == False
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Class type with this name already exists")

    class_type = ClassType(
        **class_type_data.dict(),
        created_by_id=current_user.id,
        updated_by_id=current_user.id
    )

    db.add(class_type)
    db.commit()
    db.refresh(class_type)

    return class_type


@router.get("/{class_type_id}", response_model=ClassTypeResponse)
def get_class_type(
    class_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get class type by ID"""
    class_type = db.query(ClassType).filter(
        ClassType.id == class_type_id,
        ClassType.is_archived == False
    ).first()

    if not class_type:
        raise HTTPException(status_code=404, detail="Class type not found")

    return class_type


@router.patch("/{class_type_id}", response_model=ClassTypeResponse)
def update_class_type(
    class_type_id: int,
    class_type_data: ClassTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update class type (Super Admin only)"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only Super Admin can update class types")

    class_type = db.query(ClassType).filter(
        ClassType.id == class_type_id,
        ClassType.is_archived == False
    ).first()

    if not class_type:
        raise HTTPException(status_code=404, detail="Class type not found")

    # Update fields
    update_data = class_type_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(class_type, field, value)

    class_type.updated_by_id = current_user.id

    db.commit()
    db.refresh(class_type)

    return class_type


@router.delete("/{class_type_id}")
def delete_class_type(
    class_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive class type (Super Admin only)"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only Super Admin can delete class types")

    class_type = db.query(ClassType).filter(
        ClassType.id == class_type_id,
        ClassType.is_archived == False
    ).first()

    if not class_type:
        raise HTTPException(status_code=404, detail="Class type not found")

    # Soft delete
    class_type.is_archived = True
    class_type.updated_by_id = current_user.id

    db.commit()

    return {"message": "Class type archived successfully"}
