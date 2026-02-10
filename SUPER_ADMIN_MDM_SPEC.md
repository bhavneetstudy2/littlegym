# Super Admin & Master Data Management (MDM) - Product Specification

## A) PRODUCT + UX SPECIFICATION

### 1) Information Architecture

```
├── /centers                          [Super Admin Only]
│   ├── Centers list with stats
│   └── /[centerId]
│       ├── Center overview dashboard
│       └── Enter Center Context button
│
├── /mdm                              [Super Admin + Center Admin]
│   ├── Master Data landing page
│   ├── /global                       [Super Admin CRUD, Center Admin Read]
│   │   ├── /curricula
│   │   ├── /skills
│   │   └── /class-types
│   └── /center                       [Super Admin + Center Admin CRUD]
│       ├── /batches
│       ├── /batch-mappings
│       └── /session-templates
│
├── /users                            [Super Admin: All, Center Admin: Own Center]
│   ├── Users list
│   └── /[userId]
│       └── User profile
│
└── /leads, /enrollments, /attendance [Existing modules - center-scoped]
```

**Navigation Structure:**
- Super Admin Sidebar:
  - Dashboard
  - **Centers** ⭐
  - Leads (when in center context)
  - Enrollments (when in center context)
  - Attendance (when in center context)
  - Progress (when in center context)
  - **Master Data** ⭐
  - **Users** ⭐
  - Settings

- Center Admin Sidebar:
  - Dashboard
  - Leads
  - Enrollments
  - Attendance
  - Progress
  - **Master Data** (center-scoped only)
  - **Users** (own center)
  - Settings

---

### 2) User Flows

#### Flow 1: Super Admin - Enter Center Context
```
1. Super Admin logs in → Lands on /centers
2. Sees list of all centers with cards:
   - Center name, city
   - Active students count
   - Active leads count
   - Last activity date
3. Clicks "View Center" on Mumbai Central
4. Navigates to /centers/1 (center overview)
5. Sees center stats dashboard
6. Clicks "Enter Center Context" button
7. **Center Context Bar appears** at top:
   ┌─────────────────────────────────────────────────┐
   │ 📍 Viewing: Mumbai Central | Switch | Exit      │
   └─────────────────────────────────────────────────┘
8. Now all center-scoped pages (leads, enrollments) show Mumbai data
9. Sidebar shows center-specific menu items
10. URL includes ?centerId=1 or uses context provider
```

#### Flow 2: Super Admin - Switch Center
```
1. In center context (viewing Mumbai Central)
2. Clicks "Switch" in Center Context Bar
3. Dropdown shows all centers
4. Selects "Chandigarh"
5. Context updates, page refreshes with Chandigarh data
6. Center Context Bar updates: "Viewing: Chandigarh"
```

#### Flow 3: Super Admin - Exit Center Context
```
1. In center context
2. Clicks "Exit" in Center Context Bar
3. Navigates back to /centers
4. Center Context Bar disappears
5. Center-scoped sidebar items become disabled/hidden
```

#### Flow 4: Center Admin - Auto Center Context
```
1. Center Admin logs in
2. Auto-enters their assigned center context
3. Center Context Bar shows (read-only, no switch/exit):
   ┌─────────────────────────────────────────────────┐
   │ 📍 Your Center: Mumbai Central                  │
   └─────────────────────────────────────────────────┘
4. Cannot switch or exit
5. Sees only their center's data everywhere
```

#### Flow 5: Managing Global MDM (Curricula)
```
1. Super Admin navigates to /mdm
2. Sees two sections: Global Master Data | Center Master Data
3. Clicks "Curricula"
4. Navigates to /mdm/global/curricula
5. Sees DataTable with all curricula:
   - Name, Level, Age Range, Active, Actions
6. Clicks "+ New Curriculum"
7. Side drawer opens with form:
   - Name*, Level, Age Min*, Age Max*, Description, Active
8. Fills form, clicks Save
9. Toast: "Curriculum created successfully"
10. Table refreshes with new row
```

#### Flow 6: Managing Center MDM (Batches)
```
1. Center Admin navigates to /mdm
2. Sees only: Center Master Data section
3. Clicks "Batches"
4. Navigates to /mdm/center/batches
5. Sees DataTable with their center's batches
6. Clicks "+ New Batch"
7. Drawer form opens:
   - Name*, Age Min*, Age Max*, Days of Week*, Start Time*, End Time*, Capacity, Active
8. Saves batch → created for their center only
```

---

### 3) MDM Modules

#### Global Master Data (Super Admin CRUD)

**1. Curricula**
- Purpose: Define skill development frameworks
- Fields: name, level, age_min, age_max, description, active
- Use Case: "Gymnastics Foundation Level 1" (Ages 3-5)

**2. Skills**
- Purpose: Individual skills within curricula
- Fields: curriculum_id, name, category, display_order, description, active
- Use Case: "Cartwheel", "Forward Roll", "Monkey Kick"

**3. Class Types** (Optional but Recommended)
- Purpose: Standardize class offerings across centers
- Fields: name, description, age_min, age_max, duration_minutes, active
- Use Case: "Birds", "Bugs", "Beasts", "Super Beasts"

