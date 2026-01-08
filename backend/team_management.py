import uuid
import psycopg
from psycopg.rows import dict_row

# Configuration — replace with your values
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "thirdeye",
    "user": "admin",
    "password": "admin",
}

CREATE_TABLE_SQL = """
drop table teams;
CREATE TABLE IF NOT EXISTS teams (
    team_id TEXT PRIMARY KEY,         -- string ID
    team_lead TEXT NOT NULL,
    members TEXT NOT NULL             -- comma-delimited list of members
);
"""

INSERT_SQL = "INSERT INTO teams (team_id, team_lead, members) VALUES (%s, %s, %s);"
SELECT_ALL_SQL = "SELECT team_id, team_lead, members FROM teams ORDER BY team_id;"

def get_connection(config: dict):
    conn_str = "host={host} port={port} dbname={dbname} user={user} password={password}".format(**config)
    return psycopg.connect(conn_str, row_factory=dict_row)

def create_table(conn):
    with conn.cursor() as cur:
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()

def generate_team_id():
    # UUID4 string; change if you prefer another format
    return str(uuid.uuid4())

def add_team(conn, team_lead: str, members_list, team_id: str | None = None):
    if team_id is None:
        team_id = generate_team_id()
    if isinstance(members_list, (list, tuple)):
        members = ",".join(m.strip() for m in members_list)
    else:
        members = str(members_list).strip()
    with conn.cursor() as cur:
        cur.execute(INSERT_SQL, (team_id, team_lead, members))
    conn.commit()
    return team_id

def list_teams(conn):
    with conn.cursor() as cur:
        cur.execute(SELECT_ALL_SQL)
        return cur.fetchall()

def main():
    conn = get_connection(DB_CONFIG)
    try:
        create_table(conn)
        # Example inserts
        add_team(conn, "Ockmore", ["GreyElaina", "Danarvelini", "chailandau"], 'core-team')
        add_team(conn, "Ectogen", ["lovelydinosaur", "agronholm", "thejcannon", "emmanuel-ferdman"], "team-123")
        add_team(conn, "Example", ["Zproger", "agronholm", "Zaczero"], "team-234")
        
        teams = list_teams(conn)
        for t in teams:
            print(f"team_id={t['team_id']}, lead={t['team_lead']}, members={t['members']}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
