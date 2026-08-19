# FitMetZorge Master Build Plan

Status: APPROVED PRODUCT SPECIFICATION CAPTURED
Last updated: 2026-08-15

This document is the product and execution source of truth for the FitMetZorge Master Build after Phase 0A Governance and Phase 0B Live Staging Infrastructure Verification.

## Hard Rules

- Build and verify in staging first.
- Staging GitHub: `Yourizorge/fitmetzorge-staging`.
- Staging Supabase project ref: `mokxyyullfhkfalopbzd`.
- Staging webapp: `https://yourizorge.github.io/fitmetzorge-staging/`.
- Production GitHub: `Yourizorge/fitmetzorge`.
- Production Supabase project ref: `hgoygcviutmynaihcvpd`.
- Production domain: `appfmz.nl`.
- Production is strictly forbidden without explicit owner approval.
- Do not remove working legacy functionality until replacement, migration, tests, and owner acceptance exist.
- Product functionality from this plan may not be silently removed or simplified. If implementation differs, document the technical reason and preserve the product outcome.
- Missing product choices must be marked `NEEDS DECISION`.

## Product Vision

FitMetZorge must become one complete fitness and lifestyle platform that combines training, nutrition, body weight, progress, recovery, sleep, steps, body measurements, health integrations, goals, gamification, AI coaching, and human Personal Training.

The product must serve:

- Independent Free users.
- Paying Pro users.
- Youri AI users.
- Personal Training clients.
- Trainers.
- Owner/admin of FitMetZorge.

The goal is not just to create a fitness logger. FitMetZorge must help users reach realistic goals and become more personal as relevant fitness history grows.

## Design And UX Principles

- Preserve the calm FitMetZorge visual basis and colors.
- The app must feel calm, premium, modern, fast, understandable, and not overwhelming. Member/client surfaces are mobile-first; Trainer Environment 3.0 follows the separate desktop-first strategy below.
- Daily actions must take as few steps as possible.
- Consumer navigation target: Vandaag, Training, Voeding, Progressie, Meer.
- Youri AI must be quickly reachable from important app areas.
- Premium functionality can be visible to Free users, but locked clearly.
- Locked feature clicks should show a calm, clear upgrade explanation.
- Upgrade messaging should be clear enough to convert without becoming aggressive or irritating.

## Responsive Product Strategy

FitMetZorge has two deliberate responsive priorities. These priorities apply to design, implementation, acceptance criteria, automated responsive coverage, and owner testing in every current and future phase.

### Member / Client Experience - Mobile First

The complete member/client experience is designed mobile first. The primary targets are iPhone and Android phones, the secondary target is iPad/tablet, and desktop/laptop remains supported, responsive, functional, and free of broken flows without becoming the primary design target.

A paying member must never need a laptop to use the core FitMetZorge product. All normal member functionality must ultimately be fully usable from a phone, including onboarding, Home/Vandaag, Recovery, Training, the workout builder, Exercise Picker, Active Workout Focus Mode, set entry, rest timer, workout history, PRs, Nutrition, Progress, Youri AI, subscriptions/account, and future member features.

Member UX implementation order:

1. Design and validate the real/mobile-class phone experience.
2. Adapt and validate the iPad/tablet experience.
3. Preserve responsive desktop/laptop compatibility and regression coverage.

Desktop enhancements must not compromise the phone experience for member workflows.

Persistent member navigation may never obscure member content, keyboard focus, or an interactive control. Every normal member page must reserve the measured navigation height, device bottom safe-area inset, and deliberate interaction spacing at the end of its scroll container. At maximum scroll, the final action must sit fully above the navigation with visible breathing room. Focused dialogs, bottom sheets, and task portals must render above the navigation and may temporarily hide that fixed layer when their existing open/close lifecycle reliably restores navigation, body scrolling, focus, and accessibility state.

### Member Experience - Overview First, Details On Demand

Normal member/client interfaces must show the most important overview and primary action first. Secondary detail should not be exposed automatically as one long vertical page when it is not immediately needed. Use progressive disclosure deliberately through compact summary cards, expandable sections, drill-down detail views, modals or bottom sheets, and focused task flows according to the content.

This is not an accordion-for-everything rule. Primary daily information may remain directly visible, summary or secondary information may use an accordion or expandable card, complex detail may deserve a dedicated view, and an active task may be better served by a focused flow. The goal is clarity and intentional access to depth, not uniform interaction patterns.

Every current and future normal member tab, including Recovery, Training, Nutrition, Progress, Youri AI member surfaces, and account/subscription, must answer before implementation:

1. What must the member see immediately?
2. What is secondary detail?
3. What can be collapsed?
4. What deserves its own detail screen?
5. What action should be primary?

Dashboard/Vandaag and Trackers follow separate final product purposes. Vandaag answers `Wat moet ik vandaag doen?` and contains one combined greeting/Vandaag hero, one Daily Check-in section, and one Training section. It does not duplicate standalone Steps, Water, Sleep, Wellbeing, Recovery-history, or Progress tracker cards. Trackers answers `Wat zijn mijn dagelijkse waarden en waar vul/bekijk ik die?` and remains the compact overview plus focused-detail data hub for those values. Both reuse the existing Phase 2/legacy data and save paths. The current Phase 3 schema has `day_label` and `day_order`, but no reviewed weekday/date mapping; Vandaag therefore shows a real active/paused session when present and otherwise uses a safe Training entry fallback without inventing scheduling semantics. Phase 3 Training and Member UX remain frozen. The Phase 4 architecture/readiness audit is complete; Phase 4 feature implementation has not started.

#### Future Today Analysis Placement

Future reviewed Youri AI/analysis functionality should integrate into Vandaag as the third major daily section beneath Daily Check-in and Training. The intended member-facing concept is `Jouw analyse`: an interpretation of authorized Recovery/check-in, Training, Activity, Nutrition, and Progress context according to the later backend-mediated AI, entitlement, privacy, consent, and cost-control architecture. No functional Analyse button, generated result, fake preview, browser AI call, or AI placeholder that appears operational may be added before that later phase is explicitly started and reviewed.

Trainer Environment 3.0 is explicitly exempt from blindly adopting the member composition. Its desktop-first, information-dense productivity model remains authoritative.

### Trainer Environment 3.0 - Desktop First

