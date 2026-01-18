# データベーススキーマ設計

## ERD概要

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   sites     │──┬──<│ site_tasks  │──┬──<│task_progress│
│  (現場)     │  │   │  (工程)     │  │   │  (進捗)     │
└─────────────┘  │   └─────────────┘  │   └─────────────┘
                 │                     │
                 └──<│site_daily_   │  │
                     │  reports     │  │
                     └──────────────┘  │
                                       │
┌─────────────┐      ┌─────────────┐  │
│  vehicles   │──┬──<│ gps_        │  │
│  (車両)     │  │   │  positions  │  │
└─────────────┘  │   │ (GPS位置)   │  │
                 │   └─────────────┘  │
                 │                     │
                 ├──<│ vehicle_    │  │
                 │   │  cycles     │  │
                 │   │ (運搬サイクル) │
                 │   └─────────────┘  │
                 │                     │
                 └──<│ resource_   │──┘
                     │  assignments│
                     │ (配置)      │
                     └─────────────┘

┌─────────────┐      ┌─────────────┐
│alert_rules  │──┬──<│   alerts    │──┬──<│notifications│
│(アラート定義)│  │   │(アラート発生)│  │   │  (通知)     │
└─────────────┘  │   └─────────────┘  │   └─────────────┘
                                       │
┌─────────────┐      ┌─────────────┐  │
│simulations  │──┬──<│simulation_  │  │
│(シミュレー  │  │   │  results    │  │
│ ション設定) │  │   │  (結果)     │  │
└─────────────┘  │   └─────────────┘  │
```

---

## 1. 現場管理

### sites (現場マスタ)
```sql
CREATE TABLE sites (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_code           VARCHAR(50) UNIQUE NOT NULL,
    site_name           VARCHAR(200) NOT NULL,
    location            GEOGRAPHY(POINT, 4326),  -- PostGIS
    address             VARCHAR(500),
    client_name         VARCHAR(200),
    contractor_name     VARCHAR(200),

    -- 工期
    planned_start_date  DATE NOT NULL,
    planned_end_date    DATE NOT NULL,
    actual_start_date   DATE,
    actual_end_date     DATE,

    -- 施工数量
    planned_volume      DECIMAL(12, 2),  -- 計画土量 (m³)
    actual_volume       DECIMAL(12, 2) DEFAULT 0,  -- 実績土量 (m³)

    -- ステータス
    status              VARCHAR(20) NOT NULL DEFAULT 'planning',
    -- 'planning', 'active', 'suspended', 'completed'

    -- ジオフェンス（作業エリア）
    work_area_polygon   GEOGRAPHY(POLYGON, 4326),

    -- メタデータ
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by          UUID,
    updated_by          UUID,

    CONSTRAINT chk_dates CHECK (planned_end_date >= planned_start_date)
);

CREATE INDEX idx_sites_status ON sites(status);
CREATE INDEX idx_sites_location ON sites USING GIST(location);
CREATE INDEX idx_sites_work_area ON sites USING GIST(work_area_polygon);
```

### site_tasks (工程タスク)
```sql
CREATE TABLE site_tasks (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id             UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    parent_task_id      UUID REFERENCES site_tasks(id),  -- 階層構造

    task_code           VARCHAR(50) NOT NULL,
    task_name           VARCHAR(200) NOT NULL,
    task_type           VARCHAR(50) NOT NULL,
    -- 'excavation', 'transport', 'backfill', 'inspection'

    -- 計画
    planned_start_date  DATE NOT NULL,
    planned_end_date    DATE NOT NULL,
    planned_volume      DECIMAL(12, 2),
    planned_manhours    DECIMAL(8, 2),

    -- 実績
    actual_start_date   DATE,
    actual_end_date     DATE,
    actual_volume       DECIMAL(12, 2) DEFAULT 0,
    actual_manhours     DECIMAL(8, 2) DEFAULT 0,

    -- 進捗
    progress_rate       DECIMAL(5, 2) DEFAULT 0,  -- %
    status              VARCHAR(20) DEFAULT 'pending',
    -- 'pending', 'in_progress', 'completed', 'delayed'

    -- 依存関係
    dependencies        JSONB,  -- [{"task_id": "xxx", "type": "FS"}]

    -- 順序
    display_order       INTEGER,

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_task_dates CHECK (planned_end_date >= planned_start_date),
    CONSTRAINT chk_progress CHECK (progress_rate BETWEEN 0 AND 100)
);

