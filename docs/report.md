---

<aside>
📢

과제 목표

---

1. 플랫폼 개발 전 과정
    - 요구사항 분석
    - 시스템 설계
    - 구현
    - 체크리스트 작성 및 테스트
    - 유지보수
2. 보안 약점이 무엇이고 어떻게 변경하였는지
</aside>

---

- 이름: 이시영
- 반: 22반
- GitHub 저장소: https://github.com/ltldud/secure_coding

## 플랫폼 개발 과정

### 1. 요구사항 분석

#### 기능적 요구사항

| 분류 | 요구사항 |
| --- | --- |
| 회원 관리 | 회원가입 및 로그인, 프로필 관리, 아이디 중복 불가 |
| 상품 관리 | 상품 등록 및 조회, 목록에는 이름만 노출 → 클릭 시 상세 페이지 |
| 소통 | 전체 채팅, 1:1 채팅 |
| 신고 및 제재 | 신고 사유 필수, 일정 횟수 이상 신고 시 상품 차단 후 유저 휴면 전환 |
| 송금 | 유저 간 송금 |
| 검색 | 상품 검색 |
| 관리자 | 플랫폼 전 요소 관리 |

#### 비기능적 요구사항

- 보안
- 디자인
- 안정성
- 감사 가능성
- 유지보수

### 2. 시스템 설계

#### 회원 관리

- 회원가입
- 로그인
- 마이페이지
- 공개 프로필

#### 소통

- 전체 채팅 기능
- 유저 간 1대1 채팅
- 인증되지 않은 사용자는 채팅 연결 거부
- 메시지 길이 제한, 도배 방지 속도 제한

#### 송금

- 로그인한 사용자만 송금 가능
- 본인에게 송금 불가
- 잔액 부족 시 거부
- 정지된 계정에 송금 불가
- 상품 구매는 송금과 상품 상태의 변경을 하나로 처리
- 모든 송금 내역은 감사 가능

#### 상품 관리

- 상품 등록
- 등록한 상품 확인 및 관리
- 로그인한 사용자 상품 조회 가능
- 목록엔 이름만

#### 신고 및 제재

- 불량 상품 및 사용자 신고, 사유 필수
- 동일 대상 중복 신고 불가
- 일정 횟수 이상 신고된 상품과 유저 정지
- 관리자가 신고 감사

#### 검색

- 로그인한 사용자 상품명 검색
- 상품 설명으로도 검색
- 차단된 상품은 검색 결과에서 제외
- 검색어에 의한 SQL Injection 불가

#### 관리자

- 관리자 계정은 하드코딩 불가
- 회원 관리, 상품 관리, 신고 관리, 거래 내역 등 통합 관리
- 관리자가 아닌 사용자는 접근 불가
- 중요한 조치는 감사 로그로 기록

#### 웹 페이지 설계

- 기본 페이지
    
    !image.png
    
- 회원가입 페이지
    
    !image.png
    
- 로그인 페이지
    
    !image.png
    
- 마이페이지
    
    !image.png
    
- 상품 목록 및 검색 페이지
    
    !image.png
    
- 새 상품 등록 페이지
    
    !image.png
    
- 상품 상세/수정 페이지

!image.png

!image.png

- 신고 페이지
    
    !image.png
    
- 전체 채팅 페이지
    
    !image.png
    
- 1대1 채팅 페이지
    
    !image.png
    
- 송금 페이지
    
    !image.png
    
- 거래 내역 페이지
    
    !image.png
    
- 관리자 대시보드 / 회원 관리 / 상품 관리 / 신고 관리 / 거래 관리 페이지

!image.png

!image.png

!image.png

!image.png

!image.png

#### DB 설계

- 사용자 정보
    - 사용자 아이디, 계정명, 비밀번호 해시, 소개글, 잔액, 권한, 계정 상태, 신고 누적 횟수, 로그인 실패 횟수, 잠금 해제 시각, 비밀번호 찾기 및 답변 해시
- 상품 정보
    - 상품 아이디, 상품명, 상품 설명, 가격, 판매자 아이디, 상품의 상태, 신고 누적 횟수, 사진 파일명
