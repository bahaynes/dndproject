from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from ...database import Base

class GeneratedOneShot(Base):
    __tablename__ = "generated_oneshots"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    
    title = Column(String, nullable=True)
    summary = Column(String, nullable=True)
    
    status = Column(String, default="pending") # pending, processing, completed, failed
    
    # Generation metadata
    generation_params = Column(JSON, nullable=False)  # Stored request parameters
    llm_model_used = Column(String, nullable=True)
    tokens_used = Column(Integer, default=0)
    
    # Output content
    content = Column(JSON, nullable=True)            # Raw generated content (adventure structure)
    foundry_module_path = Column(String, nullable=True) # Path to ZIP file
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    campaign = relationship("Campaign")