Trainer Environment 3.0 is designed desktop first. Laptop and desktop are the primary targets, iPad/tablet is secondary, and phone support focuses on useful responsive quick actions. Complex management workflows may intentionally use the larger desktop workspace.

The trainer environment must use desktop screen space effectively for client overview, client data, training plans, nutrition, progress, appointments/calendar, administration, finances, coaching workflows, analytics, and future trainer AI/support tooling. It must not be forced into a phone-first composition at the expense of trainer productivity.

### Responsive Testing Priority

Member feature testing priority:

1. Real phone or representative mobile-class viewport.
2. iPad/tablet.
3. Desktop/laptop regression and compatibility.

Trainer feature testing priority:

1. Desktop/laptop.
2. iPad/tablet.
3. Phone responsive quick-use compatibility.

Automated responsive checks should continue to cover phone, tablet, and desktop. Owner manual testing for normal member features should primarily happen on a real phone.

## Plans, Roles, And Entitlements

### Free

Free must provide daily value without making upgrade unnecessary.

Free onboarding includes at minimum name, age, height, weight, gender where relevant for calculations, fitness goal, and target weight where relevant. BMI is calculated automatically.

Free includes:

- Profile, age, height, weight, and BMI.
- Basic weight tracking and progress.
- Basic training.
- Maximum 4 active workout days/workouts, enforced as active `training_plan_days` under active `training_plans`.
- Workout start and logging.
- Manual input for relevant daily trackers.
- Limited nutrition preview.
- Basic goals.
- Basic streaks and achievements.
- Locked premium features visible in context.

Free excludes automatic Apple Health and Health Connect sync. Manual input must remain available where Health integration is not available or not connected.

### Pro

Target price: approximately EUR 9.99/month. Pricing must be technically configurable.

Pro includes Free plus:

- Extended training functionality.
- Unlimited relevant training capabilities.
- Extended nutrition logging.
- Full macros: kcal, protein, carbohydrates, fat.
- Full nutrition goals.
- Barcode functionality.
- Extended progress insights.
- Extended statistics and graphs.
- Apple Health integration on iOS.
- Health Connect on Android.
- Extended recovery functionality.
- Premium nutrition and training tools.

Pro does not automatically include full consumer Youri AI unless the user also has an AI entitlement through AI subscription, trial, referral reward, goal reward, or Personal Coaching.

### Youri AI Plan

Target price: approximately EUR 19.99/month. Pricing must be technically configurable.

The AI coach is named `YOURI`.

Youri AI must:

- Be recognizable through a small avatar/popup.
- Eventually use an avatar based on owner Youri Zorge.
- Not invent a face or final avatar in the absence of an approved asset.
- Mark the definitive avatar asset as `ASSET REQUIRED`.
- Avoid becoming a generic chatbot.
- Use relevant FitMetZorge data to personalize coaching.

Relevant Youri context can include goals, weight, weight trend, training, performance, progress, nutrition, macros, sleep, steps, recovery, wellbeing, body measurements, available Health data, and previous relevant coaching decisions.

### Personal Coaching / PT Clients

A real PT client uses the same consumer app, not a weaker separate client app.

While the coaching relationship is active, a Personal Coaching client receives:

- Full Pro functionality.
- Youri AI functionality.
- Linked human coach access.

No double payment for Pro/AI should be required on top of active Personal Coaching unless explicitly decided later.

Strategic coaching decisions remain under human trainer control. Youri may help the client with exercise explanation, previous performance, nutrition status, app data, and practical questions. Youri must not automatically override the trainer on calorie changes, major training plan changes, or new coaching phases.

## Onboarding And Goal Engine

Onboarding must be quick, clear, and professional.

The user provides current situation, goal, target weight where relevant, training experience, training possibilities, preferences, available days, nutrition preferences, and practical constraints.

For AI users, the app must not simply ask how much weight the user wants to lose per week. The user provides the end goal. Youri then analyzes what is realistic and discusses:

- Realistic pace.
- Estimated timeline.
- Calorie/nutrition direction.
- Training direction.
- Intermediate goals.
- Possible phasing.

Youri must be able to challenge unrealistic or unwise goals and help the user arrive at a realistic and achievable plan.

## Trial, Growth, And Rewards

### AI Trial

New users can receive a 7-day free Youri AI trial.

The product must clearly communicate:

- 7 days free.
- No payment details needed.
- No credit card required upfront.

After expiry:

- Trial stops automatically.
- User falls back to their valid package or Free.
- Data is preserved.
- Youri AI is locked.
- Upgrade option is clear.

Trial abuse must be technically prevented.

### Bring A Friend

Users can earn AI bonus days through Bring a Friend.

Required behavior:

- Existing user shares FitMetZorge.
- Friend creates a real account or downloads/activates the app according to valid referral criteria.
- Reward is validated server-side.
- Both parties can receive AI bonus according to final reward configuration.
- Maximum 2 valid referral rewards per month per user.

Prevent self-referral, duplicate abuse, repeated use of the same new user, and client-side manipulation.

### Qualified Goal Rewards

Not every small self-chosen goal may grant free AI.

When a predefined serious main goal is achieved, the reward is 1 month Youri AI for the next goal. Maximum: 2 Goal Rewards per 12 months. Paid users must not lose bonus days; bonuses should extend or stack according to final entitlement logic.

## Consumer App Functional Domains

### Home / Vandaag

Vandaag is the user's daily hub. It should surface the most relevant current actions, such as today's training, nutrition status, recovery signals, goal progress, reminders, active trial/subscription status, and Youri AI entry points when entitled.

### Training Engine

Training is a core domain. The user must consciously start a workout.

Active workout UX must be designed for quick gym use on mobile. Reps, weight, and similar numbers should use mobile picker/scrollwheel interactions where technically and ergonomically feasible.

Training must support:

- Training plans.
- Workout templates.
- Workout start.
- Pause/resume where needed.
- Sets, reps, weight.
- RIR/RPE support where relevant.
- Rest timer.
- Notes where relevant.
- Workout completion.
- Workout history.
- Personal records.
- Progress per exercise.
- Progressive overload support.
- Previous performance shown clearly.
- Local recovery/offline-safe behavior where technically responsible.