- 신고 정보
    - 신고 아이디, 신고자 아이디, 대상 유형, 대상 아이디, 신고 사유, 처리 상태
    - 동일 대상 중복 신고 방지를 위해 신고자, 대상 유형, 대상 아이디 조합에 제약
- 대화방 정보
    - 대화방 아이디, 참여자 A 아이디, 참여자 B 아이디
    - 1대1 채팅을 위해 추가
- 메시지 정보
    - 메시지 아이디, 채팅방, 발신자 아이디, 내용, 작성 시각
    - 전체 채팅방 or 1대1 대화방 공용
    - 읽음 마커 정보
    - 마커 아이디, 사용자 아이디, 채팅방, 마지막 열람 시각
    - 채팅 사이드바의 안읽음 배지를 계산하기 위해 유지보수 단계에서 추가, 사용자 + 채팅방 조합에 제약
- 거래 정보
    - 거래 아이디, 송신자 아이디, 수신자 아이디, 금액, 거래 종류, 연관 상품 아이디
    - 송금 기능을 위해 추가
- 감사 로그 정보
    - 로그 아이디, 조치자 아이디, 조치 내용, 대상
    - 관리자 조치 추적을 위해 추가

### 3. 시스템 구현

#### 사용 라이브러리

| lib | 역할 |
| --- | --- |
| Flask-SQLAlchemy | ORM, SQLite |
| Flask-Login | 세션/인증, `is_active` 오버라이드로 정지 계정 즉시 로그아웃 |
| Flask-WTF | 서버측 폼 검증 + CSRF 토큰 |
| Flask-SocketIO | 실시간 채팅 |
| Flask-Limiter | 엔드포인트별 rate limiting |
| bcrypt | 비밀번호 해시 |

#### 기능별 구현

유저 관리

- 회원가입

```python
@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("products.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(username=form.username.data).first()
        if existing is not None:
            flash("이미 존재하는 사용자명입니다.", "danger")
            return render_template("register.html", form=form)

        user = User(username=form.username.data, balance=Config.STARTING_BALANCE)
        user.set_password(form.password.data)
        user.security_question = form.security_question.data.strip()
        user.set_security_answer(form.security_answer.data)
        db.session.add(user)
        db.session.commit()
        flash("회원가입이 완료되었습니다. 로그인 해주세요.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)

```

- 로그인

```python
@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("15 per 5 minutes")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("products.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        generic_error = "아이디 또는 비밀번호가 올바르지 않습니다."

        if user is None:
            flash(generic_error, "danger")
            return render_template("login.html", form=form)

        if user.is_locked():
            flash("계정이 잠겨 있습니다. 잠시 후 다시 시도하세요.", "danger")
            return render_template("login.html", form=form)

        if user.status == "suspended":
            flash("휴면(정지) 처리된 계정입니다. 관리자에게 문의하세요.", "danger")
            return render_template("login.html", form=form)

        if not user.check_password(form.password.data):
            user.register_failed_login(Config.LOGIN_FAIL_LIMIT, Config.LOGIN_LOCK_MINUTES)
            db.session.commit()
            flash(generic_error, "danger")
            return render_template("login.html", form=form)

        user.reset_failed_login()
        db.session.commit()
        session.permanent = True
        login_user(user)
        flash("로그인 성공!", "success")
        return redirect(url_for("products.dashboard"))

    return render_template("login.html", form=form)
```

- 사용자 조회

```python
@profile_bp.route("/user/<username>")
@login_required
def view_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template("public_profile.html", profile_user=user)
```

- 마이페이지

```python
@profile_bp.route("/profile/security", methods=["POST"])
@login_required
@limiter.limit("10 per hour")
def update_security_question():
    sq_form = SecurityQuestionForm()
    if sq_form.validate_on_submit():
        if not current_user.check_password(sq_form.current_password.data):
            flash("현재 비밀번호가 올바르지 않습니다.", "danger")
            return redirect(url_for("profile.mypage"))
        current_user.security_question = sq_form.security_question.data.strip()
        current_user.set_security_answer(sq_form.security_answer.data)
        db.session.commit()
        flash("비밀번호 찾기 질문이 설정되었습니다.", "success")
    else:
        for errs in sq_form.errors.values():
            for e in errs:
                flash(e, "danger")
    return redirect(url_for("profile.mypage"))
```

