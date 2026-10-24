-- =====================================================================
-- AgriPulse Seed Data (Initial Bootstrap)
-- Synchronized with Frontend Mocks & Specifications
-- =====================================================================

-- 1. Roles
INSERT INTO roles (id, name, display_name_ar, display_name_en, description) VALUES
(1, 'SUPER_ADMIN', 'مسؤول النظام الأعلى', 'Super Administrator', 'Full system access and server configuration'),
(2, 'OPERATIONS_ADMIN', 'مدير التشغيل والداشبورد', 'Operations Administrator', 'Fleet management, UI customization and work order assignment'),
(3, 'RELIABILITY_ENGINEER', 'مهندس اعتمادية وميكانيكا', 'Lead Reliability Engineer', 'ISO 10816 vibration analysis, RUL diagnostics, and AI Copilot'),
(4, 'AGRONOMIST', 'مهندس زراعي وشبكات ري', 'Irrigation Agronomist', 'Sector management, hydraulic quotas, and field vision scans'),
(5, 'MAINTENANCE_TECH', 'فني صيانة ميداني', 'Field Maintenance Technician', 'Work order execution and LOTO safety protocols'),
(6, 'VIEWER', 'مراقب / زائر', 'System Viewer', 'Read-only access to dashboards and reports')
ON CONFLICT (id) DO NOTHING;

-- 2. Users & Profiles
-- Passwords hashed for 'SecretPassword123'
INSERT INTO users (id, email, password_hash, full_name, role_id, is_active, is_verified) VALUES
('a0000000-0000-0000-0000-000000000001', 'admin@agripulse.ai', '$2b$12$e6xG8R1qL8tJgLgqjY2vE.xT7nZz7FhB8wXkK6V3Y9Y3q7pL5rQ9W', 'AgriPulse SuperAdmin', 1, TRUE, TRUE),
('a0000000-0000-0000-0000-000000000002', 't.mansour@agripulse.ai', '$2b$12$e6xG8R1qL8tJgLgqjY2vE.xT7nZz7FhB8wXkK6V3Y9Y3q7pL5rQ9W', 'Tariq Mansour', 3, TRUE, TRUE),
('a0000000-0000-0000-0000-000000000003', 's.mansour@agripulse.ai', '$2b$12$e6xG8R1qL8tJgLgqjY2vE.xT7nZz7FhB8wXkK6V3Y9Y3q7pL5rQ9W', 'Eng. Sarah Mansour', 4, TRUE, TRUE)
ON CONFLICT (email) DO NOTHING;

-- 3. Irrigation Sectors
INSERT INTO irrigation_sectors (id, name, irrigation_type, area_hectares, target_crops, nominal_pressure_bar, nominal_flow_lpm) VALUES
('sector-delta-7', 'Sector Delta-7', 'High-Pressure Pivot Network', 1420.00, 'Wheat, Alfalfa, Maize', 6.20, 2450.00),
('sector-alpha-3', 'Sector Alpha-3', 'Subsurface Drip Irrigation', 850.00, 'Citrus Orchards, Olive Groves', 4.50, 1800.00),
('sector-gamma-12', 'Sector Gamma-12', 'Canal Intake & Booster Station', 2100.00, 'Sugar Beet, Cotton, Vegetables', 7.00, 3200.00)
ON CONFLICT (id) DO NOTHING;

-- 4. User Profiles
INSERT INTO user_profiles (user_id, phone_number, job_title, assigned_sector_id, preferred_language, theme_mode, bio) VALUES
('a0000000-0000-0000-0000-000000000001', '+20 100 000 0001', 'Platform Administrator', 'sector-delta-7', 'ar', 'living_intelligence', 'AgriPulse Cyber-Physical Infrastructure Lead'),
('a0000000-0000-0000-0000-000000000002', '+20 100 123 4567', 'Lead Reliability Engineer', 'sector-delta-7', 'ar', 'living_intelligence', 'Specialist in ISO 10816 vibration diagnostics and centrifugal pump cavitation.'),
('a0000000-0000-0000-0000-000000000003', '+20 100 765 4321', 'Lead Agronomist', 'sector-alpha-3', 'ar', 'living_intelligence', 'Precision irrigation modeling and canopy stress analysis.')
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO user_notification_preferences (user_id, email_critical_alerts, email_warning_alerts, sms_emergency_alerts, push_notifications) VALUES
('a0000000-0000-0000-0000-000000000001', TRUE, TRUE, TRUE, TRUE),
('a0000000-0000-0000-0000-000000000002', TRUE, TRUE, TRUE, TRUE),
('a0000000-0000-0000-0000-000000000003', TRUE, FALSE, FALSE, TRUE)
ON CONFLICT (user_id) DO NOTHING;

