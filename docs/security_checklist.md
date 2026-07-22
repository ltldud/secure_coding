# 보안 체크리스트 (구현 반영본)

`ugonfor/secure-coding` 과제 기준 체크리스트를 본 프로젝트 구조(회원가입/프로필, 상품, 채팅, 신고, 송금, 검색, 관리자)에 맞게 확장한 버전입니다. 각 항목은 실제 구현 위치와 함께 표시했습니다.

## 1. 회원가입 및 프로필 관리

| 체크리스트 항목 | 상태 | 구현 위치 |
|---|---|---|
| 서버측 입력 검증 (username/password 길이·문자셋) | ✅ | `security.py` (`USERNAME_RE`, `PASSWORD_RE`), `forms.py` (`RegisterForm`) |
| XSS 방지 (입력값 필터링/인코딩) | ✅ | Jinja2 autoescape 전역 적용, 사용자 입력을 `\|safe` 없이 렌더링 |
| CSRF 보호 | ✅ | `Flask-WTF CSRFProtect` 전역 등록 (`extensions.py`), 모든 폼에 `hidden_tag()` |
| 비밀번호 해시 저장 | ✅ | `security.py` `bcrypt.hashpw` + salt 자동 생성 |
| 세션 쿠키 보안 설정 (HttpOnly/SameSite/Secure) | ✅ | `config.py` `SESSION_COOKIE_HTTPONLY/SAMESITE/SECURE` |
| 세션 만료 및 재인증 | ✅ | `PERMANENT_SESSION_LIFETIME=30분`, 비밀번호 변경 시 현재 비밀번호 재확인(`blueprints/profile.py`) |
| 로그인 실패 방어 (계정 잠금/지연) | ✅ | `models.py` `User.register_failed_login` (5회 실패 시 15분 잠금) |
| 오류 메시지에 내부 정보 미노출 | ✅ | `app.py` 커스텀 에러 핸들러(403/404/429/500), 로그인 실패 시 아이디/비번 구분 없는 동일 메시지(사용자 열거 방지) |

## 2. 상품 등록 및 관리 (+ 검색)

| 체크리스트 항목 | 상태 | 구현 위치 |
|---|---|---|
| 폼 입력 검증 (제목/설명/가격) | ✅ | `forms.py` `ProductForm` (길이 제한, 가격 범위 1~10억) |
| XSS 방어 (상품 설명 등) | ✅ | Jinja2 autoescape (`view_product.html` 등) |
| 인증된 사용자만 등록 | ✅ | `@login_required` on `/product/new` |
| 소유자 확인 (수정/삭제) | ✅ | `blueprints/products.py` `edit_product`/`delete_product`에서 `seller_id` 비교, 불일치 시 403 |
| 데이터 무결성 | ✅ | SQLAlchemy 컬럼 `nullable=False`, ORM validators |
| 검색 기능 서버측 처리 | ✅ | `blueprints/products.py` `dashboard()` - ORM `ilike` + `%`/`_` 이스케이프, 파라미터 바인딩(SQL Injection 불가) |
| 차단된 상품 비노출 | ✅ | `dashboard()`에서 `status != 'blocked'` 필터, `view_product`에서 소유자/관리자 외 404 |

## 3. 실시간 채팅 및 메시징 (전체 채팅 + 1:1)

| 체크리스트 항목 | 상태 | 구현 위치 |
|---|---|---|
| 메시지 내용 검증 (길이/이스케이프) | ✅ | `blueprints/chat.py` `MAX_MESSAGE_LEN=500`, 클라이언트는 `textContent`로만 렌더링(`static/js/chat.js`) - DOM XSS 원천 차단 |
| 소켓 연결 시 사용자 인증 확인 | ✅ | `@socketio.on('connect')`에서 `current_user.is_authenticated` 체크 후 미인증 시 `disconnect()` |
| 1:1 채팅 참여자 검증 | ✅ | `join`/`send_message` 핸들러에서 `Conversation.user_a_id/user_b_id` 포함 여부 확인 |
| 서버측 메시지 데이터 검증 | ✅ | 빈 문자열/최대 길이 초과 메시지 무시 |
| Rate Limiting (도배 방지) | ✅ | `blueprints/chat.py` `_rate_limited` (10초당 8건 제한, 초과 시 system_notice) |
| 정지된 사용자 채팅 차단 | ✅ | `send_message`에서 `current_user.status == 'suspended'` 시 `disconnect()` |
| 연결 암호화 (운영 환경 WSS) | ⚠️ 운영 필요 | 로컬 개발은 평문 WS. 배포 시 리버스 프록시(Nginx)에서 TLS 종단 + WSS 필요 (README에 안내) |

## 4. 안전 거래 및 신고 (+ 자동 조치)

