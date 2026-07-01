import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import (
    String,
    text,
    UUID,
    DateTime,
    PrimaryKeyConstraint,
    Index,
    Enum,
    Integer,
)


from app.api.models.base import Base


class NotificationType(str, enum.Enum):
    EMAIL = "email"
    DIGEST = "digest"
    WEBHOOK = "webhook"


class NotificationPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    FAILED = "failed"
    DEAD_LETTERED = "dead_lettered"
    DELIVERED = "delivered"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, server_default=text("uuid_generate_v7()")
    )
    idempotency_key: Mapped[str] = mapped_column(String, unique=True)
    type: Mapped[enum.Enum] = mapped_column(
        Enum(NotificationType, values_callable=lambda e: [m.value for m in e])
    )
    priority: Mapped[enum.Enum] = mapped_column(
        Enum(NotificationPriority, values_callable=lambda e: [m.value for m in e]),
        default=NotificationPriority.MEDIUM,
    )
    status: Mapped[enum.Enum] = mapped_column(
        Enum(NotificationStatus, values_callable=lambda e: [m.value for m in e]),
        default=NotificationStatus.PENDING,
    )
    recipient: Mapped[str | None] = mapped_column(String)
    subject: Mapped[str | None] = mapped_column(String)
    body: Mapped[str | None] = mapped_column(String)
    webhook_url: Mapped[str | None] = mapped_column(String)
    payload: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dead_lettered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    faliure_reason: Mapped[str | None] = mapped_column(String)
    retry_count: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        PrimaryKeyConstraint("id", name="notifications_pk"),
        Index("idx_notifications_type_status", type, status),
        Index("idx_users_status_created_at", status, created_at),
        Index("idx_notifications_idempotency_key", idempotency_key),
    )