CREATE INDEX idx_site_tasks_site ON site_tasks(site_id);
CREATE INDEX idx_site_tasks_parent ON site_tasks(parent_task_id);
CREATE INDEX idx_site_tasks_status ON site_tasks(status);
```

### task_progress (日別進捗)
```sql
CREATE TABLE task_progress (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id             UUID NOT NULL REFERENCES site_tasks(id) ON DELETE CASCADE,
    progress_date       DATE NOT NULL,

    volume_completed    DECIMAL(12, 2) NOT NULL,  -- 当日施工量
    cumulative_volume   DECIMAL(12, 2) NOT NULL,  -- 累計施工量
    manhours            DECIMAL(8, 2),

    weather             VARCHAR(50),
    temperature_max     DECIMAL(4, 1),
    temperature_min     DECIMAL(4, 1),
    rainfall            DECIMAL(6, 2),  -- mm

    remarks             TEXT,

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by          UUID,

    UNIQUE(task_id, progress_date)
);

CREATE INDEX idx_task_progress_task ON task_progress(task_id);
CREATE INDEX idx_task_progress_date ON task_progress(progress_date);
```

### site_daily_reports (日報)
```sql
CREATE TABLE site_daily_reports (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id             UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    report_date         DATE NOT NULL,

    weather_am          VARCHAR(50),
    weather_pm          VARCHAR(50),
    temperature_max     DECIMAL(4, 1),
    temperature_min     DECIMAL(4, 1),

    -- 施工数量
    daily_volume        DECIMAL(12, 2),
    cumulative_volume   DECIMAL(12, 2),

    -- 人員・機械
    worker_count        INTEGER,
    vehicle_count       INTEGER,

    -- 作業内容
    work_description    TEXT,
    issues              TEXT,
    tomorrow_plan       TEXT,

    -- 安全
    safety_meeting      BOOLEAN DEFAULT FALSE,
    accidents           TEXT,
    near_misses         TEXT,

    -- 承認フロー
    status              VARCHAR(20) DEFAULT 'draft',
    -- 'draft', 'submitted', 'approved'
    submitted_at        TIMESTAMP WITH TIME ZONE,
    submitted_by        UUID,
    approved_at         TIMESTAMP WITH TIME ZONE,
    approved_by         UUID,

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(site_id, report_date)
);