#### Center Master Data (Center Admin + Super Admin CRUD)

**1. Batches**
- Purpose: Specific class groups at a center
- Fields: center_id, name, age_min, age_max, days_of_week (JSON), start_time, end_time, capacity, active
- Use Case: "Birds Monday-Wednesday 11:00" at Mumbai Central

**2. Batch ↔ Class Mappings** (Optional)
- Purpose: Link batches to global class types and curricula
- Fields: center_id, batch_id, class_type_id, curriculum_id
- Use Case: Map "Birds MWF Batch" → "Birds Class Type" → "Gymnastics Foundation L1"

**3. Session Templates** (Optional - Future)
- Purpose: Pre-define recurring sessions for batch scheduling
- Fields: center_id, batch_id, day_of_week, start_time, end_time, default_trainer_id, active

---

### 4) Permissions Matrix

| Feature | Super Admin | Center Admin | Trainer |
|---------|-------------|--------------|---------|
| **Centers** | | | |
| View all centers | ✅ | ❌ | ❌ |
| Enter any center context | ✅ | ❌ | ❌ |
| View center dashboard | ✅ | ✅ (own) | ❌ |
| **Global MDM** | | | |
| Curricula CRUD | ✅ | 🔍 Read | ❌ |
| Skills CRUD | ✅ | 🔍 Read | ❌ |
| Class Types CRUD | ✅ | 🔍 Read | ❌ |
| **Center MDM** | | | |
| Batches CRUD | ✅ (any center) | ✅ (own) | 🔍 Read |
| Batch Mappings CRUD | ✅ (any center) | ✅ (own) | ❌ |
| Session Templates CRUD | ✅ (any center) | ✅ (own) | ❌ |
| **Users** | | | |
| View all users | ✅ | ✅ (own center) | ❌ |
| Create/Edit users | ✅ (any center) | ✅ (own center) | ❌ |
| Delete/Deactivate users | ✅ | ✅ (own center, not self) | ❌ |
| **Operational** | | | |
| Leads | ✅ (in context) | ✅ | 🔍 Read |
| Enrollments | ✅ (in context) | ✅ | 🔍 Read |
| Attendance | ✅ (in context) | ✅ | ✅ (mark only) |
| Skill Progress | ✅ (in context) | ✅ | ✅ (update only) |

**Legend:** ✅ Full Access | 🔍 Read-Only | ❌ No Access

---

### 5) Wireframe-Level Layouts

#### Layout 1: Centers List (/centers)
```
┌────────────────────────────────────────────────────────────┐
│ [Logo] The Little Gym CRM                    [Profile ▼]   │
├────────────────────────────────────────────────────────────┤
│                                                              │
│  Centers                                   [+ New Center]   │
│  ────────────────────────────────────────────────────────  │
│                                                              │
│  [Search centers...]                    [Filter: All ▼]     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Mumbai Central│  │ Chandigarh   │  │ Bangalore    │     │
│  │ ────────────  │  │ ────────────  │  │ ────────────  │     │
│  │ 🎯 124 Active │  │ 🎯 89 Active │  │ 🎯 156 Active│     │
│  │ 📋 45 Leads   │  │ 📋 23 Leads  │  │ 📋 67 Leads  │     │
│  │ 📅 2h ago     │  │ 📅 5h ago    │  │ 📅 1h ago    │     │
│  │               │  │               │  │               │     │
│  │ [View Center] │  │ [View Center] │  │ [View Center] │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
└────────────────────────────────────────────────────────────┘
```

#### Layout 2: Center Context Bar (Active)
```
┌────────────────────────────────────────────────────────────┐
│ 📍 Viewing: Mumbai Central        [Switch ▼]  [Exit]       │
└────────────────────────────────────────────────────────────┘
```

#### Layout 3: MDM Landing (/mdm)
```
┌────────────────────────────────────────────────────────────┐
│ [Sidebar]   Master Data Management                          │
│             ════════════════════                             │
│  Centers                                                     │
│  Leads      Global Master Data (Super Admin)                │
│  Enrolls    ┌──────────────┐  ┌──────────────┐            │
│► Master Data│ Curricula    │  │ Skills       │            │
│  Users      │ 12 active    │  │ 156 items    │            │
│  Settings   │ [Manage →]   │  │ [Manage →]   │            │
│             └──────────────┘  └──────────────┘            │
│             ┌──────────────┐                               │
│             │ Class Types  │                               │
│             │ 8 active     │                               │
│             │ [Manage →]   │                               │
│             └──────────────┘                               │
│                                                              │
│             Center Master Data                              │
│             ┌──────────────┐  ┌──────────────┐            │
│             │ Batches      │  │ Mappings     │            │
│             │ 15 active    │  │ 20 mappings  │            │
│             │ [Manage →]   │  │ [Manage →]   │            │
│             └──────────────┘  └──────────────┘            │
│                                                              │
└────────────────────────────────────────────────────────────┘
```