| 체크리스트 항목 | 상태 | 구현 위치 |
|---|---|---|
| 폼 입력 검증 (target_id/reason) | ✅ | `forms.py` `ReportForm` (`target_type` 화이트리스트, `reason` 5~500자) |
| 인증된 사용자만 신고 | ✅ | `@login_required` on `/report` |
| 데이터 무결성 및 로그 관리 | ✅ | `Report` 테이블 + 자동 조치 시 `AuditLog` 기록 |
| 신고 남용 방지 (중복/반복 신고 제한) | ✅ | `Report` 테이블 `UniqueConstraint(reporter_id, target_type, target_id)` - 동일 대상 재신고 불가, `/report` 요청 자체도 rate limit(20/hour) |
| 자기 자신/자기 상품 신고 방지 | ✅ | `blueprints/reports.py` self-report 차단 |
| 임계치 초과 시 자동 차단/정지 | ✅ | `_apply_threshold()` - 상품 5회 → `blocked`, 사용자 5회 → `suspended` (`config.py` `REPORT_THRESHOLD_*`) |
| 관리자 수동 검토 | ✅ | `blueprints/admin.py` `/admin/reports` 기각(dismiss) 처리 |

## 5. 송금 (직접 설계)

| 체크리스트 항목 | 상태 | 구현 위치 |
|---|---|---|
| 인증된 사용자만 송금 | ✅ | `@login_required` on `/transfer`, `/product/<id>/purchase` |
| 입력 검증 (금액 양수, 범위) | ✅ | `forms.py` `TransferForm` `NumberRange(min=1)` |
| 잔액 부족 검증 | ✅ | `blueprints/transfers.py` `current_user.balance < amount` 체크 |
| 자기 자신에게 송금 방지 | ✅ | `receiver.id == current_user.id` 체크 |
| 정지된 사용자에게 송금 방지 | ✅ | `receiver.status == 'suspended'` 체크 |
| 원자적 처리 (부분 실패 방지) | ✅ | 잔액 차감/증가와 `Transaction` 기록을 하나의 커밋 단위로 처리 |
| 거래 로그 기록 | ✅ | `Transaction` 테이블, `/transactions`(본인)·`/admin/transactions`(전체) 조회 |
| 동시성(이중 사용) 방어 | ⚠️ 알려진 한계 | 단일 프로세스 SQLite 개발 서버 기준 안전. 운영 배포 시 RDBMS `SELECT ... FOR UPDATE` 등 필요 (코드 주석에 명시) |

## 6. 관리자 기능 (직접 설계)

| 체크리스트 항목 | 상태 | 구현 위치 |
|---|---|---|
| 관리자 권한 분리 (역할 기반 접근 제어) | ✅ | `models.py` `User.role`, `blueprints/admin.py` `admin_required` 데코레이터, 비관리자 403 |
| 관리자 계정 하드코딩 금지 | ✅ | `scripts/seed_admin.py` - 환경변수(`ADMIN_USERNAME`/`ADMIN_PASSWORD`)로만 생성, 소스에 자격증명 없음 |
| 관리자 행위 감사 로그 | ✅ | `AuditLog` 테이블에 정지/차단/삭제/기각 등 기록 |
| 자기 자신 정지 방지 | ✅ | `suspend_user()`에서 `user.id == current_user.id` 차단 |
| 회원/상품/신고/거래 전체 관리 | ✅ | `/admin/users`, `/admin/products`, `/admin/reports`, `/admin/transactions` |

## 7. 전체 시스템

| 체크리스트 항목 | 상태 | 구현 위치 |
|---|---|---|
| ORM 및 파라미터 바인딩 (SQL Injection 방지) | ✅ | 전 구간 Flask-SQLAlchemy ORM 사용, raw SQL 미사용 |
| 보안 헤더 설정 | ✅ | `app.py` `after_request` - CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, (HTTPS 시)HSTS |
| HTTPS 적용 | ⚠️ 운영 필요 | 로컬 개발은 HTTP. 배포 시 리버스 프록시에서 TLS 종단 후 `SESSION_COOKIE_SECURE=true` 설정 (README 안내) |
| 에러/예외 처리 (민감정보 미노출) | ✅ | 커스텀 에러 페이지, `debug=False`(운영), 예외는 서버 로그에만 기록 |
| 요청 크기 제한 | ✅ | `config.py` `MAX_CONTENT_LENGTH = 1MB` |
| Rate Limiting (전역) | ✅ | `Flask-Limiter` - 회원가입/로그인/신고/송금/구매 각각 개별 제한 |
| 시크릿 키 하드코딩 금지 | ✅ | `config.py` `SECRET_KEY`는 환경변수에서만 로드(`.env`, 미설정 시 프로세스별 임시 랜덤값) |
| 라이브러리 최신 버전 사용 | ✅ | `requirements.txt` 고정 버전 명시, 정기 점검 필요(운영 항목으로 README에 기재) |
