# Secure Coding 과제 보고서 — 작성 가이드 초안

> 이 문서는 "완성된 보고서"가 아니라 **작성 가이드가 포함된 초안**입니다.
> - 코드만 보고 객관적으로 확인 가능한 부분(아키텍처, DB 설계, 폼 검증 규칙, 보안 약점 표)은 실제 코드를 근거로 채워뒀습니다.
> - 반면 **"실제로 실행해서 확인한 결과"에 해당하는 부분(5.2 테스트, 스크린샷)은 일부러 비워뒀습니다.** 본인이 서버를 직접 띄우고 재현해서 채우세요 — 채점 포인트가 "직접 수행"이기 때문입니다.
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

### 2.1 기능 요구사항

| 대분류 | 요구사항 |
|---|---|
| 회원 관리 | 가입/로그인, 프로필(소개글/비밀번호) 관리, 아이디 중복 불가 |
| 상품 관리 | 등록/조회, 목록에는 이름만 노출 → 클릭 시 상세 페이지 |
| 소통 | 전체 채팅, 1:1 채팅 |
| 신고/제재 | 신고 사유 필수, 일정 횟수 이상 신고 시 상품 차단 / 유저 휴면 전환 |
| 송금 | 유저 간 송금 (직접 설계) |
| 검색 | 상품 검색 (직접 설계) |
| 관리자 | 플랫폼 전 요소 관리 (직접 설계) |

### 2.2 직접 설계한 요구사항 상세

*(작성 가이드: 아래는 실제 코드(`blueprints/transfers.py`, `blueprints/products.py`, `blueprints/admin.py`)에 이미 구현된 규칙을 정리한 것. "왜 이 규칙이 필요한가"를 본인 말로 한 문장씩 덧붙이면 좋음 — 예: "정지된 유저에게 송금을 막지 않으면 제재를 우회해 자금을 빼돌릴 수 있기 때문")*

**송금** (`blueprints/transfers.py`)
- 로그인한 사용자만 송금 가능 (`@login_required`)
- 자기 자신에게는 송금 불가 (`receiver.id == current_user.id` 체크)
- 잔액 부족 시 거부 (`current_user.balance < amount`)
- 정지(휴면)된 사용자에게는 송금 불가 (`receiver.status == "suspended"`)
- 상품 구매는 "송금 + 상품 상태 변경(`sold`)"이 하나의 커밋 단위로 처리 (`_execute_transfer`)
- 모든 송금은 `Transaction` 테이블에 기록되어 감사 가능

