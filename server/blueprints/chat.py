import time
from collections import defaultdict, deque

from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from flask_socketio import join_room, emit, disconnect

from extensions import db, socketio
from models import User, Conversation, Message

chat_bp = Blueprint("chat", __name__)

GLOBAL_ROOM = "global"
MAX_MESSAGE_LEN = 500
RATE_WINDOW_SECONDS = 10
RATE_MAX_MESSAGES = 8

# In-memory per-user send timestamps for chat rate limiting. Acceptable for a
# single-process dev deployment; a multi-process/production deployment would
# move this to a shared store (e.g. Redis) instead.
_recent_sends = defaultdict(deque)


def _rate_limited(user_id: str) -> bool:
    now = time.time()
    q = _recent_sends[user_id]
    while q and now - q[0] > RATE_WINDOW_SECONDS:
        q.popleft()
    if len(q) >= RATE_MAX_MESSAGES:
        return True
    q.append(now)
    return False


def _get_or_create_conversation(user_a_id, user_b_id):
    a, b = Conversation.pair(user_a_id, user_b_id)
    convo = Conversation.query.filter_by(user_a_id=a, user_b_id=b).first()
    if convo is None:
        convo = Conversation(user_a_id=a, user_b_id=b)
        db.session.add(convo)
        db.session.commit()
    return convo


def _sidebar_conversations(user_id):
    convos = Conversation.query.filter(
        (Conversation.user_a_id == user_id) | (Conversation.user_b_id == user_id)
    ).all()

    rows = []
    for convo in convos:
        other_id = convo.user_b_id if convo.user_a_id == user_id else convo.user_a_id
        other = db.session.get(User, other_id)
        last_message = (
            Message.query.filter_by(room=convo.id)
            .order_by(Message.created_at.desc())
            .first()
        )
        rows.append({
            "room_id": convo.id,
            "other": other,
            "last_message": last_message,
            "sort_key": last_message.created_at if last_message else convo.created_at,
        })

    rows.sort(key=lambda r: r["sort_key"], reverse=True)
    return rows


@chat_bp.route("/chat")
@login_required
def global_chat():
    history = (
        Message.query.filter_by(room=GLOBAL_ROOM)
        .order_by(Message.created_at.desc())
        .limit(50)
        .all()
    )
    history.reverse()
    return render_template(
        "chat_global.html",
        history=history,
        conversations=_sidebar_conversations(current_user.id),
        active_room=GLOBAL_ROOM,
    )


@chat_bp.route("/chat/dm/<username>")
@login_required
def direct_chat(username):
    other = User.query.filter_by(username=username).first_or_404()
    if other.id == current_user.id:
        abort(400)

    convo = _get_or_create_conversation(current_user.id, other.id)
    history = (
        Message.query.filter_by(room=convo.id)
        .order_by(Message.created_at.desc())
        .limit(50)
        .all()
    )
    history.reverse()
    return render_template(
        "chat_dm.html",
        history=history,
        other=other,
        room=convo.id,
        conversations=_sidebar_conversations(current_user.id),
        active_room=convo.id,
    )


def _sender_name(user_id):
    user = db.session.get(User, user_id)
    return user.username if user else "알수없음"


@socketio.on("connect")
def handle_connect():
    if not current_user.is_authenticated:
        disconnect()
        return False


@socketio.on("join")
def handle_join(data):
    if not current_user.is_authenticated:
        disconnect()
        return

    room = str(data.get("room", ""))[:80]
    if room == GLOBAL_ROOM:
        join_room(GLOBAL_ROOM)
        return

    convo = db.session.get(Conversation, room)
    if convo is None or current_user.id not in (convo.user_a_id, convo.user_b_id):
        disconnect()
        return
    join_room(room)


@socketio.on("send_message")
def handle_send_message(data):
    if not current_user.is_authenticated:
        disconnect()
        return

    if current_user.status == "suspended":
        disconnect()
        return

    room = str(data.get("room", ""))[:80]
    content = str(data.get("content", "")).strip()

    if not content or len(content) > MAX_MESSAGE_LEN:
        return

    if room != GLOBAL_ROOM:
        convo = db.session.get(Conversation, room)
        if convo is None or current_user.id not in (convo.user_a_id, convo.user_b_id):
            disconnect()
            return

    if _rate_limited(current_user.id):
        emit("system_notice", {"message": "너무 빠르게 메시지를 보내고 있습니다."})
        return

    msg = Message(room=room, sender_id=current_user.id, content=content)
    db.session.add(msg)
    db.session.commit()

    emit(
        "receive_message",
        {
            "room": room,
            "sender": current_user.username,
            "content": content,
            "created_at": msg.created_at.isoformat(),
        },
        room=room,
    )
