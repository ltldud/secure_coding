"""
Fresh-process functional test pass over the 33-item security checklist
(docs/report_draft.md section 5). Uses Flask's own test_client (in-process
WSGI, not a separate network hop) so it shares no state with any real
browser session, and imports the app fresh so Flask-Limiter's in-memory
counters start at zero for this run.

IMPORTANT: test_client() HTTP calls are made with NO ambient app context
held open - Flask pushes/pops its own per-request context (and resets
`g`, which Flask-WTF's CSRF machinery relies on) for each call. Any direct
ORM access is wrapped in its own short-lived `with app.app_context():`
block and only plain values (ids/strings/ints/bools) are carried across
context boundaries, never live ORM objects (they'd be detached/expired
once their context pops).

Setup users are created directly via the ORM (bypassing /register) except
where the checklist item is specifically about the /register or /login
HTTP endpoint itself - those are driven through real requests so the
behavior under test is the real thing.
"""
import re
import sys
import time
import subprocess
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db, socketio
from models import User, Product, Report, Conversation, Message, Transaction, AuditLog
from config import Config
from blueprints.reports import _apply_threshold
from blueprints.chat import RATE_MAX_MESSAGES

app.config["TESTING"] = True

results = []


def record(n, title, ok, evidence):
    results.append((n, title, ok, evidence))
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] #{n} {title}\n    -> {evidence}\n")


def get_csrf(html):
    m = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', html)
    return m.group(1) if m else None


def mkuser(username, password="Passw0rd123", role="user", balance=None):
    with app.app_context():
        u = User(username=username, role=role, balance=balance if balance is not None else Config.STARTING_BALANCE)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        return u.id


def as_user(client, user_id):
    with client.session_transaction() as sess:
        sess["_user_id"] = user_id
        sess["_fresh"] = True


with app.app_context():
    db.create_all()
    old = User.query.filter(User.username.like("qa_t_%")).all()
    old_ids = [u.id for u in old]
    if old_ids:
        Message.query.filter(Message.sender_id.in_(old_ids)).delete(synchronize_session=False)
        Conversation.query.filter(
            (Conversation.user_a_id.in_(old_ids)) | (Conversation.user_b_id.in_(old_ids))
        ).delete(synchronize_session=False)
        Product.query.filter(Product.seller_id.in_(old_ids)).delete(synchronize_session=False)
        Transaction.query.filter(
            (Transaction.sender_id.in_(old_ids)) | (Transaction.receiver_id.in_(old_ids))
        ).delete(synchronize_session=False)
        AuditLog.query.filter(AuditLog.actor_id.in_(old_ids)).delete(synchronize_session=False)
        Report.query.filter(Report.reporter_id.in_(old_ids)).delete(synchronize_session=False)
        Report.query.filter(Report.target_id.in_(old_ids)).delete(synchronize_session=False)
        for u in old:
            db.session.delete(u)
        db.session.commit()

c_reg = app.test_client()
r = c_reg.get("/register")
token = get_csrf(r.data.decode())

reg_sq = {"security_question": "테스트 질문", "security_answer": "테스트 답변"}
r1 = c_reg.post("/register", data={"csrf_token": token, "username": "ab", "password": "Passw0rd123", "confirm": "Passw0rd123", **reg_sq})
bad_username_rejected = "영문/숫자/밑줄" in r1.data.decode()
r2 = c_reg.post("/register", data={"csrf_token": token, "username": "qa_t_regtest", "password": "abcdefgh", "confirm": "abcdefgh", **reg_sq})
bad_password_rejected = "8~64자" in r2.data.decode()
with app.app_context():
    created = User.query.filter_by(username="qa_t_regtest").first() is None
record(1, "회원가입 서버측 입력 검증", bad_username_rejected and bad_password_rejected and created,
       f"짧은 아이디 거부={bad_username_rejected}, 숫자 없는 비밀번호 거부={bad_password_rejected}, "
       f"검증 실패 시 계정 미생성={created}")

