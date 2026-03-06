import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.orm import Session

from app.modules.campaigns.models import Campaign
from app.modules.oneshot.service import OneShotService
from app.modules.oneshot.schemas import OneShotGenerateRequest, AdventureStructure, Act, SceneOutline
from app.modules.oneshot.models import GeneratedOneShot
from app.modules.oneshot.foundry.journal import create_journal_entry_data

@pytest.fixture
def campaign(db_session: Session):
    camp = Campaign(name="Test Campaign", discord_guild_id="123456")
    db_session.add(camp)
    db_session.commit()
    db_session.refresh(camp)
    return camp

@pytest.mark.asyncio
async def test_generate_adventure_outline(db_session: Session, campaign: Campaign):
    # Mock LLM Response
    mock_adventure = {
        "title": "The Dark Cave",
        "hook": "Goblins stole the pie.",
        "acts": [
            {
                "title": "Act 1",
                "summary": "Enter the cave.",
                "key_npcs": ["Goblin King"],
                "scenes": [
                    {
                        "name": "Entrance",
                        "type": "exploration",
                        "description": "Dark hole.",
                        "encounters": ["2 Goblins"],
                        "transitions": ["Main Hall"]
                    }
                ]
            }
        ],
        "climax": "Fight the King.",
        "resolution": "Get the pie back."
    }
    
    with patch("app.modules.oneshot.service.llm_service") as mock_llm:
        mock_llm.generate = AsyncMock(return_value=mock_adventure)
        
        service = OneShotService(db_session)
        request = OneShotGenerateRequest(party_size=4, party_level=1)
        
        # Create Job
        job = service.create_generation_job(campaign.id, request)
        assert job.status == "pending"
        
        # Process Job
        await service.process_generation(job.id)
        
        # Verify
        db_session.refresh(job)
        assert job.status == "completed"
        assert job.title == "The Dark Cave"
        assert job.content["title"] == "The Dark Cave"
        
        # Verify LLM called
        mock_llm.generate.assert_called_once()
        call_args = mock_llm.generate.call_args
        assert "JSON" in call_args.kwargs.get("system_prompt", "") or call_args.kwargs.get("json_schema")
        
        # Verify Foundry Formatter
        adventure_struct = AdventureStructure(**job.content)
        journal = create_journal_entry_data(adventure_struct)
        assert journal["name"] == "The Dark Cave"
        assert len(journal["pages"]) >= 3 # Overview, Act 1, Conclusion
