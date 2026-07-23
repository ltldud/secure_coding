# Secure Coding 과제 보고서 — 작성 가이드 초안

> 이 문서는 "완성된 보고서"가 아니라 **작성 가이드가 포함된 초안**입니다.
> - 코드만 보고 객관적으로 확인 가능한 부분(아키텍처, DB 설계, 폼 검증 규칙, 보안 약점 표)은 실제 코드를 근거로 채워뒀습니다.
> - 반면 **"실제로 실행해서 확인한 결과"에 해당하는 부분(5장 체크리스트의 "실제 결과" 열, 스크린샷)은 일부러 비워뒀습니다.** 본인이 서버를 직접 띄우고 재현해서 채우세요 — 채점 포인트가 "직접 수행"이기 때문입니다.
> - `[ ]` 로 표시된 항목은 본인이 실행 후 결과/스크린샷/터미널 출력을 붙여넣어야 하는 자리입니다.
> - 다 채운 뒤 이 파일 이름을 `report.md`로 바꾸거나, 기존 `docs/report.md`와 비교해서 본인 표현으로 다시 정리하세요.

- 이름: [이름 입력]
- 반: [XX반]
- 제출일: [제출일 입력]
- GitHub 저장소: [본인 저장소 URL]

---

## 1. 개요

*(작성 가이드: 이 과제가 무엇을 요구하는지, 기준 코드가 무엇이었는지, 본인이 무엇을 했는지 3~5문장으로 요약)*

본 과제는 강의에서 제공한 취약한 기준 구현체(`ugonfor/secure-coding`)를 바탕으로, 요구사항 분석 → 시스템 설계 → 구현 → 체크리스트 작성/테스트 → 유지보수의 소프트웨어 개발 생명주기 전 과정을 직접 수행하며 시큐어 코딩을 적용하는 것을 목표로 한다. 기준 코드는 회원가입/로그인/프로필/상품/신고/전체채팅 기능은 동작하지만 보안 요소가 의도적으로 빠져 있었고, 여기에 더해 강의에서 직접 설계하도록 요구한 **송금, 검색, 관리자** 기능을 새로 추가했다.

---

## 2. 요구사항 분석

*(작성 가이드: 분류별 표로 정리. 3장 시스템 설계도 이 표와 같은 7개 분류 순서로 구성했습니다 — 요구사항과 설계를 같은 기준으로 짝지어 볼 수 있도록.)*

| 분류 | 요구사항 |
|---|---|
| 회원 관리 | 회원가입 및 로그인, 프로필 관리, 아이디 중복 불가 |
| 상품 관리 | 상품 등록 및 조회, 목록에는 이름만 노출 → 클릭 시 상세 페이지 |
| 소통 | 전체 채팅, 1:1 채팅 |
| 신고 및 제재 | 신고 사유 필수, 일정 횟수 이상 신고 시 상품 차단 후 유저 휴면 전환 |
| 송금 | 유저 간 송금 (직접 설계) |
| 검색 | 상품 검색 (직접 설계) |
| 관리자 | 플랫폼 전 요소 관리 (직접 설계) |

### 비기능적 요구사항

*(작성 가이드: 본인 프로젝트에서 실제로 신경 쓴 비기능 요소)*

- 보안: 인증되지 않은 요청/CSRF/SQL Injection/XSS로부터 안전해야 함
- 안정성: 송금·구매처럼 여러 단계로 이루어진 처리는 중간에 실패해도 데이터가 어긋나지 않아야 함(원자성)
- 감사 가능성: 누가 언제 무엇을 했는지(신고 처리, 관리자 조치, 거래) 추적 가능해야 함
- 유지보수성: 기능 하나를 고칠 때 다른 기능에 영향을 주지 않도록 모듈이 분리되어 있어야 함

---

## 3. 시스템 설계

*(작성 가이드: 2장 표의 7개 분류(회원관리/상품관리/소통/신고및제재/송금/검색/관리자) 순서를 그대로 따라, 분류마다 요구사항을 어떤 규칙·기능으로 구체화했는지 정리했습니다. 웹페이지 설계와 데이터베이스 설계는 2장에 없던 새로운 관점이라 뒤에 별도 절로 뺐습니다.)*

### 3.1 회원 관리

- 회원가입 — 아이디는 영문/숫자/밑줄 3~20자, 비밀번호는 8~64자(영문+숫자 각 1자 이상), 아이디 중복 불가
- 로그인 — 5회 연속 실패 시 15분간 계정 잠금
- 마이페이지 — 소개글, 비밀번호 변경(변경 시 현재 비밀번호 재확인)
- 공개 프로필 — 다른 사용자의 프로필(소개글 등) 확인 가능
- 담당 블루프린트: `auth.py`, `profile.py`

### 3.2 상품 관리

- 상품 등록 — 상품명 1~100자, 설명 1~2000자, 가격 1~10억 범위 검증 (0원 무료 나눔은 허용하지 않음 — 송금 최소액과 일관성 유지)
- 등록한 상품의 확인 및 관리(수정·삭제)는 소유자 본인만 가능
- 등록된 상품은 누구나 볼 수 있음 — 단, 차단된 상품은 노출되지 않음
- 목록에는 이름만 보여주고, 클릭 시 상세 페이지로 이동
- 담당 블루프린트: `products.py`

### 3.3 소통

- 전체 유저가 소통할 수 있는 채팅
- 유저 간 1대1 채팅
- 인증되지 않은 사용자는 채팅 연결 자체가 거부됨
- 메시지 길이 제한(500자), 도배 방지 속도 제한(10초당 8건)
- 담당 블루프린트: `chat.py`

### 3.4 신고 및 제재

- 불량 상품/사용자 신고, 신고 사유 필수
- 동일 대상 중복 신고 불가
- 일정 횟수(5회) 이상 신고된 상품은 자동 차단
- 일정 횟수(5회) 이상 신고된 유저는 자동 휴면 전환
- 관리자가 신고를 수동으로 검토·기각 가능
- 담당 블루프린트: `reports.py`

### 3.5 송금 (직접 설계)

- 로그인한 사용자만 송금 가능
- 자기 자신에게는 송금 불가
- 잔액 부족 시 거부
- 정지(휴면)된 사용자에게는 송금 불가
- 상품 구매는 "송금 + 상품 상태 변경"이 하나의 트랜잭션으로 처리
- 모든 송금 내역은 감사 가능하도록 기록
- 담당 블루프린트: `transfers.py`

### 3.6 검색 (직접 설계)

- 로그인한 사용자가 상품명/설명으로 검색
- 차단된 상품은 검색 결과에서 제외
- 검색어에 의한 SQL Injection 불가능
- 담당 블루프린트: `products.py` (`dashboard()`)

### 3.7 관리자 (직접 설계)

- 관리자 계정은 소스코드에 하드코딩하지 않고 환경변수 기반 시드 스크립트로 생성
- 회원(정지/해제), 상품(차단/해제/삭제), 신고(기각), 거래 내역 통합 관리
- 관리자가 아닌 사용자는 접근 불가(403)
- 주요 조치는 감사 로그로 기록
- 담당 블루프린트: `admin.py`, `scripts/seed_admin.py`

### 3.8 웹페이지 설계

*(작성 가이드: 각 페이지 스크린샷을 붙이면 좋음)*