-- 5. Pump Assets (Matching frontend EXACT models & statuses)
INSERT INTO pumps (
    id, name, sector_id, model, serial_number, iso_machine_class,
    rated_power_kw, rated_speed_rpm, rated_flow_lpm, rated_head_meters,
    commissioning_date, latitude, longitude, current_status, current_health_score,
    current_rul_hours, current_rul_window, current_failure_mode, urgency_level
) VALUES
('P-04', 'Pump P-04 (Zone 2 Booster)', 'sector-delta-7', 'Grundfos CR 95-2 High Flow', 'GF-2024-9941-K', 'Class II', 45.0, 2950, 1850.0, 72.0, '2023-03-15', 30.8421, 31.2543, 'CRITICAL', 42, 38, '38h – 48h operating window', 'Inner Bearing Raceway Cavitation & Micro-pitting', 'HIGH_INTERVENTION_REQUIRED'),
('P-01', 'Pump P-01 (Intake Main)', 'sector-delta-7', 'Kirloskar DB 125-330 End Suction', 'KIR-2023-4102-M', 'Class II', 55.0, 1480, 2400.0, 58.0, '2022-11-20', 30.8435, 31.2512, 'HEALTHY', 94, 5200, 'Nominal runtime (> 5000h)', 'None (Nominal operation)', 'NORMAL'),
('P-02', 'Pump P-02 (Canal Lift #1)', 'sector-delta-7', 'Grundfos NB 80-250/270', 'GF-2023-7721-A', 'Class II', 37.0, 2950, 1600.0, 65.0, '2023-01-10', 30.8410, 31.2580, 'HEALTHY', 89, 4100, 'Nominal runtime (> 4000h)', 'None (Nominal operation)', 'NORMAL'),
('P-03', 'Pump P-03 (Pivot Station 4)', 'sector-delta-7', 'Grundfos CR 64-3 Multi-Stage', 'GF-2023-8832-B', 'Class II', 30.0, 2900, 1200.0, 84.0, '2023-05-18', 30.8450, 31.2565, 'WARNING', 67, 180, '160h – 210h operating window', 'Impeller Vane Hydraulic Unbalance & Moderate Cavitation', 'MODERATE_MAINTENANCE_SCHEDULED'),
('P-05', 'Pump P-05 (Drip Header Alpha)', 'sector-alpha-3', 'Flowserve Mark 3 ANSI Centrifugal', 'FLS-2024-1188-D', 'Class II', 22.0, 2950, 950.0, 48.0, '2024-02-01', 30.7912, 31.1890, 'HEALTHY', 96, 6000, 'Nominal runtime (> 5000h)', 'None (Nominal operation)', 'NORMAL'),
('P-06', 'Pump P-06 (Booster Standby)', 'sector-gamma-12', 'Kirloskar DB 100-250', 'KIR-2024-5511-S', 'Class II', 30.0, 1480, 1400.0, 50.0, '2024-04-12', 30.9120, 31.3410, 'STANDBY', 91, 4800, 'Standby Asset', 'None (Ready on demand)', 'NORMAL')
ON CONFLICT (id) DO NOTHING;

-- 6. Initial System Thresholds (ISO 10816-3 Calibration)
INSERT INTO system_thresholds (
    id, vibration_warning_mm_s, vibration_critical_mm_s,
    temp_warning_c, temp_critical_c, suction_pressure_min_bar,
    sampling_rate_ms, alert_email, webhook_url, auto_create_work_orders
) VALUES (
    1, 4.50, 7.10, 75.00, 90.00, 0.50, 2500,
    't.mansour@agripulse.ai', 'https://scada.agripulse.internal/hooks/anomaly', TRUE
) ON CONFLICT (id) DO NOTHING;

-- 7. Active Alerts
INSERT INTO telemetry_alerts (id, pump_id, severity, title, description, triggered_value, threshold_limit, unit, is_acknowledged, is_resolved) VALUES
('ALT-2026-001', 'P-04', 'CRITICAL', 'ISO 10816 Zone D Vibration Breach', 'Pump P-04 overall RMS vibration reached 7.84 mm/s exceeding ISO 10816-3 Zone D threshold (7.10 mm/s). Immediate shutdown recommended.', 7.84, 7.10, 'mm/s', FALSE, FALSE),
('ALT-2026-002', 'P-04', 'WARNING', 'Suction Pressure Cavitation Warning', 'Suction pressure dropped to 0.38 bar causing cavitation signatures in the 1-3 kHz FFT band.', 0.38, 0.50, 'bar', TRUE, FALSE),
('ALT-2026-003', 'P-03', 'WARNING', 'Zone C Vibration Alert', 'Pump P-03 vibration reached 5.12 mm/s exceeding warning threshold (4.50 mm/s).', 5.12, 4.50, 'mm/s', TRUE, FALSE)
ON CONFLICT (id) DO NOTHING;

-- 8. Work Orders
INSERT INTO work_orders (id, pump_id, title, description, priority, status, assigned_to, created_by, due_date, estimated_hours) VALUES
('WO-2026-088', 'P-04', 'Emergency Bearing Overhaul & Impeller Cavitation Inspection', 'Perform Lockout/Tagout (LOTO) protocol. Extract SKF 7314 BEP angular contact bearings and inspect impeller vanes for cavitation pitting.', 'EMERGENCY', 'OPEN', 'a0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', NOW() + INTERVAL '2 days', 6.0),
('WO-2026-085', 'P-03', 'Hydraulic Alignment & Suction Strainer Cleaning', 'Check laser alignment between pump and motor shafts. Clean suction basket strainer to eliminate pressure drops.', 'MEDIUM', 'IN_PROGRESS', 'a0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000002', NOW() + INTERVAL '5 days', 3.5)
ON CONFLICT (id) DO NOTHING;