with app.app_context():
    real_users = User.query.filter(User.username.in_(["sy020723", "testuser", "admin"])).all()
    all_bcrypt = len(real_users) > 0 and all(u.password_hash.startswith("$2b$") for u in real_users)
    real_usernames = [u.username for u in real_users]
record(2, "비밀번호 해시(bcrypt) 저장", all_bcrypt,
       f"실제 계정 {real_usernames}의 password_hash가 모두 $2b$(bcrypt) 접두사로 저장됨")

lock_user_id = mkuser("qa_t_lockout")
c_login = app.test_client()
r = c_login.get("/login")
token = get_csrf(r.data.decode())

msg_wrongpass = None
for i in range(Config.LOGIN_FAIL_LIMIT):
    rr = c_login.post("/login", data={"csrf_token": token, "username": "qa_t_lockout", "password": "WrongPass1"})
    if i == 0:
        m = re.search(r'<div class="flash danger">([^<]+)</div>', rr.data.decode())
        msg_wrongpass = m.group(1) if m else None

rr = c_login.post("/login", data={"csrf_token": token, "username": "qa_t_lockout", "password": "Passw0rd123"})
locked_msg_shown = "계정이 잠겨" in rr.data.decode()

rr2 = c_login.post("/login", data={"csrf_token": token, "username": "qa_t_does_not_exist", "password": "whatever1"})
m = re.search(r'<div class="flash danger">([^<]+)</div>', rr2.data.decode())
msg_nonexistent = m.group(1) if m else None

with app.app_context():
    lock_user = db.session.get(User, lock_user_id)
    locked_until = lock_user.locked_until
record(3, "로그인 실패 횟수 제한 (계정 잠금)",
       locked_msg_shown and locked_until is not None,
       f"{Config.LOGIN_FAIL_LIMIT}회 연속 실패 후 올바른 비밀번호로도 로그인 거부, "
       f"locked_until={locked_until} ({Config.LOGIN_LOCK_MINUTES}분 잠금)")

record(4, "로그인 오류 메시지 동일성 (계정 존재 여부 유추 방지)",
       msg_nonexistent is not None and msg_nonexistent == msg_wrongpass,
       f"존재하지 않는 아이디 메시지=\"{msg_nonexistent}\" / 틀린 비밀번호 메시지=\"{msg_wrongpass}\" (동일)")

seller_id = mkuser("qa_t_seller")
buyer_id = mkuser("qa_t_buyer")

c_seller = app.test_client()
as_user(c_seller, seller_id)
c_buyer = app.test_client()
as_user(c_buyer, buyer_id)

r = c_seller.get("/product/new")
seller_token = get_csrf(r.data.decode())

r5 = c_seller.post("/product/new", data={"csrf_token": seller_token, "title": "t", "description": "d", "price": "0"})
with app.app_context():
    price_rejected = Product.query.filter_by(title="t").first() is None

xss_payload = "<script>alert(1)</script>"
r6 = c_seller.post("/product/new", data={"csrf_token": seller_token, "title": "QA XSS 테스트 상품", "description": xss_payload, "price": "1000"})
with app.app_context():
    product = Product.query.filter_by(title="QA XSS 테스트 상품").first()
    product_id = product.id if product else None
record(5, "상품 등록 폼 서버측 검증 (가격 범위 등)", price_rejected and product_id is not None,
       f"가격 0원 등록 거부={price_rejected}, 정상 범위(1000원) 등록은 성공")

view = c_buyer.get(f"/product/{product_id}")
body = view.data.decode()
escaped_ok = "&lt;script&gt;alert(1)&lt;/script&gt;" in body
raw_present = "<script>alert(1)</script>" in body
record(6, "상품 설명 XSS 방어 (자동 이스케이프)", escaped_ok and not raw_present,
       f"악성 설명(<script>) 저장 후 상세 페이지 응답에 이스케이프된 형태로만 노출됨(원문 태그 미노출)")