Exercise discovery has one user-facing source of truth: the contextual Exercise Picker opened from `Workout builder -> Oefening toevoegen`. It reads the canonical `public.exercises` catalog, currently 898 verified records and designed for later expansion toward circa 1,500 useful exercises. The former visible circa 72-item Exercise Library is removed. Its minimum curated core may remain internal only for offline/error safety, legacy workout rendering, legacy name resolution, migration compatibility, and static regression checks; it must never be merged into or shown as a competing catalog. Any future standalone exercise browser must use the same canonical catalog as the picker.

Each canonical exercise can include unique exercise id, canonical English name, future reviewed localized content, primary muscle group, secondary muscles, equipment, instruction, animation/visual, and metadata.

Avoid copyright-problematic assets. Training schemas must not be publicly shared between users. Achievement cards may be shareable, but personal training plans are not.

#### FitMetZorge Exercise Engine

Phase 3 establishes the FitMetZorge Exercise Engine direction:

- Central canonical exercise catalog.
- Target scale: circa 1,500 useful fitness/strength exercises, not artificial duplicates.
- Stable canonical exercise IDs and language-independent slugs.
- Consumer-friendly muscle taxonomy: borst, rug, schouders, biceps, triceps, quadriceps, hamstrings, billen/glutes, kuiten, core/buik, onderarmen, trapezius, adductoren, abductoren, full body, lower back, hip flexors where supported.
- Equipment taxonomy: machine, cable, dumbbell, barbell, Smith Machine, bodyweight, EZ-Bar, kettlebell, resistance band, TRX/suspension, landmine, plate, other.
- Final exercise language policy: Dutch intentionally shows canonical English exercise names with Dutch instructions, taxonomy, picker copy, errors, and placeholders; English shows English names/instructions/UI; German shows reviewed German names/instructions/UI with canonical English alias search and explicit English fallback only while German editorial content is incomplete.
- `canonical_name`, `name_en`, canonical slug, and canonical exercise ID remain language-independent. The schema does not duplicate a `name_nl`; Dutch resolves the display name from `name_en`. German translation changes never create a new exercise or split history, PRs, previous performance, or animation identity.
- Exercise picker with search, muscle filters, equipment filters, paginated/batched results, mobile bottom-sheet UX, and desktop modal UX.
- Active Workout Focus Mode presents one exercise and one set at a time, with pause-aware duration, prominent rest countdown, optional final-three-second haptics, session-only exercise skipping, progress context, previous performance, and a dominant gold set-save action.
- Workout history is directly openable as a read-only detail; PR presentation groups human-readable max-weight, max-reps, and estimated-1RM values under one exercise identity.
- Canonical exercise identity is used for workout history, previous performance, PR foundation, progressive overload, and later Youri AI context.
- Workout/set history keeps useful snapshots such as exercise name, equipment, muscle, and source at the time of logging so history remains understandable when catalog metadata improves later.
- Legacy exercise/animation references are mapped to canonical exercises and preserved until rights review and replacement are complete.

The first real catalog source is Kinetic `exercises-json` pinned at commit `8652d87338b43a1b7f6e11604dd8167dd8aa5a97`: 899 MIT-declared structured English exercise records, normalized conservatively to 898 after one exact semantic duplicate removal, with no artificial target padding. The structured-data artifact and root MIT notice are hash-pinned; no media fields are imported. The catalog schema, deterministic 898-row staging import, read-only verification, frontend integration, and picker portal hotfix have been completed on staging. Reviewed Dutch instructions and reviewed German names/instructions remain editorial production-readiness gates; Dutch exercise-name translation is intentionally not required. wger remains a reference candidate only with its Creative Commons and per-entry attribution/licence requirements reviewed. ExerciseDB/proprietary GIF/media datasets must not be copied blindly. No paid API, API key, or copyrighted media bulk download may be introduced without explicit owner approval.

#### Youri Avatar Exercise Animation System

Every canonical exercise must eventually be able to receive a branded FitMetZorge/Youri-avatar animation without changing the exercise identity.

The Youri-avatar animation system direction:

- Youri-avatar remains visually consistent and FitMetZorge-branded.
- The avatar demonstrates the exercise clearly.
- Avatar media replaces legacy/placeholder media over time.
- Exercise IDs, slugs, history, PRs, and progressive overload references never change when media changes.
- Runtime workout execution must not generate AI animations. Animations are pre-generated/approved assets for predictable quality, performance, cost, and mobile reliability.

Rollout stages:

- Stage A: legacy animations and branded placeholders.
- Stage B: most-used exercises receive Youri-avatar animations first.
- Stage C: further catalog batches.
- Stage D: as many relevant catalog exercises as possible receive approved Youri-avatar animation.

Phase 3 prepares the architecture for this rollout; it does not produce 1,500 AI animations.

#### Active Workout Animation

During an active workout, the current exercise must show an animation or preview slot. The preview must remain visible while logging sets, change when the current exercise changes, avoid reloading media per set, work smoothly on mobile, and fall back to a branded placeholder when no animation exists. Later this slot should default to the Youri-avatar exercise loop where available.

### Nutrition Engine

Nutrition must be fast and easy.

Paid nutrition supports all core macros:

- kcal.
- Protein.
- Carbohydrates.
- Fat.

Nutrition must support nutrition goals, day totals, meal moments, products, search, barcode, recent products, favorites, custom products, saved meals, recipes, copy day/meal, multiple nutrition options, nutrition plans, and AI support when entitlement is valid.

Free gets a useful but limited nutrition preview. Invoices do not belong in the consumer nutrition environment.

### Progressie

Progress must support:

- Weight.
- BMI.
- Weight trend.
- Week averages.
- Target weight.
- Percentage toward goal.
- Body measurements.
- Progress photos.
- Strength progress.
- PRs.
- Milestones.
- Achievements.

Measurements should include the most logical body measurements without becoming cluttered. Neck is not required by default. Calf measurement is not a required core default.

Progress photos must be private, never public by default, stored in private storage, accessed through signed URLs or equivalent secure access, never automatically shared, and analyzed by AI only with valid consent.

### Recovery / Health

Recovery must provide useful insight without claiming pseudoscientific precision.

Support sleep, steps, wellbeing, recovery feeling, relevant training load, and optional Health data.

Health integrations:

- iOS: Apple Health.
- Android: Health Connect.
- Free: no automatic Health sync.
- Pro/AI: Health sync available.

Manual input must remain available when users do not connect Health integrations. Apply data minimization and request only categories that are actually needed.

### Gamification

Avoid childish XP mechanics that exist only to fake engagement.

