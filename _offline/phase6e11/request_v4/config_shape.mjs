// Pure shape inspection. Only fixed condition names may leave this function.
export function inspectConfiguration(project, value, sessionHost) {
  const failures = [];
  if (project !== 'https://mokxyyullfhkfalopbzd.supabase.co') failures.push('project_binding');
  if (value === undefined || value === '') return [...failures, 'database_url_absent'];
  if (typeof value !== 'string') return [...failures, 'database_url_type'];
  let u;
  try { u = new URL(value); } catch { return [...failures, 'database_url_format']; }
  const direct = u.hostname === 'db.mokxyyullfhkfalopbzd.supabase.co';
  if (!['postgres:', 'postgresql:'].includes(u.protocol)) failures.push('database_protocol');
  if (!direct && u.hostname !== sessionHost) failures.push('database_host_allowlist');
  if ((u.port || '5432') !== '5432') failures.push('database_session_port');
  if (u.pathname !== '/postgres') failures.push('database_name');
  if (!u.password) failures.push('database_password_absent');
  try {
    if (decodeURIComponent(u.username) !== (direct ? 'postgres' : 'postgres.mokxyyullfhkfalopbzd')) {
      failures.push('database_role');
    }
  } catch { failures.push('database_role_encoding'); }
  try { decodeURIComponent(u.password); } catch { failures.push('database_password_encoding'); }
  if ([...u.searchParams.keys()].some(k => k !== 'sslmode')) failures.push('database_url_options');
  if (u.searchParams.getAll('sslmode').length > 1) failures.push('database_sslmode_duplicate');
  if (u.searchParams.has('sslmode') && u.searchParams.get('sslmode') !== 'verify-full') {
    failures.push('database_sslmode');
  }
  if (u.hash) failures.push('database_url_fragment');
  return failures;
}
