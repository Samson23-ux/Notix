import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, PrimaryKeyConstraint, UUID, String, text, ForeignKey, Index


from app.api.models.base import Base


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, server_default=text("uuid_generate_v7()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("users.id", name="webhook_user_id_fk", ondelete="CASCADE")
    )
    endpoint: Mapped[str] = mapped_column(String, unique=True)
    secret: Mapped[str] = mapped_column(String, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        PrimaryKeyConstraint("id", name="webhook_endpoints_pk"),
        Index("idx_webhook_endpoints_id", id, endpoint),
        Index("idx_webhook_endpoints_user_id", user_id, endpoint),
    )
