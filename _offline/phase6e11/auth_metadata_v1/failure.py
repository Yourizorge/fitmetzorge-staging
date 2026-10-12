"""Only known protocol codes and SQLSTATE; never serialize arbitrary exceptions."""
import re
KNOWN={'terminal_row_count','multiple_statements_not_allowed','missing_terminal','query_timeout','query_transport','query_send','single_row_mode','stream_order',
       'explain_send','explain_timeout','explain_transport','explain_row_shape','explain_null','explain_plan_budget','explain_terminal','explain_incomplete',
       'unregistered_readonly_query','probe_latency','probe_own_temp_io','probe_write_multiset','probe_transaction','probe_scope'}
def safe_reason(error):
    code=str(error)
    return code if code in KNOWN or re.fullmatch(r'(?:explain_)?sqlstate_[0-9A-Z]{5}',code) else 'scoped_action_failed'
