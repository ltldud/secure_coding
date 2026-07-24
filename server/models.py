import uuid
from datetime import datetime, timedelta

from flask_login import UserMixin

from extensions import db


def gen_uuid():
    return str(uuid.uuid4())


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    username = db.Column(db.String(30), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    bio = db.Column(db.String(500), default="", nullable=False)
    balance = db.Column(db.Integer, default=0, nullable=False)

    role = db.Column(db.String(10), default="user", nullable=False)
    status = db.Column(db.String(10), default="active", nullable=False)

    security_question = db.Column(db.String(200), nullable=True)
    security_answer_hash = db.Column(db.String(128), nullable=True)

    report_count = db.Column(db.Integer, default=0, nullable=False)
    failed_login_count = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    products = db.relationship("Product", backref="seller", lazy="dynamic",
                                foreign_keys="Product.seller_id")

    def set_password(self, raw_password: str):
        from security import hash_password
        self.password_hash = hash_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        from security import verify_password
        return verify_password(raw_password, self.password_hash)

    def set_security_answer(self, raw_answer: str):
        from security import hash_answer
        self.security_answer_hash = hash_answer(raw_answer)

    def check_security_answer(self, raw_answer: str) -> bool:
        from security import verify_answer
        if not self.security_answer_hash:
            return False
        return verify_answer(raw_answer, self.security_answer_hash)

    def has_security_question(self) -> bool:
        return bool(self.security_question and self.security_answer_hash)

    def is_locked(self) -> bool:
        return self.locked_until is not None and self.locked_until > datetime.utcnow()

    def register_failed_login(self, limit: int, lock_minutes: int):
        self.failed_login_count += 1
        if self.failed_login_count >= limit:
            self.locked_until = datetime.utcnow() + timedelta(minutes=lock_minutes)
            self.failed_login_count = 0

    def reset_failed_login(self):
        self.failed_login_count = 0
        self.locked_until = None

    def is_admin(self) -> bool:
        return self.role == "admin"

    def is_suspended(self) -> bool:
        return self.status == "suspended"

    @property
    def is_active(self):
        return self.status == "active"


class Product(db.Model):
    __tablename__ = "product"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(2000), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    seller_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=False, index=True)
    image_filename = db.Column(db.String(255), nullable=True)

    status = db.Column(db.String(10), default="active", nullable=False)
    report_count = db.Column(db.Integer, default=0, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


class Report(db.Model):
    __tablename__ = "report"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    reporter_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=False)
    target_type = db.Column(db.String(10), nullable=False)
    target_id = db.Column(db.String(36), nullable=False)
    reason = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(15), default="pending", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("reporter_id", "target_type", "target_id", name="uq_report_once"),
    )


class Conversation(db.Model):
    __tablename__ = "conversation"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_a_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=False)
    user_b_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("user_a_id", "user_b_id", name="uq_conversation_pair"),
    )

    @staticmethod
    def pair(u1: str, u2: str):
        return (u1, u2) if u1 < u2 else (u2, u1)


class Message(db.Model):
    __tablename__ = "message"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    room = db.Column(db.String(80), nullable=False, index=True)
    sender_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=False)
    content = db.Column(db.String(1000), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    sender = db.relationship("User")


class Transaction(db.Model):
    __tablename__ = "transaction"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    sender_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=False)
    receiver_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    kind = db.Column(db.String(10), default="transfer", nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey("product.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class ReadMarker(db.Model):
    """Per-user last-read timestamp for a chat room (global or 1:1), used to
    show an unread indicator in the chat sidebar without polling message
    content on every page load."""
    __tablename__ = "read_marker"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=False)
    room = db.Column(db.String(80), nullable=False)
    last_read_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "room", name="uq_read_marker"),
    )


class AuditLog(db.Model):
    __tablename__ = "audit_log"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    actor_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    target = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
