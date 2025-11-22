# Import all models to ensure they are registered with Base.metadata
from .modules.auth import models as auth_models
from .modules.characters import models as char_models
from .modules.items import models as item_models
from .modules.missions import models as mission_models
from .modules.sessions import models as session_models
from .modules.map import models as map_models