Use relevant achievements, streaks, milestones, PR achievements, workout milestones, and goal progress milestones at 25%, 50%, 75%, and 100%.

Streaks must be able to respect planned vacation, planned rest/pause, and realistic training schedules.

### Notifications

Notifications must be useful and not spammy.

Future notification categories include workout reminders, nutrition reminders, goal milestones, streaks, achievements, coach messages, AI check-ins, important recovery insights, and trial/subscription information.

Users need notification preferences. Push infrastructure for iOS/Android comes later; PWA/web should be used where appropriate. Frequency caps are required.

### Languages

The new architecture must support at least Dutch, English, and German. German is a standard language for the first version.

Use translation keys for navigation, buttons, errors, onboarding, training, nutrition, progress, subscriptions, emails where relevant, notifications, exercise names/instructions, and AI response language.

Exercise-language policy is intentionally asymmetric: NL uses English canonical exercise names plus Dutch instructions/UI/taxonomy; EN uses English names/instructions/UI/taxonomy; DE uses reviewed German names/instructions/UI/taxonomy and supports English canonical-name aliases in search where practical. English fallback in German staging data must remain explicitly marked as fallback and cannot count as reviewed German coverage. German exercise editorial completion is required before final production readiness.

Avoid hardcoded mixed-language UI. Country/region and units should be configurable later.

### Account And Privacy

Under Meer -> Account & Privacy, include personal data, email, password/security, language, country/region, units, Health connections, AI settings, privacy/consents, data export, and account deletion.

## Privacy / AVG Requirements

- V1 is 18+.
- Use privacy by design for personal, fitness, health, nutrition, photo, AI, and trainer/client data.
- Use separate consents where meaningful for Health integrations, progress photos, AI photo analysis, AI data use, and trainer/client linking.
- Trainer access to client data requires a valid coach-client relationship and consent path.
- Trainer A must never access Trainer B data.
- AI may use only data for which the current user/trainer has valid access and consent.
- Users must be able to export relevant data and delete their account where legally and technically applicable.
- Privacy information must be available at least in NL, EN, and DE.
- Legal/AVG review is required before production launch, including legal bases, privacy policy, processors, retention periods, AI provider, possible DPIA, data breach process, and international transfer review.
## Trainer Environment 3.0

The current trainer functionality must be migrated carefully and preserved.

Trainer Environment 3.0 follows the permanent desktop-first responsive strategy: desktop/laptop primary, iPad/tablet secondary, and phone support for useful quick actions without weakening desktop management productivity.

Target trainer environment includes dashboard, clients, client dossier, training, nutrition, progress, recovery, agenda, appointments, notes, administration, invoices, finances, and settings.

Client dossier target tabs: Overview | Training | Nutrition | Progress | Recovery | Agenda | Notes | AI.

Working current functionality must not disappear before replacement is built, tested, migration-tested, and accepted.

## Private Trainer Copilot

The trainer receives a private AI Copilot that is only visible in the trainer environment.

The PT client must not see the internal Copilot, AI Coach Inbox, internal AI analyses, internal concepts, or trainer-to-Copilot conversations.

Copilot supports client analysis, trends, stagnation, training analysis, nutrition analysis, new training concepts, new nutrition concepts, check-in preparation, draft messages, comparing multiple clients, and identifying clients who need attention.

Required workflow:

1. Client data is analyzed.
2. Copilot produces analysis and concept.
3. Trainer reviews.
4. Trainer adjusts where needed.
5. Trainer approves.
6. Client-facing change is executed.

No strategic Copilot change may go directly to a client automatically. Owner/trainer Copilot usage should be generous within reasonable cost-control rules.

## AI Coach Inbox

Trainer dashboard gets an AI Coach Inbox for signals such as weight stagnation, declining adherence, missed training, recovery trend, progress, and overload suggestions.

Priorities: normal, aandacht, belangrijk.

The inbox must avoid alert fatigue and must back signals with data.

## Owner / App Management

Owner/admin gets a separate authorized app management dashboard.

Minimum visibility:

- Total registered users.
- Active users.
- Free, Pro, Youri AI, trials, Personal Coaching.
- Upgrades, downgrades, cancellations, new users.
- DAU, WAU, MAU, DAU/MAU where useful.
- Subscription counts per package.
- Trial starts and trial-to-paid conversion.
- Referral-to-signup and referral-to-paid.
- Paid conversion and churn.
- MRR, ARR, ARPU, ARPPU, LTV when data is reliable enough.
- AI requests, usage, token/API costs, AI cost per AI subscriber, cost per active user where calculable.
- Storage/infrastructure indicators where useful.

## Retention, Churn, And Business AI

Retention is a core KPI. Support D1, D7, D30, later D90, cohort retention, Free retention, Pro retention, and AI retention.

Important funnels:

- Registration -> onboarding -> first goal -> first workout -> second workout -> first week -> D7 -> D30 -> trial -> paid -> month 2 -> month 3.

Cancellation can ask why, but answering must never block cancellation. Example reasons: too expensive, not enough use, goal reached, AI not helpful enough, nutrition, training, technical issues, another app, other.

Business Insights AI can later analyze aggregated product data. It must separate observation, correlation, hypothesis, and recommendation. It must not present unsupported causal claims as fact. Early churn-risk language should use observable signals such as decreased engagement, not unvalidated probability claims.

## A/B Test Foundation

A full experimentation system is not required for the first commercial version, but the architecture should allow later controlled experiments for onboarding, paywall, and trial copy.

Measure exposure, conversion, retention, and relevant KPI. No dark patterns.

## Target Supabase Architecture

The future architecture must not permanently depend on one giant `coach_workspaces.state` JSONB data model. The current JSONB state remains temporary legacy until migration is safely complete.

Conceptual normalized domains:

- IDENTITY: `profiles`, `user_settings`, `subscriptions`, `entitlements`.
- COACHING: `coach_client_relationships`, `coach_notes`, trainer/copilot data.
- TRAINING: `exercises`, `exercise_translations`, `training_plans`, `workouts`, `workout_exercises`, `workout_logs`, `workout_set_logs`, `personal_records`.
- NUTRITION: `nutrition_targets`, `food_logs`, `food_log_items`, `foods`, `recipes`, `saved_meals`.
- PROGRESS: `weight_logs`, `body_measurements`, `progress_photos`, `goals`, `goal_milestones`, `achievements`.
- RECOVERY: `recovery_logs`, `health_sync_connections`, health samples where needed.
- AI: `ai_threads`, `ai_messages`, `ai_recommendations`, `ai_action_proposals`, `ai_action_decisions`.
- GROWTH: `referrals`, `referral_rewards`, `goal_rewards`, `bonus_entitlements`.
- NOTIFICATIONS: `notifications`, `notification_preferences`, `push_tokens`.
- ANALYTICS: privacy-aware event and aggregate architecture.