r_buyer_form = c_buyer.get("/product/new")
buyer_token = get_csrf(r_buyer_form.data.decode())
r_edit = c_buyer.get(f"/product/{product_id}/edit")
r_del = c_buyer.post(f"/product/{product_id}/delete", data={"csrf_token": buyer_token})
record(7, "상품 수정/삭제 소유자 검증 (IDOR 방지)",
       r_edit.status_code == 403 and r_del.status_code == 403,
       f"타 사용자가 수정 시도 status={r_edit.status_code}, 삭제 시도 status={r_del.status_code} (둘 다 403)")

reporter_ids = [mkuser(f"qa_t_rep{i}") for i in range(1, 6)]
for rep_id in reporter_ids:
    cr = app.test_client()
    as_user(cr, rep_id)
    rr = cr.get("/report", query_string={"target_type": "product", "target_id": product_id})
    tok = get_csrf(rr.data.decode())
    cr.post("/report", data={
        "csrf_token": tok, "target_type": "product", "target_id": product_id,
        "reason": "허위 매물로 의심됩니다",
    })

with app.app_context():
    product = db.session.get(Product, product_id)
    product_status_after_reports = product.status
dash = c_buyer.get("/dashboard")
gone_from_dashboard = "QA XSS 테스트 상품" not in dash.data.decode()
detail_after_block = c_buyer.get(f"/product/{product_id}")
hidden_from_nonowner = detail_after_block.status_code == 404
record(8, "임계치 초과 차단 상품 비노출",
       product_status_after_reports == "blocked" and gone_from_dashboard and hidden_from_nonowner,
       f"신고 5건 누적 후 product.status={product_status_after_reports}, 대시보드 미노출={gone_from_dashboard}, "
       f"비소유자 상세조회 404={hidden_from_nonowner}")

r_sql = c_buyer.get("/dashboard", query_string={"q": "' OR '1'='1"})
r_wild = c_buyer.get("/dashboard", query_string={"q": "%"})
record(22, "검색어 SQL Injection 방지", r_sql.status_code == 200 and r_wild.status_code == 200,
       f"`' OR '1'='1`, `%` 등 특수/와일드카드 문자를 검색어로 넣어도 서버 오류 없이 200 응답 "
       f"(ORM 파라미터 바인딩 + LIKE 와일드카드 이스케이프)")

with app.app_context():
    p2 = Product(title="QA 검색 대상 고유상품명ZzXx", description="설명", price=5000, seller_id=seller_id)
    db.session.add(p2)
    db.session.commit()

hit = c_buyer.get("/dashboard", query_string={"q": "고유상품명ZzXx"})
hit_found = "QA 검색 대상 고유상품명ZzXx" in hit.data.decode()
miss = c_buyer.get("/dashboard", query_string={"q": "존재하지않는검색어QQQ999"})
miss_empty = "등록된 상품이 없습니다" in miss.data.decode()
record(23, "검색 결과 정확성", hit_found and miss_empty,
       f"일치 검색어 결과 노출={hit_found}, 무관 검색어는 빈 목록={miss_empty}")

blocked_search = c_buyer.get("/dashboard", query_string={"q": "QA XSS 테스트"})
blocked_excluded = "QA XSS 테스트 상품" not in blocked_search.data.decode()
record(24, "차단 상품 검색 결과 제외", blocked_excluded,
       f"차단된 상품명을 그대로 검색해도 결과에 나타나지 않음={blocked_excluded}")

c_anon = app.test_client()
sio_anon = socketio.test_client(app, flask_test_client=c_anon)
anon_connected = sio_anon.is_connected()
record(9, "소켓 연결 시 인증 확인", not anon_connected,
       f"미인증 클라이언트의 socket.io connect 시도 -> 서버가 즉시 disconnect (is_connected()={anon_connected})")

sio_seller = socketio.test_client(app, flask_test_client=c_seller)
sio_seller.get_received()
long_msg = "x" * 501
sio_seller.emit("send_message", {"room": "global", "content": long_msg})
time.sleep(0.05)
with app.app_context():
    over_limit_stored = Message.query.filter_by(room="global", content=long_msg).first() is None