#### Layout 4: DataTable with Drawer (/mdm/global/curricula)
```
┌────────────────────────────────────────────────────────────┐
│ Curricula                                  [+ New Curriculum]│
│ ─────────────────────────────────────────────────────────  │
│ [Search...]                    [Filter: Active ▼] [Export] │
│                                                              │
│ ┌──────────┬────────┬───────────┬────────┬────────┐       │
│ │ Name     │ Level  │ Age Range │ Active │ Actions│       │
│ ├──────────┼────────┼───────────┼────────┼────────┤       │
│ │ Gymnas...│ L1     │ 3-5 yrs   │ ✅     │ [Edit] │       │
│ │ Advanced │ L2     │ 6-9 yrs   │ ✅     │ [Edit] │       │
│ │ Tumbling │ L1     │ 4-7 yrs   │ ❌     │ [Edit] │       │
│ └──────────┴────────┴───────────┴────────┴────────┘       │
│                                            [1][2][3]        │
└────────────────────────────────────────────────────────────┘

[Drawer - when "+ New Curriculum" clicked]
                  ┌─────────────────────────────┐
                  │ Create New Curriculum   [×] │
                  ├─────────────────────────────┤
                  │ Name *                      │
                  │ [________________]          │
                  │                             │
                  │ Level                       │
                  │ [________________]          │
                  │                             │
                  │ Age Range *                 │
                  │ Min [__]  Max [__]          │
                  │                             │
                  │ Description                 │
                  │ [________________]          │
                  │ [________________]          │
                  │                             │
                  │ ☑ Active                    │
                  │                             │
                  │ [Cancel]    [Create]        │
                  └─────────────────────────────┘
```

---

### 6) UI Design Guidelines

**Color System:**
```
Primary:     #3B82F6 (Blue-500)
Success:     #10B981 (Green-500)
Warning:     #F59E0B (Amber-500)
Danger:      #EF4444 (Red-500)
Neutral:     #64748B (Slate-500)
Background:  #F8FAFC (Slate-50)
```

**Typography Scale:**
```
Heading 1:   text-3xl font-bold (30px)
Heading 2:   text-2xl font-bold (24px)
Heading 3:   text-xl font-semibold (20px)
Body:        text-base (16px)
Small:       text-sm (14px)
Tiny:        text-xs (12px)
```

**Spacing System:**
```
xs:  4px   (p-1, gap-1)
sm:  8px   (p-2, gap-2)
md:  16px  (p-4, gap-4)
lg:  24px  (p-6, gap-6)
xl:  32px  (p-8, gap-8)
```

**Component Patterns:**
- Cards: `rounded-xl shadow-sm border border-gray-200 p-6`
- Buttons: `rounded-lg px-4 py-2 font-medium transition`
- Inputs: `rounded-lg border border-gray-300 px-3 py-2 focus:ring-2`
- Tables: Sticky headers, hover rows, zebra striping optional
- Modals/Drawers: Slide from right, backdrop blur

**Loading States:**
- Skeleton loaders for tables (shimmer effect)
- Spinner for buttons during submission
- Progress bar for multi-step operations

**Empty States:**
- Illustration + Heading + Description + CTA button
- Example: "No curricula yet. Create your first curriculum to get started."

**Toasts:**
- Position: top-right
- Duration: 3s (success), 5s (error)
- Dismissible with X button

**Confirmations:**
- Only for destructive actions (Delete, Deactivate)
- Modal with heading, description, Cancel + Confirm buttons

---

## B) BACKEND (FastAPI) DELIVERABLES

### 1) Project Structure

```
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── core/
│   │   ├── database.py
│   │   ├── security.py
│   │   ├── dependencies.py          # RBAC + center scoping
│   │   └── permissions.py           # Permission checks
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py                  # BaseModel with audit fields
│   │   ├── center.py                # ⭐ NEW
│   │   ├── user.py                  # Enhanced
│   │   ├── curriculum.py            # ⭐ NEW (Global MDM)
│   │   ├── skill.py                 # ⭐ NEW (Global MDM)
│   │   ├── class_type.py            # ⭐ NEW (Global MDM)
│   │   ├── batch.py                 # Enhanced (Center MDM)
│   │   ├── batch_mapping.py         # ⭐ NEW (Center MDM)
│   │   └── session_template.py      # ⭐ NEW (Center MDM)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── center.py                # ⭐ NEW
│   │   ├── user.py
│   │   ├── curriculum.py            # ⭐ NEW
│   │   ├── skill.py                 # ⭐ NEW
│   │   ├── class_type.py            # ⭐ NEW
│   │   ├── batch.py                 # Enhanced
│   │   └── batch_mapping.py         # ⭐ NEW
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── centers.py           # ⭐ NEW
│   │       ├── users.py             # ⭐ NEW
│   │       ├── mdm/
│   │       │   ├── __init__.py
│   │       │   ├── curricula.py     # ⭐ NEW
│   │       │   ├── skills.py        # ⭐ NEW
│   │       │   ├── class_types.py   # ⭐ NEW
│   │       │   ├── batches.py       # Enhanced
│   │       │   └── batch_mappings.py # ⭐ NEW
│   │       ├── leads.py
│   │       ├── enrollments.py
│   │       └── attendance.py
│   ├── services/
│   │   ├── center_service.py        # ⭐ NEW
│   │   ├── user_service.py          # ⭐ NEW
│   │   └── mdm_service.py           # ⭐ NEW
│   └── utils/
│       └── enums.py
├── alembic/
│   └── versions/
│       └── xxx_add_mdm_tables.py    # ⭐ NEW migration
├── seed_data.py                     # ⭐ Enhanced with MDM seed
└── requirements.txt
```

