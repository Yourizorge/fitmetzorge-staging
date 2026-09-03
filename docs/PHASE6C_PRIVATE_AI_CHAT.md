# Package 6C Private AI Chat

Status: NATURAL-LANGUAGE SAFETY HOTFIX TECHNICAL PASS / READY FOR FINAL OWNER RETEST / NOT FROZEN

Date: 2026-09-03

Environment: Supabase staging `mokxyyullfhkfalopbzd` and `Yourizorge/fitmetzorge-staging` only. Production was not touched.

## Scope

Package 6C provides the mobile-first FitMetZorge AI Coach private-chat foundation in NL, EN and DE. The personal coach is displayed as `Youri AI`; the subscription/product identity remains `FitMetZorge AI Coach`. The deployed route uses a deterministic staging mock only. It does not invoke OpenAI, does not expose a provider or model selector, and cannot execute or propose application changes.

## Data And Ownership

The implementation reuses `public.ai_threads`, `public.ai_messages`, `public.ai_data_lifecycle_requests`, `ai_private.runs`, the Phase 6A consent and entitlement helpers, rate/budget/safety state, and the frozen completion/failure service RPCs. Added fields provide stable client request identity, thread revision, message sequence and run-to-source-message correlation. The only new table is `ai_private.phase6c_runtime_config`, which fixes mock mode on and external-provider mode off.

Browser roles have no direct table writes. Member RPCs derive the user from `auth.uid()`, bind threads/messages to that user, enforce current status and use fixed safe search paths. There is no trainer policy or trainer RPC. Message content is immutable; only the guarded transition to a scrubbed deleted state is permitted. Retained `hard_stop` and `review_required` metadata blocks future automatic execution but no longer functions as a chat ban; communication access remains governed by current entitlement, consent, age and mock-runtime gates.

## Member RPCs

- `fmz_phase6c_get_chat_status`
- `fmz_phase6c_create_thread`
- `fmz_phase6c_list_threads`
- `fmz_phase6c_read_thread`
- `fmz_phase6c_submit_message`
- `fmz_phase6c_export_chat`
- `fmz_phase6c_delete_thread`

`fmz_phase6c_service_begin_mock_run` is service-role only. Existing Phase 6A service completion/failure RPCs persist the strict assistant response or sanitized failure state.

## Consent, Entitlement And Retention

Chat creation and message processing require age 18+, active versioned `ai_processing` consent, and a current active `ai` or `personal_coaching` entitlement. Free, Pro-only, missing, future, inactive and expired entitlements are denied. Consent withdrawal blocks new processing immediately while preserving own history/export/delete access.

Entitlement loss starts a server-authoritative read/export/delete-only grace period of at most 90 days. Reactivation before the deadline restores active state. A minute `pg_cron` sweep scrubs message content no later than the deadline. Deletion is own-user, revision-protected and idempotent; only non-content lifecycle audit metadata remains.

## Edge And Frontend

The `youri-ai/phase6c/chat` route requires a valid member JWT and an exact bounded payload containing request, attempt and thread identities, expected revision, locale and content. It first stores or replays the user message, reserves an idempotent zero-cost mock run, validates strict localized mock output and completes the run. The server-authoritative deterministic classifier normalizes case, accents, punctuation, whitespace and common NL/EN/DE phrasing. Explicit serious signals and bounded exertion-plus-dizziness combinations return the localized professional-help hard stop; diagnosis, medication and treatment requests receive a safe refusal. Actions are always empty.

The hard-stop copy tells the member to stop exercising, states that no diagnosis is made, requests prompt professional medical assessment and directs severe, persistent or immediately dangerous symptoms to emergency help/112. A hard stop suppresses normal coaching output and has no plan, proposal or executable action.

