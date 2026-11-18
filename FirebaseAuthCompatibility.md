**Reconnaissance completed without changes.** I only inspected files and configuration names; I did not install dependencies, run the application, or execute database initialization. The repository was clean before and after inspection.

**Main finding:** the implemented application is **React/Vite + FastAPI with custom JWT authentication**. The least disruptive Firebase integration would add Google as an identity provider, verify its Firebase ID token in FastAPI, and then issue the application’s existing JWT.

Below, **verified** means supported by the inspected code. Recommendations describe proposed behavior; deployed services and live database contents were not inspected.

## 1. Project architecture overview

**Frontend — verified**

The implemented frontend is `medical-report-ai/bolt-frontend/`:

- React 18 and TypeScript.
- Vite 5 with the React plugin.
- Tailwind CSS 3, PostCSS, and Autoprefixer.
- Lucide icons, ESLint, and TypeScript checking.
- Native `fetch`; no Axios or React Router dependency.

See [bolt-frontend/package.json](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/package.json:6) and [vite.config.ts](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/vite.config.ts:6).

The entry sequence is `index.html` → `src/main.tsx` → `App`. `main.tsx` renders React under `StrictMode`; `App` wraps the application with `ToastProvider` and `AuthProvider`.

Sources: [index.html](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/index.html:13), [main.tsx](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/src/main.tsx:6), [App.tsx](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/src/App.tsx:49).

**Backend — verified**

The backend is a synchronous Python FastAPI application:

- Uvicorn serves `app.main:app`.
- SQLAlchemy handles database access.
- Pydantic handles request/response validation and settings.
- `python-jose` implements JWTs; Passlib/Bcrypt implements password hashing.
- PyMuPDF extracts PDF text.
- Google GenAI generates explanations and chat answers.
- LangChain and persistent Chroma support report retrieval.

Dependencies are listed in [backend/requirements.txt](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/requirements.txt:1). [app/main.py](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/main.py:7) creates FastAPI, adds CORS middleware, and registers five router modules.

The [README](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/README.md:7) identifies PostgreSQL on Neon. That is documented intent; the actual database connection and provider could not be verified without configuration.

**Important IDE-context finding**

These files are **zero-byte placeholders**, not an implemented Next.js application:

- [backend/app/dashboard/page.tsx](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/dashboard/page.tsx)
- [backend/app/reports/page.tsx](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/reports/page.tsx)
- [backend/package.json](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/package.json)
- The TypeScript files under `backend/services/` and `backend/types/`.

Consequently, the open `backend/app/dashboard/page.tsx` is not the implemented dashboard. The active implementation is `bolt-frontend/src/pages/DashboardPage.tsx`.

**Frontend/backend communication — verified**

All frontend API calls pass through `request<T>()` in [src/lib/api.ts](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/src/lib/api.ts:29):

- API origin is hardcoded to `http://localhost:8000`.
- Most requests use JSON; uploads use `FormData`.
- `authHeader()` attaches the saved JWT as `Authorization: Bearer …`.
- No cookie credentials option is supplied.

**Routing and major modules — verified**

Frontend navigation uses React state, rather than URL routing. `AppInner()` switches among `dashboard`, `upload`, `history`, and `trends`; `AppShell` supplies navigation controls. There are no distinct frontend `/login` or `/signup` routes.

Sources: [AppInner](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/src/App.tsx:12), [AppShell and Route](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/src/components/AppShell.tsx:14).

Backend endpoints have no `/api` prefix:

- Public: `GET /`, `POST /signup`, `POST /login`.
- Protected identity: `GET /me`.
- Protected reports: `POST /upload`, `GET /reports`, `GET /report/{report_id}`, `GET /history`.
- Protected dashboard: `GET /dashboard/{report_id}`.
- Protected trends: `GET /trends/{biomarker_name}`.
- Protected chat: `POST /chat`.

The frontend “History” page displays uploaded reports using `/reports`; the backend `/history` endpoint returns **chat history**.

Business processing is divided among `app/extraction/`, `app/services/explanation_service.py`, and `app/rag/`. `upload_report()` stores files locally, extracts/parses biomarkers, and indexes reports; `answer_question()` retrieves user-scoped context and stores chat history.

Sources: [report_routes.py](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/api/report_routes.py:34), [explanation_service.py](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/services/explanation_service.py:8), [rag/chat_service.py](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/rag/chat_service.py:70).

## 2. Authentication architecture and current login flow

**Sign-up — verified**