#### 상품 관리

- 상품 등록

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
        if form.image.data:
            product.image_filename = _save_product_image(form.image.data)
        db.session.add(product)
        db.session.commit()
        flash("상품이 등록되었습니다.", "success")
        return redirect(url_for("products.view_product", product_id=product.id))
    return render_template("new_product.html", form=form)
```

- 등록된 상품 관리

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
        if form.image.data:
            old_filename = product.image_filename
            product.image_filename = _save_product_image(form.image.data)
            _delete_product_image(old_filename)
        db.session.commit()
        flash("상품 정보가 수정되었습니다.", "success")
        return redirect(url_for("products.view_product", product_id=product.id))
    return render_template("edit_product.html", form=form, product=product)

@products_bp.route("/product/<product_id>/delete", methods=["POST"])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.seller_id != current_user.id and not current_user.is_admin():
        abort(403)
    _delete_product_image(product.image_filename)
    db.session.delete(product)
    db.session.commit()
    flash("상품이 삭제되었습니다.", "info")
    return redirect(url_for("products.my_products"))
```

- 상품 조회 및 상세 페이지

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

#### 유저 소통 기능

- 실시간 **전체 채팅**

```python
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
```

- 1대1 채팅 기능

```python
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
    global_unread = _unread_count(current_user.id, GLOBAL_ROOM)
    _mark_read(current_user.id, convo.id)
    return render_template(
        "chat_dm.html",
        history=history,
        other=other,
        room=convo.id,
        conversations=_sidebar_conversations(current_user.id),
        global_unread=global_unread,
        active_room=convo.id,
    )

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
```

#### 악성 유저 필터링

- 불량 상품 및 유저 신고

```python
@reports_bp.route("/report", methods=["GET", "POST"])
@login_required
@limiter.limit("20 per hour")
def report():
    target_type = request.values.get("target_type", "")
    target_id = request.values.get("target_id", "")

    form = ReportForm(target_type=target_type, target_id=target_id)

    if form.validate_on_submit():
        t_type = form.target_type.data
        t_id = form.target_id.data

        target = _resolve_target(t_type, t_id)
        if target is None:
            abort(404)

        if t_type == "user" and t_id == current_user.id:
            flash("자기 자신은 신고할 수 없습니다.", "danger")
            return redirect(url_for("products.dashboard"))
        if t_type == "product" and target.seller_id == current_user.id:
            flash("자신의 상품은 신고할 수 없습니다.", "danger")
            return redirect(url_for("products.dashboard"))

        rpt = Report(
            reporter_id=current_user.id,
            target_type=t_type,
            target_id=t_id,
            reason=form.reason.data.strip(),
        )
        db.session.add(rpt)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("이미 신고한 대상입니다.", "warning")
            return redirect(url_for("products.dashboard"))

        _apply_threshold(t_type, t_id)

        flash("신고가 접수되었습니다.", "success")
        return redirect(url_for("products.dashboard"))

    return render_template("report.html", form=form, target_type=target_type, target_id=target_id)
```

- 불량 상품 차단 및 유저 정지

```python
def _apply_threshold(target_type, target_id):
    count = (
        Report.query.filter_by(target_type=target_type, target_id=target_id)
        .filter(Report.status != "dismissed")
        .count()
    )

    if target_type == "product":
        product = db.session.get(Product, target_id)
        if product is None or product.status == "blocked":
            return
        product.report_count = count
        if count >= Config.REPORT_THRESHOLD_PRODUCT:
            product.status = "blocked"
            Report.query.filter_by(target_type="product", target_id=target_id).update({"status": "actioned"})
            db.session.add(AuditLog(actor_id=None, action="auto_block_product", target=target_id))
        db.session.commit()

    elif target_type == "user":
        user = db.session.get(User, target_id)
        if user is None or user.status == "suspended":
            return
        user.report_count = count
        if count >= Config.REPORT_THRESHOLD_USER:
            user.status = "suspended"
            Report.query.filter_by(target_type="user", target_id=target_id).update({"status": "actioned"})
            db.session.add(AuditLog(actor_id=None, action="auto_suspend_user", target=target_id))
        db.session.commit()
```

