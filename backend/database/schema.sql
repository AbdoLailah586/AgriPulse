-- =====================================================================
-- AgriPulse Enterprise Database Schema (PostgreSQL 15+)
-- Artificial Intelligence Engineering Graduation Project
-- Faculty of Engineering, Mansoura University
-- Conforms to ISO 10816-3 & React 18/Vite Frontend Architecture
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Clean schema drop (for fresh setup)
-- DROP SCHEMA IF EXISTS public CASCADE;
-- CREATE SCHEMA public;

-- =====================================================================
-- 1. AUTHENTICATION & ACCESS CONTROL (RBAC)
-- =====================================================================

CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name_ar VARCHAR(100) NOT NULL,
    display_name_en VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(100) UNIQUE NOT NULL,
    module VARCHAR(50) NOT NULL,
    description VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    role_id INTEGER REFERENCES roles(id) ON DELETE RESTRICT,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(255),
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id);

CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    is_revoked BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(refresh_token_hash);

-- =====================================================================
-- 2. USER PROFILES & NOTIFICATION PREFERENCES
-- =====================================================================

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    phone_number VARCHAR(30),
    job_title VARCHAR(100) DEFAULT 'Reliability Engineer',
    avatar_url VARCHAR(500),
    assigned_sector_id VARCHAR(50),
    preferred_language VARCHAR(5) DEFAULT 'ar',
    theme_mode VARCHAR(30) DEFAULT 'living_intelligence',
    bio TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_notification_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    email_critical_alerts BOOLEAN DEFAULT TRUE,
    email_warning_alerts BOOLEAN DEFAULT TRUE,
    sms_emergency_alerts BOOLEAN DEFAULT FALSE,
    push_notifications BOOLEAN DEFAULT TRUE,
    daily_telemetry_digest BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================================
-- 3. IRRIGATION SECTORS & HYDRAULIC NETWORKS
-- =====================================================================

