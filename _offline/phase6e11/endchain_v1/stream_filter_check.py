"""PG17-only synthetic filter equivalence, run in disposable CI, never hosted."""
import os
from integral_stream import statement

def run(gate):
    if os.environ.get('GITHUB_REPOSITORY')!='Yourizorge/fitmetzorge-staging':
        raise ValueError('disposable_ci_only')
    candidate=statement([{'name':'synthetic.stream_probe','predicate':'allowed'}])
    candidate=candidate.replace('"synthetic"."stream_probe"','fixture')
    sql="""with fixture as materialized (
      select case when g%2=0 then null else 0 end quantity,
             case when g<=4 then true when g=5 then null else false end allowed
      from generate_series(1,73728) g
    ), legacy as (
      select '0'::text i,encode(sha256(convert_to(to_jsonb(t)::text,'UTF8')),'hex') h,
             case when allowed then '1' else '0' end keep from fixture t
    ), candidate as ("""+candidate+""")
    select (select count(*) from fixture) source_rows,
           (select count(*) from legacy) legacy_transport_rows,
           (select count(*) from candidate) filtered_transport_rows,
           (select count(distinct h) from candidate) distinct_hashes,
           (select count(*) from fixture where allowed and quantity is null) null_rows,
           not exists ((select i,h,keep from legacy where keep='1' except all select i,h,keep from candidate)
             union all (select i,h,keep from candidate except all select i,h,keep from legacy where keep='1')) multiset_equal"""
    rows=gate.rows(sql)
    expected={'source_rows':73728,'legacy_transport_rows':73728,'filtered_transport_rows':4,
              'distinct_hashes':2,'null_rows':2,'multiset_equal':True}
    if rows!=[expected]:raise ValueError('stream_filter_pg17_equivalence')
    gate.save('stream-filter-pg17.json',{'status':'PASS','checks':expected,'disposable_only':True,
        'hosted_rows_attribution':'UNKNOWN; no table counts reconstructed from incomplete receipt',
        'row_limit_unchanged':65536,'page_limit_unchanged':8192,'hosted_admitted':False})
    return 6