1. `AuthPage.onSubmit()` calls `useAuth().signup(name, email, password)`.
2. `AuthProvider.signup()` invokes `api.signup()`, which posts JSON to `/signup`.
3. Backend `signup()` checks for an existing email, hashes the password, creates a `User`, and commits it.
4. It returns `TokenResponse`: an access token, token type, and user object.
5. The frontend saves the token and sets its authenticated user state.

Duplicate registration returns HTTP 400 with `Email already registered`.

**Sign-in — verified**

The same UI calls `AuthProvider.login()` and `POST /login`. Backend `login()` looks up the email and checks its Bcrypt password hash. Invalid credentials return HTTP 401; successful login returns the same response shape as sign-up.

Sources: [AuthPage.onSubmit](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/src/pages/AuthPage.tsx:15), [AuthProvider.login/signup](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/src/context/AuthContext.tsx:41), [auth_routes.signup/login](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/api/auth_routes.py:13).

**Frontend authentication decision — verified**

`AppInner()` reads `user` and `loading` from `useAuth()`:

- Loading: render `FullPageSpinner`.
- No user: render `AuthPage`.
- User present: render the application shell and selected page.

This is a client-side rendering gate. API authorization is enforced separately by FastAPI.

**Login UI and Google button placement**

`AuthPage` contains both login and registration modes. Registration adds a full-name field; both modes have email and password inputs.

A Google button would naturally fit **between the introductory text and the email/password form**, around [AuthPage.tsx:90](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/src/pages/AuthPage.tsx:90), with a separator before the existing form. This is a recommendation, not existing functionality.

**Successful authentication does not perform a URL redirect.** Setting `user` causes `AppInner()` to show the authenticated UI. A fresh application starts on the dashboard; signing out and signing back in can preserve the previously selected route because `AppInner` does not reset it.

**Loading and error conventions — verified**

- `AuthPage.busy` disables its submit button and displays “Please wait…”.
- Errors use `useToast().showError()`.
- `ToastProvider` dismisses notifications after five seconds.
- API failures become `Error` objects using backend `detail` or a network-error message.
- Structured validation errors are stringified rather than formatted by field.
- `ChatPanel.send()` displays chat errors inside the conversation.

Sources: [AuthPage](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/src/pages/AuthPage.tsx:137), [ToastProvider](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/src/context/ToastContext.tsx:28), [request](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/src/lib/api.ts:44), [ChatPanel.send](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/src/components/ChatPanel.tsx:50).

## 3. Relevant files and their responsibilities

The complete implemented authentication surface is:

- [src/pages/AuthPage.tsx — `AuthPage`, `onSubmit`](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/src/pages/AuthPage.tsx:6): login/registration UI and submission feedback.
- [src/context/AuthContext.tsx — `AuthProvider`, `useAuth`](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/src/context/AuthContext.tsx:22): user state, startup restoration, login, signup, and logout.
- [src/lib/api.ts — `request`, token helpers, `api`](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/src/lib/api.ts:13): token storage, Bearer headers, and HTTP requests.
- [src/App.tsx — `AppInner`](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/src/App.tsx:12): authenticated UI gate.
- [src/components/AppShell.tsx — `SidebarContent`](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/src/components/AppShell.tsx:138): user identity display and sign-out button.
- [src/types.ts — `User`, `AuthResponse`](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/src/types.ts:1): frontend authentication contracts.
- [app/api/auth_routes.py — `signup`, `login`, `get_me`](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/api/auth_routes.py:13): backend authentication endpoints.
- [app/core/security.py — password/token helpers, `get_current_user`](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/core/security.py:7): password hashing, JWT verification, and authenticated database-user resolution.
- [app/schemas/auth_schema.py — request and response models](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/schemas/auth_schema.py:4): API authentication schemas.
- [app/models/user.py — `User`](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/models/user.py:8): persisted user schema.

There is no separate authentication middleware, OAuth callback handler, dedicated protected-route component, Firebase hook, or refresh-token handler in the inspected source. FastAPI route dependencies enforce authentication.

## 4. Existing user/session management

**Users — verified**

`User` maps to the `users` table with:

- Integer primary key `id`.
- `name`.
- Unique, indexed `email`.
- Non-null `password_hash`.
- `created_at`.
- A relationship to reports.

The model has no Firebase UID, provider identity, email-verification flag, account-status flag, or role field.

`Report.user_id` and `ChatHistory.user_id` reference `users.id`. Database sessions come from `get_db()`.

Sources: [User](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/models/user.py:8), [Report](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/models/report.py:9), [ChatHistory](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/models/chat_history.py:8), [get_db](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/db/session.py:19).

**Sessions — verified**

Authentication uses **stateless application JWTs**:

- Default signing algorithm: HS256.
- `sub`: the local integer user ID encoded as a string.
- `exp`: token expiry; default lifetime is 1,440 minutes.
- Browser persistence: `localStorage`, key `medinsight_token`.
- No authentication cookies, server-side session table, refresh token, or token-revocation mechanism.

`OAuth2PasswordBearer` extracts the Bearer token; its name does not mean Google OAuth is implemented.

Sources: [create_access_token and get_current_user](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/core/security.py:18), [Settings](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/core/config.py:4), [token helpers](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/bolt-frontend/src/lib/api.ts:13).

On startup, `AuthProvider` calls `/me` if a token exists. Any failure clears it, including a temporary network failure. Later API 401 responses do not automatically clear authentication state. Logout only removes the browser token and user state; a copied JWT remains usable until expiry.

**Authorization — verified**

`get_current_user()` verifies the JWT and loads its local `User`. Routes then enforce ownership:

- `list_reports()`, `get_report()`, `get_chat_history()` filter by user ID.
- `get_dashboard()` checks report ownership.
- `get_biomarker_trend()` filters through report ownership.
- `chat()` checks report ownership.
- Chroma `_where()` filters searches by the same integer user ID.

Sources: [report routes](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/api/report_routes.py:90), [get_dashboard](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/api/dashboard_routes.py:18), [get_biomarker_trend](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/api/trend_routes.py:17), [chat](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/api/chat_routes.py:20), [Chroma _where/search](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/rag/retriever.py:35).

## 5. Recommended Firebase integration architecture

**Recommendation, assuming existing email/password login should remain:** use Firebase for Google identity and retain the current application session.

Proposed flow:

1. `AuthPage` invokes Firebase Google Sign-In through the Firebase JavaScript SDK.
2. The frontend obtains a **Firebase ID token**.
3. A new FastAPI exchange endpoint receives that token.
4. Python Firebase Admin SDK verifies its signature, issuer, audience/project, expiry, and applicable account/provider requirements.
5. The backend resolves the verified Firebase UID to a local `User`.
6. It returns the existing `TokenResponse`, issuing an application JWT with `sub=str(user.id)`.
7. `AuthProvider` saves that response using its current token/user handling.

This preserves the existing `/me` contract and ownership checks.

**Identity mapping recommendation**

Add a unique nullable `firebase_uid` to `User`, or introduce an identity table if multiple identity systems are planned. Preserve all existing integer user IDs.

For Google-only accounts, make `password_hash` nullable and update `login()` to reject password login cleanly when no hash exists. Do not fabricate passwords.

An existing-email collision should enter an explicit account-linking flow requiring proof of the existing local account. Matching email alone is insufficient because current local registration does not verify email ownership.

**Persistence recommendation**

Use Firebase as the identity bootstrap, with the application JWT remaining authoritative for UI access. Prefer in-memory Firebase persistence initially; clear Firebase state on logout. Do not render protected UI merely because Firebase has a user—the backend exchange must succeed first.

**Alternative**

Firebase could replace the application JWT system. That would require Firebase-aware `get_current_user()`, asynchronously refreshed ID tokens in `request()`, rewritten session restoration, and a plan for existing password users. It is a broader migration, not a drop-in change.

## 6. Files likely to require modification

For the recommended exchange architecture:

- `bolt-frontend/package.json` and `package-lock.json`: Firebase SDK dependency.
- `src/pages/AuthPage.tsx`: Google button, busy state, and Firebase error messages.
- `src/context/AuthContext.tsx`: Google authentication action and logout coordination.
- `src/lib/api.ts`: exchange request and environment-based API origin.
- `src/vite-env.d.ts`: typed frontend environment variables.
- `backend/requirements.txt`: Firebase Admin SDK.
- `app/core/config.py`: backend Firebase configuration.
- `app/api/auth_routes.py`: exchange endpoint and passwordless-login guard.
- `app/schemas/auth_schema.py`: exchange request schema.
- `app/models/user.py`: UID mapping and passwordless-account support.
- `README.md` and relevant ignore rules: setup and credential-handling documentation.

Likely **new files**, only after implementation authorization: a frontend Firebase initialization module, backend Firebase verification service, and database migration.

`src/types.ts`, `App.tsx`, and business routes may need little or no change if `TokenResponse`, `User`, and integer ownership IDs remain intact.

There is no migration framework in the checkout. [init_db()](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/db/init_db.py:5) only calls `create_all()`, which does not migrate existing table columns.

## 7. Dependencies and configuration

**Existing Firebase status — verified**

