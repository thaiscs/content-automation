import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class JobStatus(str, enum.Enum):
    pending = "pending"
    generating = "generating"
    awaiting_review = "awaiting_review"
    changes_requested = "changes_requested"
    approved = "approved"
    uploading_draft = "uploading_draft"
    draft_uploaded = "draft_uploaded"   # lesson exists in Teachable as draft; human publishes manually
    failed = "failed"


class WorkbookJob(Base):
    __tablename__ = "workbook_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id: Mapped[str] = mapped_column(String, nullable=False)
    module_title: Mapped[str] = mapped_column(String, nullable=False)
    learning_objectives: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.pending)
    canva_design_id: Mapped[str | None] = mapped_column(String, nullable=True)
    teachable_lesson_id: Mapped[str | None] = mapped_column(String, nullable=True)
    iteration: Mapped[int] = mapped_column(Integer, default=1)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    review_tokens: Mapped[list["ReviewToken"]] = relationship(back_populates="job")


class ReviewToken(Base):
    __tablename__ = "review_tokens"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(ForeignKey("workbook_jobs.id"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(default=False)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    job: Mapped["WorkbookJob"] = relationship(back_populates="review_tokens")