---

### 2) SQLAlchemy Models

#### models/center.py
```python
from sqlalchemy import Column, Integer, String, Boolean
from app.models.base import BaseModel

class Center(BaseModel):
    """Center (multi-tenant root entity)"""
    __tablename__ = "centers"

    name = Column(String(100), nullable=False, index=True)
    code = Column(String(20), unique=True, nullable=False)  # e.g., "MUM", "CHD"
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    timezone = Column(String(50), default="Asia/Kolkata")
    active = Column(Boolean, default=True, nullable=False)

    # Relationships
    users = relationship("User", back_populates="center")
    batches = relationship("Batch", back_populates="center")
```

#### models/curriculum.py (Global MDM)
```python
from sqlalchemy import Column, Integer, String, Text, Boolean
from app.models.base import BaseModel

class Curriculum(BaseModel):
    """Global curriculum template"""
    __tablename__ = "curricula"

    name = Column(String(100), nullable=False, index=True)
    level = Column(String(50), nullable=True)  # e.g., "Level 1", "Beginner"
    age_min = Column(Integer, nullable=False)
    age_max = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True, nullable=False)

    # Relationships
    skills = relationship("Skill", back_populates="curriculum", cascade="all, delete-orphan")
```

#### models/skill.py (Global MDM)
```python
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from app.models.base import BaseModel

class Skill(BaseModel):
    """Individual skill within a curriculum"""
    __tablename__ = "skills"

    curriculum_id = Column(Integer, ForeignKey("curricula.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=True)  # e.g., "Gymnastics", "Motor Skills"
    description = Column(Text, nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    # Relationships
    curriculum = relationship("Curriculum", back_populates="skills")
```

#### models/class_type.py (Global MDM)
```python
from sqlalchemy import Column, Integer, String, Text, Boolean
from app.models.base import BaseModel

class ClassType(BaseModel):
    """Global class type definition"""
    __tablename__ = "class_types"

    name = Column(String(100), nullable=False, unique=True)  # "Birds", "Bugs", "Beasts"
    description = Column(Text, nullable=True)
    age_min = Column(Integer, nullable=False)
    age_max = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, default=45, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
```

#### models/batch.py (Enhanced - Center MDM)
```python
from sqlalchemy import Column, Integer, String, Time, Boolean, ForeignKey, JSON
from app.models.base import BaseModel, TenantMixin

class Batch(BaseModel, TenantMixin):
    """Center-specific batch"""
    __tablename__ = "batches"

    name = Column(String(100), nullable=False, index=True)
    age_min = Column(Integer, nullable=False)
    age_max = Column(Integer, nullable=False)
    days_of_week = Column(JSON, nullable=True)  # ["Monday", "Wednesday", "Friday"]
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    capacity = Column(Integer, nullable=True)
    active = Column(Boolean, default=True, nullable=False)

    # Relationships
    center = relationship("Center", back_populates="batches")
    mappings = relationship("BatchMapping", back_populates="batch", cascade="all, delete-orphan")
```

#### models/batch_mapping.py (Center MDM)
```python
from sqlalchemy import Column, Integer, ForeignKey
from app.models.base import BaseModel, TenantMixin

class BatchMapping(BaseModel, TenantMixin):
    """Maps batch to class type and curriculum"""
    __tablename__ = "batch_mappings"

    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False, index=True)
    class_type_id = Column(Integer, ForeignKey("class_types.id"), nullable=True)
    curriculum_id = Column(Integer, ForeignKey("curricula.id"), nullable=True)

    # Relationships
    batch = relationship("Batch", back_populates="mappings")
    class_type = relationship("ClassType")
    curriculum = relationship("Curriculum")
```

---

### 3) Pydantic Schemas

#### schemas/curriculum.py
```python
from pydantic import BaseModel, Field
from typing import Optional

class CurriculumBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    level: Optional[str] = Field(None, max_length=50)
    age_min: int = Field(..., ge=0, le=18)
    age_max: int = Field(..., ge=0, le=18)
    description: Optional[str] = None
    active: bool = True

class CurriculumCreate(CurriculumBase):
    pass

class CurriculumUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    level: Optional[str] = None
    age_min: Optional[int] = Field(None, ge=0, le=18)
    age_max: Optional[int] = Field(None, ge=0, le=18)
    description: Optional[str] = None
    active: Optional[bool] = None

class CurriculumResponse(CurriculumBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

Similar schemas for: Skill, ClassType, Center, BatchMapping

---

### 4) RBAC + Center Scoping (core/dependencies.py)

```python
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import User
from app.utils.enums import UserRole

def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
) -> User:
    """Extract and validate JWT, return current user"""
    # JWT decode logic here
    pass