CREATE INDEX idx_site_reports_site ON site_daily_reports(site_id);
CREATE INDEX idx_site_reports_date ON site_daily_reports(report_date);
```

---

## 2. リソース管理

### vehicles (車両マスタ)
```sql
CREATE TABLE vehicles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_code        VARCHAR(50) UNIQUE NOT NULL,
    vehicle_name        VARCHAR(100) NOT NULL,
    vehicle_type        VARCHAR(50) NOT NULL,
    -- 'dump_truck', 'backhoe', 'bulldozer', 'excavator'

    -- 仕様
    capacity            DECIMAL(8, 2),  -- 積載量 (m³ or ton)
    manufacturer        VARCHAR(100),
    model_name          VARCHAR(100),
    year_manufactured   INTEGER,

    -- GPS端末
    gps_device_id       VARCHAR(100),
    gps_device_type     VARCHAR(50),
    -- 'gpsnext', 'trackimo', 'smartphone'

    -- ステータス
    status              VARCHAR(20) DEFAULT 'active',
    -- 'active', 'maintenance', 'retired'

    -- 現在の配置
    current_site_id     UUID REFERENCES sites(id),

    -- 車検・点検
    inspection_date     DATE,
    next_inspection     DATE,

    -- 燃費・稼働
    fuel_efficiency     DECIMAL(6, 2),  -- L/hour
    hourly_cost         DECIMAL(10, 2),  -- 円/時間

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_vehicles_type ON vehicles(vehicle_type);
CREATE INDEX idx_vehicles_status ON vehicles(status);
CREATE INDEX idx_vehicles_site ON vehicles(current_site_id);
CREATE INDEX idx_vehicles_gps_device ON vehicles(gps_device_id);
```

### workers (作業員マスタ)
```sql
CREATE TABLE workers (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_code         VARCHAR(50) UNIQUE NOT NULL,
    name                VARCHAR(100) NOT NULL,
    name_kana           VARCHAR(100),

    role                VARCHAR(50) NOT NULL,
    -- 'operator', 'driver', 'laborer', 'foreman', 'supervisor'

    qualifications      JSONB,  -- ["重機1級", "玉掛け"]

    phone_number        VARCHAR(20),
    email               VARCHAR(100),

    employment_type     VARCHAR(20),
    -- 'full_time', 'part_time', 'contractor'

    daily_rate          DECIMAL(10, 2),

    status              VARCHAR(20) DEFAULT 'active',

    current_site_id     UUID REFERENCES sites(id),

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_workers_role ON workers(role);
CREATE INDEX idx_workers_status ON workers(status);
CREATE INDEX idx_workers_site ON workers(current_site_id);
```

### resource_assignments (リソース配置)
```sql
CREATE TABLE resource_assignments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id             UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    task_id             UUID REFERENCES site_tasks(id) ON DELETE SET NULL,

    resource_type       VARCHAR(20) NOT NULL,
    -- 'vehicle', 'worker'

    vehicle_id          UUID REFERENCES vehicles(id),
    worker_id           UUID REFERENCES workers(id),

    assignment_date     DATE NOT NULL,
    start_time          TIME,
    end_time            TIME,

    actual_start_time   TIMESTAMP WITH TIME ZONE,
    actual_end_time     TIMESTAMP WITH TIME ZONE,

    status              VARCHAR(20) DEFAULT 'assigned',
    -- 'assigned', 'in_progress', 'completed', 'cancelled'

    notes               TEXT,

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_resource_exists CHECK (
        (resource_type = 'vehicle' AND vehicle_id IS NOT NULL) OR
        (resource_type = 'worker' AND worker_id IS NOT NULL)
    )
);

CREATE INDEX idx_assignments_site ON resource_assignments(site_id);
CREATE INDEX idx_assignments_task ON resource_assignments(task_id);
CREATE INDEX idx_assignments_vehicle ON resource_assignments(vehicle_id);
CREATE INDEX idx_assignments_worker ON resource_assignments(worker_id);
CREATE INDEX idx_assignments_date ON resource_assignments(assignment_date);
```

---

## 3. GPS・運行管理（TimescaleDB）

### gps_positions (GPS位置データ - Hypertable)
```sql
CREATE TABLE gps_positions (
    time                TIMESTAMP WITH TIME ZONE NOT NULL,
    vehicle_id          UUID NOT NULL REFERENCES vehicles(id),

    location            GEOGRAPHY(POINT, 4326) NOT NULL,
    latitude            DECIMAL(10, 8) NOT NULL,
    longitude           DECIMAL(11, 8) NOT NULL,
    altitude            DECIMAL(8, 2),

    speed               DECIMAL(6, 2),  -- km/h
    heading             DECIMAL(5, 2),  -- 方位角 0-360
    accuracy            DECIMAL(6, 2),  -- GPS精度 (m)

    -- デバイス情報
    device_id           VARCHAR(100),
    battery_level       INTEGER,  -- %

    -- 状態推定
    estimated_state     VARCHAR(20),
    -- 'loading', 'loaded_moving', 'unloading', 'empty_moving', 'idle'

    -- 生データ
    raw_data            JSONB,

    PRIMARY KEY (time, vehicle_id)
);

