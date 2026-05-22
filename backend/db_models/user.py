from datetime import datetime
from database import db, bcrypt

class User(db.Model):
    
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )
    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash = db.Column(
        db.String(255),
        nullable=False,
    )
    full_name = db.Column(
        db.String(100),
        nullable=True,
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
    is_active = db.Column(
        db.Boolean,
        default=True,
    )
    total_reports = db.Column(
        db.Integer,
        default=0,
    )

    reports = db.relationship(
        "Report",
        backref="owner",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def set_password(self, plain_password: str) -> None:
        
        self.password_hash = bcrypt.generate_password_hash(
            plain_password
        ).decode("utf-8")

    def check_password(self, plain_password: str) -> bool:

        return bcrypt.check_password_hash(
            self.password_hash, plain_password
        )

    def to_dict(self) -> dict:
        
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "created_at": self.created_at.isoformat()
            if self.created_at
            else None,
            "is_active": self.is_active,
            "total_reports": self.total_reports,
        }

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
