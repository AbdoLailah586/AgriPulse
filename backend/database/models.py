"""
AgriPulse Database ORM Models (SQLAlchemy 2.0 Async)
Matches PostgreSQL Schema & React 18 / Vite Frontend API Contract
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID, uuid4
from decimal import Decimal

from sqlalchemy import (
    String, Boolean, Integer, Numeric, Text, Date, DateTime, 
    ForeignKey, BigInteger, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

# =====================================================================
# 1. AUTHENTICATION & ACCESS CONTROL (RBAC)
# =====================================================================

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name_ar: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    users: Mapped[List["User"]] = relationship(back_populates="role")

class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    two_factor_secret: Mapped[Optional[str]] = mapped_column(String(255))
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    role: Mapped[Optional["Role"]] = relationship(back_populates="users")
    profile: Mapped[Optional["UserProfile"]] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    notification_preferences: Mapped[Optional["UserNotificationPreferences"]] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    assigned_work_orders: Mapped[List["WorkOrder"]] = relationship("WorkOrder", foreign_keys="WorkOrder.assigned_to", back_populates="assignee")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(30))
    job_title: Mapped[str] = mapped_column(String(100), default="Reliability Engineer")
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    assigned_sector_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("irrigation_sectors.id", ondelete="SET NULL"))
    preferred_language: Mapped[str] = mapped_column(String(5), default="ar")
    theme_mode: Mapped[str] = mapped_column(String(30), default="living_intelligence")
    bio: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="profile")
    assigned_sector: Mapped[Optional["IrrigationSector"]] = relationship()

class UserNotificationPreferences(Base):
    __tablename__ = "user_notification_preferences"

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    email_critical_alerts: Mapped[bool] = mapped_column(Boolean, default=True)
    email_warning_alerts: Mapped[bool] = mapped_column(Boolean, default=True)
    sms_emergency_alerts: Mapped[bool] = mapped_column(Boolean, default=False)
    push_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    daily_telemetry_digest: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="notification_preferences")

# =====================================================================
# 2. IRRIGATION SECTORS & HYDRAULIC NETWORKS
# =====================================================================

class IrrigationSector(Base):
    __tablename__ = "irrigation_sectors"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    irrigation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    area_hectares: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    target_crops: Mapped[str] = mapped_column(String(255), nullable=False)
    nominal_pressure_bar: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    nominal_flow_lpm: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    polygon_geojson: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    pumps: Mapped[List["Pump"]] = relationship(back_populates="sector")
    crop_scans: Mapped[List["FieldCropScan"]] = relationship(back_populates="sector")

# =====================================================================
# 3. PUMP ASSETS & DIGITAL TWIN SPECIFICATIONS
# =====================================================================

class Pump(Base):
    __tablename__ = "pumps"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    sector_id: Mapped[str] = mapped_column(String(50), ForeignKey("irrigation_sectors.id", ondelete="RESTRICT"), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    iso_machine_class: Mapped[str] = mapped_column(String(30), default="Class II")
    rated_power_kw: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    rated_speed_rpm: Mapped[int] = mapped_column(Integer, nullable=False)
    rated_flow_lpm: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    rated_head_meters: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    commissioning_date: Mapped[date] = mapped_column(Date, nullable=False)
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    schematic_svg_url: Mapped[Optional[str]] = mapped_column(String(500))
    is_operational: Mapped[bool] = mapped_column(Boolean, default=True)
    current_status: Mapped[str] = mapped_column(String(20), default="HEALTHY", index=True)
    current_health_score: Mapped[int] = mapped_column(Integer, default=100)
    current_rul_hours: Mapped[int] = mapped_column(Integer, default=4500)
    current_rul_window: Mapped[Optional[str]] = mapped_column(String(100))
    current_failure_mode: Mapped[Optional[str]] = mapped_column(String(255))
    urgency_level: Mapped[str] = mapped_column(String(50), default="NORMAL")
    last_sync_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    sector: Mapped["IrrigationSector"] = relationship(back_populates="pumps")
    telemetry_records: Mapped[List["SensorTelemetry"]] = relationship(back_populates="pump", cascade="all, delete-orphan")
    alerts: Mapped[List["TelemetryAlert"]] = relationship(back_populates="pump")
    work_orders: Mapped[List["WorkOrder"]] = relationship(back_populates="pump")

# =====================================================================
# 4. SENSOR TELEMETRY (TIMESERIES)
# =====================================================================

class SensorTelemetry(Base):
    __tablename__ = "sensor_telemetry"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    pump_id: Mapped[str] = mapped_column(String(50), ForeignKey("pumps.id", ondelete="CASCADE"), index=True, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    vibration_rms_x: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    vibration_rms_y: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    vibration_rms_z: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    vibration_rms_max: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    vibration_peak_g: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    bearing_temp_c: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    motor_casing_temp_c: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    suction_pressure_bar: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    discharge_pressure_bar: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    flow_rate_lpm: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    current_amp: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    voltage_volts: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    active_power_kw: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    frequency_hz: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    cavitation_index: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    thd_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=1.5)
    fft_spectrum_json: Mapped[Optional[dict]] = mapped_column(JSONB)

    pump: Mapped["Pump"] = relationship(back_populates="telemetry_records")

# =====================================================================
# 5. SYSTEM THRESHOLDS & SETTINGS (SETTINGS PAGE)
# =====================================================================

class SystemThresholds(Base):
    __tablename__ = "system_thresholds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    vibration_warning_mm_s: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=4.50)
    vibration_critical_mm_s: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=7.10)
    temp_warning_c: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=75.00)
    temp_critical_c: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=90.00)
    suction_pressure_min_bar: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0.50)
    sampling_rate_ms: Mapped[int] = mapped_column(Integer, default=2500)
    alert_email: Mapped[str] = mapped_column(String(255), default="t.mansour@agripulse.ai")
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500), default="https://scada.agripulse.internal/hooks/anomaly")
    auto_create_work_orders: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

# =====================================================================
# 6. TELEMETRY ALERTS
# =====================================================================

class TelemetryAlert(Base):
    __tablename__ = "telemetry_alerts"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    pump_id: Mapped[str] = mapped_column(String(50), ForeignKey("pumps.id", ondelete="CASCADE"), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    triggered_value: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    threshold_limit: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    pump: Mapped["Pump"] = relationship(back_populates="alerts")

# =====================================================================
# 7. WORK ORDERS & MAINTENANCE
# =====================================================================

class WorkOrder(Base):
    __tablename__ = "work_orders"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    pump_id: Mapped[str] = mapped_column(String(50), ForeignKey("pumps.id", ondelete="RESTRICT"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="OPEN", index=True)
    assigned_to: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    created_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    estimated_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=4.0)
    actual_downtime_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0.00)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    pump: Mapped["Pump"] = relationship(back_populates="work_orders")
    assignee: Mapped[Optional["User"]] = relationship(foreign_keys=[assigned_to], back_populates="assigned_work_orders")
    loto_steps: Mapped[List["LotoChecklist"]] = relationship(back_populates="work_order", cascade="all, delete-orphan")

class LotoChecklist(Base):
    __tablename__ = "loto_checklists"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    work_order_id: Mapped[str] = mapped_column(String(50), ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    step_title: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    work_order: Mapped["WorkOrder"] = relationship(back_populates="loto_steps")

# =====================================================================
# 8. FIELD VISION (YOLOv8 SCANS)
# =====================================================================

class FieldCropScan(Base):
    __tablename__ = "field_crop_scans"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    sector_id: Mapped[str] = mapped_column(String(50), ForeignKey("irrigation_sectors.id", ondelete="CASCADE"), nullable=False, index=True)
    associated_pump_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("pumps.id", ondelete="SET NULL"), index=True)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    annotated_image_url: Mapped[Optional[str]] = mapped_column(String(500))
    primary_diagnosis: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    severity_level: Mapped[str] = mapped_column(String(20), nullable=False)
    water_stress_correlation: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    detections_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    uploaded_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    sector: Mapped["IrrigationSector"] = relationship(back_populates="crop_scans")

# =====================================================================
# 9. ADMIN CMS & DYNAMIC UI CUSTOMIZATION
# =====================================================================

class SystemAnnouncement(Base):
    __tablename__ = "system_announcements"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    banner_type: Mapped[str] = mapped_column(String(20), default="INFO")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    target_roles: Mapped[dict] = mapped_column(JSONB, default=["ALL"])
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class UiNavigationItem(Base):
    __tablename__ = "ui_navigation_items"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title_ar: Mapped[str] = mapped_column(String(100), nullable=False)
    title_en: Mapped[str] = mapped_column(String(100), nullable=False)
    route_path: Mapped[str] = mapped_column(String(100), nullable=False)
    icon_name: Mapped[str] = mapped_column(String(50), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    required_role: Mapped[str] = mapped_column(String(50), default="VIEWER")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class FleetKpiTargets(Base):
    __tablename__ = "fleet_kpi_targets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    target_monthly_power_kwh: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=450000.00)
    target_monthly_water_m3: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=1200000.00)
    max_allowed_downtime_hours: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=12.00)
    target_fleet_health_score: Mapped[int] = mapped_column(Integer, default=85)
    updated_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

# =====================================================================
# 10. AUDIT LOGS
# =====================================================================

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    old_values: Mapped[Optional[dict]] = mapped_column(JSONB)
    new_values: Mapped[Optional[dict]] = mapped_column(JSONB)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