-- TimescaleDBのhypertable化
SELECT create_hypertable('gps_positions', 'time');

-- 空間インデックス
CREATE INDEX idx_gps_location ON gps_positions USING GIST(location);
CREATE INDEX idx_gps_vehicle ON gps_positions(vehicle_id, time DESC);

-- データ保持ポリシー（5年後に自動削除）
SELECT add_retention_policy('gps_positions', INTERVAL '5 years');

-- 圧縮ポリシー（7日以前のデータを圧縮）
ALTER TABLE gps_positions SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'vehicle_id'
);
SELECT add_compression_policy('gps_positions', INTERVAL '7 days');
```

### vehicle_cycles (運搬サイクル)
```sql
CREATE TABLE vehicle_cycles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id          UUID NOT NULL REFERENCES vehicles(id),
    site_id             UUID NOT NULL REFERENCES sites(id),
    cycle_date          DATE NOT NULL,
    cycle_number        INTEGER NOT NULL,  -- 当日の何回目

    -- 開始・終了
    start_time          TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time            TIMESTAMP WITH TIME ZONE,
    total_duration      INTERVAL,  -- 総所要時間

    -- 積込み
    loading_location    GEOGRAPHY(POINT, 4326),
    loading_start       TIMESTAMP WITH TIME ZONE,
    loading_end         TIMESTAMP WITH TIME ZONE,
    loading_duration    INTERVAL,

    -- 運搬（積載）
    loaded_moving_start TIMESTAMP WITH TIME ZONE,
    loaded_moving_end   TIMESTAMP WITH TIME ZONE,
    loaded_duration     INTERVAL,
    loaded_distance     DECIMAL(8, 2),  -- km

    -- 荷降ろし
    unloading_location  GEOGRAPHY(POINT, 4326),
    unloading_start     TIMESTAMP WITH TIME ZONE,
    unloading_end       TIMESTAMP WITH TIME ZONE,
    unloading_duration  INTERVAL,

    -- 運搬（空車）
    empty_moving_start  TIMESTAMP WITH TIME ZONE,
    empty_moving_end    TIMESTAMP WITH TIME ZONE,
    empty_duration      INTERVAL,
    empty_distance      DECIMAL(8, 2),  -- km

    -- 待機
    waiting_duration    INTERVAL,

    -- 運搬量
    volume              DECIMAL(8, 2),  -- m³

    -- 状態
    status              VARCHAR(20) DEFAULT 'in_progress',
    -- 'in_progress', 'completed', 'aborted'

    -- 異常検知
    has_anomaly         BOOLEAN DEFAULT FALSE,
    anomaly_type        VARCHAR(50),
    -- 'long_waiting', 'speed_violation', 'route_deviation'

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(vehicle_id, cycle_date, cycle_number)
);