#### 송금

- 유저 간 송금 기능

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
            flash(f"{receiver.username}님에게 {amount:,}원을 송금했습니다.", "success")
            return redirect(url_for("transfers.history"))

    return render_template("transfer.html", form=form, balance=current_user.balance)
```

- 상품 구매

```python
@transfers_bp.route("/product/<product_id>/purchase", methods=["POST"])
@login_required
@limiter.limit("30 per hour")
def purchase(product_id):
    product = Product.query.get_or_404(product_id)

    if product.status != "active":
        flash("판매 중인 상품이 아닙니다.", "danger")
        return redirect(url_for("products.view_product", product_id=product_id))
    if product.seller_id == current_user.id:
        flash("자신의 상품은 구매할 수 없습니다.", "danger")
        return redirect(url_for("products.view_product", product_id=product_id))
    if current_user.balance < product.price:
        flash("잔액이 부족합니다.", "danger")
        return redirect(url_for("products.view_product", product_id=product_id))

    seller = product.seller
    _execute_transfer(current_user, seller, product.price, kind="purchase", product=product)
    product.status = "sold"
    db.session.commit()

    flash("구매가 완료되었습니다.", "success")
    return redirect(url_for("products.view_product", product_id=product_id))
 
def _execute_transfer(sender, receiver, amount, kind="transfer", product=None):
    sender.balance -= amount
    receiver.balance += amount
    db.session.add(
        Transaction(
            sender_id=sender.id,
            receiver_id=receiver.id,
            amount=amount,
            kind=kind,
            product_id=product.id if product else None,
        )
    )
    db.session.commit()
```

- 거래 내역 조회

```python
@transfers_bp.route("/transactions")
@login_required
def history():
    txs = Transaction.query.filter(
        db.or_(Transaction.sender_id == current_user.id, Transaction.receiver_id == current_user.id)
    ).order_by(Transaction.created_at.desc()).all()
    return render_template("transactions.html", txs=txs, me=current_user)
```

#### 검색

- 상품명, 상품 설명 검색

```python
q = (request.args.get("q") or "").strip()[:100]
if q:
    escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    like = "%" + escaped + "%"
    query = query.filter(
        db.or_(
            Product.title.ilike(like, escape="\\"),
            Product.description.ilike(like, escape="\\"),
        )
    )
```

#### 관리자

- 관리자 계정 생성

```python
username = os.environ.get("ADMIN_USERNAME")
password = os.environ.get("ADMIN_PASSWORD")

if not username or not password:
    print("ADMIN_USERNAME / ADMIN_PASSWORD environment variables are required.")
    sys.exit(1)

if not is_valid_username(username):
    print("ADMIN_USERNAME must be 3-20 chars, letters/digits/underscore only.")
    sys.exit(1)

if not is_valid_password(password):
    print("ADMIN_PASSWORD must be 8-64 chars with at least one letter and one digit.")
    sys.exit(1)

with app.app_context():
    db.create_all()
    user = User.query.filter_by(username=username).first()
    if user is None:
        user = User(username=username, balance=Config.STARTING_BALANCE, role="admin")
        user.set_password(password)
        db.session.add(user)
        print(f"Created new admin user '{username}'.")
    else:
        user.role = "admin"
	      user.status = "active"
        user.set_password(password)
        print(f"Promoted existing user '{username}' to admin and reset password.")
    db.session.commit()
```

- 회원, 상품, 신고, 거래 통합 관리

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
    _log("admin_suspend_user", user.id)
    db.session.commit()
    flash(f"{user.username} 계정을 정지했습니다.", "info")
    return redirect(url_for("admin.users"))
```

#### 핵심 검증 규칙

