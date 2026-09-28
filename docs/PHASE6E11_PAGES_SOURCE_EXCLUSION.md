# 6E-11 Pages source exclusion

28 September 2026. Supplemental publication finding; no change to M42 SQL or app code.

The post-push check at commit 0085d9aec9bad737ad5a4ca6adcaad230a026837
verified all 84 public runtime assets and 88 local candidate assets unchanged.
New _offline paths returned 404, but the newly committed migration SQL path
returned HTTP 200. The root Pages build had no _config.yml exclusion for supabase.
The SQL contains no secrets and was already authorized for the public Git repository;
this was unintended site distribution, not a secret or database-data disclosure.

The minimal Jekyll config excludes only supabase and _offline from the staging site.
It does not remove repository files, migration history, evidence or app assets.
All runtime bytes must still match the previous accepted public baseline after build.
The new path checker must verify every request_v4 source, the M42 SQL path and the
diagnostic workflow path as HTTP 404 after the corrective build.

The original failed check is retained as a publication finding. It is not reported
as PASS and does not change the hosted workflow NO-GO or owner-window closure.
Final build/hash/path results are saved in the ignored request-publication-final
receipts and reported with the definitive remote HEAD.