CREATE INDEX idx_cycles_vehicle ON vehicle_cycles(vehicle_id);
CREATE INDEX idx_cycles_site ON vehicle_cycles(site_id);
CREATE INDEX idx_cycles_date ON vehicle_cycles(cycle_date);
CREATE INDEX idx_cycles_status ON vehicle_cycles(status);
```

### geofences (ジオフェンス定義)
```sql
CREATE TABLE geofences (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id             UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    name                VARCHAR(100) NOT NULL,
    fence_type          VARCHAR(50) NOT NULL,
    -- 'loading_zone', 'unloading_zone', 'waiting_area', 'restricted_area'

    geometry            GEOGRAPHY(POLYGON, 4326) NOT NULL,

    -- アラート設定
    alert_on_entry      BOOLEAN DEFAULT FALSE,
    alert_on_exit       BOOLEAN DEFAULT FALSE,
    alert_on_dwell      BOOLEAN DEFAULT FALSE,
    dwell_threshold     INTERVAL,  -- 滞留判定時間

    is_active           BOOLEAN DEFAULT TRUE,

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_geofences_site ON geofences(site_id);
CREATE INDEX idx_geofences_geometry ON geofences USING GIST(geometry);
```

---

## 4. アラート・通知

### alert_rules (アラートルール定義)
```sql
CREATE TABLE alert_rules (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_code           VARCHAR(50) UNIQUE NOT NULL,
    rule_name           VARCHAR(200) NOT NULL,
    rule_type           VARCHAR(50) NOT NULL,
    -- 'schedule_delay', 'speed_violation', 'vehicle_dwell',
    -- 'low_productivity', 'weather_warning', 'water_level'

    description         TEXT,

    -- 条件（JSON形式）
    condition_config    JSONB NOT NULL,
    -- 例: {"threshold": 60, "unit": "km/h"}

    -- アラートレベル
    severity            VARCHAR(20) NOT NULL DEFAULT 'warning',
    -- 'info', 'warning', 'error', 'critical'

    -- 適用範囲
    scope               VARCHAR(20) DEFAULT 'all',
    -- 'all', 'site', 'vehicle', 'task'
    site_id             UUID REFERENCES sites(id),
    vehicle_id          UUID REFERENCES vehicles(id),
    task_id             UUID REFERENCES site_tasks(id),

    -- 通知設定
    notification_enabled BOOLEAN DEFAULT TRUE,
    notification_channels JSONB,
    -- ["email", "line", "dashboard"]

    is_active           BOOLEAN DEFAULT TRUE,

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_alert_rules_type ON alert_rules(rule_type);
CREATE INDEX idx_alert_rules_active ON alert_rules(is_active);
```

### alerts (アラート発生履歴)
```sql
CREATE TABLE alerts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id             UUID REFERENCES alert_rules(id),

    alert_type          VARCHAR(50) NOT NULL,
    severity            VARCHAR(20) NOT NULL,
    title               VARCHAR(200) NOT NULL,
    message             TEXT NOT NULL,

    -- 関連エンティティ
    site_id             UUID REFERENCES sites(id),
    vehicle_id          UUID REFERENCES vehicles(id),
    task_id             UUID REFERENCES site_tasks(id),
    worker_id           UUID REFERENCES workers(id),

    -- 発生情報
    occurred_at         TIMESTAMP WITH TIME ZONE NOT NULL,
    location            GEOGRAPHY(POINT, 4326),

    -- 詳細データ
    context_data        JSONB,

    -- 対応状況
    status              VARCHAR(20) DEFAULT 'new',
    -- 'new', 'acknowledged', 'in_progress', 'resolved', 'dismissed'

    acknowledged_at     TIMESTAMP WITH TIME ZONE,
    acknowledged_by     UUID,
    resolved_at         TIMESTAMP WITH TIME ZONE,
    resolved_by         UUID,
    resolution_notes    TEXT,

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_alerts_occurred ON alerts(occurred_at DESC);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_site ON alerts(site_id);
CREATE INDEX idx_alerts_vehicle ON alerts(vehicle_id);
CREATE INDEX idx_alerts_severity ON alerts(severity);
```

### notifications (通知履歴)
```sql
CREATE TABLE notifications (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id            UUID REFERENCES alerts(id) ON DELETE CASCADE,

    channel             VARCHAR(20) NOT NULL,
    -- 'email', 'line', 'push', 'sms'

    recipient_type      VARCHAR(20) NOT NULL,
    -- 'user', 'role', 'group'
    recipient_id        UUID,
    recipient_address   VARCHAR(200),  -- email, phone, LINE user ID

    subject             VARCHAR(200),
    body                TEXT NOT NULL,

    -- 送信状況
    status              VARCHAR(20) DEFAULT 'pending',
    -- 'pending', 'sent', 'failed', 'read'

    sent_at             TIMESTAMP WITH TIME ZONE,
    read_at             TIMESTAMP WITH TIME ZONE,

    error_message       TEXT,
    retry_count         INTEGER DEFAULT 0,

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_notifications_alert ON notifications(alert_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_sent ON notifications(sent_at);
```

---

## 5. シミュレーション

### simulations (シミュレーション設定)
```sql
CREATE TABLE simulations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id             UUID NOT NULL REFERENCES sites(id),
    task_id             UUID REFERENCES site_tasks(id),

    simulation_name     VARCHAR(200) NOT NULL,
    simulation_type     VARCHAR(50) NOT NULL,
    -- 'cycle_time', 'resource_allocation', 'schedule_optimization'

    -- 入力パラメータ
    parameters          JSONB NOT NULL,
    /* 例:
    {
        "excavation_volume": 5000,
        "truck_capacity": 10,
        "loading_time": 5,
        "transport_distance": 3.5,
        "unloading_time": 3,
        "trucks_count": 5
    }
    */

    -- 実行情報
    status              VARCHAR(20) DEFAULT 'pending',
    -- 'pending', 'running', 'completed', 'failed'

    started_at          TIMESTAMP WITH TIME ZONE,
    completed_at        TIMESTAMP WITH TIME ZONE,
    duration            INTERVAL,

    error_message       TEXT,

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by          UUID
);

CREATE INDEX idx_simulations_site ON simulations(site_id);
CREATE INDEX idx_simulations_type ON simulations(simulation_type);
CREATE INDEX idx_simulations_status ON simulations(status);
```

### simulation_results (シミュレーション結果)
```sql
CREATE TABLE simulation_results (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id       UUID NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,

    -- 結果データ
    results             JSONB NOT NULL,
    /* 例:
    {
        "total_cycles": 50,
        "average_cycle_time": 45,
        "total_volume": 500,
        "efficiency_rate": 85.5,
        "bottleneck": "loading",
        "recommendations": ["重機を1台追加", "待機エリア拡大"]
    }
    */

    -- 時系列データ
    timeline_data       JSONB,
    -- 時間ごとの推移データ

    -- 比較用実績データ
    actual_data         JSONB,
    variance            JSONB,  -- 予実差異

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sim_results_simulation ON simulation_results(simulation_id);
```

---

## 6. ユーザー・権限管理

### users (ユーザー)
```sql
CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username            VARCHAR(50) UNIQUE NOT NULL,
    email               VARCHAR(100) UNIQUE NOT NULL,
    password_hash       VARCHAR(255) NOT NULL,

    full_name           VARCHAR(100) NOT NULL,
    phone_number        VARCHAR(20),

    role                VARCHAR(20) NOT NULL DEFAULT 'viewer',
    -- 'admin', 'manager', 'supervisor', 'operator', 'viewer'

    -- 所属
    company_name        VARCHAR(100),
    department          VARCHAR(100),

    -- 権限
    permissions         JSONB,
    -- ["sites:read", "sites:write", "vehicles:read"]

    -- アクセス可能な現場
    accessible_sites    UUID[],

    -- アカウント状態
    is_active           BOOLEAN DEFAULT TRUE,
    is_email_verified   BOOLEAN DEFAULT FALSE,

    -- 最終ログイン
    last_login_at       TIMESTAMP WITH TIME ZONE,
    last_login_ip       INET,

    -- パスワードリセット
    reset_token         VARCHAR(255),
    reset_token_expires TIMESTAMP WITH TIME ZONE,

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);
```

### refresh_tokens (リフレッシュトークン)
```sql
CREATE TABLE refresh_tokens (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token               VARCHAR(255) UNIQUE NOT NULL,

    expires_at          TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked          BOOLEAN DEFAULT FALSE,

    device_info         JSONB,
    ip_address          INET,

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);
```

---

## 7. システム管理

### audit_logs (操作ログ)
```sql
CREATE TABLE audit_logs (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             UUID REFERENCES users(id),

    action              VARCHAR(50) NOT NULL,
    -- 'create', 'update', 'delete', 'login', 'logout'

    entity_type         VARCHAR(50),
    entity_id           UUID,

    changes             JSONB,  -- 変更内容

    ip_address          INET,
    user_agent          TEXT,

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_created ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
```

---

## 8. 集計ビュー（マテリアライズドビュー）

### daily_site_summary (現場日次サマリー)
```sql
CREATE MATERIALIZED VIEW daily_site_summary AS
SELECT
    s.id AS site_id,
    s.site_name,
    d.report_date,
    d.daily_volume,
    d.cumulative_volume,
    s.planned_volume,
    ROUND((d.cumulative_volume / NULLIF(s.planned_volume, 0) * 100)::numeric, 2) AS progress_rate,
    COUNT(DISTINCT ra.vehicle_id) AS vehicle_count,
    COUNT(DISTINCT ra.worker_id) AS worker_count,
    COUNT(DISTINCT vc.id) AS total_cycles,
    AVG(EXTRACT(EPOCH FROM vc.total_duration) / 60) AS avg_cycle_time_minutes
FROM sites s
LEFT JOIN site_daily_reports d ON s.id = d.site_id
LEFT JOIN resource_assignments ra ON s.id = ra.site_id AND ra.assignment_date = d.report_date
LEFT JOIN vehicle_cycles vc ON s.id = vc.site_id AND vc.cycle_date = d.report_date
GROUP BY s.id, s.site_name, d.report_date, d.daily_volume, d.cumulative_volume, s.planned_volume;

CREATE UNIQUE INDEX idx_daily_summary_pk ON daily_site_summary(site_id, report_date);
CREATE INDEX idx_daily_summary_date ON daily_site_summary(report_date DESC);

-- 定期更新（毎日深夜）
```

### vehicle_performance_summary (車両パフォーマンスサマリー)
```sql
CREATE MATERIALIZED VIEW vehicle_performance_summary AS
SELECT
    v.id AS vehicle_id,
    v.vehicle_code,
    v.vehicle_name,
    DATE_TRUNC('day', vc.cycle_date) AS summary_date,
    COUNT(*) AS total_cycles,
    SUM(vc.volume) AS total_volume,
    AVG(EXTRACT(EPOCH FROM vc.total_duration) / 60) AS avg_cycle_time,
    AVG(EXTRACT(EPOCH FROM vc.loading_duration) / 60) AS avg_loading_time,
    AVG(EXTRACT(EPOCH FROM vc.unloading_duration) / 60) AS avg_unloading_time,
    AVG(EXTRACT(EPOCH FROM vc.waiting_duration) / 60) AS avg_waiting_time,
    SUM(vc.loaded_distance + vc.empty_distance) AS total_distance
FROM vehicles v
JOIN vehicle_cycles vc ON v.id = vc.vehicle_id
WHERE vc.status = 'completed'
GROUP BY v.id, v.vehicle_code, v.vehicle_name, DATE_TRUNC('day', vc.cycle_date);

CREATE UNIQUE INDEX idx_vehicle_perf_pk ON vehicle_performance_summary(vehicle_id, summary_date);
CREATE INDEX idx_vehicle_perf_date ON vehicle_performance_summary(summary_date DESC);
```

---

## 9. 初期データ・マスタデータ

### 地点タイプマスタ
```sql
CREATE TABLE location_types (
    code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

INSERT INTO location_types VALUES
('loading', '積込み地点', 'バックホウによる積込み場所'),
('unloading', '荷降ろし地点', 'ダンプが土砂を降ろす場所'),
('waiting', '待機場所', '車両の待機エリア'),
('fuel', '給油所', '給油場所'),
('maintenance', '整備場', '車両整備場所');
```

---

## 10. パフォーマンス最適化

### パーティショニング戦略
```sql
-- gps_positionsはTimescaleDBで自動パーティション
-- alertsは月次パーティション
CREATE TABLE alerts_2026_01 PARTITION OF alerts
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

### インデックス最適化
- B-Tree: 等価検索、範囲検索
- GiST: 空間検索（PostGIS）
- GIN: JSONB検索
- BRIN: 大量の時系列データ（TimescaleDB）

---

**作成日**: 2026-01-18
**バージョン**: 1.0