def require_role(allowed_roles: list[UserRole]):
    """Dependency factory for role-based access"""
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

def require_center_access(center_id: int):
    """Dependency factory for center access validation"""
    def center_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        # Super admin can access any center
        if current_user.role == UserRole.SUPER_ADMIN:
            return current_user

        # Center admin can only access their own center
        if current_user.center_id != center_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have access to this center"
            )

        return current_user
    return center_checker

def get_scoped_center_id(
    current_user: User = Depends(get_current_user),
    center_id: Optional[int] = None
) -> Optional[int]:
    """
    Return center_id for queries:
    - Super Admin: use provided center_id (or None for all)
    - Center Admin: always use their center_id
    """
    if current_user.role == UserRole.SUPER_ADMIN:
        return center_id  # Can be None (all centers) or specific
    return current_user.center_id  # Always scoped to their center
```

---

### 5) REST Endpoints

#### api/v1/centers.py
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(prefix="/centers", tags=["centers"])

@router.get("", response_model=List[CenterResponse])
def get_centers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Get all centers (Super Admin only)"""
    centers = db.query(Center).filter(Center.is_archived == False).all()
    return centers

@router.post("", response_model=CenterResponse)
def create_center(
    center_data: CenterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Create new center (Super Admin only)"""
    pass

@router.get("/{center_id}", response_model=CenterDetailResponse)
def get_center(
    center_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_center_access(center_id))
):
    """Get center details with stats"""
    pass

@router.get("/{center_id}/stats", response_model=CenterStatsResponse)
def get_center_stats(
    center_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_center_access(center_id))
):
    """Get center statistics (leads, enrollments, etc.)"""
    pass
```

#### api/v1/mdm/curricula.py
```python
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/mdm/curricula", tags=["mdm-global"])

@router.get("", response_model=List[CurriculumResponse])
def get_curricula(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all curricula (all roles can read)"""
    query = db.query(Curriculum).filter(Curriculum.is_archived == False)
    if active_only:
        query = query.filter(Curriculum.active == True)
    return query.offset(skip).limit(limit).all()

@router.post("", response_model=CurriculumResponse)
def create_curriculum(
    curriculum_data: CurriculumCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Create curriculum (Super Admin only)"""
    curriculum = Curriculum(**curriculum_data.dict(), created_by_id=current_user.id)
    db.add(curriculum)
    db.commit()
    db.refresh(curriculum)
    return curriculum

@router.patch("/{curriculum_id}", response_model=CurriculumResponse)
def update_curriculum(
    curriculum_id: int,
    curriculum_data: CurriculumUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN]))
):
    """Update curriculum (Super Admin only)"""
    pass
```

#### api/v1/mdm/batches.py
```python
from fastapi import APIRouter, Depends, Query

router = APIRouter(prefix="/mdm/batches", tags=["mdm-center"])

@router.get("", response_model=List[BatchResponse])
def get_batches(
    center_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get batches (scoped by center)"""
    scoped_center_id = get_scoped_center_id(current_user, center_id)

    query = db.query(Batch).filter(Batch.is_archived == False)

    if scoped_center_id is not None:
        query = query.filter(Batch.center_id == scoped_center_id)

    return query.all()

@router.post("", response_model=BatchResponse)
def create_batch(
    batch_data: BatchCreate,
    center_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_center_access(center_id))
):
    """Create batch (center-scoped)"""
    batch = Batch(
        **batch_data.dict(),
        center_id=center_id,
        created_by_id=current_user.id
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch
```

---

### 6) Query Filtering Example

```python
# Pattern for center-scoped queries
def get_filtered_query(
    db: Session,
    current_user: User,
    center_id: Optional[int] = None
):
    """Example: How to apply center filtering"""

    # Start with base query
    query = db.query(SomeModel).filter(SomeModel.is_archived == False)

    # Apply center scoping
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can filter by specific center or see all
        if center_id is not None:
            query = query.filter(SomeModel.center_id == center_id)
        # If center_id is None, returns all centers
    else:
        # Non-super admins always filtered to their center
        query = query.filter(SomeModel.center_id == current_user.center_id)

    return query
```

---

### 7) Seed Script Outline

```python
# seed_mdm_data.py
from app.core.database import SessionLocal
from app.models import Curriculum, Skill, ClassType

def seed_global_mdm():
    db = SessionLocal()

    # Seed Curricula
    curricula = [
        Curriculum(
            name="Gymnastics Foundation Level 1",
            level="Level 1",
            age_min=3,
            age_max=5,
            description="Basic gymnastics for preschoolers",
            active=True
        ),
        # ... more curricula
    ]

    # Seed Skills
    skills = [
        Skill(
            curriculum_id=1,
            name="Forward Roll",
            category="Gymnastics",
            display_order=1,
            active=True
        ),
        # ... more skills
    ]

    # Seed Class Types
    class_types = [
        ClassType(name="Giggle Worms", age_min=0, age_max=1, duration_minutes=45),
        ClassType(name="Funny Bugs", age_min=1, age_max=2, duration_minutes=45),
        ClassType(name="Birds", age_min=2, age_max=3, duration_minutes=45),
        ClassType(name="Bugs", age_min=3, age_max=4, duration_minutes=45),
        ClassType(name="Beasts", age_min=4, age_max=6, duration_minutes=60),
        ClassType(name="Super Beasts", age_min=6, age_max=9, duration_minutes=60),
        ClassType(name="Good Friends", age_min=3, age_max=5, duration_minutes=60),
        ClassType(name="Grade School", age_min=6, age_max=12, duration_minutes=60),
    ]

    db.bulk_save_objects(curricula + skills + class_types)
    db.commit()
```

