# Firebase Google authentication: backend foundation

Firebase verifies Google identity; FastAPI still issues the existing application
JWT with `sub=str(local_user.id)`. `/me`, protected routes, report ownership and
Chroma filters continue using that application JWT. No frontend changes are
included in this phase.

## Configuration

Install `requirements.txt` in an isolated Python environment. Existing
`DATABASE_URL`, `SECRET_KEY` and `GEMINI_API_KEY` remain required. See
`.env.example` for names and placeholders; never deploy example secrets.

For Google authentication, set:

- `FIREBASE_PROJECT_ID`: the exact expected Firebase project.
- `FIREBASE_SERVICE_ACCOUNT_PATH`: optional absolute path to Admin JSON
  **outside this repository**. If absent, use Application Default Credentials
  (ADC), through supported workload identity or a process environment variable
  `GOOGLE_APPLICATION_CREDENTIALS`. Pydantic reading an ADC name from `.env` does
  not export it to the Firebase SDK.

Never commit Admin JSON or log passwords/tokens. `.secrets/` and standard
`*-firebase-adminsdk-*.json` names are ignored defensively. Prefer supported
workload identity or a secret-mounted file in production; grant only the Auth
user-read permissions needed for revocation/disabled-account verification.

Admin initializes lazily, with one named app per backend process and a lock.
Missing/invalid configuration returns 503 for Google flows, while password auth
remains available. Verification pins the project and uses `check_revoked=True`.
Unsigned Firebase Auth emulator mode is rejected; tests mock verification.

In Firebase Console, enable Authentication's Google provider and its support
email. Before frontend integration, authorize the actual development/production
frontend hostnames; verify localhost explicitly. The hosting platform and
production domains are unverified, so none are assumed here.

## Existing-database migration

Alembic is new. Migrations never run during application startup. Retain a backup
and inspect the actual PostgreSQL schema before running, from `backend/`:

```sh
alembic current
alembic upgrade head
```

On an existing unversioned database, `0001_existing_schema` validates the four
legacy tables' columns, user primary key, email uniqueness and password
nullability before recording history. It creates/drops no business tables.
`0002_google_identity` then uses in-place PostgreSQL `ALTER TABLE` to:

- Add nullable `firebase_uid VARCHAR(128)` with `uq_users_firebase_uid`.
- Make `password_hash VARCHAR(255)` nullable, preserving existing hashes.
- Add `ck_users_has_authentication`: a password hash or Firebase UID is required.

PostgreSQL allows multiple NULL UIDs but enforces uniqueness for non-null UIDs.
No integer IDs, foreign keys, profiles, reports or chat records are rewritten.
No table-recreation fallback exists. Apply this migration before deploying the
updated model, since password endpoints also select the new column.

Do not blindly stamp unknown databases: stamping skips baseline validation.
The baseline does not provision empty databases. For an empty development
database only, existing `python -m app.db.init_db` creates the current schema;
inspect it, then stamp `head`. `create_all` cannot upgrade existing tables.

### Rollback

```sh
alembic downgrade 0001_existing_schema
```

Downgrade locks/checks users before changing schema. It refuses any Google-only
user without a password hash, without partial changes or deletion. Existing
Google links also require explicit acknowledgement before discarding mappings:

```sh
alembic -x allow_google_unlink=true downgrade 0001_existing_schema
```

That flag cannot bypass the Google-only guard. No passwords are invented and
no accounts are deleted. Offline downgrade is disallowed because data checks
cannot run. A code rollback retaining the expanded schema is usually safer;
the rollback release must retain the nullable-password login guard.

## API

### POST /auth/google/exchange

```json
{"id_token":"<Firebase ID token>"}
```

Only verified Firebase claims supply UID/email. Frontend `email` or `user_id`
fields are rejected. A Google provider token with verified email is required.
Invalid/expired/revoked tokens or disabled/deleted users return 401;
unverified/non-Google identities return 403; verification outages return 503.

An already-linked UID returns its original local user, without overwriting the
profile. A new UID/email creates a Google-only user with `password_hash=NULL`.
A matching password account returns 409 `google_link_required`, without a JWT
or automatic linking. Other/ambiguous collisions return `google_identity_conflict`.

### POST /auth/google/link

First authenticate through existing `/login`. Send its **application JWT** in
`Authorization: Bearer <application JWT>` and:

```json
{"id_token":"<Firebase ID token>","current_password":"<existing password>"}
```

Unchanged `get_current_user()` identifies the target. Password confirmation,
matching verified email and Google `auth_time` within five minutes are required.
Refreshing the token alone does not count as recent Google authentication.
Linking locks/reloads the account and never replaces a different UID or assigns
a UID owned by someone else. Same-account/same-UID retries are idempotent.
Google-only users cannot use password-based linking. IDs, hashes, reports and
chat records are preserved.

Both success responses retain the existing contract:

```json
{"access_token":"<application JWT>","token_type":"bearer","user":{"id":1,"name":"Example","email":"user@example.com"}}
```

New errors use `{"detail":{"code":"...","message":"..."}}`. Existing
password errors retain string `detail` responses. Future frontend work must
exchange/discard Firebase tokens, then store/restore only the application JWT.
Firebase revocation blocks future exchanges, not already-issued application
JWTs; their existing lifetime is unchanged. No session overhaul is included.

## Concurrency and email matching

UID/email uniqueness constraints arbitrate races; uniqueness failures roll back
and re-query. An email conflict never authorizes a link. Google/password creation
share a PostgreSQL transaction advisory lock keyed by case-insensitive email.
New signup rejects existing case variants rather than creating duplicates.
Stored emails and exact password-login lookup remain unchanged; Gmail aliases
and dots are not collapsed. Google exchange rejects ambiguous legacy variants.
Linking requires authentication to the intended local account.

## Tests

Install `requirements-dev.txt` plus the backend auth dependencies, then run:

```sh
python -m pytest -q
```

Without `TEST_POSTGRES_URL`, API/unit tests use isolated SQLite and PostgreSQL
migration/concurrency tests skip. For full verification, point that separate
variable at a **disposable PostgreSQL database**. Each test creates/removes its
own generated `firebase_test_*` schema. Tests override deployment settings and
never use application `DATABASE_URL` for destructive database work.

Firebase verification/credentials are mocked. Coverage includes token failures,
Google creation, password compatibility, linking, ownership preservation,
uniqueness/concurrent transactions, migration upgrade and guarded downgrade.
No migration against a live application database is part of these tests.