- 아이디: 영문/숫자/밑줄 3~20자 - `security.py: USERNAME_RE`
- 비밀번호: 8~64자, 영문+숫자 각 1자 이상 - `security.py: PASSWORD_RE`
- 비밀번호 찾기 질문 3~200자, 답변 1~200자 - `forms.py: RegisterForm/SecurityQuestionForm`
- 상품명 2000자, 가격 1 ~ 10억 - `forms.py: ProductForm`
- 상품 사진 확장자 화이트리스트, 크기 제한 - `forms.py: ProductForm`
- 신고 사유 5~500자, `target_type`은 `user`/`product` 화이트리스트만 허용 - `forms.py: ReportForm`
- 송금액 1 ~ 10억 - `forms.py: TransferForm`
- 가격대 검색 필터는 0 이상 정수만 허용 + 상태 필터는 active/sold 화이트리스트만 허용 - `blueprints/products.py: dashboard`

### 4. 체크리스트 작성 및 테스트

#### checklist

| # | Section | Checklist Item | Description |
| --- | --- | --- | --- |
| 1 | 회원 관리 | 서버측 입력 검증 | 아이디와 비밀번호에 대해 길이, 허용 문자 집합, 형식 등 서버측 검증 수행.
XSS 공격 방지를 위해 입력값 필터링 및 인코딩 적용 여부 확인 |
| 2 |  | 비밀번호 보안 | 비밀번호를 평문으로 저장하지 않고 bcrypt 등 해시 알고리즘과 고유 salt를 적용하여 암호화 저장하는지 확인 |
| 3 |  | 실패 로그인 방어 | 로그인 실패 횟수에 따른 계정 잠금 혹은 지연 메커니즘 적용 여부 확인 |
| 4 |  | 오류 메시지 | 로그인 실패 시 아이디 존재 여부를 유추할 수 없도록 동일한 오류 메시지를 사용하는지 확인 |
| 5 | 상품 등록 및 관리 | 폼 입력 검증 | 상품 제목, 설명, 가격 등의 입력 필드에 대해 서버측 검증 및 필수 항목 체크 여부 확인. 가격은 숫자 형식 및 범위 검증 적용 |
| 6 |  | XSS 방어 | 사용자 입력에 대해 HTML 태그 및 스크립트 코드 이스케이프 또는 필터링 적용 여부 확인 |
| 7 |  | 소유자 확인 | 상품 수정 및 삭제 시, 요청한 사용자가 해당 상품의 소유자인지 검증하는 로직이 있는지 확인 |
| 8 |  | 차단 상품 비노출 | 신고로 차단된 상품이 목록/검색/상세 조회에서 제외되는지 확인 |
| 9 | 실시간 채팅 | 사용자 인증 | Socket 연결 시 사용자가 인증된 상태인지 확인하는 로직이 적용되어 있는지 확인 |
| 10 |  | 메시지 내용 검증 및 Rate Limiting | 채팅 메시지에 대해 길이 제한, 허용 문자 집합 검증 여부와 동일 사용자가 단기간에 과도한 메시지를 보내지 않도록 제한하는 기능 구현 여부 확인 |
| 11 |  | 1:1 대화방 참여자 검증 | 1:1 대화방에 참여자 본인만 접근할 수 있는지 검증하는 로직이 있는지 확인 |
| 12 |  | 정상 동작 확인 | 인증된 사용자 간 전체 채팅 메시지가 정상적으로 송수신되는지 확인 |
| 13 | 안전 거래 및 신고 | 폼 입력 검증 | 신고 대상 및 신고 사유에 대해 서버측 입력 검증, 길이 제한, XSS 방어 적용 여부 확인 |
| 14 |  | 신고 남용 방지 | 동일 사용자의 반복 신고 제한 로직이 구현되어 있는지 확인 |
| 15 |  | 데이터 무결성 및 로그 관리 | 일정 횟수 이상 신고된 상품 or 사용자가 자동으로 차단 or 휴면 처리되고, 조치 내역이 기록되는지 확인 |
| 16 |  | 관리자 검토 프로세스 | 관리자가 신고를 수동으로 검토하고 기각할 수 있는 프로세스가 있는지 확인 |
| 17 | 송금 | 인증된 사용자 접근 | 로그인한 사용자만 송금 기능에 접근할 수 있는지 확인 |
| 18 |  | 자기 자신 송금 방지 | 자기 자신에게는 송금할 수 없도록 제한되어 있는지 확인 |
| 19 |  | 잔액 부족 검증 | 보유 잔액을 초과하는 금액은 송금이 거부되는지 확인 |
| 20 |  | 정지 계정 송금 방지 | 정지(휴면) 상태의 사용자에게는 송금할 수 없도록 제한되어 있는지 확인 |
| 21 |  | 원자적 처리 | 상품 구매 시 송금과 상품 상태 변경이 하나의 트랜잭션으로 처리되어, 중간 실패로 인한 데이터 불일치가 없는지 확인 |
| 22 | 검색 | SQL Injection 방지 | 검색어에 대해 파라미터 바인딩 및 와일드카드 문자 이스케이프가 적용되어 SQL Injection이 불가능한지 확인 |
| 23 |  | 검색 결과 정확성 | 검색어와 일치하는 상품만 반환되고, 일치하는 상품이 없으면 빈 목록이 반환되는지 확인 |
| 24 |  | 차단 상품 제외 | 차단된 상품이 검색 결과에 노출되지 않는지 확인 |
| 25 | 관리자 | 역할 기반 접근 제어 | 관리자가 아닌 사용자가 관리자 페이지/기능에 접근할 수 없도록 제어되어 있는지 확인 |
| 26 |  | 계정 하드코딩 금지 | 관리자 계정이 소스코드에 하드코딩되지 않고 별도 절차로 생성되는지 확인 |
| 27 |  | 조치 감사 로그 | 관리자의 주요 조치가 감사 로그로 기록되는지 확인 |
| 28 | 전체 시스템 | CSRF 보호 | 회원가입, 로그인, 상품 등록 등 모든 폼에 대해 CSRF 토큰 사용 여부를 확인하여 요청 위조 공격 방지 |
| 29 |  | 세션 쿠키 설정 | 세션 쿠키에 HttpOnly 및 Secure 플래그가 적용되어 있는지 확인 |
| 30 |  | 보안 헤더 | 클릭재킹/MIME 스니핑 방지를 위한 보안 헤더가 응답에 포함되는지 확인 |
| 31 |  | 오류 메시지 | 오류 발생 시 내부 정보가 노출되지 않도록 처리되어 있는지 확인 |
| 32 |  | 요청 크기 제한 | 과대한 요청 본문이 제한되어 자원 소모를 방지하는지 확인 |
| 33 |  | Rate Limiting | 회원가입/로그인/신고/송금 등 주요 엔드포인트에 요청 속도 제한이 적용되어 있는지 확인 |