---

## C) FRONTEND (Next.js App Router) DELIVERABLES

### 1) Folder Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx              # Root layout
│   │   ├── page.tsx                # Home/redirect
│   │   ├── login/
│   │   │   └── page.tsx
│   │   ├── centers/                # ⭐ NEW
│   │   │   ├── page.tsx            # Centers list
│   │   │   └── [centerId]/
│   │   │       └── page.tsx        # Center overview
│   │   ├── mdm/                    # ⭐ NEW
│   │   │   ├── page.tsx            # MDM landing
│   │   │   ├── global/
│   │   │   │   ├── curricula/
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── skills/
│   │   │   │   │   └── page.tsx
│   │   │   │   └── class-types/
│   │   │   │       └── page.tsx
│   │   │   └── center/
│   │   │       ├── batches/
│   │   │       │   └── page.tsx
│   │   │       └── mappings/
│   │   │           └── page.tsx
│   │   ├── users/                  # ⭐ NEW
│   │   │   ├── page.tsx
│   │   │   └── [userId]/
│   │   │       └── page.tsx
│   │   ├── leads/
│   │   ├── enrollments/
│   │   └── attendance/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppShell.tsx        # Main layout with sidebar
│   │   │   ├── Sidebar.tsx         # Enhanced with center context
│   │   │   ├── CenterContextBar.tsx # ⭐ NEW
│   │   │   └── Navbar.tsx
│   │   ├── ui/                     # Reusable components
│   │   │   ├── DataTable.tsx       # ⭐ NEW
│   │   │   ├── Drawer.tsx          # ⭐ NEW
│   │   │   ├── EmptyState.tsx      # ⭐ NEW
│   │   │   ├── ConfirmDialog.tsx   # ⭐ NEW
│   │   │   └── LoadingSkeleton.tsx # ⭐ NEW
│   │   ├── centers/                # ⭐ NEW
│   │   │   ├── CenterCard.tsx
│   │   │   └── CenterSelector.tsx
│   │   └── mdm/                    # ⭐ NEW
│   │       ├── CurriculumForm.tsx
│   │       ├── SkillForm.tsx
│   │       └── BatchForm.tsx
│   ├── hooks/
│   │   ├── useApi.ts
│   │   ├── useCenterContext.ts     # ⭐ NEW
│   │   └── usePermissions.ts       # ⭐ NEW
│   ├── contexts/
│   │   ├── AuthContext.tsx
│   │   └── CenterContext.tsx       # ⭐ NEW
│   ├── lib/
│   │   ├── api.ts
│   │   └── permissions.ts          # ⭐ NEW
│   └── types/
│       ├── index.ts
│       ├── mdm.ts                  # ⭐ NEW
│       └── center.ts               # ⭐ NEW
```

---

### 2) Layout Components

#### components/layout/CenterContextBar.tsx
```typescript
'use client';

import { useCenterContext } from '@/hooks/useCenterContext';
import { useRouter } from 'next/navigation';

export default function CenterContextBar() {
  const { selectedCenter, setSelectedCenter, centers } = useCenterContext();
  const router = useRouter();

  if (!selectedCenter) return null;

  return (
    <div className="bg-blue-50 border-b border-blue-200 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className="text-2xl">📍</span>
        <span className="text-sm text-gray-600">Viewing:</span>
        <span className="font-semibold text-gray-900">{selectedCenter.name}</span>
      </div>

      <div className="flex items-center gap-3">
        {/* Switch Center Dropdown */}
        <select
          value={selectedCenter.id}
          onChange={(e) => {
            const centerId = parseInt(e.target.value);
            const center = centers.find(c => c.id === centerId);
            if (center) setSelectedCenter(center);
          }}
          className="px-3 py-1 text-sm border border-gray-300 rounded-lg"
        >
          {centers.map(center => (
            <option key={center.id} value={center.id}>
              {center.name}
            </option>
          ))}
        </select>

        {/* Exit Button */}
        <button
          onClick={() => {
            setSelectedCenter(null);
            router.push('/centers');
          }}
          className="px-3 py-1 text-sm text-gray-700 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Exit
        </button>
      </div>
    </div>
  );
}
```

#### components/layout/AppShell.tsx
```typescript
'use client';

import { useAuth } from '@/contexts/AuthContext';
import Sidebar from './Sidebar';
import CenterContextBar from './CenterContextBar';

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();

  if (!user) return <>{children}</>;

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <CenterContextBar />
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
```

---

### 3) Key Pages

#### app/centers/page.tsx
```typescript
'use client';