-- 9. LOTO Checklist for WO-2026-088
INSERT INTO loto_checklists (work_order_id, step_number, step_title, is_verified) VALUES
('WO-2026-088', 1, 'Notify Sector Delta-7 irrigation operators of pump shutdown', TRUE),
('WO-2026-088', 2, 'Isolate 380V Main Circuit Breaker at MCC-Delta-2 and apply padlock', TRUE),
('WO-2026-088', 3, 'Close suction and discharge isolation gate valves and lock handles', FALSE),
('WO-2026-088', 4, 'Vent pump casing bleed valve and confirm Zero Mechanical & Hydraulic Energy', FALSE),
('WO-2026-088', 5, 'Attach danger warning tag: "DO NOT OPERATE - P-04 BEARING OVERHAUL"', FALSE)
ON CONFLICT DO NOTHING;

-- 10. Spare Parts Catalog
INSERT INTO spare_parts (id, part_number, name, manufacturer, stock_quantity, unit_cost) VALUES
('PART-SKF-7314', 'SKF-7314-BEP', 'Angular Contact Ball Bearing 70x150x35mm', 'SKF Sweden', 8, 3850.00),
('PART-SEAL-GF95', 'GF-96537605', 'Mechanical Cartridge Shaft Seal HQQE', 'Grundfos Denmark', 5, 5200.00),
('PART-IMP-CR95', 'GF-96537612', 'Stainless Steel Impeller Chamber Stage', 'Grundfos Denmark', 2, 11500.00)
ON CONFLICT (id) DO NOTHING;

-- 11. UI Navigation Items (Dynamic Dashboard Sidebar Control)
INSERT INTO ui_navigation_items (id, title_ar, title_en, route_path, icon_name, sort_order, is_visible, required_role) VALUES
('nav_overview', 'نظرة عامة على الأسطول', 'Fleet Overview', '/', 'LayoutDashboard', 1, TRUE, 'VIEWER'),
('nav_operations', 'العمليات والمضخات الحية', 'Live Operations', '/operations', 'Activity', 2, TRUE, 'VIEWER'),
('nav_predictive', 'الذكاء التنبؤي وعمر المضخة', 'Predictive Intelligence', '/predictive', 'TrendingUp', 3, TRUE, 'VIEWER'),
('nav_diagnostics', 'المساعد الذكي والتشخيص RAG', 'AI Diagnostics Copilot', '/diagnostics', 'Sparkles', 4, TRUE, 'VIEWER'),
('nav_field_vision', 'رؤية الحاسوب وصحة المحاصيل', 'Field Vision YOLOv8', '/field-vision', 'Eye', 5, TRUE, 'VIEWER'),
('nav_assets', 'سجل أصول المضخات', 'Pump Fleet Assets', '/assets', 'Server', 6, TRUE, 'VIEWER'),
('nav_maintenance', 'تذاكر الصيانة وإجراءات السلامة', 'Work Orders & LOTO', '/maintenance', 'Wrench', 7, TRUE, 'VIEWER'),
('nav_analytics', 'الرسوم البيانية والتحليلات', 'Telemetry Analytics', '/analytics', 'BarChart3', 8, TRUE, 'VIEWER'),
('nav_documents', 'المكتبة الهندسية والأدلة', 'Engineering Docs', '/documents', 'BookOpen', 9, TRUE, 'VIEWER'),
('nav_settings', 'إعدادات المنصة ومعايرة ISO', 'System Settings', '/settings', 'Settings', 10, TRUE, 'OPERATIONS_ADMIN')
ON CONFLICT (id) DO NOTHING;

-- 12. Dynamic System Announcement Banner
INSERT INTO system_announcements (id, title, message, banner_type, is_active, target_roles) VALUES
('b0000000-0000-0000-0000-000000000001', 'تنبيه تشغيلي عاجل: مضخة P-04 في قطاع دلتا-7', 'تجاوزت المضخة P-04 حدود الاهتزاز المسموح بها وفق مواصفة ISO 10816-3 (المنطقة D). تم إنشاء تذكرة صيانة طارئة برقم WO-2026-088 وتكليف المهندس طارق منصور.', 'CRITICAL', TRUE, '["ALL"]'::jsonb)
ON CONFLICT (id) DO NOTHING;

-- 13. Fleet KPI Targets
INSERT INTO fleet_kpi_targets (id, target_monthly_power_kwh, target_monthly_water_m3, max_allowed_downtime_hours, target_fleet_health_score) VALUES
(1, 450000.00, 1200000.00, 12.00, 85)
ON CONFLICT (id) DO NOTHING;
