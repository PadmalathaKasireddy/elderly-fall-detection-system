import os
import site
import sys
from contextlib import contextmanager

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - handled gracefully at runtime
    user_site = site.getusersitepackages()
    if user_site and user_site not in sys.path:
        sys.path.append(user_site)

    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError:
        psycopg = None
        dict_row = None


ROLE_VALUES = {"caregiver", "detection_operator"}


def _database_url():
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")

    host = os.getenv("PGHOST")
    port = os.getenv("PGPORT", "5432")
    dbname = os.getenv("PGDATABASE")
    user = os.getenv("PGUSER")
    password = os.getenv("PGPASSWORD", "")

    if not all([host, dbname, user]):
        return None

    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


@contextmanager
def get_connection():
    if psycopg is None:
        raise RuntimeError(
            "PostgreSQL driver missing. Install psycopg before using login/register."
        )

    database_url = _database_url()
    if not database_url:
        raise RuntimeError(
            "Database connection is not configured. Set DATABASE_URL or PGHOST/PGDATABASE/PGUSER/PGPASSWORD."
        )

    conn = psycopg.connect(database_url, row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()


def fetch_user_by_email(email):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, full_name, email, phone_number, role, password_hash, is_active, last_login_at
                FROM app_users
                WHERE email = %s
                """,
                (email,),
            )
            return cur.fetchone()


def create_user(full_name, email, phone_number, role, password_hash):
    if role not in ROLE_VALUES:
        raise ValueError("Unsupported role selected.")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_users (full_name, email, phone_number, role, password_hash)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
                RETURNING id, full_name, email, phone_number, role, is_active
                """,
                (full_name, email, phone_number, role, password_hash),
            )
            user = cur.fetchone()
            conn.commit()
            return user


def touch_last_login(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE app_users
                SET last_login_at = NOW()
                WHERE id = %s
                """,
                (user_id,),
            )
            conn.commit()


def create_live_fall_notification(operator_user_id, source_label="Live Stream"):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO fall_events (detected_by_user_id, source_type, source_label, event_status, confidence_score, notes)
                VALUES (%s, 'live_stream', %s, 'detected', NULL, 'Live fall detected by the monitoring operator.')
                RETURNING id, detected_at
                """,
                (operator_user_id, source_label),
            )
            event = cur.fetchone()

            cur.execute(
                """
                SELECT id
                FROM app_users
                WHERE is_active = TRUE
                  AND role = 'caregiver'
                """
            )
            recipients = cur.fetchall()

            if recipients:
                cur.executemany(
                    """
                    INSERT INTO notification_deliveries (fall_event_id, recipient_user_id, channel, delivery_status, delivered_at)
                    VALUES (%s, %s, 'portal', 'sent', NOW())
                    """,
                    [(event["id"], recipient["id"]) for recipient in recipients],
                )

            conn.commit()
            return {
                "event_id": event["id"],
                "detected_at": event["detected_at"],
                "recipient_count": len(recipients),
            }


def list_notification_feed(recipient_user_id, limit=10):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    nd.id,
                    nd.delivery_status,
                    nd.channel,
                    nd.created_at,
                    fe.source_type,
                    fe.source_label,
                    fe.event_status,
                    fe.detected_at,
                    detector.full_name AS detected_by_name,
                    detector.role AS detected_by_role
                FROM notification_deliveries AS nd
                JOIN fall_events AS fe ON fe.id = nd.fall_event_id
                LEFT JOIN app_users AS detector ON detector.id = fe.detected_by_user_id
                WHERE nd.recipient_user_id = %s
                ORDER BY nd.created_at DESC
                LIMIT %s
                """,
                (recipient_user_id, limit),
            )
            return cur.fetchall()
