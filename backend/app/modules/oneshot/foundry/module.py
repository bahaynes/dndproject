from typing import Dict, Any, List

def create_module_manifest(
    module_id: str,
    title: str,
    description: str,
    version: str = "1.0.0",
    authors: List[str] = None
) -> Dict[str, Any]:
    """
    Generate a module.json manifest for FoundryVTT.
    """
    return {
        "id": module_id,
        "title": title,
        "description": description,
        "version": version,
        "compatibility": {
            "minimum": "11",
            "verified": "12"
        },
        "authors": [{"name": a} for a in (authors or ["AI Dungeon Master"])],
        "relationships": {
            "systems": [
                {
                    "id": "dnd5e",
                    "type": "system",
                    "compatibility": {}
                }
            ]
        },
        "packs": [
            {
                "name": "adventures",
                "label": "Adventure Content",
                "path": "packs/adventures.db",
                "type": "JournalEntry"
            }
        ],
        "url": "",
        "manifest": "",
        "download": ""
    }