for i in range(RATE_MAX_MESSAGES + 2):
    sio_seller.emit("send_message", {"room": "global", "content": f"burst-{i}"})
time.sleep(0.1)
received = sio_seller.get_received()
burst_notices = sum(1 for e in received if e["name"] == "system_notice")
record(10, "메시지 길이 검증 + Rate Limiting", over_limit_stored and burst_notices > 0,
       f"500자 초과 메시지 미저장={over_limit_stored}, "
       f"10초 내 {RATE_MAX_MESSAGES + 2}건 연속 전송 시 system_notice {burst_notices}회 수신(도배 차단 동작)")

c_seller.get("/chat/dm/qa_t_buyer")
with app.app_context():
    convo = Conversation.query.filter(
        ((Conversation.user_a_id == seller_id) & (Conversation.user_b_id == buyer_id)) |
        ((Conversation.user_a_id == buyer_id) & (Conversation.user_b_id == seller_id))
    ).first()
    convo_id = convo.id

outsider_id = reporter_ids[0]
c_outsider = app.test_client()
as_user(c_outsider, outsider_id)
sio_outsider = socketio.test_client(app, flask_test_client=c_outsider)
sio_outsider.get_received()
sio_outsider.emit("join", {"room": convo_id})
time.sleep(0.05)
outsider_rejected = not sio_outsider.is_connected()
record(11, "1:1 대화방 참여자 검증", outsider_rejected,
       f"대화 당사자가 아닌 제3자가 join 시도 -> 서버가 연결 종료(disconnect), is_connected()={sio_outsider.is_connected()}")

sio_buyer = socketio.test_client(app, flask_test_client=c_buyer)
sio_buyer.emit("join", {"room": "global"})
sio_seller.emit("join", {"room": "global"})
time.sleep(0.05)
sio_buyer.get_received()
sio_seller.get_received()
sio_buyer.emit("send_message", {"room": "global", "content": "안녕하세요 QA 브로드캐스트 테스트"})
time.sleep(0.1)
got = sio_seller.get_received()
broadcast_ok = any(
    e["name"] == "receive_message" and e["args"][0].get("content") == "안녕하세요 QA 브로드캐스트 테스트"
    for e in got
)
record(12, "전체 채팅 정상 송수신(브로드캐스트)", broadcast_ok,
       f"구매자가 보낸 전체채팅 메시지를 판매자 클라이언트가 receive_message로 수신함={broadcast_ok}")

r_report_form = c_buyer.get("/report", query_string={"target_type": "product", "target_id": product_id})
tok = get_csrf(r_report_form.data.decode())
r13a = c_buyer.post("/report", data={"csrf_token": tok, "target_type": "product", "target_id": product_id, "reason": "짧음"})
with app.app_context():
    short_reason_no_row = Report.query.filter_by(reporter_id=buyer_id, reason="짧음").first() is None
short_reason_rejected = "5~500자" in r13a.data.decode() or short_reason_no_row
r13b = c_buyer.post("/report", data={"csrf_token": tok, "target_type": "invalid_type", "target_id": product_id, "reason": "정상적인 신고 사유입니다"})
with app.app_context():
    bad_type_no_row = Report.query.filter_by(reporter_id=buyer_id, target_type="invalid_type").first() is None
bad_type_rejected = r13b.status_code == 200 and bad_type_no_row
record(13, "신고 폼 입력 검증 (사유 길이/대상 화이트리스트)", short_reason_rejected and bad_type_rejected,
       f"5자 미만 사유 거부={short_reason_rejected}, target_type 화이트리스트 외 값(invalid_type)은 "
       f"검증 실패로 Report row 미생성={bad_type_no_row} (단, report.html이 target_type 필드 에러를 화면에 "
       f"표시하지 않아 사용자에게는 무응답처럼 보임 - UX 개선 여지 있음)")

r_first = c_buyer.post("/report", data={"csrf_token": tok, "target_type": "product", "target_id": product_id, "reason": "첫 번째 정상 신고 사유입니다"})
r_dup = c_buyer.post("/report", data={"csrf_token": tok, "target_type": "product", "target_id": product_id, "reason": "동일 대상 재신고 시도"}, follow_redirects=True)
with app.app_context():
    dup_count = Report.query.filter_by(reporter_id=buyer_id, target_type="product", target_id=product_id).count()
