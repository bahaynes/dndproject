import json
from typing import Any, Dict
from ..schemas import AdventureStructure

def create_journal_pages(adventure: AdventureStructure) -> list[Dict[str, Any]]:
    """Convert adventure structure into a list of Foundry journal pages."""
    pages = []
    
    # 0. Overview
    pages.append({
        "name": "00. Overview",
        "type": "text",
        "text": {
            "content": f"<h1>{adventure.title}</h1><p><strong>Hook:</strong> {adventure.hook}</p><h2>Summary</h2><p>{adventure.climax}</p>",
            "format": 1
        },
        "sort": 10000
    })
    
    # Acts
    sort_order = 20000
    for i, act in enumerate(adventure.acts, 1):
        content = f"<h2>{act.title}</h2><p>{act.summary}</p>"
        
        if act.key_npcs:
            content += "<h3>Key NPCs</h3><ul>"
            for npc in act.key_npcs:
                content += f"<li>{npc}</li>"
            content += "</ul>"
            
        content += "<h3>Scenes</h3>"
        for scene in act.scenes:
            content += f"<h4>{scene.name} ({scene.type})</h4>"
            content += f"<p>{scene.description}</p>"
            if scene.encounters:
                content += "<ul>"
                for enc in scene.encounters:
                    content += f"<li>{enc}</li>"
                content += "</ul>"
        
        pages.append({
            "name": f"Act {i}: {act.title}",
            "type": "text",
            "text": {
                "content": content,
                "format": 1
            },
            "sort": sort_order
        })
        sort_order += 10000

    # Resolution
    pages.append({
        "name": "Conclusion",
        "type": "text",
        "text": {
            "content": f"<h2>Resolution</h2><p>{adventure.resolution}</p>",
            "format": 1
        },
        "sort": sort_order
    })

    return pages

def create_journal_entry_data(adventure: AdventureStructure) -> Dict[str, Any]:
    """Returns the full JournalEntry document data (minus _id)."""
    return {
        "name": adventure.title,
        "pages": create_journal_pages(adventure),
        "folder": None,
        "sort": 0,
        "ownership": {"default": 0},
        "flags": {}
    }
