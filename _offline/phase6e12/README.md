# 6E-12 Parallel Offline Build
Owner GO during SU-487979. Independent offline work only. Historical 6E-11, migrations,
fixtures and dirty files must remain byte-identical. No hosted Supabase/Auth/JIT.
P1 manual reflection, P2 immutable registrations, P3 fresh review after source change
are implemented as proposals for owner review, not automatically accepted.
The Node contract accepts synthetic registrations and calls frozen 6E-6 read-only.
The public memory demo uses build-time evaluated, explicitly bounded examples.
Unknown browser edits get facts only, never guessed proposals. Browser role selection
is a simulation, never authentication. No storage, provider, real coaching or automatic action.

Run: node --test _offline/phase6e12/test/*.test.cjs
Build: node _offline/phase6e12/build.cjs
Preview: node _offline/phase6e12/serve.cjs