- No Firebase dependency in the frontend manifest or lockfile.
- No `firebase-admin` in backend requirements.
- No Firebase initialization, configuration files, or authentication imports.
- The `.firebase/` entry in `backend/.gitignore` is only an ignore rule.
- Supabase SDK is recorded as a dependency, but no Supabase client or authentication usage was found.

**Dependencies likely needed**

- Frontend: `firebase`.
- Python backend: `firebase-admin`.
- Optional: Alembic for managed schema migration.

A Node `firebase-admin` package and React Firebase wrapper are unnecessary for this architecture.

**Existing environment conventions — verified**

[Settings](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/core/config.py:4) reads environment variables and a working-directory-relative `.env`.

- Required names: `DATABASE_URL`, `SECRET_KEY`, `GEMINI_API_KEY`.
- Names with code defaults: `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `CHAT_MODEL`, `EMBEDDING_MODEL`, `CHROMA_DIR`.
- No overrides for those names were present in the inspection shell.
- No `.env` files were found in the checkout.
- The frontend currently reads no `import.meta.env` configuration.

The README’s frontend environment-based API URL instruction is inconsistent with the hardcoded `BASE_URL`.

**Proposed configuration names, currently absent**

- Frontend: `VITE_API_BASE_URL`, `VITE_FIREBASE_API_KEY`, `VITE_FIREBASE_AUTH_DOMAIN`, `VITE_FIREBASE_PROJECT_ID`, `VITE_FIREBASE_APP_ID`.
- Backend: `FIREBASE_PROJECT_ID`; potentially `GOOGLE_APPLICATION_CREDENTIALS`, depending on the hosting credential mechanism.

Firebase web configuration belongs in the browser bundle. Admin credentials and the application signing secret must remain server-side.

**Deployment uncertainty**

Neon is documented for the database. `.bolt/config.json` identifies the frontend scaffold, not its deployment destination. No deployment manifests were found. Production domains, Firebase authorized domains, and hosted environment configuration remain unverified.

## 8. Potential breaking changes and security concerns

1. **Token incompatibility.** Current `decode_access_token()` accepts application HS256 JWTs; Firebase tokens use a different verification contract and UID subject. Replacing the saved token with a Firebase token would break protected APIs. See `security.py`.

2. **Ownership continuity.** Replacing integer IDs with Firebase UIDs would affect foreign keys and Chroma metadata. Preserve local IDs when linking accounts. See `Report`, `ChatHistory`, and retriever `_where()`.

3. **Account takeover through email linking.** Existing `signup()` accepts an email without ownership verification. Automatically attaching Google identities by email could expose an existing account’s medical data.

4. **Passwordless schema conflict.** `User.password_hash` is non-null, and `login()` assumes a hash exists. Both schema and login behavior must accommodate Google-only users.

5. **Independent session lifetimes.** Revoking Firebase credentials or disabling a Firebase account would not automatically invalidate an already-issued application JWT. Revocation policy must be explicit.

6. **Existing browser-token exposure.** `localStorage` tokens are accessible to injected JavaScript. Adding Firebase does not remove this existing XSS-related risk.

7. **Current session/error gaps.** Startup network failures log users out; later 401s leave the authenticated UI visible. Also, `get_current_user()` converts `sub` to an integer outside its JWT-error handler, so a validly signed malformed subject can produce an unhandled error.

8. **Production origin configuration.** [CORS configuration](C:/Users/LENOVO/OneDrive/Documents/projects/ccsaproj/medical-report-ai/backend/app/main.py:18) permits every origin with credentials enabled. Production should explicitly configure allowed frontend origins, HTTPS API access, and Firebase authorized domains.

9. **Existing authentication hardening.** `SignupRequest` has no password-strength constraint, while the UI only requires four characters. No email verification, password recovery, account linking, or application-level login throttling was found. See `auth_schema.py`, `AuthPage`, and `auth_routes.py`.

10. **Migration and concurrency.** Google user creation/linking needs database uniqueness constraints and transaction handling. The current duplicate-email precheck alone does not handle concurrent registration races.

## 9. Questions and uncertainties before implementation

1. Should Google Sign-In supplement existing email/password login, or should Firebase eventually manage all authentication?
2. Is a Firebase project already available, and is its Google provider enabled?
3. Where are the frontend and backend deployed, and what are their production domains?
4. Are there existing users and medical records that must be preserved?
5. Should matching-email accounts require existing-password confirmation before linking? That is my recommendation.
6. Is the current one-day JWT session acceptable, or are refresh, immediate revocation, and synchronized logout required?
7. Should Google-only accounts remain passwordless, or support adding a password later?
8. Should sign-in use a popup, redirect, or a mobile-specific fallback?

**No implementation has been performed. I’ll wait for your next instruction.**