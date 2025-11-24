from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from .service import event_service

router = APIRouter()

@router.get("/", tags=["Events"])
async def events():
    return StreamingResponse(event_service.subscribe(), media_type="text/event-stream")
