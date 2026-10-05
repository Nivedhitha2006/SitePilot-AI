from app.database.db import Base,engine
from app.models import models
Base.metadata.create_all(bind=engine)
