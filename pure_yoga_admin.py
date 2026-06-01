#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date, timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
LIVE_CONFIG_PATH = BASE_DIR / "pure_yoga_config.json"
CONFIG_PATH = BASE_DIR / "pure_yoga_config.dev.json"
BOT_PATH = BASE_DIR / "pure_yoga_booking.py"

LOCATION_OPTIONS = [
    {"id": 19, "name": "Yoga - Ngee Ann City", "site": "yoga"},
    {"id": 22, "name": "Yoga - Asia Square Tower 1", "site": "yoga"},
    {"id": 21, "name": "Fitness - Asia Square Tower 1", "site": "fitness"},
    {"id": 31, "name": "Fitness - Ngee Ann City", "site": "fitness"},
]

HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pure Booking Admin</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --surface: #ffffff;
      --ink: #1c2430;
      --muted: #667085;
      --line: #d8dee8;
      --accent: #1b6f8f;
      --accent-dark: #155873;
      --accent-soft: #e4f7ef;
      --warn: #8f4c10;
      --danger: #a23b3b;
      --ok: #217a4a;
      --soft: #f4f2ec;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    header {
      background: #16202b;
      color: white;
      padding: 18px 24px;
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
    }
    h1 { margin: 0; font-size: 20px; font-weight: 700; }
    h2 { margin: 0 0 12px; font-size: 16px; }
    h3 { margin: 0 0 10px; font-size: 14px; }
    main {
      max-width: 1180px;
      margin: 0 auto;
      padding: 22px;
      display: grid;
      gap: 18px;
    }
    section {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }
    .topbar {
      background: var(--surface);
      border-bottom: 1px solid var(--line);
      display: flex;
      gap: 2px;
      padding: 0 22px;
    }
    .tab-button {
      appearance: none;
      border: 0;
      border-bottom: 2px solid transparent;
      border-radius: 0;
      background: transparent;
      color: var(--ink);
      padding: 13px 16px 11px;
      min-height: 38px;
      font-weight: 650;
    }
    .tab-button.active {
      color: #0b8f5c;
      border-bottom-color: #12a66a;
    }
    .tab-panel {
      display: none;
      gap: 16px;
    }
    .tab-panel.active {
      display: grid;
    }
    .panel-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
    }
    .filter-pills,
    .segmented {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .pill-button,
    .segment-button {
      background: white;
      border-color: #bfc7d4;
      color: var(--ink);
      border-radius: 999px;
      min-height: 34px;
      padding: 6px 12px;
      font-weight: 650;
    }
    .pill-button.active,
    .segment-button.active {
      background: var(--accent-soft);
      border-color: #61c89a;
      color: #08764b;
    }
    .form-panel {
      display: none;
    }
    .form-panel.active {
      display: block;
    }
    .search-layout {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 16px;
      align-items: start;
    }
    .result-box {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfd;
      padding: 12px;
      min-height: 74px;
      white-space: pre-wrap;
    }
    .run-preview {
      display: grid;
      gap: 10px;
    }
    .run-target {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfd;
      padding: 12px;
      display: grid;
      gap: 10px;
    }
    .run-target-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
    }
    .run-target-title {
      font-weight: 800;
      overflow-wrap: anywhere;
    }
    .run-target-meta {
      color: var(--muted);
      font-size: 13px;
      margin-top: 2px;
    }
    .run-target-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: flex-end;
      align-items: center;
    }
    .run-target.pending-skip {
      border-color: #e6c26d;
      background: #fff9e8;
    }
    .run-target.saved-skip {
      border-color: #b7c3d5;
      background: #f1f4f8;
    }
    .run-empty {
      border: 1px dashed var(--line);
      border-radius: 8px;
      color: var(--muted);
      padding: 18px;
      text-align: center;
    }
    details.console {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      overflow: hidden;
    }
    details.console summary {
      cursor: pointer;
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      font-weight: 700;
      list-style-position: inside;
    }
    .console-body {
      padding: 12px;
      display: grid;
      gap: 10px;
    }
    .console-body textarea {
      min-height: 86px;
      max-height: 220px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
    }
    label {
      display: grid;
      gap: 5px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 650;
    }
    input, select, button, textarea {
      font: inherit;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 9px 10px;
      background: white;
      color: var(--ink);
      min-width: 0;
      min-height: 44px;
    }
    textarea {
      min-height: 170px;
      width: 100%;
      resize: vertical;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 12px;
      white-space: pre;
    }
    button {
      background: var(--accent);
      color: white;
      border-color: var(--accent);
      cursor: pointer;
      font-weight: 700;
    }
    button.secondary {
      background: white;
      color: var(--accent);
    }
    button.danger {
      background: var(--danger);
      border-color: var(--danger);
    }
    button.ghost-danger {
      background: white;
      color: var(--danger);
      border-color: #e4b6b6;
      opacity: 0;
      min-height: 32px;
      padding: 5px 9px;
    }
    tr:hover button.ghost-danger,
    tr:focus-within button.ghost-danger {
      opacity: 1;
    }
    button:disabled {
      opacity: 0.55;
      cursor: wait;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    th, td {
      text-align: left;
      border-bottom: 1px solid var(--line);
      padding: 9px 8px;
      vertical-align: top;
    }
    th { color: var(--muted); font-size: 12px; }
    tr.is-hidden { display: none; }
    td.actions-cell {
      width: 1%;
      white-space: nowrap;
    }
    .target-table-wrap {
      overflow-x: auto;
    }
    .target-cards {
      display: none;
      gap: 10px;
    }
    .target-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfd;
      padding: 12px;
      display: grid;
      gap: 10px;
    }
    .target-card-head {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: flex-start;
    }
    .target-card-title {
      font-size: 15px;
      font-weight: 800;
      overflow-wrap: anywhere;
    }
    .target-card-subtitle {
      color: var(--muted);
      font-size: 13px;
      margin-top: 2px;
    }
    .target-card-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px 12px;
    }
    .target-card-field {
      min-width: 0;
    }
    .target-card-label {
      color: var(--muted);
      font-size: 11px;
      font-weight: 750;
      text-transform: uppercase;
    }
    .target-card-value {
      margin-top: 2px;
      overflow-wrap: anywhere;
    }
    .suggestions {
      display: grid;
      gap: 8px;
      margin-top: 12px;
    }
    .suggestion {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 9px 10px;
      background: #fbfcfd;
    }
    .suggestion button { padding: 6px 9px; white-space: nowrap; }
    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }
    .compact-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .status {
      border-left: 4px solid var(--accent);
      padding: 10px 12px;
      background: #eef7fb;
      border-radius: 6px;
      white-space: pre-wrap;
    }
    .status.ok { border-color: var(--ok); background: #eef8f2; }
    .status.warn { border-color: var(--warn); background: #fff6e8; }
    .status.err { border-color: var(--danger); background: #fff1f1; }
    .muted { color: var(--muted); }
    .pill {
      display: inline-block;
      padding: 2px 7px;
      border-radius: 999px;
      background: #edf0f4;
      color: #425066;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }
    .pill.oneoff {
      background: #e7f2ff;
      color: #1265a8;
    }
    .pill.recurring {
      background: #ddf6eb;
      color: #08764b;
    }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
    @media (max-width: 860px) {
      .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 560px) {
      .grid { grid-template-columns: 1fr; }
      header { align-items: flex-start; flex-direction: column; }
      main { padding: 14px; gap: 14px; }
      section { padding: 14px; }
      .topbar { overflow-x: auto; padding: 0 10px; }
      .tab-button { flex: 0 0 auto; padding-inline: 12px; }
      .panel-head { align-items: stretch; flex-direction: column; }
      .search-layout { grid-template-columns: 1fr; }
      .run-target-head { flex-direction: column; }
      .run-target-actions { justify-content: stretch; }
      .run-target-actions button { width: 100%; }
      .compact-grid { grid-template-columns: 1fr; }
      .toolbar { display: grid; grid-template-columns: 1fr; }
      .toolbar button { width: 100%; }
      .target-table-wrap { display: none; }
      .target-cards { display: grid; }
      button.ghost-danger { opacity: 1; }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Pure Booking Admin</h1>
      <div class="muted">Local dev config editor for one-off and recurring targets</div>
    </div>
    <div id="summary" class="mono"></div>
  </header>
  <nav class="topbar" aria-label="Primary">
    <button class="tab-button active" type="button" data-tab="targets">Targets</button>
    <button class="tab-button" type="button" data-tab="preview">Active run</button>
    <button class="tab-button" type="button" data-tab="add">+ Add target</button>
    <button class="tab-button" type="button" data-tab="search">Search classes</button>
  </nav>
  <main>
    <div id="tab_targets" class="tab-panel active">
      <section>
        <div class="panel-head">
          <div class="filter-pills" aria-label="Target filters">
            <button class="pill-button active" type="button" data-target-filter="all">All</button>
            <button class="pill-button" type="button" data-target-filter="recurring">Recurring</button>
            <button class="pill-button" type="button" data-target-filter="oneoff">One-off</button>
          </div>
          <div class="toolbar">
            <button class="secondary" id="lookup_active">Lookup date</button>
            <button class="secondary" id="clean_expired">Clean expired</button>
          </div>
        </div>
        <div class="target-table-wrap" style="margin-top: 14px;">
          <table>
            <thead>
              <tr>
                <th>Type</th>
                <th>Day</th>
                <th>Class</th>
                <th>Time</th>
                <th>Location</th>
                <th>Teacher</th>
                <th>Pri</th>
                <th>Class Date</th>
                <th>Run Date</th>
                <th></th>
              </tr>
            </thead>
            <tbody id="targets"></tbody>
          </table>
        </div>
        <div id="target_cards" class="target-cards" style="margin-top: 14px;"></div>
      </section>

      <details class="console" open>
        <summary>Output log</summary>
        <div class="console-body">
          <div id="status" class="status">Ready.</div>
          <textarea id="output" readonly></textarea>
        </div>
      </details>
    </div>

    <div id="tab_preview" class="tab-panel">
      <section>
        <div class="panel-head">
          <h2>Active Run Preview</h2>
          <div class="toolbar">
            <button class="secondary" id="reset_run_skips">Undo All</button>
            <button id="save_run_skips">Save Skip Changes</button>
          </div>
        </div>
        <div class="grid compact-grid">
          <label>Booking Run Date
            <input id="preview_run_date" type="date">
          </label>
          <label>Class Date
            <input id="preview_class_date" type="date" readonly>
          </label>
        </div>
        <div id="run_preview_summary" class="status" style="margin-top: 14px;">Choose a booking run date to preview active targets.</div>
        <div id="run_preview" class="run-preview" style="margin-top: 14px;"></div>
      </section>
    </div>

    <div id="tab_add" class="tab-panel">
      <section>
        <div class="panel-head">
          <h2>Add Target</h2>
          <div class="segmented" aria-label="Target type">
            <button class="segment-button active" type="button" data-add-mode="oneoff">One-off</button>
            <button class="segment-button" type="button" data-add-mode="recurring">Recurring</button>
          </div>
        </div>

        <div id="form_oneoff" class="form-panel active">
          <div class="grid">
            <label>Class Date
              <input id="class_date" type="date">
            </label>
            <label>Booking Run Date
              <input id="booking_run_date" type="date" readonly>
            </label>
            <label>Site
              <select id="site">
                <option value="yoga">Yoga / Pilates</option>
                <option value="fitness">Fitness</option>
              </select>
            </label>
            <label>Location
              <select id="location"></select>
            </label>
            <label>Class Name
              <input id="class_name" placeholder="Type part of class name">
            </label>
            <label>Start Time
              <input id="start_time" placeholder="12:30">
            </label>
            <label>Teacher
              <input id="teacher_name" placeholder="Sandy">
            </label>
            <label>Priority
              <input id="priority" type="number" min="1" value="1">
            </label>
          </div>
          <div class="toolbar" style="margin-top: 14px;">
            <button id="save_oneoff">Save One-Off</button>
            <button class="secondary" id="clear_oneoff">Clear One-Off Form</button>
          </div>
        </div>

        <div id="form_recurring" class="form-panel">
          <div class="grid">
            <label>Day
              <select id="rec_day">
                <option>Mon</option>
                <option>Tue</option>
                <option>Wed</option>
                <option>Thu</option>
                <option>Fri</option>
                <option>Sat</option>
                <option>Sun</option>
              </select>
            </label>
            <label>Site
              <select id="rec_site">
                <option value="yoga">Yoga / Pilates</option>
                <option value="fitness">Fitness</option>
              </select>
            </label>
            <label>Location
              <select id="rec_location"></select>
            </label>
            <label>Priority
              <input id="rec_priority" type="number" min="1" value="1">
            </label>
            <label>Class Name
              <input id="rec_class_name" placeholder="Reformer Signature">
            </label>
            <label>Start Time
              <input id="rec_start_time" placeholder="10:00">
            </label>
            <label>Teacher
              <input id="rec_teacher_name" placeholder="Kelvin">
            </label>
          </div>
          <div class="toolbar" style="margin-top: 14px;">
            <button id="save_recurring">Save Recurring</button>
            <button class="secondary" id="clear_recurring">Clear Recurring Form</button>
          </div>
        </div>
      </section>
    </div>

    <div id="tab_search" class="tab-panel">
      <div class="search-layout">
        <section>
          <h2>Search Live Classes</h2>
          <div class="grid compact-grid">
            <label>Class Date
              <input id="search_class_date" type="date">
            </label>
            <label>Site
              <select id="search_site">
                <option value="yoga">Yoga / Pilates</option>
                <option value="fitness">Fitness</option>
              </select>
            </label>
            <label>Location
              <select id="search_location"></select>
            </label>
            <label>Class Name
              <input id="search_class_name" placeholder="Type at least 3 letters">
            </label>
          </div>
          <div class="toolbar" style="margin-top: 14px;">
            <button id="load_schedule">Search Live Classes</button>
            <button class="secondary" id="clear_suggestions">Clear Results</button>
          </div>
          <div id="suggestions" class="suggestions"></div>
          <div id="search_results" class="result-box muted" style="margin-top: 12px;">Search results will appear here.</div>
        </section>

        <section>
          <h2>Check Saved Targets</h2>
          <label>Class Date
            <input id="lookup_class_date" type="date">
          </label>
          <div class="toolbar" style="margin-top: 14px;">
            <button id="lookup_new">Check Saved Targets For Date</button>
          </div>
          <div id="lookup_results" class="result-box muted" style="margin-top: 12px;">Lookup results will appear here.</div>
        </section>
      </div>
    </div>
  </main>
  <script>
    const locations = __LOCATIONS__;
    const $ = (id) => document.getElementById(id);
    let loadedClasses = [];
    let searchTimer = null;
    let allTargets = [];
    let targetFilter = "all";
    let pendingRunSkips = new Set();

    function setStatus(text, kind = "") {
      $("status").className = "status" + (kind ? " " + kind : "");
      $("status").textContent = text;
    }

    function showOutput(text, shouldScroll = true) {
      $("output").value = text;
      if (shouldScroll) {
        $("status").scrollIntoView({behavior: "smooth", block: "start"});
      }
    }

    async function api(path, body) {
      const opts = body === undefined ? {} : {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body),
      };
      const response = await fetch(path, opts);
      const data = await response.json();
      if (!response.ok || data.ok === false) {
        throw new Error(data.error || `HTTP ${response.status}`);
      }
      return data;
    }

    function locationById(id) {
      return locations.find((item) => String(item.id) === String(id));
    }

    function fillLocationSelect(siteId, locationId) {
      const site = $(siteId).value;
      $(locationId).innerHTML = "";
      for (const item of locations.filter((loc) => loc.site === site)) {
        const opt = document.createElement("option");
        opt.value = item.id;
        opt.textContent = item.name;
        $(locationId).appendChild(opt);
      }
    }

    function fillLocations() {
      fillLocationSelect("site", "location");
    }

    function fillSearchLocations() {
      fillLocationSelect("search_site", "search_location");
      renderSuggestions();
    }

    function fillRecurringLocations() {
      fillLocationSelect("rec_site", "rec_location");
    }

    function switchTab(tabName) {
      document.querySelectorAll(".tab-button").forEach((button) => {
        button.classList.toggle("active", button.dataset.tab === tabName);
      });
      document.querySelectorAll(".tab-panel").forEach((panel) => {
        panel.classList.toggle("active", panel.id === `tab_${tabName}`);
      });
    }

    function switchAddMode(mode) {
      document.querySelectorAll(".segment-button").forEach((button) => {
        button.classList.toggle("active", button.dataset.addMode === mode);
      });
      $("form_oneoff").classList.toggle("active", mode === "oneoff");
      $("form_recurring").classList.toggle("active", mode === "recurring");
    }

    function targetKind(target) {
      return target.booking_run_date ? "oneoff" : "recurring";
    }

    function dateFromString(value) {
      return value ? new Date(`${value}T00:00:00Z`) : null;
    }

    function dateToString(value) {
      return value.toISOString().slice(0, 10);
    }

    function addDays(value, days) {
      const date = dateFromString(value);
      if (!date) return "";
      date.setUTCDate(date.getUTCDate() + days);
      return dateToString(date);
    }

    function dayName(value) {
      const date = dateFromString(value);
      if (!date) return "";
      return ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][date.getUTCDay()];
    }

    function todayString() {
      const now = new Date();
      const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
      return local.toISOString().slice(0, 10);
    }

    function targetRunDate(target, classDate) {
      if (target.booking_run_date) return target.booking_run_date;
      const bookingOpenDays = Number(target.booking_open_days ?? 5);
      return addDays(classDate, -bookingOpenDays);
    }

    function targetClassDateForRun(target, runDate) {
      if (target.class_date) return target.class_date;
      const classDaysAhead = Number(target.class_days_ahead ?? target.booking_open_days ?? 5);
      return addDays(runDate, classDaysAhead);
    }

    function isTargetForRun(target, runDate) {
      const classDate = targetClassDateForRun(target, runDate);
      if (!classDate) return false;
      if (targetRunDate(target, classDate) !== runDate) return false;
      const days = target.days || [];
      return !days.length || days.includes(dayName(classDate));
    }

    function isSavedSkipped(target, runDate) {
      return (target.skip_booking_run_dates || []).includes(runDate);
    }

    function targetType(target) {
      const kind = targetKind(target);
      return kind === "oneoff" ? '<span class="pill oneoff">one-off</span>' : '<span class="pill recurring">recurring</span>';
    }

    function targetSummary(target) {
      const day = (target.days || []).join(", ") || "No day";
      const time = target.start_time || "No time";
      const location = target.location_name || target.location_id || "No location";
      return `${day} · ${time} · ${location}`;
    }

    function targetField(label, value) {
      return `
        <div class="target-card-field">
          <div class="target-card-label">${label}</div>
          <div class="target-card-value">${value || "—"}</div>
        </div>
      `;
    }

    function targetCard(target) {
      return `
        <article class="target-card">
          <div class="target-card-head">
            <div>
              <div class="target-card-title">${target.class_name || "Untitled target"}</div>
              <div class="target-card-subtitle">${targetSummary(target)}</div>
            </div>
            ${targetType(target)}
          </div>
          <div class="target-card-grid">
            ${targetField("Teacher", target.teacher_name)}
            ${targetField("Priority", target.priority ?? "")}
            ${targetField("Class Date", target.class_date)}
            ${targetField("Run Date", target.booking_run_date)}
          </div>
          <button class="secondary delete-target-mobile" type="button" data-delete-index="${target._index}">Delete</button>
        </article>
      `;
    }

    function filteredTargets() {
      return allTargets.filter((target) => targetFilter === "all" || targetKind(target) === targetFilter);
    }

    function runTargetDetails(target, runDate) {
      const classDate = targetClassDateForRun(target, runDate);
      return `${classDate || "No class date"} · ${target.start_time || "No time"} · ${target.location_name || target.location_id || "No location"} · priority ${target.priority ?? "—"}`;
    }

    function runTargetStatus(target, runDate) {
      if (pendingRunSkips.has(target._index)) {
        return targetKind(target) === "oneoff" ? '<span class="pill">will remove one-off</span>' : '<span class="pill">will skip this run</span>';
      }
      if (isSavedSkipped(target, runDate)) return '<span class="pill">skipped</span>';
      return targetType(target);
    }

    function renderRunPreview() {
      const runDate = $("preview_run_date").value;
      const classDate = runDate ? addDays(runDate, 5) : "";
      $("preview_class_date").value = classDate;
      const box = $("run_preview");
      if (!runDate) {
        $("run_preview_summary").className = "status";
        $("run_preview_summary").textContent = "Choose a booking run date to preview active targets.";
        box.innerHTML = "";
        return;
      }
      const matching = allTargets.filter((target) => isTargetForRun(target, runDate));
      const active = matching.filter((target) => !isSavedSkipped(target, runDate));
      const savedSkipped = matching.filter((target) => isSavedSkipped(target, runDate));
      const pendingCount = pendingRunSkips.size;
      $("run_preview_summary").className = "status" + (pendingCount ? " warn" : " ok");
      $("run_preview_summary").textContent = `${active.length} scheduled target(s), ${savedSkipped.length} already skipped, ${pendingCount} unsaved skip change(s) for ${runDate}.`;
      if (!matching.length) {
        box.innerHTML = '<div class="run-empty">No targets are scheduled for this booking run date.</div>';
        return;
      }
      box.innerHTML = matching.map((target) => {
        const savedSkip = isSavedSkipped(target, runDate);
        const pendingSkip = pendingRunSkips.has(target._index);
        const classes = ["run-target", pendingSkip ? "pending-skip" : "", savedSkip ? "saved-skip" : ""].join(" ").trim();
        const action = savedSkip
          ? '<span class="muted">Saved skip</span>'
          : pendingSkip
            ? `<button class="secondary" type="button" data-undo-run-skip="${target._index}">Undo</button>`
            : `<button class="secondary" type="button" data-run-skip="${target._index}">Skip this run</button>`;
        return `
          <article class="${classes}">
            <div class="run-target-head">
              <div>
                <div class="run-target-title">${target.class_name || "Untitled target"}</div>
                <div class="run-target-meta">${runTargetDetails(target, runDate)}</div>
                <div class="run-target-meta">${target.teacher_name || "No teacher"} · ${targetKind(target) === "oneoff" ? "one-off target" : "recurring target"}</div>
              </div>
              <div class="run-target-actions">
                ${runTargetStatus(target, runDate)}
                ${action}
              </div>
            </div>
          </article>
        `;
      }).join("");
      document.querySelectorAll("[data-run-skip]").forEach((button) => {
        button.addEventListener("click", () => {
          pendingRunSkips.add(Number(button.dataset.runSkip));
          renderRunPreview();
        });
      });
      document.querySelectorAll("[data-undo-run-skip]").forEach((button) => {
        button.addEventListener("click", () => {
          pendingRunSkips.delete(Number(button.dataset.undoRunSkip));
          renderRunPreview();
        });
      });
    }

    function renderConfig(data) {
      $("summary").textContent = `${data.target_count} target(s)`;
      allTargets = data.targets;
      const targets = filteredTargets();
      $("targets").innerHTML = targets.map((target) => `
        <tr>
          <td>${targetType(target)}</td>
          <td>${(target.days || []).join(", ")}</td>
          <td>${target.class_name || ""}</td>
          <td>${target.start_time || ""}</td>
          <td>${target.location_name || target.location_id || ""}</td>
          <td>${target.teacher_name || ""}</td>
          <td>${target.priority ?? ""}</td>
          <td>${target.class_date || ""}</td>
          <td>${target.booking_run_date || ""}</td>
          <td class="actions-cell">
            <button class="ghost-danger" type="button" data-delete-index="${target._index}">Delete</button>
          </td>
        </tr>
      `).join("");
      $("target_cards").innerHTML = targets.map(targetCard).join("");
      document.querySelectorAll("[data-delete-index]").forEach((button) => {
        button.addEventListener("click", () => deleteTarget(Number(button.dataset.deleteIndex)));
      });
      renderRunPreview();
    }

    async function refreshConfig() {
      const data = await api("/api/config");
      renderConfig(data);
    }

    function setRunDateFromClassDate(clearSuggestionsAfter = true) {
      const value = $("class_date").value;
      if (!value) return;
      const date = new Date(`${value}T00:00:00Z`);
      date.setUTCDate(date.getUTCDate() - 5);
      $("booking_run_date").value = date.toISOString().slice(0, 10);
      if (clearSuggestionsAfter) {
        loadedClasses = [];
        renderSuggestions();
      }
    }

    function autoRunDate() {
      setRunDateFromClassDate(true);
    }

    function clearOneOffForm() {
      $("class_date").value = "";
      $("booking_run_date").value = "";
      $("site").value = "yoga";
      fillLocations();
      $("class_name").value = "";
      $("start_time").value = "";
      $("teacher_name").value = "";
      $("priority").value = "1";
      loadedClasses = [];
      renderSuggestions();
    }

    function clearRecurringForm() {
      $("rec_day").value = "Mon";
      $("rec_site").value = "yoga";
      fillRecurringLocations();
      $("rec_priority").value = "1";
      $("rec_class_name").value = "";
      $("rec_start_time").value = "";
      $("rec_teacher_name").value = "";
    }

    function clearSuggestions() {
      loadedClasses = [];
      if (searchTimer) {
        clearTimeout(searchTimer);
        searchTimer = null;
      }
      renderSuggestions();
      $("search_results").textContent = "Search results will appear here.";
      $("search_results").className = "result-box muted";
    }

    function cleanText(value) {
      return (value || "").toLowerCase().replace(/[^a-z0-9]+/g, "");
    }

    function classDisplay(item) {
      return `${item.class_date} ${item.start_time} | ${item.class_name} | ${item.teacher_name} | ${item.location_name}`;
    }

    function applyClass(item) {
      $("site").value = item.site;
      fillLocations();
      $("location").value = String(item.location_id);
      $("class_date").value = item.class_date;
      setRunDateFromClassDate(false);
      $("class_name").value = item.class_name;
      $("start_time").value = item.start_time;
      $("teacher_name").value = item.teacher_name;
      switchTab("add");
      switchAddMode("oneoff");
      setStatus(`Filled add-target form with ${item.class_name}.`, "ok");
      renderSuggestions();
    }

    function renderSuggestions() {
      const box = $("suggestions");
      const query = cleanText($("search_class_name").value);
      const currentLocation = Number($("search_location").value || 0);
      const shown = loadedClasses
        .filter((item) => !currentLocation || item.location_id === currentLocation)
        .filter((item) => !query || cleanText(item.class_name).includes(query))
        .slice(0, 12);
      if (!shown.length) {
        box.innerHTML = loadedClasses.length ? '<div class="muted">No matching suggestions for this text/location.</div>' : "";
        return;
      }
      box.innerHTML = shown.map((item, index) => `
        <div class="suggestion">
          <div>
            <strong>${classDisplay(item)}</strong>
            <div class="muted mono">class_id=${item.class_id}</div>
          </div>
          <button class="secondary" type="button" data-suggestion="${index}">Use</button>
        </div>
      `).join("");
      [...box.querySelectorAll("button[data-suggestion]")].forEach((button) => {
        button.addEventListener("click", () => applyClass(shown[Number(button.dataset.suggestion)]));
      });
    }

    function oneOffPayload() {
      const loc = locationById($("location").value);
      return {
        site: $("site").value,
        days: [],
        class_name: $("class_name").value.trim(),
        start_time: $("start_time").value.trim(),
        location_id: Number($("location").value),
        location_name: loc ? loc.name : "",
        teacher_name: $("teacher_name").value.trim(),
        teacher_policy: "prefer_named_teacher",
        mode: "book_all",
        priority: Number($("priority").value || 1),
        class_date: $("class_date").value,
        booking_run_date: $("booking_run_date").value,
        booking_open_days: 5,
        schedule_window_days: 1,
      };
    }

    function recurringPayload() {
      const loc = locationById($("rec_location").value);
      return {
        site: $("rec_site").value,
        days: [$("rec_day").value],
        class_name: $("rec_class_name").value.trim(),
        start_time: $("rec_start_time").value.trim(),
        location_id: Number($("rec_location").value),
        location_name: loc ? loc.name : "",
        teacher_name: $("rec_teacher_name").value.trim(),
        teacher_policy: "prefer_named_teacher",
        mode: "book_all",
        priority: Number($("rec_priority").value || 1),
        class_days_ahead: 5,
        booking_open_days: 5,
        schedule_window_days: 1,
      };
    }

    async function runButton(button, fn) {
      button.disabled = true;
      try {
        await fn();
      } catch (error) {
        setStatus(error.message, "err");
        $("status").scrollIntoView({behavior: "smooth", block: "start"});
      } finally {
        button.disabled = false;
      }
    }

    async function loadClassSuggestions() {
      const targetDate = $("search_class_date").value;
      const typed = $("search_class_name").value.trim();
      if (!targetDate && typed.length < 3) {
        throw new Error("Type at least 3 letters of a class name, or choose a class date first.");
      }
      $("search_results").textContent = "Searching live classes...";
      $("search_results").className = "result-box";
      const data = await api("/api/classes", {
        target_date: targetDate,
        site: $("search_site").value,
        location_id: Number($("search_location").value),
        query: typed,
      });
      loadedClasses = data.classes;
      renderSuggestions();
      $("search_results").textContent = data.classes.length
        ? data.classes.map(classDisplay).join("\n")
        : "No live classes matched this search.";
      $("search_results").className = "result-box";
      const suffix = typed ? ` matching "${typed}"` : "";
      setStatus(`Loaded ${data.classes.length} live class(es). Showing suggestions${suffix}; click Use to fill the form.`, "ok");
    }

    function scheduleAutoSearch() {
      if (searchTimer) clearTimeout(searchTimer);
      const typed = $("search_class_name").value.trim();
      if ($("search_class_date").value || typed.length < 3) {
        renderSuggestions();
        return;
      }
      searchTimer = setTimeout(() => {
        runButton($("load_schedule"), loadClassSuggestions);
      }, 650);
    }

    async function deleteTarget(index) {
      const target = allTargets.find((item) => item._index === index);
      const label = target ? `${target.class_name || "target"} ${target.start_time || ""}`.trim() : "this target";
      if (!confirm(`Delete ${label} from the current UI config?`)) return;
      const data = await api("/api/delete-target", {index});
      renderConfig(data.config);
      setStatus(`Deleted ${label}.`, "ok");
      showOutput(JSON.stringify(data.deleted, null, 2), false);
    }

    async function saveRunSkips() {
      const runDate = $("preview_run_date").value;
      const indices = [...pendingRunSkips];
      if (!runDate) throw new Error("Choose a booking run date first.");
      if (!indices.length) {
        setStatus("No skip changes to save.", "warn");
        return;
      }
      const data = await api("/api/apply-run-skips", {run_date: runDate, indices});
      pendingRunSkips = new Set();
      renderConfig(data.config);
      const removedCount = data.removed_oneoffs.length;
      const skippedCount = data.skipped_recurring.length;
      setStatus(`Saved ${skippedCount} recurring skip(s) and removed ${removedCount} one-off target(s) for ${runDate}.`, "ok");
      showOutput(JSON.stringify({run_date: runDate, skipped_recurring: data.skipped_recurring, removed_oneoffs: data.removed_oneoffs}, null, 2), false);
    }

    document.querySelectorAll(".tab-button").forEach((button) => {
      button.addEventListener("click", () => switchTab(button.dataset.tab));
    });
    document.querySelectorAll(".segment-button").forEach((button) => {
      button.addEventListener("click", () => switchAddMode(button.dataset.addMode));
    });
    document.querySelectorAll("[data-target-filter]").forEach((button) => {
      button.addEventListener("click", () => {
        targetFilter = button.dataset.targetFilter;
        document.querySelectorAll("[data-target-filter]").forEach((item) => {
          item.classList.toggle("active", item.dataset.targetFilter === targetFilter);
        });
        renderConfig({target_count: allTargets.length, targets: allTargets});
      });
    });

    $("site").addEventListener("change", fillLocations);
    $("search_site").addEventListener("change", fillSearchLocations);
    $("rec_site").addEventListener("change", fillRecurringLocations);
    $("class_date").addEventListener("change", autoRunDate);
    $("preview_run_date").addEventListener("change", () => {
      pendingRunSkips = new Set();
      renderRunPreview();
    });
    $("search_class_name").addEventListener("input", scheduleAutoSearch);
    $("search_class_name").addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        runButton($("load_schedule"), loadClassSuggestions);
      }
    });
    $("search_location").addEventListener("change", renderSuggestions);
    $("clear_oneoff").addEventListener("click", () => {
      clearOneOffForm();
      setStatus("Cleared one-off form.", "ok");
    });
    $("clear_recurring").addEventListener("click", () => {
      clearRecurringForm();
      setStatus("Cleared recurring form.", "ok");
    });
    $("clear_suggestions").addEventListener("click", () => {
      clearSuggestions();
      setStatus("Cleared suggestions.", "ok");
    });
    $("reset_run_skips").addEventListener("click", () => {
      pendingRunSkips = new Set();
      renderRunPreview();
      setStatus("Undid unsaved skip changes.", "ok");
    });
    $("save_run_skips").addEventListener("click", () => runButton($("save_run_skips"), saveRunSkips));
    $("save_oneoff").addEventListener("click", () => runButton($("save_oneoff"), async () => {
      const data = await api("/api/add-oneoff", oneOffPayload());
      renderConfig(data.config);
      $("output").value = JSON.stringify(data.target, null, 2);
      setStatus("Saved one-off target.", "ok");
    }));
    $("save_recurring").addEventListener("click", () => runButton($("save_recurring"), async () => {
      const data = await api("/api/add-recurring", recurringPayload());
      renderConfig(data.config);
      $("output").value = JSON.stringify(data.target, null, 2);
      setStatus("Saved recurring target.", "ok");
    }));
    $("load_schedule").addEventListener("click", () => runButton($("load_schedule"), loadClassSuggestions));
    $("lookup_new").addEventListener("click", () => runButton($("lookup_new"), async () => {
      const targetDate = $("lookup_class_date").value;
      if (!targetDate) throw new Error("Choose a class date first.");
      setStatus(`Checking saved targets for ${targetDate}...`);
      $("lookup_results").textContent = `Checking saved targets for ${targetDate}...`;
      $("lookup_results").className = "result-box";
      const data = await api("/api/lookup", {target_date: targetDate, list_classes: true});
      $("lookup_results").textContent = data.output || "Lookup completed with no output.";
      $("lookup_results").className = "result-box";
      showOutput(data.output, false);
      setStatus(data.exit_code === 0 ? "Lookup matched." : "Lookup completed with no-match or warning.", data.exit_code === 0 ? "ok" : "warn");
    }));
    $("lookup_active").addEventListener("click", () => runButton($("lookup_active"), async () => {
      setStatus("Checking active target date...");
      const data = await api("/api/lookup", {target_date: "", list_classes: false});
      showOutput(data.output);
      setStatus(data.exit_code === 0 ? "Lookup matched." : "Lookup completed with no-match or warning.", data.exit_code === 0 ? "ok" : "warn");
    }));
    $("clean_expired").addEventListener("click", () => runButton($("clean_expired"), async () => {
      if (!confirm("Clean expired one-off targets from the current UI config?")) return;
      const data = await api("/api/clean-expired", {});
      renderConfig(data.config);
      $("output").value = `Removed ${data.removed} expired one-off target(s).`;
      setStatus(`Removed ${data.removed} expired one-off target(s).`, "ok");
    }));

    fillLocations();
    fillSearchLocations();
    fillRecurringLocations();
    $("preview_run_date").value = todayString();
    refreshConfig().catch((error) => setStatus(error.message, "err"));
  </script>
