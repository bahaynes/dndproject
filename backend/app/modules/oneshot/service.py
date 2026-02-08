from sqlalchemy.orm import Session
from datetime import datetime
import json
import logging

from .models import GeneratedOneShot
from .schemas import OneShotGenerateRequest, AdventureStructure
from .prompts.adventure import ADVENTURE_SYSTEM_PROMPT
from ...llm_service import llm_service
from ..campaigns.models import Campaign
from ..missions.models import Mission

logger = logging.getLogger(__name__)

class OneShotService:
    def __init__(self, db: Session):
        self.db = db

    def create_generation_job(self, campaign_id: int, request: OneShotGenerateRequest) -> GeneratedOneShot:
        """Create a pending job entry in the database."""
        db_job = GeneratedOneShot(
            campaign_id=campaign_id,
            status="pending",
            generation_params=request.model_dump(),
            created_at=datetime.utcnow()
        )
        self.db.add(db_job)
        self.db.commit()
        self.db.refresh(db_job)
        return db_job

    async def process_generation(self, job_id: int):
        """
        Background task to run the generation pipeline.
        Phase 1: Generate Adventure Outline.
        """
        logger.info(f"Starting generation job {job_id}")
        job = self.db.query(GeneratedOneShot).filter(GeneratedOneShot.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        try:
            job.status = "processing"
            self.db.commit()
            
            # 1. Aggregate Context
            context = self._aggregate_context(job.campaign_id, job.generation_params)
            
            # 2. Generate Adventure via LLM
            adventure_json = await self._generate_adventure_outline(context, job.generation_params)
            
            # 3. Save Results
            job.content = adventure_json
            job.title = adventure_json.get("title", "Untitled Adventure")
            job.summary = adventure_json.get("hook", "")
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
            job.status = "failed"
            self.db.commit()

    def _aggregate_context(self, campaign_id: int, params: dict) -> str:
        """Collect relevant campaign data for the LLM prompt."""
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        context_parts = [f"Campaign Name: {campaign.name}"]
        
        # Add selected missions if any
        mission_ids = params.get("mission_ids", [])
        if mission_ids:
            missions = self.db.query(Mission).filter(Mission.id.in_(mission_ids)).all()
            for m in missions:
                context_parts.append(f"Mission Inspiration: {m.name} - {m.description}")
        
        # Add region info
        region = params.get("hex_region")
        if region:
            context_parts.append(f"Region Focus: {region}")
            
        return "\n".join(context_parts)

    async def _generate_adventure_outline(self, context: str, params: dict) -> dict:
        """Call LLM service to generate the 3-act structure."""
        user_prompt = f"""
        CONTEXT:
        {context}

        PARAMETERS:
        - Party Size: {params.get('party_size')}
        - Level: {params.get('party_level')}
        - Duration: {params.get('duration_hours')} hours
        - Tone: {params.get('tone')}
        
        Generate a 3-Act adventure outline now.
        """
        
        # Using the schema logic purely for prompt instruction in Phase 1
        # In future phases we might pass the schema object directly if LLM library supports it
        response = await llm_service.generate(
            system_prompt=ADVENTURE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            json_schema=AdventureStructure.model_json_schema(),
            temperature=0.7
        )
        
        if isinstance(response, str):
            import json
            # Attempt to parse if returned as string (fallback)
            return json.loads(response)
        return response

    def get_job(self, job_id: int) -> GeneratedOneShot:
        return self.db.query(GeneratedOneShot).filter(GeneratedOneShot.id == job_id).first()

    def list_jobs(self, campaign_id: int):
        return self.db.query(GeneratedOneShot)\
            .filter(GeneratedOneShot.campaign_id == campaign_id)\
            .order_by(GeneratedOneShot.created_at.desc())\
            .all()