#### test

체크리스트 표에 있는 33개 항목을 브라우저로 손으로 클릭해보는 대신 Claude Code와 함께 작성한  `server/scripts/checklist_test.py`에 33개 항목을 전부 재현하는 자동화 테스트 스크립트를 작성해 테스트했다.

!image.png

!image.png

!image.png

### 유지보수

이 플랫폼에서 느낀 불편함 4가지는 다음과 같다.

1. 상품 사진이 없는 것
2. 비밀번호 찾기 기능 부재
3. 채팅에 안읽음 표시가 있으면 좋겠다
4. 상품을 검색할 때 필터가 있으면 좋겠다.

- **상품 사진**
    - 중고거래 플랫폼인데 사진 없이 텍스트로만 물건을 올려야 했던 게 가장 크게 체감된 문제였다. `Product`에 `image_filename` 컬럼을 추가하고, 업로드된 파일의 원본 이름을 그대로 믿지 않고 서버에서 `uuid` 기반 새 파일명을 생성해 저장한다. 확장자 화이트리스트와 용량 제한은 폼 검증 단계에서 걸러낸다.
    - 상품 사진 코드
        
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
        
    - 저장 시 파일명 재생성 코드
        
        ```python
        def _save_product_image(file_storage):
            ext = file_storage.filename.rsplit(".", 1)[-1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"   # 원본 파일명은 신뢰하지 않음
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            file_storage.save(os.path.join(Config.UPLOAD_FOLDER, filename))
            return filename
        ```
        
        !image.png
        
