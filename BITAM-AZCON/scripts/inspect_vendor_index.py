from sqlalchemy import create_engine, text

e = create_engine("sqlite:///azcon.db")
with e.connect() as con:
    rows = con.execute(
        text("SELECT name, sql FROM sqlite_master WHERE tbl_name='vendors'")
    ).fetchall()
    for r in rows:
        print(r)
