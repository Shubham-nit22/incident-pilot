from evals.evaluators import grounded

REF = {"intent": "info_request", "category": "database", "acceptable_actions": []}

# A made-up test excerpt, not real documentation text
EXCERPT = (
    "The pg_stat_statements module tracks planning and execution statistics of "
    "SQL statements. To use it, add pg_stat_statements to shared_preload_libraries "
    "in postgresql.conf and restart the server."
)

good_answer = (
    "pg_stat_statements tracks planning and execution statistics of SQL statements. "
    "To enable it, add it to shared_preload_libraries in postgresql.conf and restart [1]."
)
bad_answer = good_answer + (
    " It also automatically rewrites slow queries and is enabled by default on "
    "every installation."
)

for name, answer in [("good", good_answer), ("bad", bad_answer)]:
    result = grounded({"summary": answer, "retrieved_texts": [EXCERPT]}, REF)
    print(name, "->", result["score"], "|", result["comment"])