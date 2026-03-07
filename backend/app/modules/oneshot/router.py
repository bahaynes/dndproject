from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from ...dependencies import get_db, get_current_user
from ...database import SessionLocal
from ...modules.auth.models import User
from .schemas import OneShotGenerateRequest, OneShotResponse, OneShotDetailResponse
from .service import OneShotService, run_generation_background

router = APIRouter(
    prefix="/oneshot",
    tags=["oneshot"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[OneShotResponse])
def list_oneshots(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all generated one-shots for the user's campaign.
    """
    if not current_user.campaign_id:
        return []

    service = OneShotService(db)
    return service.list_jobs(current_user.campaign_id)

@router.post("/generate", response_model=OneShotResponse)
async def generate_oneshot(
    request: OneShotGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start a background job to generate a One-Shot adventure.
    """
    # Verify campaign access (User must belong to a campaign)
    if not current_user.campaign_id:
        raise HTTPException(status_code=400, detail="User not part of a campaign")

    service = OneShotService(db)
    job = service.create_generation_job(current_user.campaign_id, request)

    # Launch background processing with its own DB session so the request
    # session being closed after response does not kill the task.
    background_tasks.add_task(run_generation_background, job.id, SessionLocal)

    return job

@router.get("/{job_id}", response_model=OneShotDetailResponse)
def get_oneshot_status(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get status and results of a generation job.
    """
    service = OneShotService(db)
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="One-shot not found")

    # Security check
    if job.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this one-shot")

    return job

@router.get("/{job_id}/foundry-json")
def get_oneshot_foundry_json(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the FoundryVTT Journal Entry JSON for the generated adventure.
    """
    service = OneShotService(db)
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="One-shot not found")

    if job.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not job.content:
        raise HTTPException(status_code=400, detail="Generation not complete")

    from .schemas import AdventureStructure
    from .foundry.journal import create_journal_entry_data

    try:
        structure = AdventureStructure(**job.content)
        journal_data = create_journal_entry_data(structure)
        return journal_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to format for Foundry: {str(e)}")