</body>
</html>
"""


def load_config() -> dict[str, Any]:
    ensure_config_exists()
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_config(config: dict[str, Any]) -> None:
    with CONFIG_PATH.open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def ensure_config_exists() -> None:
    if CONFIG_PATH.exists():
        return
    if not LIVE_CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
    CONFIG_PATH.write_text(LIVE_CONFIG_PATH.read_text(encoding="utf-8"), encoding="utf-8")


def public_config(config: dict[str, Any]) -> dict[str, Any]:
    targets = []
    for index, target in enumerate(config.get("targets", [])):
        public_target = {
            key: target.get(key)
            for key in (
                "site",
                "days",
                "class_name",
                "start_time",
                "location_id",
                "location_name",
                "teacher_name",
                "teacher_policy",
                "mode",
                "priority",
                "class_date",
                "booking_run_date",
                "skip_booking_run_dates",
                "class_days_ahead",
                "booking_open_days",
                "schedule_window_days",
            )
        }
        public_target["_index"] = index
        targets.append(public_target)
    return {
        "ok": True,
        "target_count": len(targets),
        "config_path": str(CONFIG_PATH),
        "live_config_path": str(LIVE_CONFIG_PATH),
        "is_live_config": CONFIG_PATH == LIVE_CONFIG_PATH,
        "targets": targets,
        "booking": {
            "aggressive_probe_lead_ms": config.get("booking", {}).get("aggressive_probe_lead_ms"),
            "focus_first_head_start_ms": config.get("booking", {}).get("focus_first_head_start_ms"),
        },
    }


def validate_oneoff(payload: dict[str, Any]) -> dict[str, Any]:
    required = ["site", "class_name", "start_time", "location_id", "location_name", "class_date", "booking_run_date"]
    missing = [key for key in required if payload.get(key) in ("", None)]
    if missing:
        raise ValueError(f"Missing required field(s): {', '.join(missing)}")

    class_date = date.fromisoformat(str(payload["class_date"]))
    booking_run_date = date.fromisoformat(str(payload["booking_run_date"]))
    if booking_run_date != class_date - timedelta(days=5):
        raise ValueError("Booking run date should be exactly 5 days before class date.")

    target = {
        "site": str(payload["site"]),
        "days": [class_date.strftime("%a")],
        "class_name": str(payload["class_name"]).strip(),
        "start_time": str(payload["start_time"]).strip(),
        "location_id": int(payload["location_id"]),
        "location_name": str(payload["location_name"]).strip(),
        "teacher_name": str(payload.get("teacher_name", "")).strip(),
        "teacher_policy": "prefer_named_teacher",
        "mode": "book_all",
        "priority": int(payload.get("priority") or 1),
        "class_date": class_date.isoformat(),
        "booking_run_date": booking_run_date.isoformat(),
        "booking_open_days": 5,
        "schedule_window_days": 1,
    }
    return target


def validate_recurring(payload: dict[str, Any]) -> dict[str, Any]:
    required = ["site", "days", "class_name", "start_time", "location_id", "location_name"]
    missing = [key for key in required if payload.get(key) in ("", None, [])]
    if missing:
        raise ValueError(f"Missing required field(s): {', '.join(missing)}")

    days = payload.get("days")
    if not isinstance(days, list) or not days:
        raise ValueError("Choose at least one day for a recurring target.")

    return {
        "site": str(payload["site"]),
        "days": [str(day) for day in days],
        "class_name": str(payload["class_name"]).strip(),
        "start_time": str(payload["start_time"]).strip(),
        "location_id": int(payload["location_id"]),
        "location_name": str(payload["location_name"]).strip(),
        "teacher_name": str(payload.get("teacher_name", "")).strip(),
        "teacher_policy": "prefer_named_teacher",
        "mode": "book_all",
        "priority": int(payload.get("priority") or 1),
        "class_days_ahead": 5,
        "booking_open_days": 5,
        "schedule_window_days": 1,
    }


def normalize_search_text(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def fetch_classes(payload: dict[str, Any]) -> list[dict[str, Any]]:
    import pure_yoga_booking as bot_module

    target_date_raw = str(payload.get("target_date", "")).strip()
    query = normalize_search_text(str(payload.get("query", "")).strip())
    if target_date_raw:
        start_date = date.fromisoformat(target_date_raw)
        schedule_days = 1
    else:
        start_date = date.today()
        schedule_days = 14
    site = str(payload.get("site", "yoga")).strip() or "yoga"
    location_id = int(payload.get("location_id") or 0)
    if not location_id:
        raise ValueError("Choose a location before loading class suggestions.")

    config = bot_module.load_config(CONFIG_PATH)
    bot = bot_module.PureYogaBot(config, CONFIG_PATH)
    client = bot_module.SiteClient(bot, site, [location_id])
    client.bootstrap_headers()
    client.fetch_locations()
    classes = client.fetch_schedule(start_date, schedule_days)
    rows = []
    for item in classes:
        item_date = str(item.get("start_date") or "")
        if target_date_raw and item_date != target_date_raw:
            continue
        if int(item.get("location_id") or 0) != location_id:
            continue
        class_type = item.get("class_type", {})
        class_name = class_type.get("name") or ""
        if query and query not in normalize_search_text(class_name):
            continue
        teacher = item.get("teacher", {})
        rows.append(
            {
                "site": site,
                "class_id": item.get("id"),
                "class_date": item_date,
                "class_name": class_name,
                "start_time": item.get("start_time_display") or item.get("start_time") or "",
                "teacher_name": teacher.get("full_name") or teacher.get("name") or "",
                "location_id": location_id,
                "location_name": client.location_name(location_id),
            }
        )
    return sorted(rows, key=lambda row: (row["class_date"], row["start_time"], row["class_name"]))


def run_lookup(target_date: str, list_classes: bool) -> tuple[int, str]:
    command = [sys.executable, str(BOT_PATH), "--config", str(CONFIG_PATH), "--lookup-only"]
    if target_date:
        command.extend(["--target-date", target_date])
    if list_classes:
        command.append("--list-classes")
    completed = subprocess.run(
        command,
        cwd=str(BASE_DIR),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=45,
        check=False,
    )
    return completed.returncode, completed.stdout


def clean_expired(config: dict[str, Any]) -> int:
    today = date.today()
    kept = []
    removed = 0
    for target in config.get("targets", []):
        run_date_raw = target.get("booking_run_date")
        if run_date_raw:
            try:
                run_date = date.fromisoformat(str(run_date_raw))
            except ValueError:
                kept.append(target)
                continue
            if run_date < today:
                removed += 1
                continue
        kept.append(target)
    config["targets"] = kept
    return removed


def delete_target(config: dict[str, Any], index: int) -> dict[str, Any]:
    targets = config.get("targets", [])
    if index < 0 or index >= len(targets):
        raise ValueError("Target not found.")
    return targets.pop(index)


def apply_run_skips(config: dict[str, Any], run_date_raw: str, indices_raw: Any) -> dict[str, Any]:
    run_date = date.fromisoformat(str(run_date_raw))
    if not isinstance(indices_raw, list) or not indices_raw:
        raise ValueError("Choose at least one target to skip.")

    indices = sorted({int(item) for item in indices_raw}, reverse=True)
    targets = config.get("targets", [])
    skipped_recurring = []
    removed_oneoffs = []

    for index in indices:
        if index < 0 or index >= len(targets):
            raise ValueError("Target not found.")

    for index in indices:
        target = targets[index]
        if target.get("booking_run_date"):
            removed_oneoffs.append(targets.pop(index))
            continue
        skip_dates = [str(item) for item in (target.get("skip_booking_run_dates") or [])]
        if run_date.isoformat() not in skip_dates:
            skip_dates.append(run_date.isoformat())
        target["skip_booking_run_dates"] = sorted(set(skip_dates))
        skipped_recurring.append(target)

    return {
        "skipped_recurring": skipped_recurring,
        "removed_oneoffs": removed_oneoffs,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "PureYogaAdmin/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[admin] {self.address_string()} {fmt % args}")

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, exc: Exception, status: HTTPStatus = HTTPStatus.BAD_REQUEST) -> None:
        self.send_json({"ok": False, "error": str(exc)}, status)

    def do_GET(self) -> None:
        try:
            if self.path == "/" or self.path.startswith("/?"):
                body = HTML.replace("__LOCATIONS__", json.dumps(LOCATION_OPTIONS)).encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if self.path == "/api/config":
                self.send_json(public_config(load_config()))
                return
            self.send_json({"ok": False, "error": "Not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self.send_error_json(exc, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:
        try:
            payload = self.read_json()
            if self.path == "/api/add-oneoff":
                config = load_config()
                target = validate_oneoff(payload)
                config.setdefault("targets", []).append(target)
                save_config(config)
                self.send_json({"ok": True, "target": target, "config": public_config(config)})
                return
            if self.path == "/api/add-recurring":
                config = load_config()
                target = validate_recurring(payload)
                config.setdefault("targets", []).append(target)
                save_config(config)
                self.send_json({"ok": True, "target": target, "config": public_config(config)})
                return
            if self.path == "/api/classes":
                classes = fetch_classes(payload)
                self.send_json({"ok": True, "classes": classes})
                return
            if self.path == "/api/lookup":
                exit_code, output = run_lookup(str(payload.get("target_date", "")).strip(), bool(payload.get("list_classes")))
                self.send_json({"ok": True, "exit_code": exit_code, "output": output})
                return
            if self.path == "/api/clean-expired":
                config = load_config()
                removed = clean_expired(config)
                save_config(config)
                self.send_json({"ok": True, "removed": removed, "config": public_config(config)})
                return
            if self.path == "/api/delete-target":
                config = load_config()
                deleted = delete_target(config, int(payload.get("index")))
                save_config(config)
                self.send_json({"ok": True, "deleted": deleted, "config": public_config(config)})
                return
            if self.path == "/api/apply-run-skips":
                config = load_config()
                result = apply_run_skips(config, str(payload.get("run_date", "")).strip(), payload.get("indices"))
                save_config(config)
                self.send_json({"ok": True, **result, "config": public_config(config)})
                return
            self.send_json({"ok": False, "error": "Not found"}, HTTPStatus.NOT_FOUND)
        except subprocess.TimeoutExpired:
            self.send_error_json(RuntimeError("Lookup timed out after 45 seconds."), HTTPStatus.REQUEST_TIMEOUT)
        except Exception as exc:
            self.send_error_json(exc)


def main() -> int:
    global CONFIG_PATH
    parser = argparse.ArgumentParser(description="Local admin UI for Pure Yoga booking config.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8501)
    parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_PATH,
        help=(
            "Config file for UI reads/writes. Defaults to pure_yoga_config.dev.json "
            "so UI testing does not affect the live booking config."
        ),
    )
    args = parser.parse_args()
    CONFIG_PATH = args.config if args.config.is_absolute() else BASE_DIR / args.config
    ensure_config_exists()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    mode = "LIVE CONFIG" if CONFIG_PATH == LIVE_CONFIG_PATH else "dev config"
    print(f"Pure Booking Admin running at http://{args.host}:{args.port}/ ({mode}: {CONFIG_PATH})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping admin server.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
