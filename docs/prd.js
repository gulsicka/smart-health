<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>SmartHealth PRD — Part A</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #f4f6f9;
    color: #1a1a1a;
    padding: 40px 24px;
    font-size: 14px;
    line-height: 1.6;
  }

  /* ── Cover ── */
  .cover {
    background: linear-gradient(135deg, #1a237e 0%, #1565c0 60%, #0288d1 100%);
    border-radius: 16px;
    padding: 52px 48px;
    margin-bottom: 36px;
    color: #fff;
  }
  .cover-tag {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.6);
    margin-bottom: 12px;
  }
  .cover h1 {
    font-size: 36px;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin-bottom: 6px;
  }
  .cover-sub {
    font-size: 15px;
    color: rgba(255,255,255,0.75);
    margin-bottom: 28px;
  }
  .cover-meta {
    display: flex;
    gap: 28px;
    font-size: 12px;
    color: rgba(255,255,255,0.7);
    border-top: 1px solid rgba(255,255,255,0.2);
    padding-top: 20px;
    margin-top: 20px;
  }
  .cover-meta span strong { color: #fff; display: block; font-size: 13px; }

  /* ── Sections ── */
  .section {
    background: #fff;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    padding: 32px 36px;
    margin-bottom: 24px;
  }
  .section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
    padding-bottom: 14px;
    border-bottom: 2px solid #e8f0fe;
  }
  .section-num {
    background: #1565c0;
    color: #fff;
    font-size: 12px;
    font-weight: 700;
    width: 28px;
    height: 28px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .section-title {
    font-size: 17px;
    font-weight: 700;
    color: #1a237e;
  }

  /* ── Text ── */
  p { margin-bottom: 12px; color: #374151; }
  p:last-child { margin-bottom: 0; }

  /* ── Service grid ── */
  .service-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 12px;
    margin-top: 16px;
  }
  .service-card {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 14px 16px;
    border-left: 4px solid #1565c0;
  }
  .service-card .svc-name {
    font-weight: 700;
    font-size: 13px;
    color: #1565c0;
    margin-bottom: 4px;
  }
  .service-card .svc-desc { font-size: 12px; color: #6b7280; }

  /* ── Use cases ── */
  .uc-list { display: flex; flex-direction: column; gap: 14px; }
  .uc-item {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 14px 16px;
  }
  .uc-item .uc-title {
    font-weight: 700;
    font-size: 13px;
    color: #1a237e;
    margin-bottom: 8px;
  }
  .uc-item ul { padding-left: 18px; }
  .uc-item ul li { font-size: 13px; color: #374151; margin-bottom: 4px; }

  /* ── FR subsections ── */
  .fr-group { margin-bottom: 22px; }
  .fr-group-title {
    font-size: 13px;
    font-weight: 700;
    color: #1565c0;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid #e8f0fe;
  }
  .fr-list { display: flex; flex-direction: column; gap: 6px; }
  .fr-item { display: flex; gap: 10px; align-items: flex-start; }
  .fr-id {
    font-size: 11px;
    font-weight: 700;
    color: #fff;
    background: #1565c0;
    padding: 2px 7px;
    border-radius: 4px;
    flex-shrink: 0;
    margin-top: 1px;
  }
  .fr-id.timescale { background: #2e7d32; }
  .fr-id.orphan    { background: #6a1b9a; }
  .fr-text { font-size: 13px; color: #374151; }

  /* ── Tables ── */
  table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px; }
  th {
    background: #1a237e;
    color: #fff;
    padding: 10px 12px;
    text-align: left;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.3px;
  }
  td { padding: 9px 12px; border-bottom: 1px solid #f0f0f0; color: #374151; vertical-align: top; }
  tr:nth-child(even) td { background: #f8faff; }
  tr:hover td { background: #eef2ff; }
  .badge {
    display: inline-block;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    background: #e8f0fe;
    color: #1565c0;
  }
  .badge.green  { background: #e8f5e9; color: #2e7d32; }
  .badge.purple { background: #f3e5f5; color: #6a1b9a; }
  .badge.orange { background: #fff3e0; color: #e65100; }

  /* ── Timeline ── */
  .timeline { display: flex; flex-direction: column; gap: 16px; margin-top: 8px; }
  .tl-item { display: flex; gap: 16px; }
  .tl-dot {
    flex-shrink: 0;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #1565c0;
    margin-top: 5px;
    position: relative;
  }
  .tl-dot::after {
    content: '';
    position: absolute;
    top: 12px;
    left: 5px;
    width: 2px;
    height: calc(100% + 8px);
    background: #c5cae9;
  }
  .tl-item:last-child .tl-dot::after { display: none; }
  .tl-content {}
  .tl-week { font-size: 12px; font-weight: 700; color: #1565c0; margin-bottom: 4px; }
  .tl-date { font-size: 11px; color: #9ca3af; margin-bottom: 6px; }
  .tl-content ul { padding-left: 16px; }
  .tl-content ul li { font-size: 13px; color: #374151; margin-bottom: 3px; }

  /* ── NFR chips ── */
  .nfr-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 10px; margin-top: 4px; }
  .nfr-item {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 12px 14px;
    display: flex;
    gap: 10px;
  }
  .nfr-id {
    font-size: 11px;
    font-weight: 700;
    color: #1565c0;
    flex-shrink: 0;
    min-width: 52px;
  }
  .nfr-cat { font-size: 11px; font-weight: 700; color: #374151; margin-bottom: 2px; }
  .nfr-text { font-size: 12px; color: #6b7280; }
</style>
</head>
<body>

<!-- Cover -->
<div class="cover">
  <div class="cover-tag">Product Requirements Document</div>
  <h1>SmartHealth</h1>
  <div class="cover-sub">Intelligent Healthcare Operations Platform — Part A</div>
  <div class="cover-meta">
    <span><strong>Author</strong>Gulsicka</span>
    <span><strong>Date</strong>July 2026</span>
    <span><strong>Status</strong>In Progress</span>
    <span><strong>Version</strong>1.2 (TimescaleDB)</span>
  </div>
</div>

<!-- 1. Product Overview -->
<div class="section">
  <div class="section-header">
    <div class="section-num">1</div>
    <div class="section-title">Product Overview</div>
  </div>
  <p>SmartHealth is a microservices-based healthcare operations platform built with Python and FastAPI. It manages the full lifecycle of healthcare operations — from user onboarding and role management through to appointment booking, visit tracking, real-time analytics, and async notifications.</p>
  <p>The system is designed around independent, deployable services that communicate via REST APIs, Kafka events, and Temporal workflows, with full observability through Prometheus, Grafana, and Jaeger.</p>

  <div class="service-grid">
    <div class="service-card">
      <div class="svc-name">auth-service</div>
      <div class="svc-desc">JWT authentication, RBAC, Redis token blacklisting</div>
    </div>
    <div class="service-card">
      <div class="svc-name">patient-service</div>
      <div class="svc-desc">Patient profile management, Kafka event publishing</div>
    </div>
    <div class="service-card">
      <div class="svc-name">provider-service</div>
      <div class="svc-desc">Provider profiles, clinics, departments, availability scheduling</div>
    </div>
    <div class="service-card">
      <div class="svc-name">appointment-service</div>
      <div class="svc-desc">Booking, status state machine, Kafka event publishing</div>
    </div>
    <div class="service-card">
      <div class="svc-name">analytics-service</div>
      <div class="svc-desc">Kafka consumer, Redis counters, TimescaleDB hypertable event store, filterable analytics API</div>
    </div>
    <div class="service-card">
      <div class="svc-name">notification-service</div>
      <div class="svc-desc">Celery worker, persists notifications to Postgres via RabbitMQ</div>
    </div>
    <div class="service-card">
      <div class="svc-name">temporal-workflow</div>
      <div class="svc-desc">Temporal worker running all workflow and compensation logic</div>
    </div>
  </div>
</div>

<!-- 2. Key Use Cases -->
<div class="section">
  <div class="section-header">
    <div class="section-num">2</div>
    <div class="section-title">Key Use Cases</div>
  </div>
  <div class="uc-list">

    <div class="uc-item">
      <div class="uc-title">UC-01 · User Registration &amp; Role Assignment</div>
      <ul>
        <li>Admin registers a new user with roles (patient, provider, fd_staff, admin)</li>
        <li>Temporal UserCreationWorkflow creates patient/provider records in respective services</li>
        <li>On success: user activated, success notification dispatched via RabbitMQ</li>
        <li>On failure: compensation runs — provider deleted → patient deleted → user deleted → failure notification sent</li>
      </ul>
    </div>

    <div class="uc-item">
      <div class="uc-title">UC-02 · User Role Update</div>
      <ul>
        <li>Admin assigns new roles to an existing user via PUT /users/{id}</li>
        <li>Temporal UpdateUserWorkflow creates new patient/provider records for the added roles</li>
        <li>On failure: newly assigned roles removed, failure notification sent</li>
      </ul>
    </div>

    <div class="uc-item">
      <div class="uc-title">UC-03 · Provider Availability Setup</div>
      <ul>
        <li>Admin configures a provider's working schedule across clinics</li>
        <li>System generates availability slots for the next 30 days</li>
        <li>Patients can query booked slots before requesting an appointment</li>
      </ul>
    </div>

    <div class="uc-item">
      <div class="uc-title">UC-04 · Appointment Booking</div>
      <ul>
        <li>Patient or FD Staff submits a booking request via POST /appointments</li>
        <li>Temporal AppointmentValidationWorkflow validates entities, checks availability, checks for conflicts</li>
        <li>On success: appointment created, Kafka event published, booking notification sent</li>
        <li>On failure: failed_workflow activity called, failure notification sent</li>
      </ul>
    </div>

    <div class="uc-item">
      <div class="uc-title">UC-05 · Visit Lifecycle Management</div>
      <ul>
        <li>Staff/provider transitions appointment through: requested → confirmed → checked_in → in_progress → completed</li>
        <li>Each transition is role-restricted (fd_staff checks in, provider marks in_progress)</li>
        <li>No-show and cancellation are supported at appropriate stages</li>
        <li>Every status change publishes a Kafka event consumed by analytics-service</li>
      </ul>
    </div>

    <div class="uc-item">
      <div class="uc-title">UC-06 · Real-Time &amp; Historical Analytics</div>
      <ul>
        <li>Analytics-service consumes Kafka events from appointment-service and patient-service</li>
        <li>Tracks: total appointments, completions, cancellations, daily breakdowns, cancellation rate (Redis)</li>
        <li>Tracks total unique patients via patient.created Kafka events</li>
        <li>Tracks average wait time: time between checked_in and in_progress per appointment</li>
        <li>Persists all appointment events to TimescaleDB hypertable for historical, time-bucketed filtering by clinic, provider, and event type</li>
      </ul>
    </div>

    <div class="uc-item">
      <div class="uc-title">UC-07 · Notifications</div>
      <ul>
        <li>Notifications dispatched via Celery tasks over RabbitMQ, persisted to notification-db</li>
        <li>Covers: user_created, user_creation_failed, role_updated, role_update_failed, booking_created, booking_failed, booking_confirmation, appointment_cancellation</li>
      </ul>
    </div>

    <div class="uc-item">
      <div class="uc-title">UC-08 · System Observability</div>
      <ul>
        <li>Prometheus scrapes /metrics from all 5 FastAPI services</li>
        <li>Grafana dashboards visualise request rates, p99 latency, and error rates</li>
        <li>All services push OTLP traces to Jaeger on port 4317 for distributed tracing</li>
      </ul>
    </div>

    <div class="uc-item">
      <div class="uc-title">UC-09 · Orphan Data &amp; Cascade Cleanup</div>
      <ul>
        <li>Admin deletes a user — auth-service soft-deletes the user (status = deleted) and publishes user.deleted to users.events Kafka topic</li>
        <li>patient-service and provider-service consume user.deleted, set is_deleted = true on matching records, and publish patient.deleted / provider.deleted events</li>
        <li>appointment-service consumes patient.deleted and provider.deleted and cancels all active (requested, confirmed, checked_in) appointments</li>
        <li>auth-service consumes patient.deleted and provider.deleted and removes the corresponding role from the user — user is not deleted</li>
        <li>Admin deletes a patient record directly — patient soft-deleted, patient.deleted published; auth removes patient role; appointments cancelled</li>
        <li>Admin deletes a provider record directly — provider soft-deleted, provider.deleted published; auth removes provider role; appointments cancelled</li>
        <li>Medical records are never hard-deleted; is_deleted flag preserves data for audit and legal compliance</li>
      </ul>
    </div>

  </div>
</div>

<!-- 3. Functional Requirements -->
<div class="section">
  <div class="section-header">
    <div class="section-num">3</div>
    <div class="section-title">Functional Requirements</div>
  </div>

  <div class="fr-group">
    <div class="fr-group-title">Authentication &amp; Authorisation</div>
    <div class="fr-list">
      <div class="fr-item"><span class="fr-id">FR-01</span><span class="fr-text">JWT-based authentication with configurable expiry</span></div>
      <div class="fr-item"><span class="fr-id">FR-02</span><span class="fr-text">Role-based access control: admin, patient, provider, fd_staff</span></div>
      <div class="fr-item"><span class="fr-id">FR-03</span><span class="fr-text">Redis-based token blacklisting on logout (jti key with TTL)</span></div>
      <div class="fr-item"><span class="fr-id">FR-04</span><span class="fr-text">Login blocked for users with status: pending</span></div>
    </div>
  </div>

  <div class="fr-group">
    <div class="fr-group-title">User Management</div>
    <div class="fr-list">
      <div class="fr-item"><span class="fr-id">FR-05</span><span class="fr-text">Create user with name, email, number, password, and one or more roles</span></div>
      <div class="fr-item"><span class="fr-id">FR-06</span><span class="fr-text">User status set to pending on creation; activated by Temporal workflow</span></div>
      <div class="fr-item"><span class="fr-id">FR-07</span><span class="fr-text">Update user fields and roles via PUT /users/{id}</span></div>
      <div class="fr-item"><span class="fr-id">FR-08</span><span class="fr-text">Remove roles from a user via PATCH /users/{id}/remove_roles</span></div>
      <div class="fr-item"><span class="fr-id">FR-09</span><span class="fr-text">Temporal UserCreationWorkflow with rollback: delete provider → patient → user on failure</span></div>
      <div class="fr-item"><span class="fr-id">FR-10</span><span class="fr-text">Temporal UpdateUserWorkflow with rollback: remove newly assigned roles on failure</span></div>
    </div>
  </div>

  <div class="fr-group">
    <div class="fr-group-title">Patient &amp; Provider Management</div>
    <div class="fr-list">
      <div class="fr-item"><span class="fr-id">FR-11</span><span class="fr-text">Patient profile creation linked to user_id; consistency enforced via JWT (no cross-DB FK)</span></div>
      <div class="fr-item"><span class="fr-id">FR-12</span><span class="fr-text">Provider profile with department assignment</span></div>
      <div class="fr-item"><span class="fr-id">FR-13</span><span class="fr-text">Clinic and department management</span></div>
      <div class="fr-item"><span class="fr-id">FR-14</span><span class="fr-text">Provider availability setup — generates slots for next 30 days</span></div>
      <div class="fr-item"><span class="fr-id">FR-15</span><span class="fr-text">Query booked slots by provider, date, and clinic</span></div>
    </div>
  </div>

  <div class="fr-group">
    <div class="fr-group-title">Appointment Booking &amp; Visit Lifecycle</div>
    <div class="fr-list">
      <div class="fr-item"><span class="fr-id">FR-16</span><span class="fr-text">Appointment booking via Temporal workflow (entity validation, availability check, conflict check)</span></div>
      <div class="fr-item"><span class="fr-id">FR-17</span><span class="fr-text">Conflict prevention: checks overlapping active appointments for the provider in the time slot</span></div>
      <div class="fr-item"><span class="fr-id">FR-18</span><span class="fr-text">Appointment status state machine with enforced valid transitions</span></div>
      <div class="fr-item"><span class="fr-id">FR-19</span><span class="fr-text">Role-restricted status transitions (e.g. only patient/admin can cancel)</span></div>
      <div class="fr-item"><span class="fr-id">FR-20</span><span class="fr-text">Kafka event published on appointment created and on every status update</span></div>
    </div>
  </div>

  <div class="fr-group">
    <div class="fr-group-title">Analytics</div>
    <div class="fr-list">
      <div class="fr-item"><span class="fr-id">FR-21</span><span class="fr-text">Kafka consumer with event deduplication (Redis event_id key, 24h TTL)</span></div>
      <div class="fr-item"><span class="fr-id">FR-22</span><span class="fr-text">Redis counters: total appointments, completions, cancellations, daily breakdowns</span></div>
      <div class="fr-item"><span class="fr-id">FR-23</span><span class="fr-text">Total unique patients tracked via patient.created Kafka events from patient-service</span></div>
      <div class="fr-item"><span class="fr-id">FR-24</span><span class="fr-text">Average wait time: duration between checked_in and in_progress per appointment</span></div>
      <div class="fr-item"><span class="fr-id">FR-25</span><span class="fr-text">GET /analytics endpoint returning all real-time metrics (Redis counters)</span></div>
      <div class="fr-item"><span class="fr-id timescale">FR-34</span><span class="fr-text">GET /analytics/filter endpoint — filter appointment events by date range, clinic, and provider, grouped into daily time buckets via TimescaleDB time_bucket()</span></div>
      <div class="fr-item"><span class="fr-id timescale">FR-35</span><span class="fr-text">GET /analytics/total-created endpoint — count total events of a given event type within a date range (TimescaleDB)</span></div>
    </div>
  </div>

  <div class="fr-group">
    <div class="fr-group-title">Notifications</div>
    <div class="fr-list">
      <div class="fr-item"><span class="fr-id">FR-26</span><span class="fr-text">Celery tasks dispatched via RabbitMQ from temporal-workflow and analytics-service</span></div>
      <div class="fr-item"><span class="fr-id">FR-27</span><span class="fr-text">8 notification task types covering user lifecycle and appointment lifecycle events</span></div>
      <div class="fr-item"><span class="fr-id">FR-28</span><span class="fr-text">All notifications persisted to notification-db (Postgres)</span></div>
      <div class="fr-item"><span class="fr-id">FR-29</span><span class="fr-text">Notification failures isolated via inner try/except — do not trigger workflow rollback</span></div>
    </div>
  </div>

  <div class="fr-group">
    <div class="fr-group-title">Orphan Data &amp; Cascade Cleanup</div>
    <div class="fr-list">
      <div class="fr-item"><span class="fr-id orphan">FR-30</span><span class="fr-text">Soft delete on users: DELETE /users/{id} sets status = deleted and publishes user.deleted to users.events Kafka topic</span></div>
      <div class="fr-item"><span class="fr-id orphan">FR-31</span><span class="fr-text">Soft delete on patients and providers: is_deleted flag set to true when a user.deleted event is consumed; records are never hard-deleted</span></div>
      <div class="fr-item"><span class="fr-id orphan">FR-32</span><span class="fr-text">Role cleanup on record deletion: when a patient or provider record is deleted (directly or via cascade), the corresponding role is removed from the user in auth-service; user is not deleted</span></div>
      <div class="fr-item"><span class="fr-id orphan">FR-33</span><span class="fr-text">Appointment cascade cancellation: appointment-service consumes patient.deleted and provider.deleted events and cancels all active appointments for that patient or provider</span></div>
    </div>
  </div>
</div>

<!-- 4. Non-Functional Requirements -->
<div class="section">
  <div class="section-header">
    <div class="section-num">4</div>
    <div class="section-title">Non-Functional Requirements</div>
  </div>
  <div class="nfr-grid">
    <div class="nfr-item"><div class="nfr-id">NFR-01</div><div><div class="nfr-cat">Scalability</div><div class="nfr-text">Each service is independently containerised and horizontally scalable</div></div></div>
    <div class="nfr-item"><div class="nfr-id">NFR-02</div><div><div class="nfr-cat">Fault Tolerance</div><div class="nfr-text">Temporal workflows retry failed activities and run compensation on unrecoverable failure</div></div></div>
    <div class="nfr-item"><div class="nfr-id">NFR-03</div><div><div class="nfr-cat">Decoupling</div><div class="nfr-text">Services communicate via Kafka events and Temporal; no direct HTTP calls for async flows</div></div></div>
    <div class="nfr-item"><div class="nfr-id">NFR-04</div><div><div class="nfr-cat">Data Isolation</div><div class="nfr-text">Each service owns its own Postgres database; no shared DB or cross-DB foreign keys</div></div></div>
    <div class="nfr-item"><div class="nfr-id">NFR-05</div><div><div class="nfr-cat">Security</div><div class="nfr-text">All endpoints require JWT; roles enforced per route; tokens blacklisted on logout via Redis</div></div></div>
    <div class="nfr-item"><div class="nfr-id">NFR-06</div><div><div class="nfr-cat">Observability</div><div class="nfr-text">Prometheus scrapes /metrics from all services; Grafana dashboards for request rate, latency, errors</div></div></div>
    <div class="nfr-item"><div class="nfr-id">NFR-07</div><div><div class="nfr-cat">Traceability</div><div class="nfr-text">OpenTelemetry spans pushed to Jaeger via OTLP; full distributed trace per request</div></div></div>
    <div class="nfr-item"><div class="nfr-id">NFR-08</div><div><div class="nfr-cat">Idempotency</div><div class="nfr-text">Kafka event deduplication via Redis; Temporal workflow IDs prevent duplicate workflows</div></div></div>
    <div class="nfr-item"><div class="nfr-id">NFR-09</div><div><div class="nfr-cat">Consistency</div><div class="nfr-text">Temporal saga pattern ensures cross-service consistency; compensation undoes partial state on failure</div></div></div>
    <div class="nfr-item"><div class="nfr-id">NFR-10</div><div><div class="nfr-cat">Portability</div><div class="nfr-text">Full system runs via docker compose up with a single command; no manual service setup required</div></div></div>
    <div class="nfr-item"><div class="nfr-id">NFR-11</div><div><div class="nfr-cat">Data Integrity</div><div class="nfr-text">Orphan data handled via Kafka event chains; soft deletes preserve medical records for audit and legal compliance; no cross-DB foreign keys required</div></div></div>
  </div>
</div>

<!-- 5. Delivery Timeline -->
<div class="section">
  <div class="section-header">
    <div class="section-num">5</div>
    <div class="section-title">Delivery Timeline &amp; Milestones</div>
  </div>

  <table style="margin-bottom:24px;">
    <thead>
      <tr>
        <th>Milestone</th><th>Week</th><th>Part</th><th>% Alloc.</th><th>Expected Start</th><th>Expected End</th><th>Actual Completion</th>
      </tr>
    </thead>
    <tbody>
      <tr><td rowspan="3"><strong>Part A</strong></td><td>Week 1</td><td>Part A</td><td>0.5</td><td>10-Jun-2026</td><td>24-Jun-2026</td><td><span class="badge green">21-Jun-2026</span></td></tr>
      <tr><td>Week 2</td><td>Part A</td><td>0.5</td><td>25-Jun-2026</td><td>09-Jul-2026</td><td><span class="badge green">09-Jul-2026</span></td></tr>
      <tr><td>Week 3</td><td>Part A</td><td>1</td><td>10-Jul-2026</td><td>17-Jul-2026</td><td><span class="badge green">16-Jul-2026</span></td></tr>
    </tbody>
  </table>

  <div class="timeline">
    <div class="tl-item">
      <div class="tl-dot"></div>
      <div class="tl-content">
        <div class="tl-week">Week 1 <span style="font-weight:400;color:#9ca3af;">— Actual: 21-Jun-2026</span></div>
        <ul>
          <li>auth-service: user registration, JWT login/logout, RBAC, Redis token blacklist</li>
          <li>patient-service: patient profile CRUD</li>
          <li>provider-service: provider, clinic, department management, availability scheduling</li>
          <li>Separate Postgres containers per service, Docker Compose networking</li>
        </ul>
      </div>
    </div>
    <div class="tl-item">
      <div class="tl-dot"></div>
      <div class="tl-content">
        <div class="tl-week">Week 2 <span style="font-weight:400;color:#9ca3af;">— Actual: 09-Jul-2026</span></div>
        <ul>
          <li>appointment-service: booking, status state machine, booked-slot query</li>
          <li>Temporal UserCreationWorkflow with rollback (patient/provider creation + compensation)</li>
          <li>Temporal AppointmentValidationWorkflow (validation, availability, conflict detection)</li>
          <li>Kafka integration: appointment.created and appointment.status_updated events</li>
          <li>analytics-service: Kafka consumer with deduplication, Redis counters, GET /analytics</li>
        </ul>
      </div>
    </div>
    <div class="tl-item">
      <div class="tl-dot"></div>
      <div class="tl-content">
        <div class="tl-week">Week 3 <span style="font-weight:400;color:#9ca3af;">— Actual: 16-Jul-2026</span></div>
        <ul>
          <li>Temporal UpdateUserWorkflow with role rollback</li>
          <li>Celery + RabbitMQ notification system with 8 notification task types</li>
          <li>patient-service Kafka producer: patient.created events for total_patients tracking</li>
          <li>Analytics: total_patients counter, average wait time metric</li>
          <li>Prometheus + Grafana: request rate, p99 latency, error rate dashboards</li>
          <li>OpenTelemetry + Jaeger: distributed tracing across all 5 services</li>
        </ul>
      </div>
    </div>
    <div class="tl-item">
      <div class="tl-dot" style="background:#6a1b9a;"></div>
      <div class="tl-content">
        <div class="tl-week" style="color:#6a1b9a;">Post Part A <span style="font-weight:400;color:#9ca3af;">— Actual: 21-Jul-2026</span></div>
        <ul>
          <li>Orphan data handling: soft delete on users, patients, and providers</li>
          <li>Kafka event chain: user.deleted → patient/provider soft delete → role removal → appointment cancellation</li>
          <li>auth-service Kafka consumer: removes patient/provider role on record deletion</li>
          <li>appointment-service Kafka consumer: cancels active appointments on patient/provider deletion</li>
          <li>is_deleted flag on patients and providers; status = deleted on users</li>
          <li>TimescaleDB analytics: appointment_events hypertable, time_bucket() filtered queries, GET /analytics/filter and GET /analytics/total-created endpoints</li>
        </ul>
      </div>
    </div>
  </div>
</div>

<!-- 6. Traceability Matrix -->
<div class="section">
  <div class="section-header">
    <div class="section-num">6</div>
    <div class="section-title">Traceability Matrix</div>
  </div>
  <p style="margin-bottom:14px;">Maps each functional requirement to its use case(s), delivering service(s), and delivery week.</p>
  <table>
    <thead>
      <tr><th>FR ID</th><th>Requirement Summary</th><th>Use Case(s)</th><th>Service(s)</th><th>Week</th></tr>
    </thead>
    <tbody>
      <tr><td><strong>FR-01</strong></td><td>JWT authentication</td><td>UC-01–08</td><td>auth-service</td><td><span class="badge">Week 1</span></td></tr>
      <tr><td><strong>FR-02</strong></td><td>Role-based access control</td><td>UC-01–08</td><td>auth-service</td><td><span class="badge">Week 1</span></td></tr>
      <tr><td><strong>FR-03</strong></td><td>Redis token blacklisting</td><td>UC-01–08</td><td>auth-service, Redis</td><td><span class="badge">Week 1</span></td></tr>
      <tr><td><strong>FR-04</strong></td><td>Login blocked for pending users</td><td>UC-01</td><td>auth-service</td><td><span class="badge">Week 1</span></td></tr>
      <tr><td><strong>FR-05</strong></td><td>Create user with roles</td><td>UC-01</td><td>auth-service</td><td><span class="badge">Week 1</span></td></tr>
      <tr><td><strong>FR-06</strong></td><td>User pending → active via Temporal</td><td>UC-01</td><td>auth-service, temporal-workflow</td><td><span class="badge">Week 3</span></td></tr>
      <tr><td><strong>FR-07</strong></td><td>Update user fields and roles</td><td>UC-02</td><td>auth-service</td><td><span class="badge">Week 2</span></td></tr>
      <tr><td><strong>FR-08</strong></td><td>Remove roles from user</td><td>UC-02</td><td>auth-service</td><td><span class="badge">Week 2</span></td></tr>
      <tr><td><strong>FR-09</strong></td><td>UserCreationWorkflow with rollback</td><td>UC-01</td><td>temporal-workflow, patient, provider</td><td><span class="badge">Week 2/3</span></td></tr>
      <tr><td><strong>FR-10</strong></td><td>UpdateUserWorkflow with rollback</td><td>UC-02</td><td>temporal-workflow, provider</td><td><span class="badge">Week 3</span></td></tr>
      <tr><td><strong>FR-11</strong></td><td>Patient profile creation</td><td>UC-01</td><td>patient-service</td><td><span class="badge">Week 1</span></td></tr>
      <tr><td><strong>FR-12</strong></td><td>Provider profile creation</td><td>UC-01,02</td><td>provider-service</td><td><span class="badge">Week 1</span></td></tr>
      <tr><td><strong>FR-13</strong></td><td>Clinic and department management</td><td>UC-03</td><td>provider-service</td><td><span class="badge">Week 1</span></td></tr>
      <tr><td><strong>FR-14</strong></td><td>Provider availability setup (30 days)</td><td>UC-03</td><td>provider-service</td><td><span class="badge">Week 1</span></td></tr>
      <tr><td><strong>FR-15</strong></td><td>Booked slot query</td><td>UC-04</td><td>appointment-service</td><td><span class="badge">Week 2</span></td></tr>
      <tr><td><strong>FR-16</strong></td><td>Appointment booking via Temporal</td><td>UC-04</td><td>temporal-workflow, appointment</td><td><span class="badge">Week 2</span></td></tr>
      <tr><td><strong>FR-17</strong></td><td>Conflict prevention</td><td>UC-04</td><td>temporal-workflow, appointment</td><td><span class="badge">Week 2</span></td></tr>
      <tr><td><strong>FR-18</strong></td><td>Appointment status state machine</td><td>UC-05</td><td>appointment-service</td><td><span class="badge">Week 2</span></td></tr>
      <tr><td><strong>FR-19</strong></td><td>Role-restricted status transitions</td><td>UC-05</td><td>appointment-service</td><td><span class="badge">Week 2</span></td></tr>
      <tr><td><strong>FR-20</strong></td><td>Kafka events on appointment changes</td><td>UC-05,06</td><td>appointment-service, Kafka</td><td><span class="badge">Week 2</span></td></tr>
      <tr><td><strong>FR-21</strong></td><td>Kafka consumer with deduplication</td><td>UC-06</td><td>analytics-service, Redis</td><td><span class="badge">Week 2</span></td></tr>
      <tr><td><strong>FR-22</strong></td><td>Redis counters (appts/completions)</td><td>UC-06</td><td>analytics-service, Redis</td><td><span class="badge">Week 2</span></td></tr>
      <tr><td><strong>FR-23</strong></td><td>Total patients via patient.created</td><td>UC-06</td><td>patient-service, analytics-service</td><td><span class="badge">Week 3</span></td></tr>
      <tr><td><strong>FR-24</strong></td><td>Average wait time metric</td><td>UC-06</td><td>analytics-service, Redis</td><td><span class="badge">Week 3</span></td></tr>
      <tr><td><strong>FR-25</strong></td><td>GET /analytics endpoint</td><td>UC-06</td><td>analytics-service</td><td><span class="badge">Week 2</span></td></tr>
      <tr><td><strong>FR-26</strong></td><td>Celery tasks via RabbitMQ</td><td>UC-07</td><td>temporal-workflow, analytics, notif</td><td><span class="badge">Week 3</span></td></tr>
      <tr><td><strong>FR-27</strong></td><td>8 notification task types</td><td>UC-07</td><td>notification-service</td><td><span class="badge">Week 3</span></td></tr>
      <tr><td><strong>FR-28</strong></td><td>Notifications persisted to DB</td><td>UC-07</td><td>notification-service</td><td><span class="badge">Week 3</span></td></tr>
      <tr><td><strong>FR-29</strong></td><td>Notification failure isolation</td><td>UC-07</td><td>temporal-workflow</td><td><span class="badge">Week 3</span></td></tr>
      <tr><td><strong>FR-30</strong></td><td>Soft delete user + publish user.deleted</td><td>UC-09</td><td>auth-service, Kafka</td><td><span class="badge purple">Post A</span></td></tr>
      <tr><td><strong>FR-31</strong></td><td>Soft delete patient/provider on cascade</td><td>UC-09</td><td>patient-service, provider-service</td><td><span class="badge purple">Post A</span></td></tr>
      <tr><td><strong>FR-32</strong></td><td>Role removal on patient/provider delete</td><td>UC-09</td><td>auth-service (consumer)</td><td><span class="badge purple">Post A</span></td></tr>
      <tr><td><strong>FR-33</strong></td><td>Appointment cancellation on cascade</td><td>UC-09</td><td>appointment-service (consumer)</td><td><span class="badge purple">Post A</span></td></tr>
      <tr><td><strong>FR-34</strong></td><td>GET /analytics/filter (TimescaleDB)</td><td>UC-06</td><td>analytics-service, TimescaleDB</td><td><span class="badge green">Post A</span></td></tr>
      <tr><td><strong>FR-35</strong></td><td>GET /analytics/total-created (TimescaleDB)</td><td>UC-06</td><td>analytics-service, TimescaleDB</td><td><span class="badge green">Post A</span></td></tr>
    </tbody>
  </table>
</div>

</body>
</html>