import { useState } from 'react';
import { useCenters } from '@/hooks/useApi';
import CenterCard from '@/components/centers/CenterCard';

export default function CentersPage() {
  const { centers, loading } = useCenters();

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Centers</h1>
          <p className="text-gray-600">Manage all Little Gym centers</p>
        </div>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg">
          + New Center
        </button>
      </div>

      {loading ? (
        <div>Loading...</div>
      ) : (
        <div className="grid grid-cols-3 gap-6">
          {centers.map(center => (
            <CenterCard key={center.id} center={center} />
          ))}
        </div>
      )}
    </div>
  );
}
```

#### app/mdm/page.tsx
```typescript
'use client';

import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';

export default function MDMPage() {
  const { user } = useAuth();
  const isSuperAdmin = user?.role === 'SUPER_ADMIN';

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Master Data Management</h1>

      {isSuperAdmin && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Global Master Data</h2>
          <div className="grid grid-cols-3 gap-4">
            <MDMCard
              title="Curricula"
              count={12}
              href="/mdm/global/curricula"
            />
            <MDMCard
              title="Skills"
              count={156}
              href="/mdm/global/skills"
            />
            <MDMCard
              title="Class Types"
              count={8}
              href="/mdm/global/class-types"
            />
          </div>
        </section>
      )}

      <section>
        <h2 className="text-xl font-semibold mb-4">Center Master Data</h2>
        <div className="grid grid-cols-3 gap-4">
          <MDMCard
            title="Batches"
            count={15}
            href="/mdm/center/batches"
          />
          <MDMCard
            title="Batch Mappings"
            count={20}
            href="/mdm/center/mappings"
          />
        </div>
      </section>
    </div>
  );
}
```

#### app/mdm/global/curricula/page.tsx
```typescript
'use client';

import { useState } from 'react';
import { useCurricula } from '@/hooks/useApi';
import DataTable from '@/components/ui/DataTable';
import Drawer from '@/components/ui/Drawer';
import CurriculumForm from '@/components/mdm/CurriculumForm';

export default function CurriculaPage() {
  const { curricula, loading, refetch } = useCurricula();
  const [showDrawer, setShowDrawer] = useState(false);

  const columns = [
    { key: 'name', label: 'Name' },
    { key: 'level', label: 'Level' },
    { key: 'age_range', label: 'Age Range', render: (row) => `${row.age_min}-${row.age_max} years` },
    { key: 'active', label: 'Active', render: (row) => row.active ? '✅' : '❌' },
  ];

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Curricula</h1>
        <button
          onClick={() => setShowDrawer(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg"
        >
          + New Curriculum
        </button>
      </div>

      <DataTable
        data={curricula}
        columns={columns}
        loading={loading}
      />

      <Drawer
        open={showDrawer}
        onClose={() => setShowDrawer(false)}
        title="Create New Curriculum"
      >
        <CurriculumForm
          onSuccess={() => {
            setShowDrawer(false);
            refetch();
          }}
        />
      </Drawer>
    </div>
  );
}
```

---

### 4) State Management - Center Context

#### contexts/CenterContext.tsx
```typescript
'use client';

import { createContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import { api } from '@/lib/api';
import type { Center } from '@/types';

interface CenterContextType {
  selectedCenter: Center | null;
  setSelectedCenter: (center: Center | null) => void;
  centers: Center[];
  loading: boolean;
}

export const CenterContext = createContext<CenterContextType>({
  selectedCenter: null,
  setSelectedCenter: () => {},
  centers: [],
  loading: false,
});

export function CenterContextProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [selectedCenter, setSelectedCenterState] = useState<Center | null>(null);
  const [centers, setCenters] = useState<Center[]>([]);
  const [loading, setLoading] = useState(false);

  // Fetch centers for super admin
  useEffect(() => {
    if (user?.role === 'SUPER_ADMIN') {
      fetchCenters();
    } else if (user?.center_id) {
      // Auto-select center for center admin
      fetchUserCenter();
    }
  }, [user]);

  const fetchCenters = async () => {
    setLoading(true);
    try {
      const data = await api.get<Center[]>('/api/v1/centers');
      setCenters(data);
    } catch (error) {
      console.error('Failed to fetch centers:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserCenter = async () => {
    if (!user?.center_id) return;
    setLoading(true);
    try {
      const data = await api.get<Center>(`/api/v1/centers/${user.center_id}`);
      setSelectedCenterState(data);
      setCenters([data]);
    } catch (error) {
      console.error('Failed to fetch user center:', error);
    } finally {
      setLoading(false);
    }
  };

  const setSelectedCenter = (center: Center | null) => {
    setSelectedCenterState(center);
    // Store in localStorage for persistence
    if (center) {
      localStorage.setItem('selectedCenterId', center.id.toString());
    } else {
      localStorage.removeItem('selectedCenterId');
    }
  };

  return (
    <CenterContext.Provider value={{ selectedCenter, setSelectedCenter, centers, loading }}>
      {children}
    </CenterContext.Provider>
  );
}
```

#### hooks/useCenterContext.ts
```typescript
import { useContext } from 'react';
import { CenterContext } from '@/contexts/CenterContext';

export function useCenterContext() {
  const context = useContext(CenterContext);
  if (!context) {
    throw new Error('useCenterContext must be used within CenterContextProvider');
  }
  return context;
}
```

---

### 5) API Client Pattern

#### lib/api.ts (Enhanced)
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getHeaders(): HeadersInit {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Include center context if available
    const centerId = typeof window !== 'undefined' ? localStorage.getItem('selectedCenterId') : null;
    if (centerId) {
      headers['X-Center-Id'] = centerId;
    }

    return headers;
  }

  async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const url = new URL(`${this.baseUrl}${endpoint}`);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }

    return response.json();
  }

  // post, patch, delete methods...
}

export const api = new ApiClient(API_BASE_URL);
```

---

### 6) Reusable UI Components

#### components/ui/DataTable.tsx
```typescript
'use client';

interface Column<T> {
  key: string;
  label: string;
  render?: (row: T) => React.ReactNode;
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  loading?: boolean;
  onRowClick?: (row: T) => void;
}

export default function DataTable<T extends { id: number }>({
  data,
  columns,
  loading,
  onRowClick,
}: DataTableProps<T>) {
  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50 sticky top-0">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((row) => (
            <tr
              key={row.id}
              onClick={() => onRowClick?.(row)}
              className={onRowClick ? 'cursor-pointer hover:bg-gray-50' : ''}
            >
              {columns.map((column) => (
                <td key={column.key} className="px-6 py-4 whitespace-nowrap text-sm">
                  {column.render ? column.render(row) : (row as any)[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

#### components/ui/Drawer.tsx
```typescript
'use client';

interface DrawerProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export default function Drawer({ open, onClose, title, children }: DrawerProps) {
  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="fixed right-0 top-0 h-full w-[500px] bg-white shadow-xl z-50 flex flex-col">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold">{title}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            ✕
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-6">
          {children}
        </div>
      </div>
    </>
  );
}
```

---

### 7) Form Validation with Zod

```typescript
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

const curriculumSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  level: z.string().optional(),
  age_min: z.number().min(0).max(18),
  age_max: z.number().min(0).max(18),
  description: z.string().optional(),
  active: z.boolean().default(true),
});