- **비밀번호 찾기**
    - 본인 계정 비밀번호를 잊어버렸을 때 복구할 방법이 전혀 없었던 점이 이번 과제를 진행하며 직접 겪은 문제였다. 이메일 발송 인프라 없이도 동작하도록, 가입 시 사용자가 직접 정의한 보안 질문/답변으로 본인 확인 후 새 비밀번호를 설정하는 2단계 플로우를 추가했다. 답변은 비밀번호와 마찬가지로 평문 저장하지 않고 `bcrypt`로 해시한다.
    - 답변 해시 저장/검증 코드
        
        ```python
        def _normalize_answer(raw_answer: str) -> str:
            return raw_answer.strip().lower()
        
        def hash_answer(raw_answer: str) -> str:
            return bcrypt.hashpw(_normalize_answer(raw_answer).encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        
        def verify_answer(raw_answer: str, answer_hash: str) -> bool:
            return bcrypt.checkpw(_normalize_answer(raw_answer).encode("utf-8"), answer_hash.encode("utf-8"))
        ```
        
    - 재설정 라우트 코드
        
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
        
    
    !image.png
    
    !image.png
    
    !image.png
    
    !image.png
    
- **채팅 안읽음 표시**
    - 상대가 말을 걸었는지 매번 대화방에 직접 들어가서 확인해야 했던 문제를 해결했다. `ReadMarker` 테이블에 사용자별, 채팅방별 마지막 열람 시각을 기록해두고, 그 이후에 온 메시지 수를 사이드바에 배지로 보여준다.
    - 읽음 유무 처리 코드
        
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
        
        !image.png
        
- **검색 필터**
    - 상품이 많으면 제목/설명 검색만으로는 원하는 걸 찾기 불편할 것이다. 대시보드 검색에 가격대와 판매상태 필터를 추가했다.
    - 필터 적용 코드
        
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
        
        !image.png
        

## 보안 강화

