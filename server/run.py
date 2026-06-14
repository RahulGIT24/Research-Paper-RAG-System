import uvicorn
from alembic import command
from alembic.config import Config

if __name__ == "__main__":
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    # Start FastAPI
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)