type CurriculumFormData = z.infer<typeof curriculumSchema>;

export function CurriculumForm({ onSuccess }: { onSuccess: () => void }) {
  const { register, handleSubmit, formState: { errors } } = useForm<CurriculumFormData>({
    resolver: zodResolver(curriculumSchema),
  });

  const onSubmit = async (data: CurriculumFormData) => {
    await api.post('/api/v1/mdm/curricula', data);
    onSuccess();
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-1">Name *</label>
        <input {...register('name')} className="w-full px-3 py-2 border rounded-lg" />
        {errors.name && <p className="text-red-500 text-sm">{errors.name.message}</p>}
      </div>
      {/* More fields... */}
      <button type="submit" className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg">
        Create
      </button>
    </form>
  );
}
```

---

### 8) Tailwind UI Guidelines

**tailwind.config.ts:**
```typescript
export default {
  theme: {
    extend: {
      colors: {
        primary: '#3B82F6',
        success: '#10B981',
        warning: '#F59E0B',
        danger: '#EF4444',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      borderRadius: {
        'xl': '12px',
        '2xl': '16px',
      },
    },
  },
};
```

**Component Class Patterns:**
```typescript
// Card
const cardClasses = "bg-white rounded-xl shadow-sm border border-gray-200 p-6";

// Button Primary
const buttonPrimary = "px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium";

// Input
const inputClasses = "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent";

// Badge
const badgeClasses = "px-2 py-1 text-xs font-semibold rounded-full";
```

---

## IMPLEMENTATION SUMMARY

### Backend Priority Order:
1. ✅ Models (centers, curricula, skills, class_types, batches, mappings)
2. ✅ Schemas (Pydantic Create/Update/Response)
3. ✅ RBAC dependencies (require_role, require_center_access)
4. ✅ Endpoints (centers, mdm/curricula, mdm/skills, mdm/batches)
5. ✅ Seed script (global MDM data)

### Frontend Priority Order:
1. ✅ Center Context (provider, hook, localStorage)
2. ✅ CenterContextBar component
3. ✅ Centers list page + Center overview page
4. ✅ MDM landing page
5. ✅ DataTable + Drawer components
6. ✅ Curricula/Skills/Batches pages with CRUD
7. ✅ Users management page

### Testing Checklist:
- [ ] Super Admin can view all centers
- [ ] Super Admin can enter/exit center context
- [ ] Super Admin can switch between centers
- [ ] Center Admin auto-enters their center context
- [ ] Center Admin cannot switch centers
- [ ] Global MDM CRUD works (Super Admin only)
- [ ] Center MDM CRUD works (center-scoped)
- [ ] All API endpoints enforce RBAC
- [ ] Center context persists across page navigation
- [ ] Leads/Enrollments respect center context

---

This specification provides a complete, simple, and operationally strong foundation for Super Admin and MDM functionality. Start with the backend models and RBAC, then build the frontend center context system, followed by MDM pages.
