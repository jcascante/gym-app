---
paths:
  - "frontend/src/**/*.ts"
  - "frontend/src/**/*.tsx"
---

# Frontend Conventions

## Components
- Functional components only, no class components
- Named exports only — never `export default` for components
- Co-locate CSS module with component: `Component.tsx` + `Component.css`
- Modal components use consistent class names: `modal-overlay`, `modal-content`

## TypeScript
- Strict mode is on — no implicit `any`
- Define types/interfaces in `src/types/` and import them
- Props interfaces defined inline or in same file as component

## API calls
- All API calls go through `apiFetch<T>()` in `services/api.ts`
- One service module per domain (`clients.ts`, `programs.ts`, `workouts.ts`, etc.)
- Catch `ApiError` (has `.status`) for HTTP-level error handling
- JWT is stored in `localStorage` and attached automatically by `apiFetch`

## Auth & routing
- Wrap protected routes with `ProtectedRoute` in `App.tsx`
- Auth state lives in `AuthContext` — use `useContext(AuthContext)` to read `user`, `isAuthenticated`
- Never read from `localStorage` directly for auth state — use the context

## State management
- No global state library — use React Context for shared state, `useState`/`useReducer` locally
- `AuthContext` is the only global context currently

## Styling
- CSS modules only — no inline styles, no global class names except in `index.css`
- Class names in `.css` files should be camelCase (e.g., `.modalContent`)

## Vite proxy
- `/api` proxies to backend — never hardcode `localhost:8000` in service calls
- All API paths start with `/api/v1/`

## i18n
- i18next is configured — use `useTranslation()` hook for any user-visible strings