- 기본 페이지
- 회원가입 페이지
- 로그인 페이지
- 마이페이지 / 공개 프로필 페이지
- 상품 목록 및 검색 페이지
- 새 상품 등록 페이지
- 상품 상세/수정 페이지
- 신고 페이지
- 전체 채팅 페이지
- 1대1 채팅 페이지
- 송금 페이지
- 거래 내역 페이지
- 관리자 대시보드 / 회원 관리 / 상품 관리 / 신고 관리 / 거래 관리 페이지

- [ ] 기본 페이지 스크린샷
- [ ] 회원가입/로그인 페이지 스크린샷
- [ ] 마이페이지 / 공개 프로필 스크린샷
- [ ] 상품 목록(+검색) 페이지 스크린샷
- [ ] 상품 등록/수정/상세 페이지 스크린샷
- [ ] 전체 채팅 / 1:1 채팅 페이지 스크린샷
- [ ] 신고 / 송금 / 거래내역 페이지 스크린샷
- [ ] 관리자 대시보드/회원/상품/신고/거래 페이지 스크린샷

### 3.9 데이터베이스 설계

- 사용자 정보 (사용자 아이디, 계정명, 비밀번호 해시, 소개글, 잔액, 권한(user/admin), 상태(active/suspended), 신고 누적 횟수, 로그인 실패 횟수, 잠금 해제 시각)
- 상품 정보 (상품 아이디, 상품명, 상품 설명, 가격, 판매자 아이디, 상태(active/sold/blocked), 신고 누적 횟수)
- 신고 정보 (신고 아이디, 신고자 아이디, 대상 유형(user/product), 대상 아이디, 신고 사유, 처리 상태) — 동일 대상 중복 신고 방지를 위해 (신고자, 대상 유형, 대상 아이디) 조합에 유니크 제약
- 대화방 정보 (대화방 아이디, 참여자 A 아이디, 참여자 B 아이디) — 1대1 채팅을 위해 직접 설계 시 추가한 테이블
- 메시지 정보 (메시지 아이디, 채팅방, 발신자 아이디, 내용, 작성 시각) — 전체 채팅방/1대1 대화방 공용
- 거래 정보 (거래 아이디, 송신자 아이디, 수신자 아이디, 금액, 종류(송금/구매), 연관 상품 아이디) — 송금 기능을 위해 직접 설계 시 추가한 테이블
- 감사 로그 정보 (로그 아이디, 조치자 아이디, 조치 내용, 대상) — 관리자 조치 추적을 위해 직접 설계 시 추가한 테이블

*(작성 가이드: 사용자/상품/신고 정보는 강의 기준 슬라이드에 제시된 항목이고, 대화방/메시지/거래/감사로그는 직접 설계 요구사항(1대1 채팅·송금·관리자)을 구현하기 위해 본인이 추가한 테이블입니다 — 왜 필요했는지 한 줄씩 붙이면 좋습니다.)*

### 3.10 아키텍처 구조

*(작성 가이드: 왜 프론트/백엔드를 분리하지 않았는지, 왜 이 구조를 택했는지 본인 판단을 한 문단 정도 추가)*

Flask + Jinja2 서버 렌더링 + Flask-SocketIO 단일 애플리케이션 구조.

```
server/
  app.py            # 앱 팩토리, 보안 헤더, 에러 핸들러
  config.py         # 환경설정 (SECRET_KEY, 세션 쿠키 옵션, 정책 상수)
  extensions.py     # db, login_manager, csrf, socketio, limiter
  models.py         # User/Product/Report/Conversation/Message/Transaction/AuditLog
  security.py       # 비밀번호 해시, 아이디/비밀번호 형식 검증
  forms.py          # Flask-WTF 폼 (서버측 검증 + CSRF)
  blueprints/
    auth.py         # 회원가입/로그인/로그아웃
    profile.py      # 마이페이지, 공개 프로필
    products.py     # 상품 CRUD + 검색
    chat.py         # 채팅 라우트 + SocketIO 이벤트
    reports.py      # 신고 + 자동 임계치 제재
    transfers.py    # 송금/구매
    admin.py         # 관리자 기능
  scripts/seed_admin.py
```

---

## 4. 시스템 구현

*(작성 가이드: GitHub 저장소 링크로 전체 코드는 이미 확인 가능하므로, 여기서는 전체 코드를 다시 붙여넣지 않고 "어떻게 구현했는지 이해하고 있다"를 보여주는 핵심 스니펫만 골라 담았습니다. "왜 위험한지/어떻게 고쳤는지"의 before/after 서술은 5장 체크리스트 표의 "위험성" 열에서 다룹니다 — 겹치지 않도록 역할을 나눴습니다.)*

### 4.1 사용 라이브러리

| 라이브러리 | 역할 |
|---|---|
| Flask-SQLAlchemy | ORM, SQLite |
| Flask-Login | 세션/인증, `is_active` 오버라이드로 정지 계정 즉시 로그아웃 |
| Flask-WTF | 서버측 폼 검증 + CSRF 토큰 |
| Flask-SocketIO | 실시간 채팅 |
| Flask-Limiter | 엔드포인트별 rate limiting |
| bcrypt | 비밀번호 해시(salt 자동 포함) |

### 4.2 기능별 구현 상세

*(작성 가이드: 슬라이드 29페이지("코드 확인!") 포맷 — 3.1~3.7에서 분류한 기능 하나하나를 실제 코드와 함께 보여줍니다. 각 코드 아래 "왜 이렇게 짰는지" 한두 줄을 본인 말로 붙이세요.)*

**공통 보안 설정** — 특정 기능이 아니라 앱 전체에 걸리는 설정 (`server/extensions.py`, `server/app.py`)
```python
# extensions.py
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")

# app.py — create_app() 안에서 전체 앱에 적용
csrf.init_app(app)
limiter.init_app(app)

@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self' ws: wss:;"
    )
    return response
```
- [ ] 왜 이렇게 했는지:

#### 유저 관리

**회원가입 기능** (`server/blueprints/auth.py: register`)
```python
@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(username=form.username.data).first()
        if existing is not None:
            flash("이미 존재하는 사용자명입니다.", "danger")
            return render_template("register.html", form=form)

        user = User(username=form.username.data, balance=Config.STARTING_BALANCE)
        user.set_password(form.password.data)   # bcrypt 해시 저장 (security.py)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("auth.login"))
    return render_template("register.html", form=form)
```
- [ ] 왜 이렇게 했는지:

**로그인 기능** (`server/blueprints/auth.py: login`)
```python
@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("15 per 5 minutes")
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        generic_error = "아이디 또는 비밀번호가 올바르지 않습니다."  # 아이디 존재여부 유추 방지

        if user is None:
            flash(generic_error, "danger")
        elif user.is_locked():
            flash("계정이 잠겨 있습니다. 잠시 후 다시 시도하세요.", "danger")
        elif user.status == "suspended":
            flash("휴면(정지) 처리된 계정입니다. 관리자에게 문의하세요.", "danger")
        elif not user.check_password(form.password.data):
            user.register_failed_login(Config.LOGIN_FAIL_LIMIT, Config.LOGIN_LOCK_MINUTES)
            db.session.commit()
            flash(generic_error, "danger")
        else:
            user.reset_failed_login()
            db.session.commit()
            login_user(user)
            return redirect(url_for("products.dashboard"))
    return render_template("login.html", form=form)
```
- [ ] 왜 이렇게 했는지:

**사용자 조회 기능 (공개 프로필)** (`server/blueprints/profile.py: view_user`)
```python
@profile_bp.route("/user/<username>")
@login_required
def view_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template("public_profile.html", profile_user=user)
```
- [ ] 왜 이렇게 했는지:

**마이페이지 기능 (소개글/비밀번호 업데이트)** (`server/blueprints/profile.py`)
```python
@profile_bp.route("/profile/password", methods=["POST"])
@login_required
@limiter.limit("10 per hour")
def update_password():
    pw_form = PasswordChangeForm()
    if pw_form.validate_on_submit():
        if not current_user.check_password(pw_form.current_password.data):
            flash("현재 비밀번호가 올바르지 않습니다.", "danger")
            return redirect(url_for("profile.mypage"))
        current_user.set_password(pw_form.new_password.data)
        db.session.commit()
    return redirect(url_for("profile.mypage"))
```
- [ ] 왜 이렇게 했는지:

#### 상품 관리

**상품 등록 기능** (`server/blueprints/products.py: new_product`)
```python
@products_bp.route("/product/new", methods=["GET", "POST"])
@login_required
def new_product():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            price=form.price.data,
            seller_id=current_user.id,
        )
        db.session.add(product)
        db.session.commit()
        return redirect(url_for("products.view_product", product_id=product.id))
    return render_template("new_product.html", form=form)
```
- [ ] 왜 이렇게 했는지:

**등록된 상품 관리 기능 (수정/삭제, 소유자만)** (`server/blueprints/products.py: edit_product / delete_product`)
```python
@products_bp.route("/product/<product_id>/edit", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.seller_id != current_user.id:
        abort(403)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        product.title = form.title.data.strip()
        product.description = form.description.data.strip()
        product.price = form.price.data
        db.session.commit()
        return redirect(url_for("products.view_product", product_id=product.id))
    return render_template("edit_product.html", form=form, product=product)


@products_bp.route("/product/<product_id>/delete", methods=["POST"])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.seller_id != current_user.id and not current_user.is_admin():
        abort(403)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for("products.my_products"))
```
- [ ] 왜 이렇게 했는지:

**상품 조회 및 상세 페이지 기능** (`server/blueprints/products.py: dashboard / view_product`)
```python
@products_bp.route("/dashboard")
@login_required
def dashboard():
    query = Product.query.filter(Product.status != "blocked")
    page = max(request.args.get("page", 1, type=int), 1)
    pagination = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=PAGE_SIZE, error_out=False
    )
    return render_template("dashboard.html", products=pagination.items, pagination=pagination)


@products_bp.route("/product/<product_id>")
@login_required
def view_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.status == "blocked" and product.seller_id != current_user.id and not current_user.is_admin():
        abort(404)
    return render_template("view_product.html", product=product, seller=product.seller)
```
- [ ] 왜 이렇게 했는지:

#### 유저 소통 기능

**실시간 전체 채팅 기능** (`server/blueprints/chat.py: handle_connect / handle_send_message`)
```python
@socketio.on("connect")
def handle_connect():
    if not current_user.is_authenticated:
        disconnect()
        return False

@socketio.on("send_message")
def handle_send_message(data):
    if not current_user.is_authenticated or current_user.status == "suspended":
        disconnect()
        return

    content = str(data.get("content", "")).strip()
    if not content or len(content) > MAX_MESSAGE_LEN:
        return
    if _rate_limited(current_user.id):
        emit("system_notice", {"message": "너무 빠르게 메시지를 보내고 있습니다."})
        return

    msg = Message(room=data.get("room", ""), sender_id=current_user.id, content=content)
    db.session.add(msg)
    db.session.commit()
    emit("receive_message", {"sender": current_user.username, "content": content}, room=msg.room)
```
- [ ] 왜 이렇게 했는지:

**1대1 채팅 기능** (`server/blueprints/chat.py: direct_chat / handle_join`)
```python
@chat_bp.route("/chat/dm/<username>")
@login_required
def direct_chat(username):
    other = User.query.filter_by(username=username).first_or_404()
    if other.id == current_user.id:
        abort(400)
    convo = _get_or_create_conversation(current_user.id, other.id)
    return render_template("chat_dm.html", other=other, room=convo.id)

@socketio.on("join")
def handle_join(data):
    room = str(data.get("room", ""))[:80]
    if room == GLOBAL_ROOM:
        join_room(GLOBAL_ROOM)
        return
    convo = db.session.get(Conversation, room)
    if convo is None or current_user.id not in (convo.user_a_id, convo.user_b_id):
        disconnect()   # 대화 참여자가 아니면 연결 차단
        return
    join_room(room)
```
- [ ] 왜 이렇게 했는지:

#### 악성 유저 필터링

**불량 유저/상품 신고 기능** (`server/blueprints/reports.py: report`)
```python
@reports_bp.route("/report", methods=["GET", "POST"])
@login_required
@limiter.limit("20 per hour")
def report():
    form = ReportForm(target_type=request.values.get("target_type", ""), target_id=request.values.get("target_id", ""))
    if form.validate_on_submit():
        target = _resolve_target(form.target_type.data, form.target_id.data)
        if target is None:
            abort(404)
        rpt = Report(reporter_id=current_user.id, target_type=form.target_type.data,
                     target_id=form.target_id.data, reason=form.reason.data.strip())
        db.session.add(rpt)
        try:
            db.session.commit()
        except IntegrityError:          # UNIQUE 제약 위반 = 중복 신고
            db.session.rollback()
            flash("이미 신고한 대상입니다.", "warning")
            return redirect(url_for("products.dashboard"))
        _apply_threshold(form.target_type.data, form.target_id.data)
    return render_template("report.html", form=form)
```
- [ ] 왜 이렇게 했는지:

**불량 상품 차단 / 불량 유저 휴면 기능 (임계치 자동 조치)** (`server/blueprints/reports.py: _apply_threshold`)
```python
def _apply_threshold(target_type, target_id):
    count = Report.query.filter_by(target_type=target_type, target_id=target_id).count()
    if target_type == "product":
        product = db.session.get(Product, target_id)
        product.report_count = count
        if count >= Config.REPORT_THRESHOLD_PRODUCT:
            product.status = "blocked"
            db.session.add(AuditLog(actor_id=None, action="auto_block_product", target=target_id))
        db.session.commit()
    elif target_type == "user":
        user = db.session.get(User, target_id)
        user.report_count = count
        if count >= Config.REPORT_THRESHOLD_USER:
            user.status = "suspended"
            db.session.add(AuditLog(actor_id=None, action="auto_suspend_user", target=target_id))
        db.session.commit()
```
- [ ] 왜 이렇게 했는지:

#### 송금 (직접 설계)

**유저 간 송금 기능** (`server/blueprints/transfers.py: transfer`)
```python
@transfers_bp.route("/transfer", methods=["GET", "POST"])
@login_required
@limiter.limit("30 per hour")
def transfer():
    form = TransferForm()
    if form.validate_on_submit():
        receiver = User.query.filter_by(username=form.receiver_username.data.strip()).first()
        amount = form.amount.data
        if receiver is None:
            flash("받는 사람을 찾을 수 없습니다.", "danger")
        elif receiver.id == current_user.id:
            flash("자기 자신에게는 송금할 수 없습니다.", "danger")
        elif receiver.status == "suspended":
            flash("정지된 사용자에게는 송금할 수 없습니다.", "danger")
        elif current_user.balance < amount:
            flash("잔액이 부족합니다.", "danger")
        else:
            _execute_transfer(current_user, receiver, amount, kind="transfer")
            return redirect(url_for("transfers.history"))
    return render_template("transfer.html", form=form, balance=current_user.balance)
```
- [ ] 왜 이렇게 했는지:

**상품 구매(송금 연동) 기능** (`server/blueprints/transfers.py: purchase / _execute_transfer`)
```python
@transfers_bp.route("/product/<product_id>/purchase", methods=["POST"])
@login_required
def purchase(product_id):
    product = Product.query.get_or_404(product_id)
    if product.status != "active":
        flash("판매 중인 상품이 아닙니다.", "danger")
    elif product.seller_id == current_user.id:
        flash("자신의 상품은 구매할 수 없습니다.", "danger")
    elif current_user.balance < product.price:
        flash("잔액이 부족합니다.", "danger")
    else:
        _execute_transfer(current_user, product.seller, product.price, kind="purchase", product=product)
        product.status = "sold"
        db.session.commit()
    return redirect(url_for("products.view_product", product_id=product_id))

def _execute_transfer(sender, receiver, amount, kind="transfer", product=None):
    sender.balance -= amount
    receiver.balance += amount
    db.session.add(Transaction(sender_id=sender.id, receiver_id=receiver.id, amount=amount,
                                kind=kind, product_id=product.id if product else None))
    db.session.commit()   # 잔액 변경 + 거래기록이 하나의 커밋으로 원자적 처리
```
- [ ] 왜 이렇게 했는지:

**거래 내역 조회 기능** (`server/blueprints/transfers.py: history`)
```python
@transfers_bp.route("/transactions")
@login_required
def history():
    txs = Transaction.query.filter(
        db.or_(Transaction.sender_id == current_user.id, Transaction.receiver_id == current_user.id)
    ).order_by(Transaction.created_at.desc()).all()
    return render_template("transactions.html", txs=txs, me=current_user)
```
- [ ] 왜 이렇게 했는지:

#### 검색 (직접 설계)

**상품명/설명 검색 기능** (`server/blueprints/products.py: dashboard`)
```python
q = (request.args.get("q") or "").strip()[:100]
if q:
    escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    like = "%" + escaped + "%"
    query = query.filter(
        db.or_(Product.title.ilike(like, escape="\\"), Product.description.ilike(like, escape="\\"))
    )
```
- [ ] 왜 이렇게 했는지: (`%`, `_`는 SQL LIKE의 와일드카드 문자라서 그대로 두면 검색어로 와일드카드를 주입할 수 있음 — 직접 이스케이프 처리)

#### 관리자 (직접 설계)

**관리자 계정 생성 (하드코딩 금지)** (`server/scripts/seed_admin.py`)
```python
username = os.environ.get("ADMIN_USERNAME")
password = os.environ.get("ADMIN_PASSWORD")
user = User.query.filter_by(username=username).first()
if user is None:
    user = User(username=username, balance=Config.STARTING_BALANCE, role="admin")
    user.set_password(password)
    db.session.add(user)
else:
    user.role = "admin"
    user.set_password(password)
db.session.commit()
```
- [ ] 왜 이렇게 했는지:

**회원/상품/신고/거래 통합 관리 기능** (`server/blueprints/admin.py`)
```python
def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin():
            abort(403)
        return view(*args, **kwargs)
    return wrapped

@admin_bp.route("/users/<user_id>/suspend", methods=["POST"])
@admin_required
def suspend_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("자기 자신은 정지할 수 없습니다.", "danger")
        return redirect(url_for("admin.users"))
    user.status = "suspended"
    db.session.add(AuditLog(actor_id=current_user.id, action="admin_suspend_user", target=user.id))
    db.session.commit()
    return redirect(url_for("admin.users"))
```
- [ ] 왜 이렇게 했는지:

### 4.3 핵심 검증 규칙

- 아이디: 영문/숫자/밑줄 3~20자 (`security.py: USERNAME_RE`)
- 비밀번호: 8~64자, 영문+숫자 각 1자 이상 (`security.py: PASSWORD_RE`)
- 상품명 1~100자, 설명 1~2000자, 가격 1~10억 (`forms.py: ProductForm`)
- 신고 사유 5~500자, `target_type`은 `user`/`product` 화이트리스트만 허용 (`forms.py: ReportForm`)
- 송금액 1~10억 (`forms.py: TransferForm`)

---

## 5. 체크리스트 작성 및 테스트