Names are directional. Better table normalization may be proposed later, but functional domains must remain covered.

## Security, RLS, And Authorization

- RLS is primary database security.
- Never rely on hidden UI buttons for security.
- Sensitive actions require server-side authorization.
- Service-role keys never go to frontend.
- AI keys never go to frontend.
- Payment secrets never go to frontend.
- Trainer sees only linked clients.
- Client sees only own/allowed data.
- Owner/admin access is explicit through role/claims and safe backend rules.
- Use least privilege.
- Audit important actions.
- Do not log unnecessary personal, fitness, or health data.

## AI Backend

Never call an AI provider directly from the browser.

Required flow:

1. App calls secure backend/Edge Function.
2. Backend authenticates user.
3. Backend checks authorization.
4. Backend checks entitlement.
5. Backend retrieves relevant context.
6. Backend calls AI provider.
7. Backend validates structured response.
8. Backend stores proposal/action only where allowed.

AI cannot have unlimited direct database write access. Strategic actions require proposal -> approval -> execution. AI usage and cost logging are mandatory. No AI call without valid entitlement. Rate limiting and cost control are required.

## Entitlement Engine

The entitlement engine is the single source of truth for plan and feature access decisions.

Free/Pro/AI access must be enforced server-side, not only through UI state.

Entitlements cover barcode, Health sync, AI Coach, workout capability limits, premium analytics, bonus AI, and Personal Coaching included access.

A minimal entitlement foundation must exist before phases that consume entitlement state. Phase 1 establishes the smallest safe entitlement contract/read model needed for later gates. Phase 7 expands this into subscriptions, trials, referrals, goal rewards, bonus days, payment-provider webhooks, and package lifecycle logic.

Trials, referrals, goal rewards, and Personal Coaching access must become real temporary entitlements/credits, not frontend hacks.

## Payments

Payment provider is `NEEDS DECISION`.

Architecture must safely support Free, Pro, AI, monthly, yearly where offered, upgrades, downgrades, cancellation, failed payment, grace period where appropriate, trial, bonus days, refunds where relevant.

Payment provider/webhooks are source of truth for paid subscriptions. Never trust client-side `premium=true`. Payment work starts in staging test mode first.

## Storage

Phase 0B verified that staging currently has no Storage buckets.

Target storage:

- Progress photos in private bucket.
- Sensitive uploads private.
- Signed URL or equivalent secure access.
- Exercise media in separate read-only/public or CDN-like asset architecture where appropriate.
- No sensitive files public.

## Production Scale Target

Production scale target: FitMetZorge should be architected for at least circa 1,000 registered/active users as the first serious scale goal.

This is an architecture target, not a claim that 1,000 concurrent or active users have already been proven. Before broad production launch, relevant journeys must be tested under realistic expected load.

Production-readiness requirements for this target:

- Database indexes for catalog filters, workout history, user sessions, set logs, exercise references, entitlements, and RLS query paths.
- Efficient queries with no avoidable N+1 patterns and no unbounded per-user history reads.
- RLS policies that remain efficient and keep user/trainer/client isolation as the primary security boundary.
- Exercise picker pagination/batching/virtualization where needed.
- Media lazy-loading, thumbnails, caching headers, and a storage/CDN strategy for exercise animations.
- API and Supabase request efficiency, avoiding polling and unnecessary repeated hydration.
- Rate limiting and abuse controls where backend or Edge Function endpoints are introduced.
- Graceful failure behavior for network loss, partial save, retry, and offline-safe active workouts.
- Frontend error monitoring, failed DB request monitoring, auth failure monitoring, performance metrics, slow query monitoring, Edge Function/API errors, and storage/media errors before production.
- Supabase backup strategy, restore procedure, migration rollback/forward-fix strategy, and recovery process for accidental data corruption.
- Security review for cross-user access, cross-trainer access, premium bypass, media access, secret exposure, and IDOR-like paths.
- Load/performance tests before broad production launch for concurrent logins, exercise catalog browsing, workout start, set logging, workout completion, history reads, recovery reads/writes, and trainer/client flows where relevant.

## Staging, Production, And Release Process

Staging is permanent and separate from production.

All new development follows:

1. Build in staging.
2. Test in staging.
3. Review.
4. Owner approval.
5. Only then consider production.

Staging and production require separate Supabase projects, configs, secrets, and deployment. Do not copy production data to staging without safe anonymization/sanitization.

## Current Staging Functionality To Preserve

Phase 0 established current staging functionality that must be preserved until replacements are accepted:

- Trainer dashboard.
- Member/client management.
- Client invite.
- Goals.
- Training builder.
- Exercise library.
- Nutrition.
- Recipe/macro functionality.
- Trackers.
- Agenda.
- Appointment types.
- Administration.
- Invoices.
- Rates.
- Finances.
- Settings.
- Client dashboard.
- Client training.
- Client nutrition.
- Client trackers.
- Client agenda.
- Supabase Auth.
- Session persistence.
- Password reset.
- Cloud workspace sync.
- Invitation flow.

## Legacy Migration

Current legacy anchors:

- `profiles`.
- `coach_workspaces`.
- `coach_workspaces.state` JSONB.

Relationships to preserve:

- Auth user <-> `profiles.id`.
- Trainer <-> `profiles.trainer_id`.
- Client <-> `profiles.client_id`.
- Trainer workspace <-> `coach_workspaces.trainer_id`.
- Legacy client id <-> `state.clients[].id`.

Migration must be designed and rehearsed in staging first. No destructive production migration without backup, rehearsal, validation, rollback plan, and explicit owner approval.

## Web, PWA, iOS, And Android

First build full new functionality as web/PWA in staging.

PWA requirements:

- Excellent mobile UX.
- Responsive.
- Fast.
- Installable where possible.
- Handles poor connection well.
- Protects active workouts from data loss.

