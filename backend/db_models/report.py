import json
from datetime import datetime
from database import db

class Report(db.Model):

    __tablename__ = "reports"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )
    report_uuid = db.Column(
        db.String(36),
        unique=True,
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    filename = db.Column(
        db.String(255),
        nullable=False,
    )
    score = db.Column(
        db.Integer,
        nullable=False,
    )
    verdict = db.Column(
        db.String(20),
        nullable=False,
    )
    confidence = db.Column(
        db.Float,
        nullable=False,
    )
    reasons = db.Column(
        db.Text,
        nullable=False,
    )
    breakdown = db.Column(
        db.Text,
        nullable=False,
    )
    summary = db.Column(
        db.String(500),
        nullable=False,
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    def to_dict(self) -> dict:
        
        try:
            decoded_reasons = json.loads(self.reasons)
        except (json.JSONDecodeError, TypeError):
            decoded_reasons = self.reasons

        try:
            decoded_breakdown = json.loads(self.breakdown)
        except (json.JSONDecodeError, TypeError):
            decoded_breakdown = self.breakdown

        return {
            "id": self.id,
            "report_uuid": self.report_uuid,
            "user_id": self.user_id,
            "filename": self.filename,
            "score": self.score,
            "verdict": self.verdict,
            "confidence": self.confidence,
            "reasons": decoded_reasons,
            "breakdown": decoded_breakdown,
            "summary": self.summary,
            "created_at": self.created_at.isoformat()
            if self.created_at
            else None,
        }

    @classmethod
    def from_analysis(
        cls,
        user_id: int,
        report_uuid: str,
        filename: str,
        score_result: dict,
    ) -> "Report":
        
        return cls(
            report_uuid=report_uuid,
            user_id=user_id,
            filename=filename,
            score=score_result.get("score", 0),
            verdict=score_result.get("verdict", "Unknown"),
            confidence=score_result.get("confidence", 0.0),
            reasons=json.dumps(
                score_result.get("reasons", [])
            ),
            breakdown=json.dumps(
                score_result.get("breakdown", {})
            ),
            summary=score_result.get("summary", ""),
        )

    def __repr__(self) -> str:
        return (
            f"<Report id={self.id} uuid={self.report_uuid!r} "
            f"verdict={self.verdict!r}>"
        )