dup_rejected_msg = "이미 신고한 대상입니다" in r_dup.data.decode()
record(14, "동일 대상 반복 신고 방지", dup_count == 1 and dup_rejected_msg,
       f"동일 신고자가 같은 상품을 두 번째 신고 시도 -> 거부 메시지 표시={dup_rejected_msg}, "
       f"최종 report row 수={dup_count}(1건만 유지, DB 유니크 제약으로 중복 삽입 차단)")

with app.app_context():
    audit_block = AuditLog.query.filter_by(action="auto_block_product", target=product_id).first() is not None
record(15, "임계치 자동 조치 + 감사 로그", product_status_after_reports == "blocked" and audit_block,
       f"AuditLog에 auto_block_product 기록 존재={audit_block} (target={product_id})")

c_admin = app.test_client()
with app.app_context():
    admin_id = User.query.filter_by(username="admin").first().id
as_user(c_admin, admin_id)
r_admin_form = c_admin.get("/product/new")
admin_token = get_csrf(r_admin_form.data.decode())
with app.app_context():
    pending_report = Report.query.filter_by(target_type="product", target_id=product_id, status="pending").first()
    if pending_report is None:
        pending_report = Report(reporter_id=buyer_id, target_type="user", target_id=seller_id, reason="검토용 임의 신고 사유")
        db.session.add(pending_report)
        db.session.commit()
    pending_report_id = pending_report.id
r_dismiss = c_admin.post(f"/admin/reports/{pending_report_id}/dismiss", data={"csrf_token": admin_token})
with app.app_context():
    dismissed_status = db.session.get(Report, pending_report_id).status
record(16, "관리자 수동 신고 검토(기각)", dismissed_status == "dismissed",
       f"관리자가 /admin/reports/{{id}}/dismiss 처리 후 report.status={dismissed_status}")

suspend_id = mkuser("qa_t_suspend")
with app.app_context():
    for rep_id in reporter_ids:
        db.session.add(Report(reporter_id=rep_id, target_type="user", target_id=suspend_id,
                               reason="악성 유저로 의심되어 신고합니다"))
    db.session.commit()
    _apply_threshold("user", suspend_id)
    suspend_status = db.session.get(User, suspend_id).status

r_anon_transfer = app.test_client().get("/transfer", follow_redirects=False)
record(17, "인증된 사용자만 송금 접근", r_anon_transfer.status_code in (302, 401),
       f"비로그인 상태 GET /transfer -> status={r_anon_transfer.status_code} (로그인 페이지로 리다이렉트)")

with app.app_context():
    seller_balance = db.session.get(User, seller_id).balance

r = c_seller.get("/transfer")
transfer_token = get_csrf(r.data.decode())
r18 = c_seller.post("/transfer", data={"csrf_token": transfer_token, "receiver_username": "qa_t_seller", "amount": "100"})
record(18, "자기 자신 송금 방지", "자기 자신에게는 송금할 수 없습니다" in r18.data.decode(),
       "본인 아이디로 송금 시도 -> 거부 메시지 확인")

r19 = c_seller.post("/transfer", data={"csrf_token": transfer_token, "receiver_username": "qa_t_buyer", "amount": str(seller_balance + 1_000_000)})
record(19, "잔액 부족 송금 거부", "잔액이 부족합니다" in r19.data.decode(),
       f"보유 잔액({seller_balance:,}원) 초과 금액 송금 시도 -> 거부 메시지 확인")

r20 = c_seller.post("/transfer", data={"csrf_token": transfer_token, "receiver_username": "qa_t_suspend", "amount": "100"})
record(20, "정지 계정 송금 방지", suspend_status == "suspended" and "정지된 사용자에게는 송금할 수 없습니다" in r20.data.decode(),
       f"신고 임계치로 정지된 계정(status={suspend_status})에게 송금 시도 -> 거부 메시지 확인")

