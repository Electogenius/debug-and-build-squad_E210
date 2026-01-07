import psycopg

conn_info = {
    "host": "localhost",
    "port": 5432,
    "dbname": "thirdeye",
    "user": "admin",
    "password": "admin"
}

query = "SELECT author, execution, impact, visibility, total, percentile, silent_architect FROM scores ORDER BY percentile DESC;"

with psycopg.connect(**conn_info) as conn:
    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
        # print header
        print(f"{'author':20} {'execution':10} {'impact':10} {'visibility':10} {'total':10} {'pct':7} {'silent'}")
        for r in rows:
            author, execution, impact, visibility, total, percentile, silent = r
            print(f"{author:20} {execution:10.3f} {impact:10.3f} {visibility:10.3f} {total:10.3f} {percentile:6.2f}% {str(silent):6}")