Do not immediately create three separate codebases. Reuse as much code as possible. Native integrations may be needed later for Apple Health, Health Connect, push, barcode/camera, photos, biometrics where later relevant, and native store requirements.

Release path after mature PWA:

1. iOS TestFlight staging build.
2. Android internal/closed staging build.
3. Mobile QA on staging backend.
4. Later production store builds only after approval.

## Test Strategy

Built does not mean ready. Ready means built, automatically tested, functionally tested, security checked, and reviewed.

Minimum test coverage areas:

- Auth: signup, confirm, login, logout, reset, invite, invite acceptance.
- Training: plan, workout start, set log, picker, timer, history, PR, offline/reconnect.
- Nutrition: manual entry, macros, search, barcode, meals, recipes, AI features.
- Progress: weight, BMI, measurements, photos, milestones.
- Entitlements: Free, Pro, AI, trial, referral, goal reward, Personal Coaching.
- Security: RLS, cross-user isolation, cross-trainer isolation, premium bypass, IDOR-like access, server-side role checks, secret exposure.
- AI: correct context, missing data handling, no hallucinated facts, proposal flow, trainer priority, cost/rate rules.
- Languages: NL, EN, DE.

Bug classes:

- P0: data loss, security leak, production touched, payment error, app unusable.
- P1: important feature broken, wrong entitlement, important AI error, trainer/client flow broken.
- P2: polish, spacing, small translation, visual detail.

No release with open P0. No release with release-blocking P1.

## Build Phases And Gates

Each phase requires documentation update, implementation notes, acceptance criteria, tests, owner-visible test flow, security impact review, rollback/restoration notes for any changed state, known issues, and a stop-for-review exit gate before moving to the next major phase.

### Phase 0 - Governance And Infrastructure Verification

Status: COMPLETE.

Includes baseline audit, Phase 0A governance, and Phase 0B live staging infrastructure verification.

Gate: completed and approved before this Master Plan Specification.

### Phase 1 - Accounts And Onboarding

Status: COMPLETE.

Scope: account/profile foundation, onboarding, language/account settings foundation, goal engine basis, legacy-safe profile linking, and the minimal entitlement foundation needed for later Free/Pro/AI/PT gates.

Explicitly out of scope for Phase 1: payment-provider integration, AI provider calls, native Health sync, training/nutrition/progress rebuilds, Storage bucket creation, and production work.

Acceptance gate:

- Existing trainer/client login, reset, invite, and invite acceptance flows still work in staging.
- Existing trainer/client profile and workspace relationships remain intact.
- New consumer onboarding captures required Free fields.
- BMI is calculated.
- Goal engine stores realistic goal inputs without allowing unsafe pace selection.
- Minimal entitlement source-of-truth contract exists for Free/Pro/AI/PT access decisions without implementing payments or subscriptions yet.
- NL/EN/DE translation structure exists for the new surfaces.
- Rollback/restoration notes exist for any changed auth/profile/onboarding state.
- No production touched.
- Tests and owner test flow documented.

Gate result: PASS. Owner final verification passed for Phase 1 tests 1-12, live Supabase schema/RLS/RPC metadata, Free entitlement foundation, NL/EN/DE primary client/Lid i18n, password reset, invite/relink flows, standalone Free/Lid safety, and performance retest on phone and laptop. Ready for Phase 2: YES, after explicit owner instruction only.

### Phase 2 - Home + Recovery

Status: COMPLETE.

Scope: Vandaag hub, manual recovery inputs, sleep/steps/wellbeing/recovery feeling, training-load placeholders, Health-sync placeholders without native sync yet unless explicitly approved.

Gate: Free manual recovery works, Pro/AI Health-sync entitlement points consume the Phase 1 entitlement foundation and remain controlled, rollback/safety notes exist, tests/review complete.

Gate result: PASS. Owner final verification passed for Phase 2 tests 1-12: Vandaag/Home hub, recovery persistence, Free Health entitlement gate, training-load placeholder, Trackers/Vandaag bidirectional compatibility, recovery date isolation, NL/EN/DE Phase 2 surfaces, existing linked client compatibility, logout and performance, recovery input validation, and final regression. Live staging database verification passed for `public.recovery_logs`, RLS, policies, constraints, indexes, FK, updated-at trigger, and grants hardening. `authenticated` has exactly `INSERT`, `SELECT`, and `UPDATE`; `anon` and `PUBLIC` have no privileges. No trainer SELECT policy was added; trainer normalized recovery read-access is intentionally deferred. Ready for Phase 3: YES, after explicit owner instruction only.

### Phase 3 - Training Engine

Status: FUNCTIONALLY COMPLETE / FROZEN. The live staging Training Engine, verified 898-row canonical catalog, Exercise Picker, builder/edit/reorder/save, UUID persistence, Free max-4 active workout-day enforcement, accordion, archive/restore, Active Workout Focus Mode, compact set entry, duration, rest timer, vibration, previous performance, clickable History, grouped PR UX, and instruction disclosure/state have passed final owner real-phone acceptance. No new Training functionality is authorized during the pre-Phase 4 Member UX Consistency work.

Scope: normalized training model design, canonical exercise catalog and single contextual picker, workout templates/plans, mobile-first collapsible Training sections, saved-workout editing for future sessions, non-destructive plan/exercise archiving, discoverable archived workouts with server-authoritative restore, one-exercise-at-a-time Focus Mode, pause-aware duration, set logging, rest timer and optional haptics, clickable history, grouped PR foundation, previous performance, progressive overload, offline-safe behavior, Free max-4 active workout-day enforcement, and legacy training bridge preservation. Editing or archiving a reusable plan must never rewrite completed workout sessions, set logs, snapshots, or canonical exercise identity.

Responsive priority: Phase 3 member Training is mobile-first. Exercise Picker, workout builder, Active Workout Focus Mode, set entry, rest timer, vibration, previous performance, workout history, and PR display must be designed and owner-tested on a real/mobile-class phone first, then tablet, with desktop maintained as a fully functional compatibility target.

Gate: legacy training still available until accepted replacement exists, core workout can be completed in staging, Free limits consume the Phase 1 entitlement foundation, rollback/safety notes exist, tests/review complete.

Catalog execution order was completed on staging in the approved sequence: final local schema/seed review -> owner/external approval -> catalog schema migration -> read-only schema/RLS/grants verification -> reviewed 898-row import -> read-only count/UUID/slug/taxonomy/provenance verification -> reviewed frontend UUID/catalog integration -> live cache verification. Future catalog or content changes require the same review-first discipline. No completed staging step implies production approval.