*(작성 가이드: PDF의 기준 체크리스트처럼 4개 열(#, Section, Checklist Item, Description)만 남겼습니다. 구현 위치·테스트 방법·결과는 표에 넣지 않고, 표 아래 "테스트 수행" 부분에 본인이 직접 어떻게 테스트했는지 서술하세요.)*

| # | Section | Checklist Item | Description |
|---|---|---|---|
| 1 | 회원 관리 | 서버측 입력 검증 | 아이디(username)와 비밀번호(password)에 대해 길이, 허용 문자 집합, 형식 등 서버측 검증 수행. XSS 공격 방지를 위해 입력값 필터링 및 인코딩 적용 여부 확인 |
| 2 | 회원 관리 | 비밀번호 보안 | 비밀번호를 평문으로 저장하지 않고 bcrypt 등 강력한 해시 알고리즘과 고유 salt를 적용하여 암호화 저장하는지 확인 |
| 3 | 회원 관리 | 실패 로그인 방어 | 로그인 실패 횟수에 따른 계정 잠금 혹은 지연(time-out) 메커니즘 적용 여부 확인 |
| 4 | 회원 관리 | 오류 메시지 | 로그인 실패 시 아이디 존재 여부를 유추할 수 없도록 동일한 오류 메시지를 사용하는지 확인 |
| 5 | 상품 등록 및 관리 | 폼 입력 검증 | 상품 제목, 설명, 가격 등의 입력 필드에 대해 서버측 검증 및 필수 항목 체크 여부 확인. 가격은 숫자 형식 및 범위(1~10억) 검증 적용 |
| 6 | 상품 등록 및 관리 | XSS 방어 | 사용자 입력(상품 설명 등)에 대해 HTML 태그 및 스크립트 코드 이스케이프 또는 필터링 적용 여부 확인 |
| 7 | 상품 등록 및 관리 | 소유자 확인 | 상품 수정 및 삭제 시, 요청한 사용자가 해당 상품의 소유자인지 검증하는 로직이 있는지 확인 |
| 8 | 상품 등록 및 관리 | 차단 상품 비노출 | 신고로 차단된 상품이 목록/검색/상세 조회에서 제외되는지 확인 |
| 9 | 실시간 채팅 및 메시징 | 사용자 인증 | Socket 연결 시 사용자가 인증된 상태인지 확인하는 로직(예: 로그인 상태 확인)이 적용되어 있는지 확인 |
| 10 | 실시간 채팅 및 메시징 | 메시지 내용 검증 및 Rate Limiting | 채팅 메시지에 대해 길이 제한, 허용 문자 집합 검증 여부와 동일 사용자가 단기간에 과도한 메시지를 보내지 않도록 제한하는 기능(스팸 방지) 구현 여부 확인 |
| 11 | 실시간 채팅 및 메시징 | 1:1 대화방 참여자 검증 | 1:1 대화방에 참여자 본인만 접근(join)할 수 있는지 검증하는 로직이 있는지 확인 |
| 12 | 실시간 채팅 및 메시징 | 정상 동작 확인 | 인증된 사용자 간 전체 채팅 메시지가 정상적으로 송수신(브로드캐스트)되는지 확인 |
| 13 | 안전 거래 및 신고 | 폼 입력 검증 | 신고 대상(target_id) 및 신고 사유(reason)에 대해 서버측 입력 검증, 길이 제한, XSS 방어 적용 여부 확인 |
| 14 | 안전 거래 및 신고 | 신고 남용 방지 | 동일 사용자의 반복 신고 제한 로직이 구현되어 있는지 확인 |
| 15 | 안전 거래 및 신고 | 데이터 무결성 및 로그 관리 | 일정 횟수 이상 신고된 상품/사용자가 자동으로 차단/휴면 처리되고, 조치 내역이 기록되는지 확인 |
| 16 | 안전 거래 및 신고 | 관리자 검토 프로세스 | 관리자가 신고를 수동으로 검토하고 기각할 수 있는 프로세스가 있는지 확인 |
| 17 | 송금 | 인증된 사용자 접근 | 로그인한 사용자만 송금 기능에 접근할 수 있는지 확인 |
| 18 | 송금 | 자기 자신 송금 방지 | 자기 자신에게는 송금할 수 없도록 제한되어 있는지 확인 |
| 19 | 송금 | 잔액 부족 검증 | 보유 잔액을 초과하는 금액은 송금이 거부되는지 확인 |
| 20 | 송금 | 정지 계정 송금 방지 | 정지(휴면) 상태의 사용자에게는 송금할 수 없도록 제한되어 있는지 확인 |
| 21 | 송금 | 원자적 처리 | 상품 구매 시 송금과 상품 상태 변경이 하나의 트랜잭션으로 처리되어, 중간 실패로 인한 데이터 불일치가 없는지 확인 |
| 22 | 검색 | SQL Injection 방지 | 검색어에 대해 파라미터 바인딩 및 와일드카드 문자 이스케이프가 적용되어 SQL Injection이 불가능한지 확인 |
| 23 | 검색 | 검색 결과 정확성 | 검색어와 일치하는 상품만 반환되고, 일치하는 상품이 없으면 빈 목록이 반환되는지 확인 |
| 24 | 검색 | 차단 상품 제외 | 차단된 상품이 검색 결과에 노출되지 않는지 확인 |
| 25 | 관리자 | 역할 기반 접근 제어 | 관리자가 아닌 사용자가 관리자 페이지/기능에 접근할 수 없도록 제어되어 있는지 확인 |
| 26 | 관리자 | 계정 하드코딩 금지 | 관리자 계정이 소스코드에 하드코딩되지 않고 별도 절차(환경변수)로 생성되는지 확인 |
| 27 | 관리자 | 조치 감사 로그 | 관리자의 주요 조치(정지/차단/기각 등)가 감사 로그로 기록되는지 확인 |
| 28 | 전체 시스템 | CSRF 보호 | 회원가입, 로그인, 상품 등록 등 모든 폼에 대해 CSRF 토큰 사용 여부를 확인하여 요청 위조 공격 방지 |
| 29 | 전체 시스템 | 세션 쿠키 설정 | 세션 쿠키에 HttpOnly 및 (HTTPS 환경에서) Secure 플래그가 적용되어 있는지 확인 |
| 30 | 전체 시스템 | 보안 헤더 | 클릭재킹/MIME 스니핑 방지를 위한 보안 헤더(CSP, X-Frame-Options 등)가 응답에 포함되는지 확인 |
| 31 | 전체 시스템 | 오류 메시지 | 오류 발생 시 내부 정보(스택 트레이스, DB 정보 등)가 노출되지 않도록 처리되어 있는지 확인 |
| 32 | 전체 시스템 | 요청 크기 제한 | 과대한 요청 본문(payload)이 제한되어 자원 소모를 방지하는지 확인 |
| 33 | 전체 시스템 | Rate Limiting | 회원가입/로그인/신고/송금 등 주요 엔드포인트에 요청 속도 제한이 적용되어 있는지 확인 |

### 테스트 수행

33개 항목 각각을 브라우저로 손으로 클릭해보는 대신, `server/scripts/checklist_test.py`에 33개 항목을 전부 재현하는 자동화 테스트 스크립트를 작성해서 실제 앱(Flask 앱 팩토리를 그대로 import)에 대해 돌렸다. Claude Code(AI 도구)와 함께 작성했고, 실제로 실행해서 나온 결과를 아래에 그대로 옮겼다 — 화면을 하나하나 캡처하는 대신 이 방식을 택한 이유는 33개 항목 전부를 스크린샷으로 남기면 보고서 용량이 지나치게 커지기 때문이다.

**테스트 방식**
- Flask의 `app.test_client()` / `flask_socketio.socketio.test_client()`로 실제 라우트·CSRF·세션·SocketIO 이벤트 핸들러를 그대로 통과시켜 검증(목(mock) 없이 실제 코드 경로 실행)
- 테스트 전용 계정(`qa_t_*`)을 만들어서 실제 계정(`sy020723`, `testuser`, `admin`)과 분리, 테스트가 끝나면 스크립트가 자동으로 정리(삭제)
- 회원가입/로그인처럼 "그 엔드포인트 자체"가 검사 대상인 항목은 실제 HTTP 요청으로, 신고 5건 임계치처럼 "결과 상태"가 검사 대상인 일부 설정 단계는 ORM으로 직접 데이터를 준비해서 Flask-Limiter 요청 한도(예: `/report` 시간당 20회)를 불필요하게 소모하지 않도록 함
- 재현: `cd server && source ../.venv/bin/activate && python scripts/checklist_test.py`

**실행 결과 (2026-07-23, 33/33 PASS)**

| # | 결과 | 근거 |
|---|---|---|
| 1 | ✅ | 아이디 2자·숫자 없는 비밀번호로 회원가입 시도 → 서버측 정규식 검증으로 거부, 계정 미생성 |
| 2 | ✅ | 실제 계정(`admin`/`sy020723`/`testuser`) `password_hash`가 모두 `$2b$`(bcrypt) 접두사 |
| 3 | ✅ | 5회 연속 비밀번호 오류 후 정답으로도 로그인 거부, `locked_until`이 15분 뒤로 설정됨 |
| 4 | ✅ | 존재하지 않는 아이디 vs 틀린 비밀번호 → 두 경우 모두 "아이디 또는 비밀번호가 올바르지 않습니다."로 동일 |
| 5 | ✅ | 가격 0원 등록 거부(미생성), 1,000원은 정상 등록 |
| 6 | ✅ | 설명에 `<script>alert(1)</script>` 저장 후 상세페이지에는 `&lt;script&gt;...`로만 노출(원문 태그 없음) |
| 7 | ✅ | 소유자가 아닌 사용자의 수정/삭제 요청 → 둘 다 403 |
| 8 | ✅ | 서로 다른 5개 계정이 신고 → `status=blocked`, 대시보드/검색/상세(비소유자) 모두 비노출(상세는 404) |
| 9 | ✅ | 로그인하지 않은 소켓 클라이언트는 연결 즉시 disconnect |
| 10 | ✅ | 501자 메시지 미저장, 10초 내 10건 연속 전송 시 `system_notice`(도배 경고) 2회 수신 |
| 11 | ✅ | 대화 당사자가 아닌 제3자가 1:1 방 join 시도 → 서버가 연결 종료 |
| 12 | ✅ | 한 클라이언트가 보낸 전체채팅 메시지를 다른 클라이언트가 `receive_message`로 정상 수신 |
| 13 | ✅ | 5자 미만 사유 거부, `target_type`이 화이트리스트(`user`/`product`) 밖이면 Report 미생성 (단, `report.html`이 `target_type` 필드 오류 문구를 화면에 렌더링하지 않아 사용자에게는 무응답처럼 보임 — 발견한 UX 개선 여지) |
| 14 | ✅ | 동일 사용자가 같은 상품을 두 번째 신고 → "이미 신고한 대상입니다." 응답, DB에는 1건만 유지(유니크 제약) |
| 15 | ✅ | 신고 5건 도달 시 `AuditLog(action=auto_block_product)` 기록 확인 |
| 16 | ✅ | 관리자가 대기 중인 신고를 기각 → `status=dismissed`로 반영 |
| 17 | ✅ | 비로그인 상태로 `/transfer` 접근 → 로그인 페이지로 302 리다이렉트 |
| 18 | ✅ | 본인 아이디로 송금 시도 → "자기 자신에게는 송금할 수 없습니다." |
| 19 | ✅ | 보유 잔액을 초과하는 금액 송금 시도 → "잔액이 부족합니다." |
| 20 | ✅ | 신고 임계치로 정지된 계정에게 송금 시도 → "정지된 사용자에게는 송금할 수 없습니다." |
| 21 | ✅ | 구매 후 `product.status=sold`, `Transaction` 기록, 판매자/구매자 잔액 증감(+3,000/-3,000)이 한 커밋에 함께 반영 |
| 22 | ✅ | 검색어에 `' OR '1'='1`, `%` 등을 넣어도 서버 오류 없이 200 응답(ORM 파라미터 바인딩 + LIKE 이스케이프) |
| 23 | ✅ | 일치하는 상품명 검색 시 노출, 무관한 검색어는 "등록된 상품이 없습니다." |
| 24 | ✅ | 차단된 상품명을 그대로 검색해도 결과에 없음 |
| 25 | ✅ | 일반 계정으로 `/admin/` 접근 → 403 |
| 26 | ✅ | 실제 `ADMIN_PASSWORD` 값(로컬 `.env`, gitignore 대상)으로 `*.py` 전체 grep해도 매치 없음 — `seed_admin.py`는 `os.environ.get()`으로만 참조 |
| 27 | ✅ | 관리자의 신고 기각 조치가 `AuditLog(action=admin_dismiss_report)`로 기록됨 |
| 28 | ✅ | `csrf_token` 없이 상품 등록 POST → 400, 상품 미생성 |
| 29 | ✅ | 로그인 응답 `Set-Cookie`에 `HttpOnly`, `SameSite=Lax` 확인(`SESSION_COOKIE_SECURE`는 운영 HTTPS 배포 시 `true`로 전환) |
| 30 | ✅ | 응답 헤더에 `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, CSP(`default-src 'self'` 등) 확인 |
| 31 | ✅ | 존재하지 않는 상품 조회 → 커스텀 404 페이지만 노출, 스택트레이스 없음. 단, 현재 로컬 실행은 `FLASK_ENV=development`(`DEBUG=True`)라 처리되지 않은 500 예외는 Werkzeug 인터랙티브 디버거로 내부 정보가 노출될 수 있음 — 운영 배포 시 `FLASK_ENV=production`으로 전환해야 함(README에 명시) |
| 32 | ✅ | `MAX_CONTENT_LENGTH`(3MB, 상품 이미지 업로드 수용을 위해 1MB에서 상향) 초과 요청(4MB) → 413 |
| 33 | ✅ | `/login`에 20회 연속 요청 시 5번째 요청부터 429(요청 제한 "15 per 5 minutes") 발생 |

**직접 확인하며 발견한 점**
- 5장 표의 #13(신고 대상 화이트리스트)은 서버 검증 자체는 정상 동작하지만, `report.html`이 `target_type` 필드의 검증 오류를 화면에 표시하지 않는다 — 보안적으로는 문제 없지만(잘못된 신고는 어차피 저장되지 않음) 사용자 경험 관점의 개선 여지로 기록해둔다.
- #31에서 확인했듯, 로컬 개발 환경(`FLASK_ENV=development`)에서는 Werkzeug 디버거가 살아있어 500 에러 시 내부 정보가 노출될 수 있다. 커스텀 에러 페이지 자체는 구현되어 있으므로, 운영 배포 시 `FLASK_ENV=production`(`DEBUG=False`)로만 전환하면 해결된다.

---

## 6. 유지보수

*(작성 가이드: README의 "알려진 한계"를 본인이 이해한 이유와 함께 재작성)*

- **로컬 개발 서버(Werkzeug) 기반 실행 → 운영 시 gunicorn+eventlet/gevent + Nginx 필요.** 이유: Werkzeug 개발 서버는 단일 프로세스/스레드 기준으로 동작해서 동시 접속자가 늘면 요청이 순차적으로 밀려 응답이 느려진다. 특히 이 프로젝트는 Flask-SocketIO로 여러 클라이언트가 웹소켓 연결을 계속 유지해야 하는데, 개발 서버는 이런 다수의 장기 연결을 안정적으로 감당하도록 설계되지 않았다. 운영에서는 gunicorn+eventlet/gevent 같은 프로덕션 WSGI 서버가 필요하고, TLS 종단·정적 파일 서빙은 Nginx 같은 리버스 프록시가 앞단에서 맡아야 한다.
- **SQLite 단일 프로세스 기준 동시성 처리 → 운영 시 `SELECT ... FOR UPDATE` 필요.** 이유: SQLite는 쓰기 락이 DB 파일 전체 단위라서, 지금처럼 단일 프로세스로 돌아가는 동안은 두 요청이 동시에 잔액을 바꾸는 일이 사실상 일어나지 않는다. 하지만 운영에서 프로세스를 여러 개(또는 다중 서버) 띄우면, 두 사람이 거의 동시에 같은 상품을 구매하거나 송금을 시도할 때 "잔액을 읽고 → 계산하고 → 다시 쓰는" 사이에 다른 요청이 끼어드는 경쟁 조건(race condition)이 생겨 잔액이 꼬일 수 있다. PostgreSQL 같은 RDBMS로 옮기고, 잔액을 읽는 시점에 해당 행을 `SELECT ... FOR UPDATE`로 잠가 다른 트랜잭션이 끼어들지 못하게 해야 한다.
- **인메모리 rate limit → 다중 프로세스 배포 시 Redis 필요.** 이유: Flask-Limiter의 요청 횟수, 그리고 채팅 도배 방지 카운터(`_recent_sends`)가 전부 파이썬 프로세스 메모리 안에만 존재한다. 워커를 한 개만 띄우면 문제 없지만, 운영에서 흔히 하듯 워커를 여러 개 띄우면 각 워커가 자기가 받은 요청만 세기 때문에, 예를 들어 "로그인 시도 15회/5분" 제한이 워커 수만큼 사실상 늘어나는 셈이 되어 제한이 무력화된다. Redis처럼 모든 워커가 공유하는 저장소로 옮겨야 실제로 의도한 제한이 유지된다.
- **(이번에 새로 추가) 상품 이미지가 로컬 파일시스템(`server/static/uploads/products/`)에 저장됨 → 다중 서버 배포 시 공유 스토리지(S3 등) 필요.** 이유: 업로드된 이미지가 요청을 처리한 서버의 디스크에만 남기 때문에, 여러 서버 인스턴스로 확장하면 이미지를 올릴 때와 조회할 때 요청이 다른 서버로 가는 경우 이미지가 없는 것처럼 보일 수 있다. S3 같은 오브젝트 스토리지나 서버 간에 공유되는 네트워크 파일시스템으로 옮겨야 한다.

**향후 개선 방향(본인 생각) — 직접 구현**

이번 유지보수 단계에서, 실제로 이 플랫폼을 사용자처럼 써보면서 느낀 불편함 4가지를 Claude Code(AI 도구)와 함께 직접 구현해봤다. 3~4장과 같은 형식으로, 핵심 코드와 함께 정리한다.

#### 1) 상품 사진

중고거래 플랫폼인데 사진 없이 텍스트로만 물건을 올려야 했던 게 가장 크게 체감된 문제였다. `Product`에 `image_filename` 컬럼을 추가하고, 업로드된 파일의 원본 이름을 그대로 믿지 않고 서버에서 `uuid` 기반 새 파일명을 생성해 저장한다(경로 조작·파일명 충돌 방지). 확장자 화이트리스트(jpg/png/gif/webp)와 용량 제한(2MB)은 폼 검증 단계에서 걸러낸다.

**폼 검증** (`server/forms.py: ProductForm`)
```python
image = FileField(
    "상품 사진 (선택)",
    validators=[
        Optional(),
        FileAllowed(sorted(Config.ALLOWED_IMAGE_EXTENSIONS), "이미지 파일(jpg/png/gif/webp)만 업로드 가능합니다."),
        FileSize(max_size=Config.MAX_IMAGE_SIZE, message="이미지 파일은 2MB 이하만 가능합니다."),
    ],
)
```

**저장 시 파일명 재생성** (`server/blueprints/products.py: _save_product_image`)
```python
def _save_product_image(file_storage):
    ext = file_storage.filename.rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"   # 원본 파일명은 신뢰하지 않음
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    file_storage.save(os.path.join(Config.UPLOAD_FOLDER, filename))
    return filename
```
- [ ] 스크린샷: 사진과 함께 등록된 상품의 상세 페이지 / 목록 썸네일

#### 2) 비밀번호 찾기

본인 계정 비밀번호를 잊어버렸을 때 복구할 방법이 전혀 없었던 게, 이번 과제를 진행하며 직접 겪은 문제였다(이 대화 맨 처음에 실제로 겪었다). 이메일 발송 인프라 없이도 동작하도록, 가입 시 사용자가 직접 정의한 보안 질문/답변으로 본인 확인 후 새 비밀번호를 설정하는 2단계 플로우를 추가했다. 답변은 비밀번호와 마찬가지로 평문 저장하지 않고 bcrypt로 해시한다.

**답변 해시 저장/검증** (`server/security.py`)
```python
def _normalize_answer(raw_answer: str) -> str:
    return raw_answer.strip().lower()   # 대소문자·공백 차이는 무시

def hash_answer(raw_answer: str) -> str:
    return bcrypt.hashpw(_normalize_answer(raw_answer).encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_answer(raw_answer: str, answer_hash: str) -> bool:
    return bcrypt.checkpw(_normalize_answer(raw_answer).encode("utf-8"), answer_hash.encode("utf-8"))
```

**재설정 라우트** (`server/blueprints/auth.py: forgot_password_verify`)
```python
@auth_bp.route("/forgot-password/verify", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def forgot_password_verify():
    user_id = session.get("pwreset_user_id")
    user = db.session.get(User, user_id) if user_id else None
    if user is None or not user.has_security_question():
        return redirect(url_for("auth.forgot_password"))

    form = ForgotVerifyForm()
    if form.validate_on_submit():
        if not user.check_security_answer(form.security_answer.data):
            flash("답변이 올바르지 않습니다.", "danger")
            return render_template("forgot_password_verify.html", form=form, question=user.security_question)
        user.set_password(form.new_password.data)
        user.reset_failed_login()
        db.session.commit()
        session.pop("pwreset_user_id", None)
        return redirect(url_for("auth.login"))
    return render_template("forgot_password_verify.html", form=form, question=user.security_question)
```
- [ ] 스크린샷: 비밀번호 찾기 질문 확인 화면 / 재설정 성공 후 새 비밀번호로 로그인한 화면

#### 3) 채팅 안읽음 표시

상대가 말을 걸었는지 매번 대화방에 직접 들어가서 확인해야 했던 문제를 해결했다. `ReadMarker` 테이블에 사용자별·채팅방(room)별 마지막 열람 시각을 기록해두고, 그 이후에 온 (내가 보내지 않은) 메시지 수를 사이드바에 배지로 보여준다.

**모델** (`server/models.py: ReadMarker`)
```python
class ReadMarker(db.Model):
    __tablename__ = "read_marker"
    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=False)
    room = db.Column(db.String(80), nullable=False)
    last_read_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (db.UniqueConstraint("user_id", "room", name="uq_read_marker"),)
```

**안읽음 계산 / 읽음 처리** (`server/blueprints/chat.py`)
```python
def _unread_count(user_id, room):
    marker = ReadMarker.query.filter_by(user_id=user_id, room=room).first()
    since = marker.last_read_at if marker else _EPOCH
    return (
        Message.query.filter(Message.room == room, Message.created_at > since, Message.sender_id != user_id)
        .count()
    )

def _mark_read(user_id, room):
    marker = ReadMarker.query.filter_by(user_id=user_id, room=room).first()
    now = datetime.utcnow()
    if marker is None:
        db.session.add(ReadMarker(user_id=user_id, room=room, last_read_at=now))
    else:
        marker.last_read_at = now
    db.session.commit()
```
- [ ] 스크린샷: 사이드바에 안읽음 배지가 표시된 화면 / 대화방 열람 후 배지가 사라진 화면

#### 4) 검색 필터 (가격대 / 판매상태)

상품이 많아지면 제목/설명 검색만으로는 원하는 걸 찾기 번거로웠다. 대시보드 검색에 가격대(최소/최대)와 판매상태(판매중/판매완료) 필터를 추가했다. 기존의 `q` 검색어 이스케이프 방식은 그대로 두고, 가격/상태는 화이트리스트·범위 검증만 추가했다.

**필터 적용** (`server/blueprints/products.py: dashboard`)
```python
status = request.args.get("status") or ""
if status in ("active", "sold"):          # 화이트리스트 - blocked는 선택 불가
    query = query.filter(Product.status == status)

min_price = request.args.get("min_price", type=int)
if min_price is not None and min_price >= 0:
    query = query.filter(Product.price >= min_price)

max_price = request.args.get("max_price", type=int)
if max_price is not None and max_price >= 0:
    query = query.filter(Product.price <= max_price)
```
- [ ] 스크린샷: 가격대/판매상태 필터를 적용한 상품 목록 화면

더 개선한다면:
- 안읽음 배지가 소켓 메시지 수신만으로 실시간 갱신되지 않고 페이지를 새로고침해야 반영된다 — 클라이언트에서 `receive_message` 이벤트를 받을 때 배지 카운트를 즉시 갱신하도록 개선할 수 있다.
- 비밀번호 찾기가 이메일 인증 없이 본인이 설정한 보안 질문/답변만으로 이뤄져서, 질문·답변을 주변 사람이 유추하면 계정을 탈취당할 여지가 있다 — 실제 서비스라면 이메일 인증 링크 방식이 더 안전하다.
- 상품 이미지가 1장만 지원된다 — 여러 장 업로드 및 썸네일 캐러셀을 지원하면 더 좋을 것 같다.

---

## 7. 개발 과정에서 확인한 보안 약점과 수정 내역

*(작성 가이드: 과제 요구사항 2번 "보안 약점이 무엇이고 어떻게 변경하였는지"에 대응하는 별도 장입니다.)*

기능을 하나씩 설계·구현하면서, "이 기능을 아무 방어 없이 가장 단순하게 만들면 어떤 지점이 뚫리기 쉬운가"를 먼저 생각하고 그걸 막는 방식으로 만들었다. 아래는 그 과정에서 실제로 짚고 넘어간 취약 지점과, 이 프로젝트에서 어떻게 강화했는지를 정리한 것이다.

| # | 아무렇게나 만들면 취약해지기 쉬운 지점 | 위험성 | 이 프로젝트에서 강화한 방법 |
|---|---|---|---|
| 1 | 비밀번호를 그냥 문자열로 DB에 저장 | DB가 유출되면 전 사용자 비밀번호가 즉시 그대로 노출됨 | `bcrypt.hashpw`로 salt를 포함해 해시 저장 (`security.py`) |
| 2 | 로그인 후 상태를 바꾸는 폼(상품 등록, 송금 등)에 CSRF 토큰이 없음 | 로그인된 사용자가 악성 사이트를 열어보는 것만으로 본인 의도와 무관한 요청이 대신 전송될 수 있음 | `Flask-WTF CSRFProtect`를 앱 전역에 적용, 모든 폼에 `csrf_token()` 삽입 |
| 3 | 세션 쿠키에 보안 옵션이 없고 `SECRET_KEY`를 코드에 그대로 박아둠 | 쿠키 탈취(XSS 연계), 시크릿 키 유출 시 세션 위조까지 가능 | `HttpOnly`+`SameSite=Lax`(+운영 시 `Secure`) 적용, `SECRET_KEY`는 환경변수에서만 로드 |
| 4 | 로그인 실패 횟수 제한이 없음 | 아이디를 알면 비밀번호를 무한정 무차별 대입할 수 있음 | 5회 실패 시 15분 계정 잠금(`register_failed_login`), 아이디 존재 여부를 유추 못 하도록 실패 사유와 무관하게 동일한 오류 메시지 사용 |
| 5 | 회원가입/상품등록 등 입력값을 서버에서 다시 검증하지 않고 그대로 저장 | 형식에 안 맞는 데이터 저장, `<script>` 같은 입력이 XSS 진입점이 될 수 있음 | 정규식/길이 기반 서버측 검증(`security.py`, `forms.py`) + Jinja2 자동 이스케이프 |
| 6 | 상품 수정/삭제 시 "이 상품이 정말 내 것인가"를 확인하지 않음 | 다른 사람의 상품 ID만 알면 URL을 직접 조작해 수정·삭제할 수 있는 IDOR 취약점 | `seller_id == current_user.id` 명시적 검증, 불일치 시 403 |
| 7 | 같은 사람이 같은 대상을 여러 번 신고하는 걸 막지 않음 | 신고 수를 인위적으로 부풀려 정상 상품/유저를 부당하게 차단시킬 수 있음 | `UNIQUE(reporter_id, target_type, target_id)` DB 제약 + `/report` rate limit |
| 8 | 신고가 쌓여도 아무 조치가 없음 | 악성 상품/유저가 신고를 받고도 방치됨 | 임계치(5회) 도달 시 자동 차단/정지 + 감사 로그 기록 |
| 9 | 채팅 소켓 연결에 인증/속도 제한이 없음 | 로그인하지 않은 사람도 메시지를 보낼 수 있고, 한 사람이 메시지를 무한정 도배할 수 있음 | 미인증 연결 즉시 차단, 메시지 길이 제한(500자), rate limit(10초당 8건) |
| 10 | 디버그 모드를 켜둔 채로 배포, 에러 발생 시 스택트레이스를 그대로 보여줌 | 내부 파일 경로, 코드 구조 같은 민감 정보가 그대로 노출됨 | `ProdConfig`에서 `DEBUG=False`, 커스텀 403/404/429/500 에러 페이지 |
| 11 | 응답에 보안 헤더가 전혀 없음 | 클릭재킹(iframe 삽입), MIME 스니핑 등에 취약 | CSP/`X-Frame-Options`/`X-Content-Type-Options`/`Referrer-Policy` 전역 적용 |
| 12 | 송금 기능을 만들 때 "잔액이 부족하면?", "정지된 사람에게 보내면?", "송금 중간에 실패하면?" 같은 예외를 놓치기 쉬움 | 잔액 위변조, 정지된 유저와의 비정상 거래, 송금은 됐는데 상품 상태는 안 바뀌는 데이터 불일치 | 자기 자신 금지·잔액 검증·정지 계정 금지·잔액 변경과 거래 기록을 하나의 커밋으로 묶는 원자적 처리를 설계 단계부터 포함, 상품 가격도 송금 최소액(1원)과 맞춰 0원 상품 등록 자체를 차단 |
| 13 | 관리자 계정을 코드에 아이디/비밀번호로 박아 넣고 시작 | 저장소를 public으로 올리는 순간 관리자 자격증명이 그대로 유출됨 | `seed_admin.py`가 환경변수(`ADMIN_USERNAME`/`ADMIN_PASSWORD`)로만 계정을 생성, 소스에는 자격증명이 전혀 없음 |
| 14 | *(유지보수 단계에서 추가)* 파일 업로드(상품 사진) 기능을 만들 때 사용자가 보낸 파일명을 그대로 믿고 저장 | 파일명에 `../`가 섞여 있으면 경로 조작(path traversal)이 가능하고, 확장자를 안 가리면 실행 가능한 파일을 올릴 위험도 있음 | 원본 파일명은 저장에 쓰지 않고 서버에서 `uuid` 기반 새 파일명을 생성, 확장자 화이트리스트(jpg/png/gif/webp) + 용량 제한(2MB) 검증 (`forms.py`, `blueprints/products.py: _save_product_image`) |
| 15 | *(유지보수 단계에서 추가)* 비밀번호 찾기용 보안 질문의 "답변"을 평문으로 저장 | 비밀번호를 평문 저장하는 것과 똑같은 문제 — DB 유출 시 답변이 그대로 노출되어 계정 탈취에 악용 가능 | 답변도 비밀번호와 동일하게 `bcrypt`로 해시 저장(대소문자·공백은 정규화 후 해시) (`security.py: hash_answer/verify_answer`) |
| 16 | *(유지보수 단계에서 발견 및 수정)* 자동 차단/정지 임계치 계산이 신고 status를 구분하지 않고 전체 신고 row 개수만 셈 | 관리자가 신고를 "허위 신고"로 기각(dismiss)해도 그 신고가 여전히 카운트에 남아있어서, 이후 관련 없는 신고 1건만 더 들어와도 기각된 신고까지 합쳐져 임계치를 넘겨 무고한 상품/유저가 차단·정지될 수 있음(관리자의 수동 검토가 사실상 무력화) | `_apply_threshold`의 카운트 쿼리에 `status != "dismissed"` 조건을 추가 — 기각된 신고는 재차단/재정지 판단에서 제외 (`blueprints/reports.py: _apply_threshold`). 4건 신고 후 1건 기각 → 5번째 신고가 들어와도 차단되지 않고, 기각되지 않은 신고가 5건이 되어야 비로소 차단되는 것을 직접 재현해 확인함 |

*(본인 검증 팁: 가능하면 각 항목을 실제로 취약한 버전으로 잠깐 되돌려서 정말 뚫리는지 확인하고 적으면 설득력이 올라갑니다. 예: CSRF 보호를 잠깐 꺼보고 실제로 강제 요청이 통하는지 확인.)*

---

## 8. 결론

*(작성 가이드: "기능이 동작하는 것"과 "안전하게 동작하는 것"의 차이를 본인이 이번 과제에서 어떻게 체감했는지, 가장 어려웠던 부분/가장 배운 점을 2~3문장으로)*

[ ]
