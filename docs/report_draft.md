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

*(작성 가이드: 기존 기준 체크리스트(csv)의 "Section | Checklist Item | Description" 형식처럼, 분류마다 표를 쪼개지 않고 하나의 연속된 표로 합쳤습니다. 여기에 "구현 위치 → 테스트 방법 → 실제 결과" 열을 더해서, 과제 요구사항의 "체크리스트 작성 및 테스팅"과 "보안 약점 확인/수정 내역 작성"을 표 하나로 동시에 충족합니다. **"실제 결과" 열은 본인이 직접 실행해서 채우세요 — 이 보고서에서 가장 중요한 부분입니다.**)*

먼저 서버를 띄웁니다.

```bash
cd ~/github_repo/secure_coding
source .venv/bin/activate
cd server
python app.py
```

| # | Section (분류) | Checklist Item (항목) | Description (위험성 / 왜 필요한가) | 구현 위치 | 테스트 방법 | 실제 결과 |
|---|---|---|---|---|---|---|
| 1 | 회원 관리 | 서버측 입력 검증 (아이디/비밀번호 형식) | 형식에 맞지 않는 데이터 저장, 후속 XSS의 진입점 | `security.py`, `forms.py` | 회원가입 아이디에 `<script>` 입력 | [ ] |
| 2 | 회원 관리 | 비밀번호 해시 저장 | DB 유출 시 전 사용자 비밀번호 즉시 노출 | `security.py: hash_password` | DB 파일에서 `password_hash` 값이 평문이 아닌지 확인 | [ ] |
| 3 | 회원 관리 | 로그인 실패 방어 (계정 잠금) | 무차별 대입(brute-force) 공격 | `models.py: register_failed_login` | 로그인 5회 실패 후 6번째 시도 | [ ] |
| 4 | 회원 관리 | 계정 존재 여부 미노출 | 로그인 실패 메시지로 아이디 목록을 유추(사용자 열거) | `auth.py: login()` 동일 오류 메시지 | 존재하는/존재하지 않는 아이디로 각각 로그인 실패 시 메시지 비교 | [ ] |
| 5 | 상품 관리 | 폼 입력 검증 (제목/설명/가격) | 비정상 데이터 저장 (0원/음수 상품은 송금 최소액과 불일치) | `forms.py: ProductForm` | 가격에 0/음수/10억 초과 값 입력 | [ ] |
| 6 | 상품 관리 | XSS 방어 (상품 설명 등) | 저장형 XSS로 세션 탈취 가능 | Jinja2 autoescape | 설명에 `<img onerror=...>` 입력 후 상세 페이지 조회 | [ ] |
| 7 | 상품 관리 | 소유자 확인 (수정/삭제) | IDOR — 타인이 내 상품을 조작 | `products.py: edit_product/delete_product` | 다른 계정으로 상품 수정/삭제 시도 → 403 | [ ] |
| 8 | 상품 관리 | 차단된 상품 비노출 | 신고로 차단된 악성 상품이 계속 노출됨 | `products.py: dashboard()/view_product()` | 차단된 상품을 검색하거나 URL로 직접 접근 | [ ] |
| 9 | 소통 (채팅) | 소켓 연결 시 인증 확인 | 비로그인 사용자의 스팸/도배 | `chat.py: handle_connect` | 로그인 없이 소켓 연결 시도 → 연결 거부 | [ ] |
| 10 | 소통 (채팅) | 메시지 검증/속도 제한 | 도배(스팸)로 서비스 저하 | `chat.py: MAX_MESSAGE_LEN`, `_rate_limited` | 짧은 시간 내 메시지 다수 전송 | [ ] |
| 11 | 소통 (채팅) | 1:1 채팅 참여자 검증 | 타인의 1:1 대화를 엿볼 수 있음 | `chat.py: handle_join` | 대화 참여자가 아닌 계정으로 해당 방 join 시도 | [ ] |
| 12 | 소통 (채팅) | 인증된 전체 채팅 송수신 | (정상 동작 확인) | `chat.py: handle_send_message` | 로그인 상태로 전체 채팅 송수신 → 정상 브로드캐스트 | [ ] |
| 13 | 신고 및 제재 | 신고 사유 필수/형식 검증 | 근거 없는 신고 남용 | `forms.py: ReportForm` | 사유 없이 신고, `target_type` 위조 시도 | [ ] |
| 14 | 신고 및 제재 | 중복 신고 방지 | 동일인이 반복 신고해 신고 수 조작 | `models.py: Report` UniqueConstraint | 같은 대상을 같은 계정으로 두 번 신고 | [ ] |
| 15 | 신고 및 제재 | 임계치 도달 시 자동 조치 | 신고가 누적돼도 방치되면 악성 상품/유저 존속 | `reports.py: _apply_threshold` | 서로 다른 5개 계정으로 같은 상품 신고 → `blocked` 전환 | [ ] |
| 16 | 신고 및 제재 | 관리자 수동 검토(기각) | 자동조치가 오탐일 경우 되돌릴 수단 필요 | `admin.py: dismiss_report` | 관리자 계정으로 신고 기각 처리 | [ ] |
| 17 | 송금 | 인증된 사용자만 송금 | 비로그인 상태의 임의 송금 | `transfers.py` `@login_required` | 로그인 없이 `/transfer` 접근 | [ ] |
| 18 | 송금 | 자기 자신 송금 방지 | 무의미한 자가 거래로 로직 악용 | `transfers.py: transfer()` | 본인 아이디로 송금 시도 | [ ] |
| 19 | 송금 | 잔액 부족 검증 | 잔액 위·변조(음수 잔액) | `transfers.py: transfer()` | 보유 잔액보다 큰 금액 송금 시도 | [ ] |
| 20 | 송금 | 정지 유저에게 송금 금지 | 제재를 우회한 자금 이동 | `transfers.py: transfer()` | 정지 상태 계정으로 송금 시도 | [ ] |
| 21 | 송금 | 원자적 처리 (구매 = 송금 + 상태변경) | 중간 실패 시 돈만 빠지고 상품 상태는 그대로인 정합성 붕괴 | `transfers.py: _execute_transfer` | 상품 구매 후 구매자/판매자 잔액, 상품 상태, 거래내역 모두 확인 | [ ] |
| 22 | 검색 | SQL Injection 방지 | 검색어로 DB를 임의 조회/조작 | `products.py: dashboard()` (ilike + `%`/`_`/`\` 이스케이프) | 검색어에 `' OR '1'='1` 입력 | [ ] |
| 23 | 검색 | 부분 문자열 검색 정확성 | (정상 동작 확인) | `products.py: dashboard()` | 존재하는 검색어 / 존재하지 않는 검색어 각각 조회 | [ ] |
| 24 | 검색 | 차단 상품 검색 결과 제외 | 차단된 악성 상품이 검색으로 재노출 | `products.py: dashboard()` | 차단된 상품명으로 검색 | [ ] |
| 25 | 관리자 | 역할 기반 접근 제어 | 비인가자의 관리 기능 접근 | `admin.py: admin_required` | 일반 계정으로 `/admin/` 접근 → 403 | [ ] |
| 26 | 관리자 | 관리자 계정 하드코딩 금지 | 저장소가 공개되는 순간 자격증명 유출 | `scripts/seed_admin.py` | 소스코드 전체에서 비밀번호 문자열 검색(grep) | [ ] |
| 27 | 관리자 | 관리자 조치 감사 로그 | 조치 이력 추적 불가 | `admin.py: _log()` | 회원 정지/상품 차단 후 `audit_log` 테이블 확인 | [ ] |
| 28 | 전체 시스템 | CSRF 보호 | 로그인된 사용자를 대상으로 한 CSRF 공격 | `extensions.py` (`CSRFProtect`) | CSRF 토큰 없이 상품 등록 POST → 400 | [ ] |
| 29 | 전체 시스템 | 세션 쿠키 보안 옵션 | 세션 탈취(XSS 연계), 시크릿 키 유출 시 세션 위조 | `config.py: SESSION_COOKIE_*`, `SECRET_KEY` | 응답의 `Set-Cookie` 헤더에서 `HttpOnly`/`SameSite` 확인 | [ ] |
| 30 | 전체 시스템 | 보안 헤더 | 클릭재킹, MIME 스니핑 | `app.py: set_security_headers` | `curl -I`로 CSP/X-Frame-Options 등 확인 | [ ] |
| 31 | 전체 시스템 | 디버그 모드/에러 페이지 | 스택 트레이스 등 내부 정보 노출 | `config.py: DEBUG=False`, `app.py` 에러 핸들러 | 존재하지 않는 페이지 접근, 500 유도 후 응답 내용 확인 | [ ] |
| 32 | 전체 시스템 | 요청 크기 제한 | 과대 payload로 인한 자원 소모 | `config.py: MAX_CONTENT_LENGTH` | 1MB 초과 요청 전송 | [ ] |
| 33 | 전체 시스템 | Rate Limiting | 무차별 대입/도배/자원 소모 | `Flask-Limiter` (엔드포인트별) | 회원가입/로그인 등을 짧은 시간에 반복 요청 | [ ] |

*(본인 검증 팁: "Description" 열이 바로 과제에서 요구하는 "보안 약점"입니다. 가능하면 각 항목을 실제로 취약한 버전으로 잠깐 되돌려서 정말 뚫리는지 확인하고 "실제 결과"에 적으면 설득력이 올라갑니다. 예: CSRF 보호를 잠깐 꺼보고 실제로 강제 요청이 통하는지 확인.)*

---

## 6. 유지보수

*(작성 가이드: README의 "알려진 한계"를 본인이 이해한 이유와 함께 재작성)*

- 로컬 개발 서버(Werkzeug) 기반 실행 → 운영 시 gunicorn+eventlet/gevent + Nginx 필요, 이유: [ ]
- SQLite 단일 프로세스 기준 동시성 처리 → 운영 시 `SELECT ... FOR UPDATE` 필요, 이유: [ ]
- 인메모리 rate limit → 다중 프로세스 배포 시 Redis 필요, 이유: [ ]
- 향후 개선 방향(본인 생각): [ ]

---

## 7. 결론

*(작성 가이드: "기능이 동작하는 것"과 "안전하게 동작하는 것"의 차이를 본인이 이번 과제에서 어떻게 체감했는지, 가장 어려웠던 부분/가장 배운 점을 2~3문장으로)*

[ ]