Functional gate result: PASS. Reviewed Dutch exercise instructions, reviewed German exercise localization, and Youri-avatar exercise animations remain separate content/media gates. They do not reopen the frozen Phase 3 functional scope. Dashboard/Vandaag, Trackers, and onboarding hydration are accepted as the frozen Member UX baseline. The Phase 4 Nutrition architecture/readiness audit may proceed without reopening Phase 3.

### Phase 4 - Nutrition Engine

Scope: nutrition targets, day totals, meal moments, foods, custom foods, saved meals, recipes, macros, copy meal/day, barcode foundation behind flag.

Gate: Free preview and Pro nutrition behavior consume the Phase 1 entitlement foundation, macro totals are correct, invoices remain outside consumer nutrition, rollback/safety notes exist, tests/review complete.

Phase status: IN PROGRESS. Architecture/readiness status: COMPLETE. Owner product contract: LOCKED. Schema Slice 1: COMPLETE / LIVE / VERIFIED ON STAGING. Functional Slice 2 is owner-tested and frozen. The atomic `fmz_phase4_replace_food_log_item` contract is live and verified. Functional Slice 3 daily logging, macro progress, and the global member bottom-navigation safe-area contract are owner-tested, complete, and frozen. Slice 4A provider/local-first contract is LOCKED. Slice 4B alias/search is LIVE / COMPLETE on staging. Slice 4C operational state is LIVE / READ-ONLY VERIFIED on staging. The USDA `nutrition-provider` search/lookup runtime is deployed and controlled authenticated smoke verification passed on staging. Slice 4D transient provider-snapshot logging has passed final semantic review and is synchronized to GitHub, but its migration is not executed and its Edge/frontend extensions are not deployed. No canonical provider import, member frontend integration, Open Food Facts, or production action has occurred.

Phase 4 must preserve legacy `coach_workspaces.state` Nutrition until a reviewed cutover exists. New normalized member data starts own-user only; no broad trainer access, AI execution, service-role frontend, invoices, destructive legacy cleanup, or unreviewed food import belongs in the initial slice.

Locked tier contract:

- Free: calorie/protein/carbohydrate/fat targets, canonical search, unlimited normal daily logging, totals, maximum 10 active private custom foods, and seven-day history.
- Pro: full self-service Nutrition, full retained history, favorites, recents, saved meals, own recipes, meal/day copy, and later feature-flagged barcode.
- AI: all Pro Nutrition; Youri execution remains Phase 6.
- PT: full member Nutrition and future trainer-guided targets/plans/adherence under separate reviewed trainer authorization; no broad trainer policy in the initial slice.

Food identity is provider-neutral. Open Food Facts and USDA are preferred future roles; NEVO is excluded until legal/license approval. Initial logging is search -> select -> amount/portion -> log -> totals. Initial targets use one explicit daily target and never infer weekends as rest days. Actual logs, targets, and plans remain separate. Historical log snapshots are immutable. Custom foods, saved meals, and recipes are private.

Schema Slice 1 contains only Nutrition preferences/timezone, foods, food portions, targets, day logs, log items, and their minimum security/RPC foundation. It contains no food rows/import, provider API, saved meals, recipes, favorites, copy, plan assignment, barcode, calculator implementation, trainer RLS, AI, frontend, or legacy backfill.

Schema Slice 1 execution gate: PASS. The reviewed migration and corrected read-only JSON checker both completed successfully on staging `mokxyyullfhkfalopbzd`. Functional Slices 2 and 3 are owner-tested and frozen; the separately reviewed atomic replacement RPC is live and verified. Slice 4A locks a local-first hybrid direction: reviewed USDA generic data, Open Food Facts Dutch/EU branded and future barcode data only after legal approval, and private custom foods for gaps. Slice 4B is live and limited to `food_aliases`, reviewed prefix/trigram indexes and read-only catalog access; the frozen search RPC remains unchanged. Slice 4C's private HMAC-keyed caches, atomic USDA rate buckets and circuit state are live and verified. The USDA Edge search/lookup runtime is deployed and smoke-verified on staging without canonical mutation.

Slice 4D logging contract: an authenticated member may log a revalidated USDA candidate as an immutable transient provider snapshot without a canonical `foods` row. The browser supplies a signed candidate token plus normal log inputs only; all nutrition and provenance authority is derived in the Edge Function. Initial provider consumption is grams-only against an explicit 100 g basis. The log row keeps `food_id = NULL`, never promotes into `foods`, `food_portions`, or `food_aliases`, and remains intelligible without future cache availability. Stable item/request UUIDs, exact-payload replay comparison, transaction advisory locks, Free seven-day history, current Pro/AI/PT full history, and atomic replacement are database-enforced. Browser archive-plus-readd editing and USDA serving portions are not allowed. The existing archive RPC is reused. Provider log/replace RPCs are service-role-only; member frontend integration remains a later explicit gate.

Permanent provider identity rule: `PHASE4_PROVIDER_CANDIDATE_UUID_NAMESPACE = 23440733-7e58-4c21-ad15-591eae6ab8ac`, generated and locked on 2026-08-19. UUIDv5 names use exact format `provider_code:provider_food_id`, initially `usda_fdc:<fdcId>`. The namespace is non-secret, never regenerated, and identical in staging and future production. The separate Phase 3 exercise namespace remains frozen and is not reused.

### Phase 5 - Progressie

Scope: weight/BMI/trends/week averages, target percentage, body measurements, progress photos, PR and milestone surfaces, private storage design/implementation when approved.

Gate: photos are private, no unwanted sharing, AI photo analysis is consent-gated, private storage/RLS rollback notes exist if storage is introduced, tests/review complete.

### Phase 6 - Youri AI Core

Scope: AI backend, entitlement checks, context retrieval, structured responses, Youri UI entry points, avatar support placeholder, AI logs/cost controls, proposal pattern.

Gate: no browser-to-AI calls, no AI call without entitlement from the single entitlement source, no secrets exposed, missing data handled without hallucinated facts, rollback/safety notes exist, tests/review complete.

### Phase 7 - Subscriptions + Entitlements + Growth

Scope: expand the Phase 1 entitlement foundation into subscriptions, trials, referral rewards, goal rewards, bonus entitlements, package configuration, and payment-provider integration only after provider decision.

