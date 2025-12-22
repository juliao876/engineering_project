from datetime import datetime
from typing import Optional

from sqlalchemy import func, TIMESTAMP, text
from sqlmodel import Field, SQLModel

class BaseSQL(SQLModel):
    created: Optional[datetime] = Field(sa_type=TIMESTAMP(timezone=True),
                                        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
                                        nullable=False,
                                        )
    modified: Optional[datetime] = Field(sa_type=TIMESTAMP(timezone=True),
                                         sa_column_kwargs={"onupdate": func.now()},)