CREATE TABLE IF NOT EXISTS app_users (
    id BIGSERIAL PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone_number VARCHAR(30),
    role VARCHAR(40) NOT NULL CHECK (role IN ('caregiver', 'detection_operator')),
    password_hash TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS fall_events (
    id BIGSERIAL PRIMARY KEY,
    detected_by_user_id BIGINT REFERENCES app_users(id) ON DELETE SET NULL,
    source_type VARCHAR(30) NOT NULL CHECK (source_type IN ('live_stream', 'uploaded_video')),
    source_label VARCHAR(255),
    event_status VARCHAR(30) NOT NULL DEFAULT 'detected' CHECK (event_status IN ('detected', 'acknowledged', 'resolved')),
    confidence_score NUMERIC(5, 2),
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS notification_deliveries (
    id BIGSERIAL PRIMARY KEY,
    fall_event_id BIGINT NOT NULL REFERENCES fall_events(id) ON DELETE CASCADE,
    recipient_user_id BIGINT NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    channel VARCHAR(30) NOT NULL DEFAULT 'portal' CHECK (channel IN ('portal', 'email', 'sms')),
    delivery_status VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK (delivery_status IN ('pending', 'sent', 'failed', 'seen')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    delivered_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_app_users_role ON app_users(role);
CREATE INDEX IF NOT EXISTS idx_fall_events_detected_at ON fall_events(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_notification_deliveries_recipient ON notification_deliveries(recipient_user_id, created_at DESC);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_app_users_updated_at ON app_users;

CREATE TRIGGER trg_app_users_updated_at
BEFORE UPDATE ON app_users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