CREATE TABLE IF NOT EXISTS irrigation_sectors (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    irrigation_type VARCHAR(100) NOT NULL,
    area_hectares NUMERIC(10, 2) NOT NULL,
    target_crops VARCHAR(255) NOT NULL,
    nominal_pressure_bar NUMERIC(6, 2) NOT NULL,
    nominal_flow_lpm NUMERIC(10, 2) NOT NULL,
    polygon_geojson JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add foreign key constraint to user_profiles now that irrigation_sectors exists
ALTER TABLE user_profiles 
    ADD CONSTRAINT fk_profile_sector 
    FOREIGN KEY (assigned_sector_id) 
    REFERENCES irrigation_sectors(id) 
    ON DELETE SET NULL;

-- =====================================================================
-- 4. PUMP ASSETS & DIGITAL TWIN SPECIFICATIONS
-- =====================================================================

CREATE TABLE IF NOT EXISTS pumps (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    sector_id VARCHAR(50) REFERENCES irrigation_sectors(id) ON DELETE RESTRICT,
    model VARCHAR(100) NOT NULL,
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    iso_machine_class VARCHAR(30) DEFAULT 'Class II',
    rated_power_kw NUMERIC(8, 2) NOT NULL,
    rated_speed_rpm INTEGER NOT NULL,
    rated_flow_lpm NUMERIC(10, 2) NOT NULL,
    rated_head_meters NUMERIC(8, 2) NOT NULL,
    commissioning_date DATE NOT NULL,
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    schematic_svg_url VARCHAR(500),
    is_operational BOOLEAN DEFAULT TRUE,
    current_status VARCHAR(20) DEFAULT 'HEALTHY' CHECK (current_status IN ('HEALTHY', 'WARNING', 'CRITICAL', 'STANDBY', 'OFFLINE')),
    current_health_score INTEGER CHECK (current_health_score BETWEEN 0 AND 100) DEFAULT 100,
    current_rul_hours INTEGER DEFAULT 4500,
    current_rul_window VARCHAR(100),
    current_failure_mode VARCHAR(255),
    urgency_level VARCHAR(50) DEFAULT 'NORMAL',
    last_sync_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pumps_sector ON pumps(sector_id);
CREATE INDEX IF NOT EXISTS idx_pumps_status ON pumps(current_status);
CREATE INDEX IF NOT EXISTS idx_pumps_health ON pumps(current_health_score);

-- =====================================================================
-- 5. SENSOR TELEMETRY & TIMESERIES
-- =====================================================================

CREATE TABLE IF NOT EXISTS sensor_telemetry (
    id BIGSERIAL PRIMARY KEY,
    pump_id VARCHAR(50) REFERENCES pumps(id) ON DELETE CASCADE,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    vibration_rms_x NUMERIC(6, 3) NOT NULL,
    vibration_rms_y NUMERIC(6, 3) NOT NULL,
    vibration_rms_z NUMERIC(6, 3) NOT NULL,
    vibration_rms_max NUMERIC(6, 3) NOT NULL,
    vibration_peak_g NUMERIC(6, 3) NOT NULL,
    bearing_temp_c NUMERIC(6, 2) NOT NULL,
    motor_casing_temp_c NUMERIC(6, 2) NOT NULL,
    suction_pressure_bar NUMERIC(6, 3) NOT NULL,
    discharge_pressure_bar NUMERIC(6, 3) NOT NULL,
    flow_rate_lpm NUMERIC(10, 2) NOT NULL,
    current_amp NUMERIC(8, 2) NOT NULL,
    voltage_volts NUMERIC(8, 2) NOT NULL,
    active_power_kw NUMERIC(8, 2) NOT NULL,
    frequency_hz NUMERIC(6, 2) NOT NULL,
    cavitation_index NUMERIC(6, 3) NOT NULL,
    thd_percent NUMERIC(5, 2) DEFAULT 1.5,
    fft_spectrum_json JSONB
);

-- High-performance indexes for timeseries analysis
CREATE INDEX IF NOT EXISTS idx_telemetry_pump_time ON sensor_telemetry(pump_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_time_brin ON sensor_telemetry USING brin(recorded_at);

-- =====================================================================
-- 6. WEIBULL PREDICTIVE INTELLIGENCE & ML INFERENCE LOGS
-- =====================================================================

CREATE TABLE IF NOT EXISTS weibull_predictions (
    id BIGSERIAL PRIMARY KEY,
    pump_id VARCHAR(50) REFERENCES pumps(id) ON DELETE CASCADE,
    inference_time TIMESTAMPTZ DEFAULT NOW(),
    rul_estimated_hours INTEGER NOT NULL,
    rul_lower_bound_hours INTEGER NOT NULL,
    rul_upper_bound_hours INTEGER NOT NULL,
    shape_parameter_beta NUMERIC(6, 3) NOT NULL,
    scale_parameter_eta NUMERIC(10, 2) NOT NULL,
    failure_probability_24h NUMERIC(5, 4) NOT NULL,
    failure_probability_7d NUMERIC(5, 4) NOT NULL,
    diagnosed_fault VARCHAR(150),
    top_shap_features JSONB
);

CREATE INDEX IF NOT EXISTS idx_weibull_pump ON weibull_predictions(pump_id, inference_time DESC);

-- =====================================================================
-- 7. SYSTEM THRESHOLDS & ISO 10816-3 CALIBRATION (SETTINGS PAGE)
-- =====================================================================

CREATE TABLE IF NOT EXISTS system_thresholds (
    id INTEGER PRIMARY KEY DEFAULT 1,
    vibration_warning_mm_s NUMERIC(5, 2) NOT NULL DEFAULT 4.50,
    vibration_critical_mm_s NUMERIC(5, 2) NOT NULL DEFAULT 7.10,
    temp_warning_c NUMERIC(5, 2) NOT NULL DEFAULT 75.00,
    temp_critical_c NUMERIC(5, 2) NOT NULL DEFAULT 90.00,
    suction_pressure_min_bar NUMERIC(5, 2) NOT NULL DEFAULT 0.50,
    sampling_rate_ms INTEGER NOT NULL DEFAULT 2500,
    alert_email VARCHAR(255) NOT NULL DEFAULT 't.mansour@agripulse.ai',
    webhook_url VARCHAR(500) DEFAULT 'https://scada.agripulse.internal/hooks/anomaly',
    auto_create_work_orders BOOLEAN DEFAULT TRUE,
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT single_row_system_thresholds CHECK (id = 1)
);

-- =====================================================================
-- 8. TELEMETRY ALERTS & INCIDENT LIFECYCLE
-- =====================================================================

CREATE TABLE IF NOT EXISTS telemetry_alerts (
    id VARCHAR(50) PRIMARY KEY,
    pump_id VARCHAR(50) REFERENCES pumps(id) ON DELETE CASCADE,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('CRITICAL', 'WARNING', 'INFO')),
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    triggered_value NUMERIC(8, 2) NOT NULL,
    threshold_limit NUMERIC(8, 2) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by UUID REFERENCES users(id),
    acknowledged_at TIMESTAMPTZ,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_pump ON telemetry_alerts(pump_id);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON telemetry_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON telemetry_alerts(is_resolved);

-- =====================================================================
-- 9. MAINTENANCE WORK ORDERS & LOTO SAFETY PROTOCOL
-- =====================================================================

CREATE TABLE IF NOT EXISTS work_orders (
    id VARCHAR(50) PRIMARY KEY,
    pump_id VARCHAR(50) REFERENCES pumps(id) ON DELETE RESTRICT,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL CHECK (priority IN ('EMERGENCY', 'HIGH', 'MEDIUM', 'LOW')),
    status VARCHAR(30) NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'IN_PROGRESS', 'PENDING_PARTS', 'COMPLETED', 'CANCELLED')),
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    due_date TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    estimated_hours NUMERIC(6, 2) DEFAULT 4.0,
    actual_downtime_hours NUMERIC(6, 2),
    total_cost NUMERIC(12, 2) DEFAULT 0.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_work_orders_pump ON work_orders(pump_id);
CREATE INDEX IF NOT EXISTS idx_work_orders_status ON work_orders(status);
CREATE INDEX IF NOT EXISTS idx_work_orders_assigned ON work_orders(assigned_to);

CREATE TABLE IF NOT EXISTS loto_checklists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_order_id VARCHAR(50) REFERENCES work_orders(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    step_title VARCHAR(255) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by UUID REFERENCES users(id),
    verified_at TIMESTAMPTZ,
    CONSTRAINT uq_wo_step UNIQUE (work_order_id, step_number)
);

CREATE TABLE IF NOT EXISTS spare_parts (
    id VARCHAR(50) PRIMARY KEY,
    part_number VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    manufacturer VARCHAR(100) NOT NULL,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    unit_cost NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS work_order_parts (
    work_order_id VARCHAR(50) REFERENCES work_orders(id) ON DELETE CASCADE,
    part_id VARCHAR(50) REFERENCES spare_parts(id) ON DELETE RESTRICT,
    quantity_used INTEGER NOT NULL DEFAULT 1,
    unit_cost_at_time NUMERIC(10, 2) NOT NULL,
    PRIMARY KEY (work_order_id, part_id)
);

-- =====================================================================
-- 10. AI DIAGNOSTICS & RAG KNOWLEDGE BASE
-- =====================================================================

CREATE TABLE IF NOT EXISTS rag_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100) NOT NULL,
    file_url VARCHAR(500),
    content_markdown TEXT NOT NULL,
    total_chunks INTEGER DEFAULT 0,
    vector_collection_name VARCHAR(100) DEFAULT 'agripulse_knowledge',
    is_indexed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_diagnostic_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    pump_id VARCHAR(50) REFERENCES pumps(id) ON DELETE SET NULL,
    session_title VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_chat_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID REFERENCES ai_diagnostic_sessions(id) ON DELETE CASCADE,
    sender_role VARCHAR(20) NOT NULL CHECK (sender_role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    citations_json JSONB,
    model_name VARCHAR(100) DEFAULT 'gemini-1.5-pro',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_session ON ai_chat_messages(session_id);

-- =====================================================================
-- 11. FIELD VISION & CROP PATHOLOGY (YOLOv8 SCANS)
-- =====================================================================

CREATE TABLE IF NOT EXISTS field_crop_scans (
    id VARCHAR(50) PRIMARY KEY,
    sector_id VARCHAR(50) REFERENCES irrigation_sectors(id) ON DELETE CASCADE,
    associated_pump_id VARCHAR(50) REFERENCES pumps(id) ON DELETE SET NULL,
    image_url VARCHAR(500) NOT NULL,
    annotated_image_url VARCHAR(500),
    primary_diagnosis VARCHAR(100) NOT NULL,
    confidence_score NUMERIC(5, 4) NOT NULL,
    severity_level VARCHAR(20) NOT NULL CHECK (severity_level IN ('LOW', 'MODERATE', 'HIGH', 'CRITICAL')),
    water_stress_correlation NUMERIC(5, 2) NOT NULL,
    detections_json JSONB,
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    scanned_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scans_sector ON field_crop_scans(sector_id);
CREATE INDEX IF NOT EXISTS idx_scans_pump ON field_crop_scans(associated_pump_id);

-- =====================================================================
-- 12. ADMIN CMS & DYNAMIC UI CUSTOMIZATION
-- =====================================================================

CREATE TABLE IF NOT EXISTS system_announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    banner_type VARCHAR(20) DEFAULT 'INFO' CHECK (banner_type IN ('INFO', 'WARNING', 'CRITICAL', 'SUCCESS')),
    is_active BOOLEAN DEFAULT TRUE,
    target_roles JSONB DEFAULT '["ALL"]'::jsonb,
    starts_at TIMESTAMPTZ DEFAULT NOW(),
    ends_at TIMESTAMPTZ,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ui_navigation_items (
    id VARCHAR(50) PRIMARY KEY,
    title_ar VARCHAR(100) NOT NULL,
    title_en VARCHAR(100) NOT NULL,
    route_path VARCHAR(100) NOT NULL,
    icon_name VARCHAR(50) NOT NULL,
    sort_order INTEGER NOT NULL,
    is_visible BOOLEAN DEFAULT TRUE,
    required_role VARCHAR(50) DEFAULT 'VIEWER',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fleet_kpi_targets (
    id INTEGER PRIMARY KEY DEFAULT 1,
    target_monthly_power_kwh NUMERIC(12, 2) NOT NULL DEFAULT 450000.00,
    target_monthly_water_m3 NUMERIC(12, 2) NOT NULL DEFAULT 1200000.00,
    max_allowed_downtime_hours NUMERIC(8, 2) NOT NULL DEFAULT 12.00,
    target_fleet_health_score INTEGER NOT NULL DEFAULT 85,
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT single_row_fleet_kpis CHECK (id = 1)
);

-- =====================================================================
-- 13. AUDIT LOGS & OPERATIONAL SECURITY TRACE
-- =====================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(30) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_logs(created_at DESC);