**검색** (`blueprints/products.py` `dashboard()`)
- 로그인한 사용자가 상품명/설명 부분 문자열로 검색
- `Product.status != "blocked"` 필터로 차단된 상품은 노출되지 않음
- ORM `ilike` + `%`/`_`/`\` 이스케이프 처리로 검색어에 의한 SQL Injection/와일드카드 남용 방지

**관리자** (`blueprints/admin.py`, `scripts/seed_admin.py`)
- 관리자 계정은 소스코드에 하드코딩하지 않고 `scripts/seed_admin.py` + 환경변수(`ADMIN_USERNAME`/`ADMIN_PASSWORD`)로 생성
- `admin_required` 데코레이터로 비관리자는 403
- 회원 정지/해제, 상품 차단/해제/삭제, 신고 기각, 거래 내역 조회 기능 제공
- 주요 조치는 `AuditLog`에 기록 (`_log()`)

---

## 3. 시스템 설계

### 3.1 아키텍처

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

### 3.2 페이지 설계

*(작성 가이드: 각 페이지 스크린샷을 붙이면 좋음)*

- [ ] 기본 페이지 스크린샷
- [ ] 회원가입/로그인 페이지 스크린샷
- [ ] 마이페이지 / 공개 프로필 스크린샷
- [ ] 상품 목록(+검색) 페이지 스크린샷
- [ ] 상품 등록/수정/상세 페이지 스크린샷
- [ ] 전체 채팅 / 1:1 채팅 페이지 스크린샷
- [ ] 신고 / 송금 / 거래내역 페이지 스크린샷
- [ ] 관리자 대시보드/회원/상품/신고/거래 페이지 스크린샷

### 3.3 데이터베이스 설계

| 테이블 | 주요 컬럼 |
|---|---|
| `user` | id, username(unique), password_hash, bio, balance, role, status, report_count, failed_login_count, locked_until |
| `product` | id, title, description, price, seller_id(FK), status, report_count |
| `report` | id, reporter_id(FK), target_type, target_id, reason, status, **UNIQUE(reporter_id, target_type, target_id)** |
| `conversation` | id, user_a_id(FK), user_b_id(FK), **UNIQUE(user_a_id, user_b_id)** |
| `message` | id, room, sender_id(FK), content, created_at |
| `transaction` | id, sender_id(FK), receiver_id(FK), amount, kind(transfer/purchase), product_id(FK, nullable) |
| `audit_log` | id, actor_id(FK, nullable), action, target |

*(작성 가이드: 기준 코드 대비 어떤 컬럼/테이블을 왜 추가했는지 한 줄씩. 예: `balance` — 송금 기능을 위해 필요, `locked_until` — 로그인 잠금 구현을 위해 필요, 등)*

---

## 4. 시스템 구현

*(작성 가이드: 블루프린트 단위로 나눈 이유, 사용한 라이브러리와 각각의 역할을 본인 말로. 아래는 참고용 표)*

| 라이브러리 | 역할 |
|---|---|
| Flask-SQLAlchemy | ORM, SQLite |
| Flask-Login | 세션/인증, `is_active` 오버라이드로 정지 계정 즉시 로그아웃 |
| Flask-WTF | 서버측 폼 검증 + CSRF 토큰 |
| Flask-SocketIO | 실시간 채팅 |
| Flask-Limiter | 엔드포인트별 rate limiting |
| bcrypt | 비밀번호 해시(salt 자동 포함) |

핵심 검증 규칙 (`security.py`, `forms.py`):
- 아이디: 영문/숫자/밑줄 3~20자 (`USERNAME_RE`)
- 비밀번호: 8~64자, 영문+숫자 각 1자 이상 (`PASSWORD_RE`)
- 상품명 1~100자, 설명 1~2000자, 가격 0~10억 (`ProductForm`)
- 신고 사유 5~500자, `target_type`은 `user`/`product` 화이트리스트만 허용
- 송금액 1~10억 (`TransferForm`)

---

## 5. 체크리스트 작성 및 테스트

### 5.1 체크리스트

*(작성 가이드: `docs/security_checklist.md`에 7개 섹션·34개 항목이 이미 정리되어 있음. 그대로 가져다 쓰기보다, 본인이 코드 위치를 다시 확인하며 표를 재작성하는 걸 추천. 아래는 시작점.)*

| 영역 | 항목 | 구현 위치 |
|---|---|---|
| 회원가입 | 서버측 입력 검증 | `security.py`, `forms.py` |
| 회원가입 | 비밀번호 해시 저장 | `security.py: hash_password` |
| 회원가입 | 로그인 실패 방어 | `models.py: register_failed_login` |
| 상품 | 소유자 확인(수정/삭제) | `blueprints/products.py: edit_product/delete_product` |
| 상품 | 검색 SQL Injection 방지 | `blueprints/products.py: dashboard` |
| 채팅 | 소켓 연결 인증 확인 | `blueprints/chat.py: handle_connect` |
| 신고 | 중복 신고 방지 | `models.py: Report.__table_args__` (UniqueConstraint) |
| 신고 | 임계치 자동 제재 | `blueprints/reports.py: _apply_threshold` |
| 송금 | 자기 자신/정지유저/잔액부족 차단 | `blueprints/transfers.py: transfer` |
| 관리자 | 역할 기반 접근 제어 | `blueprints/admin.py: admin_required` |
| 전체 | CSRF 보호 | `extensions.py` (CSRFProtect 등록) |
| 전체 | 보안 헤더 | `app.py: set_security_headers` |

### 5.2 실제 테스트 수행 결과

**여기가 이 보고서에서 가장 중요한 부분입니다. 반드시 본인이 직접 실행해서 채우세요.**

먼저 서버를 띄웁니다.

```bash
cd ~/github_repo/secure_coding
source .venv/bin/activate
cd server
python app.py
```

아래 표의 각 시나리오를 브라우저 또는 `curl`로 직접 재현하고, "실제 결과" 칸과 스크린샷/터미널 출력을 채우세요.

| # | 테스트 시나리오 | 기대 결과 | 실제 결과 (본인 작성) |
|---|---|---|---|
| 1 | CSRF 토큰 없이 상품 등록 POST | 400 거부 | [ ] |
| 2 | 로그인 폼에 `' OR '1'='1` 입력 | 로그인 실패 | [ ] |
| 3 | 회원가입 아이디에 `<script>` 입력 | 형식 검증 실패 | [ ] |
| 4 | 상품 설명에 `<img onerror=...>` 입력 후 상세 페이지 조회 | 이스케이프되어 스크립트 미실행 | [ ] |
| 5 | 타인의 상품 수정/삭제 시도 | 403 | [ ] |
| 6 | 상품 검색(부분 문자열 / 존재하지 않는 검색어) | 일치 상품만 반환 / 빈 목록 | [ ] |
| 7 | 상품 구매 | 잔액 차감/증가, 상품 상태 `sold`, 거래내역 기록 | [ ] |
| 8 | 동일 상품에 서로 다른 5명이 신고 | 임계치 도달 시 자동 차단 | [ ] |
| 9 | 관리자가 아닌 사용자가 `/admin/` 접근 | 403 | [ ] |
| 10 | 로그인 실패 5회 반복 | 6번째부터 계정 잠금 메시지 | [ ] |
| 11 | 인증되지 않은 상태로 소켓 연결 | 연결 거부 | [ ] |
| 12 | 인증된 상태로 전체 채팅 송수신 | 정상 브로드캐스트 | [ ] |
| 13 | 응답 헤더 확인 (`curl -I`) | CSP/X-Frame-Options/HttpOnly 등 확인 | [ ] |

*(팁: 1~10, 13번은 `curl`로 재현 가능. 11~12번은 브라우저 개발자도구 콘솔에서 소켓 연결 로그를 캡처하거나, `python-socketio` 클라이언트 스크립트로 확인 가능.)*

---

## 6. 유지보수

*(작성 가이드: README의 "알려진 한계"를 본인이 이해한 이유와 함께 재작성)*

- 로컬 개발 서버(Werkzeug) 기반 실행 → 운영 시 gunicorn+eventlet/gevent + Nginx 필요, 이유: [ ]
- SQLite 단일 프로세스 기준 동시성 처리 → 운영 시 `SELECT ... FOR UPDATE` 필요, 이유: [ ]
- 인메모리 rate limit → 다중 프로세스 배포 시 Redis 필요, 이유: [ ]
- 향후 개선 방향(본인 생각): [ ]

---

## 7. 개발 과정에서 확인한 보안 약점과 수정 내역

*(이 표는 채점에서 가장 중요한 파트 중 하나입니다. 가능하면 각 항목에 실제 코드 스니펫(before/after)을 추가하세요.)*

| # | 기준 코드의 문제 | 위험성 | 본 프로젝트의 수정 |
|---|---|---|---|
| 1 | 비밀번호 평문 저장 | DB 유출 시 전 사용자 비밀번호 즉시 노출 | `bcrypt.hashpw`로 salt 포함 해시 저장 (`security.py`) |
| 2 | 모든 폼에 CSRF 토큰 없음 | 로그인된 사용자 대상 CSRF 공격 가능 | `Flask-WTF CSRFProtect` 전역 적용, 모든 폼에 `csrf_token()` 삽입 |
| 3 | 세션 쿠키 보안 옵션 없음, `SECRET_KEY` 하드코딩 | 세션 탈취, 시크릿 키 유출 시 세션 위조 | `HttpOnly`+`SameSite=Lax`(+운영시 `Secure`), `SECRET_KEY`는 환경변수 전용 |
| 4 | 로그인 실패 횟수 제한 없음 | 무차별 대입 공격에 취약 | 5회 실패 시 15분 잠금(`register_failed_login`), 동일한 오류 메시지로 계정 존재 여부 유추 방지 |
| 5 | 서버측 입력 검증 전무 | 취약한 데이터 저장, XSS 진입점 | 정규식 기반 검증(`security.py`, `forms.py`) |
| 6 | 상품 수정/삭제 자체가 없어 접근 제어 검증 대상 없음 | 기능 추가 시 IDOR 취약점 발생 가능 | `seller_id == current_user.id` 명시적 검증, 불일치 시 403 |
| 7 | 신고 중복/남용 방지 로직 없음 | 신고 수 인위적 부풀리기 가능 | `UNIQUE(reporter_id, target_type, target_id)` 제약 + rate limit |
| 8 | 신고 누적돼도 조치 없음 | 악성 상품/유저 방치 | 임계치(5회) 도달 시 자동 차단/정지 |
| 9 | 채팅 인증/검증/속도제한 없음 | 비로그인 스팸, 도배성 남용 | 미인증 연결 차단, 메시지 길이 제한(500자), rate limit(10초당 8건) |
| 10 | 디버그 모드 고정, 오류 시 스택 트레이스 노출 | 내부 경로 등 민감 정보 노출 | `ProdConfig`에서 `DEBUG=False`, 커스텀 에러 페이지 |
| 11 | 보안 헤더 전무 | 클릭재킹, MIME 스니핑 취약 | CSP/X-Frame-Options/X-Content-Type-Options/Referrer-Policy 적용 |
| 12 | (신규) 송금 설계 시 놓치기 쉬운 예외 처리 | 잔액 위변조, 정지 유저와 비정상 거래 | 자기 자신 금지·잔액 검증·정지 계정 금지·원자적 처리·거래 로그 설계 단계부터 포함 |
| 13 | (신규) 관리자 계정 하드코딩 위험 | 저장소 공개 시 자격증명 유출 | `seed_admin.py`에서 환경변수로만 생성, 소스에 자격증명 미포함 |

*(본인 검증 팁: 7장 각 항목에 대해 "실제로 취약한 버전으로 되돌리면 어떻게 뚫리는지" 한 줄 실험해보고 적으면 설득력이 올라갑니다. 예: CSRF 보호를 잠깐 꺼보고 실제로 타 사이트에서 강제 요청이 통하는지 확인.)*

---

## 8. 결론

*(작성 가이드: "기능이 동작하는 것"과 "안전하게 동작하는 것"의 차이를 본인이 이번 과제에서 어떻게 체감했는지, 가장 어려웠던 부분/가장 배운 점을 2~3문장으로)*

[ ]