The focused chat UX uses a compact `Youri AI` header, `FitMetZorge AI Coach` subtitle, the owner-supplied and owner-approved `Youri-AI-avatar-3D-v3.png`, staging-test status, mobile history switcher, readable user/assistant bubbles, empty-state prompts, processing and retry states, and a secondary export/delete menu. The approved avatar appears in the header and beside Youri AI messages; stable circular CSS crops preserve the full face and hairstyle, while a neutral `AI` fallback appears only when the local image cannot load. The composer is one horizontal bottom row at every supported width: a rounded one-to-four-line textarea on the left and a fixed circular send action on the right. Safety output is visually distinct without moving classification authority into the browser. Previously hydrated content may remain visible offline, but new content is never silently queued or represented as processed. Mobile layouts cover 320x700 and 390x844, with tablet and desktop compatibility.

## Approved Youri AI Avatar

- Owner approval: YES; official Package 6C source identity: `Youri-AI-avatar-3D-v3.png`.
- Metadata-free lossless master: `assets/youri-ai-avatar-3d-v3-master.png`; 1254x1254; 1,864,738 bytes; SHA-256 `53EDC8C376F097417ABDE7B74F4C9D85CEBAD4E2A676AE65620A4CBD65DA2E57`.
- Lossless runtime asset: `assets/youri-ai-avatar-3d-v3-256.webp`; 256x256; 53,188 bytes; SHA-256 `257F31E6FE4FAA7FECF5FB9874EED06D4018DC8C60958AA714E7D4B79A7517DC`.
- The master is pixel-identical to the supplied PNG after metadata-free re-encoding. The runtime asset is a downscaled, lossless avatar derivative; the face was not generated, reshaped or retouched.
- No personal reference photographs are stored in the repository. Only the approved final avatar master and runtime derivative are committed.

## Owner Safety Hotfix

The owner sentence `Ik heb pijn op de borst en ben erg duizelig tijdens het sporten.` previously missed the hard-stop route because the serious-pattern list recognized the compound `borstpijn` but not the natural phrase `pijn op de borst`, and did not combine exercise context with dizziness. A later owner test exposed two remaining bounded-language gaps: `pijn in de borst` was not accepted alongside `pijn op de borst`, and the noun `duizeligheid` was not accepted alongside `duizelig`. The browser payload and presentation were correct.

Edge v41 closes those server-only gaps with explicit NL/EN/DE concepts for chest pain, pressure and tightness; dizziness and fainting; breathlessness; and exertion context. It recognizes first-person natural variants after deterministic case, accent, punctuation and whitespace normalization. A bounded negation check keeps statements such as `geen borstpijn` and `niet duizelig` clear, while educational questions without current personal symptoms and normal chest-training or post-training muscle-soreness language remain outside the hard stop. Prompt-injection wording cannot suppress classification. Every hard stop retains the existing exercise-stop, no-diagnosis, prompt-assessment and urgent-help copy and always returns zero actions.

## Continued Chat Correction

The follow-up defect was caused by `ai_private.phase6c_chat_status`: its communication gate reused the persisted member safety state and denied every later thread, message and mock-run request after a `hard_stop`. Deleting the conversation correctly scrubbed content but did not erase safety metadata, so deletion could not restore access. Migration `20260903145000_phase6c_request_scoped_safety.sql` replaces only that private gate function. A hard stop remains persisted and `automatic_execution_blocked=true`, while `communication_allowed` and `chat_write_allowed` stay true when the independent entitlement, consent, age and mock-runtime gates pass.

The corrected live sequence is proven with an isolated synthetic member: exact risk message -> hard stop -> normal safe follow-up -> new conversation -> repeated risk hard stop -> safety-override refusal -> delete risk thread -> new conversation. No action proposal was created, operational metadata contained no raw fixture message, all four mock runs cost zero, and every synthetic row was removed afterward. Consent withdrawal and entitlement loss still deny new processing; cross-member and trainer isolation remain intact.

## Evidence

