import configparser
import redshift_connector
import pandas as pd
from pathlib import Path


def get_config(config_path=None):
    if config_path is None:
        config_path = Path(__file__).parent / "redshift_config.ini"
    config = configparser.ConfigParser()
    config.read(config_path)
    return config["redshift"]


def get_connection(config_path=None):
    cfg = get_config(config_path)
    conn = redshift_connector.connect(
        host=cfg["host"],
        port=int(cfg["port"]),
        database=cfg["database"],
        user=cfg["user"],
        password=cfg["password"],
    )
    # Kill any query that runs longer than 10 minutes
    cursor = conn.cursor()
    cursor.execute("SET statement_timeout = 600000")
    cursor.close()
    return conn


def run_query(query, config_path=None, retries=3, delay=15):
    import time
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            conn = get_connection(config_path)
            try:
                df = pd.read_sql(query, conn)
                return df
            finally:
                conn.close()
        except Exception as e:
            last_err = e
            if attempt < retries:
                print(f"[redshift_client] attempt {attempt} failed: {e} — retrying in {delay}s")
                time.sleep(delay)
    raise last_err


if __name__ == "__main__":
    df = run_query("SELECT 1 AS test")
    print(df)
