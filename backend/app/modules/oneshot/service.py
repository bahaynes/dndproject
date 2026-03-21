from sqlalchemy.orm import Session
from datetime import datetime, timezone
import json
import logging

from .models import GeneratedOneShot
from .schemas import OneShotGenerateRequest, AdventureStructure
from .prompts.adventure import ADVENTURE_SYSTEM_PROMPT
from ...llm_service import llm_service
from ..campaigns.models import Campaign
from ..missions.models import Mission
from ..factions.models import FactionReputation
from ..maps.models import HexMap, Hex
from ..sessions.models import GameSession

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
            created_at=datetime.now(timezone.utc)
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
            job.completed_at = datetime.now(timezone.utc)
            
            self.db.commit()
            logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
            job.status = "failed"
            job.content = {"error": str(e)}
            self.db.commit()

    def _aggregate_context(self, campaign_id: int, params: dict) -> str:
        """Collect Aphtharton-specific campaign data for the LLM prompt."""
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        context_parts = [f"Campaign: {campaign.name}"]

        # Revelation layer
        revelation_layer = params.get("revelation_layer", "early")
        layer_labels = {"early": "Layer One — The Frame Shifts", "mid": "Layer Two — The Council Surfaces", "late": "Layer Three — The Thing Speaks"}
        context_parts.append(f"Revelation Layer: {layer_labels.get(revelation_layer, revelation_layer)}")

        # Faction reputation levels
        reputations = self.db.query(FactionReputation).filter(
            FactionReputation.campaign_id == campaign_id
        ).all()
        if reputations:
            rep_lines = [f"  - {r.faction_name}: {r.level:+d}" for r in reputations]
            context_parts.append("Current Faction Standing:\n" + "\n".join(rep_lines))

        # Mission inspirations
        mission_ids = params.get("mission_ids", [])
        if mission_ids:
            missions = self.db.query(Mission).filter(Mission.id.in_(mission_ids)).all()
            for m in missions:
                context_parts.append(f"Mission Seed: {m.name} — {m.description or 'No description'}")

        # Region focus
        region = params.get("hex_region")
        if region:
            context_parts.append(f"Region Focus: {region}")

        # Discovered hexes with state/faction
        hex_map = self.db.query(HexMap).filter(HexMap.campaign_id == campaign_id).first()
        if hex_map:
            discovered = self.db.query(Hex).filter(
                Hex.map_id == hex_map.id,
                Hex.is_discovered == True  # noqa: E712
            ).all()
            if discovered:
                hex_lines = []
                for h in discovered:
                    line = f"  - ({h.q},{h.r}) {h.terrain}"
                    if h.hex_state and h.hex_state != "wilderness":
                        line += f" [{h.hex_state.replace('_', ' ')}]"
                    if h.controlling_faction:
                        line += f" controlled by {h.controlling_faction}"
                    if h.linked_location_name:
                        line += f" — {h.linked_location_name}"
                    notes = h.player_notes or []
                    if notes:
                        line += f" ({len(notes)} player note(s))"
                    hex_lines.append(line)
                context_parts.append("Known Hex Map (discovered hexes):\n" + "\n".join(hex_lines[:30]))

        # Last 3 completed session field reports
        recent_sessions = (
            self.db.query(GameSession)
            .filter(
                GameSession.campaign_id == campaign_id,
                GameSession.status == "Completed",
                GameSession.field_report != None  # noqa: E711
            )
            .order_by(GameSession.session_date.desc())
            .limit(3)
            .all()
        )
        if recent_sessions:
            report_parts = []
            for s in recent_sessions:
                report_parts.append(f"  [{s.name}]: {s.field_report}")
            context_parts.append("Recent Field Reports from the Board:\n" + "\n".join(report_parts))

        return "\n\n".join(context_parts)

    async def _generate_adventure_outline(self, context: str, params: dict) -> dict:
        """Call LLM service to generate the 3-act structure."""
        user_prompt = f"""
CAMPAIGN CONTEXT:
{context}

PARAMETERS:
- Party Size: {params.get('party_size')}
- Level: {params.get('party_level')}
- Duration: {params.get('duration_hours')} hours
- Tone: {params.get('tone')}
- Revelation Layer: {params.get('revelation_layer', 'early')}

Generate a 3-Act adventure outline for The Inheritors now. The session must be framed as a question, not an objective. Use proper Aphtharton nouns. Match monster tiers and revelation depth to the revelation layer provided.
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
