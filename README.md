# secure_coding
## 중고거래 플랫폼 (Tiny Secondhand Shopping Platform)

WhiteHat School Secure Coding 과제용 프로젝트입니다. Flask 기반 단일 서버 앱으로 회원가입/로그인, 상품 등록·조회·검색, 전체/1:1 채팅, 신고 및 자동 제재, 유저 간 송금(상품 구매 포함), 관리자 기능을 제공합니다.


## 기술 스택

- Python 3.12, Flask 3
- Flask-SQLAlchemy (ORM, SQLite)
- Flask-Login (세션/인증)
- Flask-WTF (폼 검증 + CSRF 보호)
- Flask-SocketIO (실시간 채팅)
- Flask-Limiter (요청 속도 제한)
- bcrypt (비밀번호 해시)

## 환경 설정

```bash
git clone <이 저장소 URL>
cd secure_coding

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

cd server
pip install -r requirements.txt
```

### 환경변수 설정

`server/.env.example`을 복사해 `server/.env`를 만들고 값을 채웁니다.

```bash
cp .env.example .env
```

```
FLASK_ENV=development
SECRET_KEY=<openssl rand -hex 32 등으로 생성한 랜덤 값>
SESSION_COOKIE_SECURE=false      # HTTPS 운영 배포 시 true로 변경

ADMIN_USERNAME=admin
ADMIN_PASSWORD=<8자 이상, 영문+숫자 포함>
```

`SECRET_KEY`를 비워두면 프로세스를 재시작할 때마다 새 값이 생성되어 기존 로그인 세션이 모두 끊기므로, 로컬 개발이라도 값을 채워두는 것을 권장합니다.

### 관리자 계정 생성

관리자 계정은 소스코드에 하드코딩하지 않고, 환경변수로 시드 스크립트를 통해 생성합니다. (DB 테이블도 이 스크립트 실행 시 함께 생성됩니다.)

```bash
python scripts/seed_admin.py
```

## 실행 방법

```bash
python app.py
```

기본적으로 `http://127.0.0.1:5000` 에서 서버가 실행됩니다.

- 일반 사용자: `/register`에서 직접 가입 (가입 시 기본 잔액 1,000,000원 지급)
- 관리자: 위에서 생성한 `ADMIN_USERNAME` / `ADMIN_PASSWORD`로 로그인 후 우측 상단 "관리자" 메뉴

외부 기기(모바일 등)에서 테스트하려면 ngrok으로 터널링할 수 있습니다.

```bash
# optional
sudo snap install ngrok
ngrok http 5000
```

## 주요 기능

- **회원 관리**: 회원가입/로그인/로그아웃, 마이페이지(소개글·비밀번호·비밀번호 찾기 질문 변경), 공개 프로필 조회
- **비밀번호 찾기**: 가입 시 등록한 보안 질문/답변으로 본인 확인 후 비밀번호 재설정 (`/forgot-password`)
- **상품 관리**: 등록/수정/삭제(소유자만), 사진 업로드(선택, 2MB 이하), 목록 조회, 검색(제목/설명/가격대/판매상태), 상세 페이지
- **채팅**: 전체 채팅방(소켓 기반), 상품 판매자와의 1:1 채팅, 사이드바에서 대화 목록과 안읽음 표시 확인
- **신고/제재**: 유저·상품 신고, 임계치(5회) 초과 시 자동 차단/정지, 관리자 수동 검토
- **송금/구매**: 유저 간 송금, 상품 구매(자동 송금 + 상품 상태 변경), 거래 내역 조회
- **관리자**: 회원/상품/신고/거래 통합 관리, 계정 정지·해제, 상품 차단·삭제

## 보안 관련 주요 설계

자세한 내용은 [`docs/security_checklist.md`](docs/security_checklist.md) 참고. 요약:

- 비밀번호 bcrypt 해시 저장, 로그인 5회 실패 시 15분 계정 잠금
- 모든 폼에 CSRF 토큰 적용 (Flask-WTF)
- 세션 쿠키 HttpOnly/SameSite=Lax, HTTPS 환경에서는 Secure 플래그 활성화
- 전 구간 ORM 파라미터 바인딩으로 SQL Injection 방지, Jinja2 autoescape + 채팅 클라이언트 `textContent` 렌더링으로 XSS 방지
- 상품 수정/삭제 소유자 검증, 관리자 기능 역할 기반 접근 제어(403)
- 신고 중복 제출 방지(유니크 제약) 및 신고/로그인/회원가입/송금 등 주요 엔드포인트 rate limiting
- 보안 헤더(CSP, X-Frame-Options, X-Content-Type-Options 등) 전역 적용
- 관리자 계정은 환경변수 기반 시드 스크립트로만 생성(하드코딩 금지)