| # | 취약 지점 | 위험성 | 강화한 방법 |
| --- | --- | --- | --- |
| 1 | 비밀번호를 그냥 문자열로 DB에 저장 | DB가 유출되면 전 사용자 비밀번호가 즉시 그대로 노출됨 | `bcrypt.hashpw`로 salt를 포함해 해시 저장 |
| 2 | 로그인 후 상태를 바꾸는 폼에 CSRF 토큰이 없음 | 로그인된 사용자가 악성 사이트를 열어보는 것만으로 본인 의도와 무관한 요청이 대신 전송될 수 있음 | `Flask-WTF CSRFProtect`를 앱 전역에 적용, 모든 폼에 `csrf_token()` 삽입 |
| 3 | 세션 쿠키에 보안 옵션이 없고 `SECRET_KEY`를 코드에 그대로 박아둠 | 쿠키 탈취(XSS 연계), 시크릿 키 유출 시 세션 위조까지 가능 | `HttpOnly`+`SameSite=Lax` 적용, `SECRET_KEY`는 환경변수에서만 로드 |
| 4 | 로그인 실패 횟수 제한이 없음 | 아이디를 알면 비밀번호를 무한정 무차별 대입할 수 있음 | 5회 실패 시 15분 계정 잠금, 아이디 존재 여부를 유추 못 하도록 실패 사유와 무관하게 동일한 오류 메시지 사용 |
| 5 | 회원가입/상품등록 등 입력값을 서버에서 다시 검증하지 않고 그대로 저장 | 형식에 안 맞는 데이터 저장, `<script>` 같은 입력이 XSS 진입점이 될 수 있음 | 정규식/길이 기반 서버측 검증인 `security.py`, `forms.py` + Jinja2 자동 이스케이프 |
| 6 | 상품 수정/삭제 시 이 상품이 정말 내 것인지를 확인하지 않음 | 다른 사람의 상품 ID만 알면 URL을 직접 조작해 수정 및 삭제할 수 있는 IDOR 취약점 | `seller_id == current_user.id` 명시적 검증 |
| 7 | 같은 사람이 같은 대상을 여러 번 신고하는 걸 막지 않음 | 신고 수를 인위적으로 부풀려 정상 상품/유저를 부당하게 차단시킬 수 있음 | `UNIQUE(reporter_id, target_type, target_id)` DB 제약 + `/report` rate limit |
| 8 | 신고가 쌓여도 아무 조치가 없음 | 악성 상품/유저가 신고를 받고도 방치됨 | 임계치 도달 시 자동 차단/정지 + 감사 로그 기록 |
| 9 | 채팅 소켓 연결에 인증/속도 제한이 없음 | 로그인하지 않은 사람도 메시지를 보낼 수 있고, 한 사람이 메시지를 무한정 도배할 수 있음 | 미인증 연결 즉시 차단, 메시지 길이 제한, rate limit |
| 10 | 디버그 모드를 켜둔 채로 배포, 에러 발생 시 스택트레이스를 그대로 보여줌 | 내부 파일 경로, 코드 구조 같은 민감 정보가 그대로 노출됨 | `ProdConfig`에서 `DEBUG=False`, 커스텀 403/404/429/500 에러 페이지 |
| 11 | 응답에 보안 헤더가 전혀 없음 | 클릭재킹, MIME 스니핑 등에 취약 | CSP/`X-Frame-Options`/`X-Content-Type-Options`/`Referrer-Policy` 전역 적용 |
| 12 | 송금 기능을 만들 때 “잔액이 부족하면?, 정지된 사람에게 보내면?, 송금 중간에 실패하면?” 같은 예외를 놓치기 쉬움 | 잔액 위변조, 정지된 유저와의 비정상 거래, 송금은 됐는데 상품 상태는 안 바뀌는 데이터 불일치 | 자기 자신 금지, 잔액 검증, 정지 계정 금지, 잔액 변경과 거래 기록을 하나의 커밋으로 묶어 처리를 설계 단계부터 포함, 상품 가격도 송금 최소액과 맞춰 0원 상품 등록 자체를 차단 |
| 13 | 관리자 계정을 코드에 아이디/비밀번호로 박아 넣고 시작 | 저장소를 public으로 올리는 순간 관리자 자격증명이 그대로 유출됨 | `seed_admin.py`가 환경변수로만 계정을 생성, 소스에는 자격증명이 전혀 없음 |
| 14 | 파일 업로드 기능을 만들 때 사용자가 보낸 파일명을 그대로 믿고 저장 | 파일명에 `../` 이 섞여 있으면 경로 조작이 가능하고, 확장자를 안 가리면 실행 가능한 파일을 올릴 위험도 있음 | 원본 파일명은 저장에 쓰지 않고 서버에서 `uuid` 기반 새 파일명을 생성, 확장자 화이트리스트 + 용량 제한 검증 |
| 15 | 비밀번호 찾기용 보안 질문의 답변을 평문으로 저장 |  DB 유출 시 답변이 그대로 노출되어 계정 탈취에 악용 가능 | 답변도 비밀번호와 동일하게 `bcrypt`로 해시 저장 |
| 16 | 자동 차단/정지 임계치 계산이 신고 status를 구분하지 않고 전체 신고 row 개수만 셈 | 관리자가 신고를 허위 신고로 기각해도 그 신고가 여전히 카운트에 남아있어서, 이후 관련 없는 신고 1건만 더 들어와도 기각된 신고까지 합쳐져 임계치를 넘겨 무고한 상품/유저가 차단 및 정지될 수 있음 | `_apply_threshold`의 카운트 쿼리에 `status != "dismissed"` 조건을 추가 → 기각된 신고는 재차단/재정지 판단에서 제외.
4건 신고 후 1건 기각 → 5번째 신고가 들어와도 차단되지 않고, 기각되지 않은 신고가 5건이 되어야 비로소 차단되는 것을 직접 재현해 확인함 |