- Migration: `supabase/migrations/20260902203000_phase6c_private_ai_chat.sql`
- Migration SHA-256: `131E63FF165069A4D2861EADEC838AD47906CF74A382C0F7CE8AB99F91D8D26F`
- Live migration history: `20260903085454` / `phase6c_private_ai_chat`
- Request-scoped safety migration: `supabase/migrations/20260903145000_phase6c_request_scoped_safety.sql`; SHA-256 `35EF14F978AD6500ABD086B5DB80DBEC2D875A2A8DDEB39825E8B0AC2B57A831`
- Request-scoped safety migration history: `20260903125150` / `phase6c_request_scoped_safety`
- Request-scoped read-only verifier: `supabase/verification/20260903145000_phase6c_request_scoped_safety_verification.sql`; SHA-256 `F45C64E09EB37447BE97629229824C1BF5A72CCF7063B93D36472B59853DA1D6`; result 16 PASS / 0 FAIL
- Request-scoped transactional E2E: `supabase/tests/20260903145000_phase6c_request_scoped_safety_e2e.sql`; SHA-256 `F2046E2403EC1CEA5ED680DC67F75CF00432DD91604BB0F28B38C9CE34A0BAAF`; result PASS with rollback and 0 fixtures
- Read-only verifier: `supabase/verification/20260902203000_phase6c_private_ai_chat_verification.sql`
- Verifier SHA-256: `CA1A5D407E8631A36B4C8629EFF5A529EF0010B8D408760CEF54E2339114552D`
- Verifier result: 37 PASS / 0 FAIL
- Transactional E2E: `supabase/tests/20260902203000_phase6c_private_ai_chat_transactional_e2e.sql`
- E2E SHA-256: `A3372F6DC48ECD97549F1BA8C7D499FA1981EF653A1565AC3A06C1A450DDBD22`
- E2E result: PASS with rollback; fixtures remaining 0
- Edge: `youri-ai` v41 ACTIVE; JWT verification enabled; bundle SHA-256 `b4c61d47baa620cf7af62842dec3b660fdd40da30cc58c5da221147ab86a3fc2`
- Continued-chat implementation/runtime commit: `8dfa235`
- Approved-avatar runtime commit: `abc724fec6115ce85c810fb2f53ff2e5e6a01740`
- Natural-language safety implementation commit: `bb5076a`
- Frontend cache: `20260903-phase6c-approved-avatar1`
- Frontend runtime set: `index.html`, `app.js`, `assets/phase6c-private-ai-chat.js`, `assets/youri-ai-avatar-3d-v3-256.webp` and `assets/youri-ai-avatar-3d-v3-master.png`
- Live natural-language Edge proof: 12/12 PASS at HTTP 200. All three final owner sentences, chest pain alone, EN/DE variants, repeated risk and prompt injection returned `hard_stop`; normal chest training, negated symptoms, an educational question and a normal follow-up remained `clear`. Every response had zero actions and zero external calls/cost.
- Live proof used one isolated synthetic staging account. The account and every related fixture category were removed; eighteen post-cleanup counts were zero. The owner account and its chat data were not used or changed.
- Live assembled runtime: 320x700 and 390x844 chat UI render without console errors, truncation or horizontal overflow
- Package 6C handler: 17/17 PASS
- Package 6C static: 117/117 PASS
- Package 6C browser/responsive: 85/85 PASS
- Combined Phase 6 Edge tests: 53/53 PASS
- Frozen regressions: Phase 1 75/75; Phase 2 46/46; Phase 3 222/222; Member UX 56/56; Phase 4 schema 90/90 and Nutrition browser 138/138; Phase 5 116/116 and 53/53; Phase 6A 93/93; Phase 6B 98/98
- Security and performance advisors: zero current notices; no hotfix regression

## Safety Boundary

External AI calls during Package 6C: 0. External AI cost: EUR 0.00. Real-member OpenAI processing enabled: NO. Trainers can read private chat: NO. The natural-language hotfix changed no schema, RLS, ACL, frontend or member row; only isolated synthetic setup/cleanup rows existed during the live proof. Test fixtures remaining: 0. The earlier request-scoped gate migration remains frozen. The owner's retained hard-stop metadata and chat content were not changed; read-only status proves communication allowed with automatic execution blocked. The exact owner-test AI entitlement remains active once through `2026-09-10T23:59:59Z`. Production touched: NO. Package 6D started: NO. Owner real-phone retest is still required before acceptance or freeze.