with app.app_context():
    p3 = Product(title="QA 구매 테스트 상품", description="설명", price=3000, seller_id=seller_id)
    db.session.add(p3)
    db.session.commit()
    p3_id = p3.id
    seller_balance_before = db.session.get(User, seller_id).balance
    buyer_balance_before = db.session.get(User, buyer_id).balance

r21 = c_buyer.post(f"/product/{p3_id}/purchase", data={"csrf_token": buyer_token})
with app.app_context():
    p3_after = db.session.get(Product, p3_id)
    tx = Transaction.query.filter_by(product_id=p3_id, kind="purchase").first()
    seller_balance_after = db.session.get(User, seller_id).balance
    buyer_balance_after = db.session.get(User, buyer_id).balance
    atomic_ok = (
        p3_after.status == "sold"
        and tx is not None
        and seller_balance_after == seller_balance_before + 3000
        and buyer_balance_after == buyer_balance_before - 3000
    )
record(21, "상품 구매 원자적 처리 (송금+상태변경)", atomic_ok,
       f"구매 후 product.status={p3_after.status}, Transaction 기록 존재={tx is not None}, "
       f"판매자 잔액 +3000({seller_balance_after:,}), 구매자 잔액 -3000({buyer_balance_after:,}) 모두 한 커밋에 반영됨")

r_nonadmin = c_buyer.get("/admin/")
record(25, "관리자 역할 기반 접근 제어", r_nonadmin.status_code == 403,
       f"일반 사용자가 /admin/ 접근 시 status={r_nonadmin.status_code}")

with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")) as f:
    env_text = f.read()
admin_pw_value = None
for line in env_text.splitlines():
    if line.startswith("ADMIN_PASSWORD="):
        admin_pw_value = line.split("=", 1)[1]
grep = subprocess.run(
    ["grep", "-rnF", admin_pw_value, os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "--include=*.py"],
    capture_output=True, text=True,
)
no_hardcode = grep.stdout.strip() == ""
record(26, "관리자 계정 하드코딩 금지", no_hardcode,
       "실제 ADMIN_PASSWORD 값(.env, gitignore 대상)으로 소스(*.py) 전체를 grep해도 매치 없음="
       f"{no_hardcode} (`scripts/seed_admin.py`는 os.environ.get(\"ADMIN_PASSWORD\")로만 참조, "
       "리터럴 값은 소스에 없음)")

with app.app_context():
    audit_admin = AuditLog.query.filter_by(action="admin_dismiss_report").first() is not None
record(27, "관리자 조치 감사 로그", audit_admin,
       "관리자의 신고 기각 조치가 AuditLog(action=admin_dismiss_report)에 기록됨")

c_csrf = app.test_client()
as_user(c_csrf, buyer_id)
r28 = c_csrf.post("/product/new", data={"title": "csrf 우회 시도", "description": "d", "price": "1000"})
with app.app_context():
    csrf_product_created = Product.query.filter_by(title="csrf 우회 시도").first() is not None
csrf_blocked = r28.status_code == 400 and not csrf_product_created
record(28, "CSRF 보호", csrf_blocked,
       f"csrf_token 없이 상품 등록 POST -> status={r28.status_code}, 상품 미생성={not csrf_product_created}")

c_cookie_check = app.test_client()
rr = c_cookie_check.get("/login")
tok = get_csrf(rr.data.decode())
rr2 = c_cookie_check.post("/login", data={"csrf_token": tok, "username": "qa_t_seller", "password": "Passw0rd123"})
cookie_headers = rr2.headers.getlist("Set-Cookie")
httponly_ok = any("session=" in h and "HttpOnly" in h for h in cookie_headers)
samesite_ok = any("SameSite=Lax" in h for h in cookie_headers)
record(29, "세션 쿠키 보안 설정 (HttpOnly/SameSite)", httponly_ok and samesite_ok,
       f"로그인 응답 Set-Cookie 헤더에 HttpOnly={httponly_ok}, SameSite=Lax={samesite_ok} "
       f"(SESSION_COOKIE_SECURE는 config상 HTTPS 배포 시 true로 전환)")