Gate: server-side entitlements remain the single source of truth, 7-day trial ends automatically, referral abuse prevention exists, payment work is staging test mode only, rollback/safety notes exist, tests/review complete.

### Phase 8 - Gamification + Notifications

Scope: achievements, streaks, milestones, goal reward triggers, notification preferences, frequency caps, PWA/web notification foundation where appropriate.

Gate: gamification is meaningful, streaks respect rest/vacation logic, no spam behavior, notification rollback/safety notes exist, tests/review complete.

### Phase 9 - Traineromgeving 3.0

Scope: migrate/preserve trainer dashboard, clients, dossier tabs, training, nutrition, progress, recovery, agenda, notes, admin, invoices, finance, settings.

Gate: current trainer functionality is preserved or replaced with accepted equivalent, cross-trainer isolation holds, rollback/safety notes exist for any migrated trainer/client data, tests/review complete.

### Phase 10 - Private Trainer Copilot

Scope: internal-only trainer Copilot, AI Coach Inbox, proposal/review/approval workflows, owner/trainer generous usage under cost control.

Gate: client cannot see internal Copilot artifacts, strategic changes require trainer approval, AI signals are data-backed, rollback/safety notes exist for any AI proposals/actions, tests/review complete.

### Phase 11 - Owner Analytics + Retention + Business Insights

Scope: owner/admin dashboard, user/package metrics, engagement metrics, subscription metrics, retention/churn funnels, AI/storage/infra costs, Business Insights AI foundation.

Gate: owner access is explicit, metrics are privacy-aware, AI separates observation/correlation/hypothesis/recommendation, analytics rollback/safety notes exist, tests/review complete.

### Phase 12 - Final PWA Polish

Scope: responsive polish, performance, installability, offline behavior, navigation polish, language QA, accessibility and release hardening.

Gate: full PWA staging QA ready, no open P0, no release-blocking P1, rollback/restoration notes are complete for changed state, tests/review complete.

### Phase Dependency Rules

- Phase 1 creates the account, onboarding, goal, legacy-linking, language, and minimal entitlement foundations used by later phases.
- Phases 2-6 may consume the Phase 1 entitlement foundation but must not depend on payment-provider integration, subscription webhooks, referral rewards, or goal rewards.
- Phase 6 may implement AI entitlement checks against the entitlement foundation, but full subscription/growth lifecycle logic belongs to Phase 7.
- Phase 7 expands entitlements and growth after the core consumer domains and AI access gates exist.
- Phase 9 trainer work must preserve existing trainer/client flows before Phase 10 Copilot depends on trainer data.
- Phase 10 Copilot depends on Phase 6 AI backend and Phase 9 trainer data boundaries.
- Phase 11 owner analytics depends on privacy-aware events from earlier phases and must not expose raw cross-user data without authorization.
- Native iOS/Android builds must not start before PWA maturity and staging QA.

### Phase Safety And Rollback Rule

Every Phase 1-12 implementation report must include a rollback or restoration note. If no persistent state changed, the report must explicitly say so. If database/storage/Auth/payment/AI state changed, the phase cannot exit until restoration, rollback, or forward-fix safety is documented and tested where practical.
### Post Phase 12 Release Path

1. Full staging QA.
2. Controlled beta, starting around 20 real testers and later 20-50 if appropriate.
3. iOS TestFlight staging.
4. Android internal/closed staging.
5. Mobile QA.
6. Production Readiness Review.
7. Explicit owner approval.
8. Production migration/release only after approval.

## Reporting After Each Feature Or Phase

Every implementation phase report must include:

- What was built, in normal Dutch.
- Where to find it in staging.
- How it works.
- What the owner can test.
- Technical explanation.
- Tests run and results.
- What is not built yet.
- Files changed.
- Migrations.
- Security impact.
- Known issues.
- Production touched: expected answer is NO during Master Build.

## Commits And Change Management

Use small logical commits. Avoid one giant mega update.

Database migrations are append-only after applied. Do not silently rewrite old applied migrations.

Example commit scopes: create normalized training schema, add training RLS, add workout session persistence, add workout picker, add entitlement checks, add tests.

## Feature Flags

Use feature flags for large or unfinished capabilities where useful:

- `ai_coach_enabled`.
- `nutrition_barcode_enabled`.
- `owner_analytics_enabled`.

Goal: unfinished areas must not be accidentally exposed broadly.

## AI Cost Control

Hard requirement: no valid AI entitlement means no paid AI call.

Log where useful:

- User.
- Plan.
- AI feature.
- Request count.
- Token/use estimate.
- Cost.
- Date.
- Rate-limit status.

Protect against bugs or abuse that could cause unexpected AI costs. Free users without active AI entitlement/trial/reward should have EUR 0 paid AI consumption.

## Beta And Product Validation

Before the first major commercial launch, run controlled beta.

Guideline: about 20 real testers first, then optionally 20-50.

Measure onboarding completion, first workout, second workout, D7, D30, trial usage, conversion, bugs, performance, feature use, AI quality, and cancellation feedback.

## Production Release

Codex may never independently release production.

Production Readiness Report must include PASS/FAIL for functionality, security, migrations, RLS, payments, NL/EN/DE, PWA, iOS, Android, migration rehearsal, backup ready, and rollback ready.

Production release requires explicit owner approval.

## NEEDS DECISION / ASSET REQUIRED

- Payment provider and exact integration approach.
- Final public pricing and yearly/monthly package rules.
- Definitive Youri avatar asset: `ASSET REQUIRED`.
- Native app framework/reuse strategy after PWA maturity.
- Barcode provider/data source.
- Phase 4 normalized trainer-client authorization and relationship-end behavior before the trainer Nutrition slice.
- Nutrition calculator formula, deterministic safety bounds, caution/escalation, and disclaimer before calculator implementation.
- Phase 4 day-copy replacement undo/recovery mechanism before day-copy implementation.
- Nutrition external-data launch catalog, licensing, attribution, and provider operations before import/API integration.
- Nutrition retention, export, deletion, and legal/AVG review before production launch.
- AI provider/model policy and cost budget limits.
- Exact Apple Health and Health Connect implementation path.
- Legal/AVG review outcome before production.
- Exact referral reward and goal reward stacking behavior.
- Beta cohort selection and operational process.
- Production launch timing and approval checklist owner signoff.