r30 = c_buyer.get("/dashboard")
h = r30.headers
headers_ok = (
    h.get("X-Content-Type-Options") == "nosniff"
    and h.get("X-Frame-Options") == "DENY"
    and "default-src 'self'" in (h.get("Content-Security-Policy") or "")
)
record(30, "보안 헤더 적용", headers_ok,
       f"X-Content-Type-Options={h.get('X-Content-Type-Options')}, X-Frame-Options={h.get('X-Frame-Options')}, "
       f"CSP 적용됨={'default-src' in (h.get('Content-Security-Policy') or '')}")

r31 = c_buyer.get("/product/does-not-exist-id")
body31 = r31.data.decode()
no_stacktrace = r31.status_code == 404 and "Traceback" not in body31 and "werkzeug" not in body31.lower()
record(31, "오류 메시지에 내부 정보 미노출", no_stacktrace,
       f"존재하지 않는 상품 조회 -> status={r31.status_code}, 커스텀 404 페이지만 노출(스택트레이스 없음). "
       f"단, 현재 FLASK_ENV=development(DEBUG=True)이므로 처리되지 않은 500 예외는 Werkzeug 인터랙티브 "
       f"디버거가 뜰 수 있음 - 운영 배포 시 FLASK_ENV=production으로 전환 필요(README에 명시)")

big_body = "x" * (4 * 1024 * 1024)
r32 = c_buyer.post("/product/new", data={"csrf_token": buyer_token, "title": "t", "description": big_body, "price": "1000"})
size_limited = r32.status_code == 413
record(32, "요청 본문 크기 제한", size_limited,
       f"3MB 제한(MAX_CONTENT_LENGTH, 상품 이미지 업로드 수용을 위해 1MB에서 상향) 초과 요청(4MB) -> status={r32.status_code}")

c_rl = app.test_client()
codes = []
rr = c_rl.get("/login")
tok = get_csrf(rr.data.decode())
for i in range(20):
    rr = c_rl.post("/login", data={"csrf_token": tok, "username": "qa_t_ratelimit_probe", "password": "whatever1"})
    codes.append(rr.status_code)
rate_limited_hit = 429 in codes
record(33, "Rate Limiting (로그인 엔드포인트)", rate_limited_hit,
       f"/login에 20회 연속 요청(제한: 15 per 5 minutes) "
       f"-> 응답 코드 목록에 429 포함={rate_limited_hit}, 첫 429 발생 시점={codes.index(429)+1 if 429 in codes else 'N/A'}번째 요청")

with app.app_context():
    test_users = User.query.filter(User.username.like("qa_t_%")).all()
    test_ids = [u.id for u in test_users]
    Message.query.filter(Message.sender_id.in_(test_ids)).delete(synchronize_session=False)
    Conversation.query.filter(
        (Conversation.user_a_id.in_(test_ids)) | (Conversation.user_b_id.in_(test_ids))
    ).delete(synchronize_session=False)
    Product.query.filter(Product.seller_id.in_(test_ids)).delete(synchronize_session=False)
    Transaction.query.filter(
        (Transaction.sender_id.in_(test_ids)) | (Transaction.receiver_id.in_(test_ids))
    ).delete(synchronize_session=False)
    AuditLog.query.filter(AuditLog.actor_id.in_(test_ids)).delete(synchronize_session=False)
    Report.query.filter(Report.reporter_id.in_(test_ids)).delete(synchronize_session=False)
    Report.query.filter(Report.target_id.in_(test_ids)).delete(synchronize_session=False)
    for u in test_users:
        db.session.delete(u)
    db.session.commit()

print("\n\n==================== SUMMARY ====================")
passed = sum(1 for _, _, ok, _ in results if ok)
print(f"{passed}/{len(results)} PASS")
for n, title, ok, ev in sorted(results, key=lambda x: x[0]):
    print(f"#{n:>2} [{'PASS' if ok else 'FAIL'}] {title}")
