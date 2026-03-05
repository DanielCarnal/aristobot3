#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LOG AGGREGATOR — Aristobot3 Logging Infrastructure

Mode interactif : python tools/log_aggregator.py
Mode script     : python tools/log_aggregator.py --all --last 5 --level ERROR

Output : fichier markdown horodaté dans tools/output/
"""

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

# Chemins relatifs au projet
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
OUTPUT_DIR = PROJECT_ROOT / "tools" / "output"

# Mapping composants -> fichiers de log
COMPONENTS = {
    "heartbeat": {"file": "terminal2.log", "label": "Terminal 2 - Heartbeat"},
    "trading":   {"file": "terminal3.log", "label": "Terminal 3 - Trading Engine"},
    "exchange":  {"file": "terminal5.log", "label": "Terminal 5 - Exchange Gateway"},
    "webhook":   {"file": "terminal6.log", "label": "Terminal 6 - Webhook Receiver"},
    "django":    {"file": "terminal1.log", "label": "Terminal 1 - Daphne/Django"},
    "monitor":   {"file": "terminal7.log", "label": "Terminal 7 - Order Monitor"},
}

# Seuils alertes (ms)
ALERT_THRESHOLDS = {
    "api_exchange": {"warning": 500, "critical": 2000},
    "redis":         {"warning": 200, "critical": 1000},
    "db_write":      {"warning": 1000, "critical": 3000},
}

# Mots-cles pour categoriser les operations
OPERATION_KEYWORDS = {
    "api_exchange": [
        "bitget", "binance", "kraken", "exchange", "api call",
        "place_order", "get_balance", "fetch_open", "fetch_closed",
    ],
    "redis": [
        "redis", "pub", "sub", "publish", "exchange_requests",
        "exchange_responses", "webhook_raw",
    ],
    "db_write": [
        "save", "create", "objects.create", "signal sauve",
        "enregistr", "db write",
    ],
}


def collect_log_files(selected_components, last_n=None):
    """Collecte les fichiers de log pour les composants selectes"""
    files = []
    for comp in selected_components:
        if comp not in COMPONENTS:
            continue
        base_name = COMPONENTS[comp]["file"].replace(".log", "")
        # Fichier principal + fichiers rotes (rotation loguru: terminal2.log.2026-01-31_14-30-00_0.log)
        candidates = sorted(
            LOGS_DIR.glob(f"{base_name}*"),
            key=lambda f: f.stat().st_mtime if f.exists() else 0,
            reverse=True
        )
        if last_n:
            candidates = candidates[:last_n]
        files.extend(candidates)
    return files


def parse_loguru_json(line):
    """Parse une ligne de log loguru JSON (format serialize=True)"""
    try:
        entry = json.loads(line.strip())
        if "record" in entry:
            record = entry["record"]
            return {
                "timestamp": record.get("time", {}).get("repr", ""),
                "level": record.get("level", {}).get("name", "UNKNOWN"),
                "message": record.get("message", ""),
                "terminal_name": record.get("extra", {}).get("terminal_name", "unknown"),
                "trace_id": record.get("extra", {}).get("trace_id"),
                "component": record.get("extra", {}).get("component", ""),
                "extra": record.get("extra", {}),
                "name": record.get("name", ""),
                "function": record.get("function", ""),
                "line": record.get("line", 0),
            }
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    return None


def parse_timestamp(ts_str):
    """Parse timestamp ISO8601 en datetime"""
    if not ts_str:
        return None
    try:
        # Loguru repr format: "2026-01-31 14:32:15.123456+00:00"
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def read_and_parse_logs(files, level_filter=None, trace_filter=None):
    """Lit et parse les fichiers de log avec filtres"""
    entries = []
    for log_file in files:
        if not log_file.exists():
            continue
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    entry = parse_loguru_json(line)
                    if not entry:
                        continue
                    if level_filter and entry["level"] != level_filter.upper():
                        continue
                    if trace_filter and entry.get("trace_id") != trace_filter:
                        continue
                    entry["_source_file"] = log_file.name
                    entries.append(entry)
        except (OSError, UnicodeDecodeError) as e:
            print(f"  [WARN] Erreur lecture {log_file}: {e}", file=sys.stderr)
    # Trier par timestamp
    entries.sort(key=lambda e: e["timestamp"])
    return entries


def categorize_operation(message):
    """Categorise une operation pour les alertes"""
    msg_lower = message.lower()
    for op_type, keywords in OPERATION_KEYWORDS.items():
        for kw in keywords:
            if kw in msg_lower:
                return op_type
    return None


def extract_duration_ms(entry):
    """Extrait la duree en ms depuis extra ou depuis le texte du message"""
    extra = entry.get("extra", {})
    for key in ["elapsed_ms", "duration_ms", "response_time_ms"]:
        if key in extra:
            try:
                return float(extra[key])
            except (ValueError, TypeError):
                pass

    # Fallback: parser depuis le message (ex: "-> 200 (279ms)" ou "[279ms]")
    match = re.search(r'\((\d+)ms\)', entry.get("message", ""))
    if not match:
        match = re.search(r'\[(\d+)ms\]', entry.get("message", ""))
    if match:
        return float(match.group(1))

    return None


def build_causal_timeline(entries):
    """Construit les timelines causales groupees par trace_id"""
    traces = defaultdict(list)
    ungrouped = []
    for entry in entries:
        tid = entry.get("trace_id")
        if tid:
            traces[tid].append(entry)
        else:
            ungrouped.append(entry)
    return traces, ungrouped


def check_alerts(entries):
    """Verifie les seuils d'alerte"""
    alerts = []
    for entry in entries:
        duration = extract_duration_ms(entry)
        if duration is None:
            continue
        op_type = categorize_operation(entry["message"])
        if op_type and op_type in ALERT_THRESHOLDS:
            thresholds = ALERT_THRESHOLDS[op_type]
            if duration >= thresholds["critical"]:
                alerts.append({
                    "severity": "CRITIQUE",
                    "type": op_type,
                    "duration_ms": duration,
                    "threshold_ms": thresholds["critical"],
                    "entry": entry,
                })
            elif duration >= thresholds["warning"]:
                alerts.append({
                    "severity": "WARNING",
                    "type": op_type,
                    "duration_ms": duration,
                    "threshold_ms": thresholds["warning"],
                    "entry": entry,
                })
    return alerts


def format_timeline_entry(entry, base_time=None):
    """Formate une entree pour la timeline causale"""
    ts = parse_timestamp(entry["timestamp"])
    delay_str = "0ms"
    if base_time and ts:
        delta_ms = (ts - base_time).total_seconds() * 1000
        delay_str = f"+{delta_ms:.0f}ms"

    duration = extract_duration_ms(entry)
    duration_str = f" [{duration:.0f}ms]" if duration else ""

    # Alerte inline
    alert_tag = ""
    op_type = categorize_operation(entry["message"])
    if op_type and duration:
        thresholds = ALERT_THRESHOLDS.get(op_type, {})
        if duration >= thresholds.get("critical", float("inf")):
            alert_tag = " **[CRITIQUE]**"
        elif duration >= thresholds.get("warning", float("inf")):
            alert_tag = " *[SLOW]*"

    return f"  {entry['level']:<8} | {delay_str:>10} | {entry['message']}{duration_str}{alert_tag}"


def generate_markdown(entries, traces, ungrouped, alerts, config):
    """Genere le rapport markdown"""
    now = datetime.now(timezone.utc)
    lines = []

    lines.append("# Log Aggregator — Aristobot3")
    lines.append(f"**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"**Components:** {', '.join(config.get('components', []))}")
    if config.get("level"):
        lines.append(f"**Level filter:** {config['level']}")
    if config.get("trace"):
        lines.append(f"**Trace filter:** `{config['trace']}`")
    lines.append(
        f"**Total entries:** {len(entries)} | "
        f"**Traces:** {len(traces)} | **Alerts:** {len(alerts)}"
    )
    lines.append("")

    # Alertes
    if alerts:
        lines.append("---")
        lines.append("")
        lines.append("## Alertes")
        lines.append("")
        lines.append("| Sev | Type | Duree | Seuil | Message |")
        lines.append("|---|---|---|---|---|")
        for alert in sorted(alerts, key=lambda a: a["duration_ms"], reverse=True):
            e = alert["entry"]
            lines.append(
                f"| {alert['severity']} | {alert['type']} | "
                f"{alert['duration_ms']:.0f}ms | "
                f">{alert['threshold_ms']}ms | "
                f"`{e['message'][:80]}` |"
            )
        lines.append("")

    # Timelines causales
    if traces:
        lines.append("---")
        lines.append("")
        lines.append("## Timelines Causales (par trace_id)")
        lines.append("")
        for trace_id, trace_entries in sorted(traces.items()):
            lines.append(f"### `{trace_id}`")
            lines.append("")
            base_time = parse_timestamp(trace_entries[0]["timestamp"])
            lines.append("```")
            for entry in trace_entries:
                lines.append(format_timeline_entry(entry, base_time))
            lines.append("```")
            lines.append("")

    # Logs sans trace_id
    lines.append("---")
    lines.append("")
    lines.append("## Logs")
    lines.append("")
    if ungrouped:
        lines.append(f"### Sans trace_id ({len(ungrouped)} entrees)")
        lines.append("")
        lines.append("```")
        for entry in ungrouped[-50:]:
            ts_short = entry["timestamp"][:23] if entry["timestamp"] else "N/A"
            lines.append(
                f"  {ts_short} | {entry['level']:<8} | "
                f"[{entry.get('_source_file', '')}] {entry['message']}"
            )
        lines.append("```")
        lines.append("")

    # Resume par terminal
    lines.append("---")
    lines.append("")
    lines.append("## Resume par terminal")
    lines.append("")
    terminal_counts = defaultdict(lambda: defaultdict(int))
    for entry in entries:
        t = entry.get("terminal_name", "unknown")
        terminal_counts[t][entry["level"]] += 1

    lines.append("| Terminal | DEBUG | INFO | WARNING | ERROR | Total |")
    lines.append("|---|---|---|---|---|---|")
    for terminal in sorted(terminal_counts.keys()):
        counts = terminal_counts[terminal]
        total = sum(counts.values())
        lines.append(
            f"| {terminal} | "
            f"{counts.get('DEBUG', 0)} | "
            f"{counts.get('INFO', 0)} | "
            f"{counts.get('WARNING', 0)} | "
            f"{counts.get('ERROR', 0)} | "
            f"{total} |"
        )
    lines.append("")

    return "\n".join(lines)


def interactive_mode():
    """Mode interactif — selection des composants via menu"""
    print("\n" + "=" * 60)
    print("  LOG AGGREGATOR — Aristobot3")
    print("=" * 60)
    print()
    print("Composants disponibles:")
    print()

    comp_list = list(COMPONENTS.keys())
    for i, comp in enumerate(comp_list, 1):
        info = COMPONENTS[comp]
        exists = "OK" if (LOGS_DIR / info["file"]).exists() else " X"
        print(f"  [{i}] {info['label']:45s} [{exists}]")
    print(f"  [A] Tous les composants")
    print()

    selection = input("Selection (ex: 1,3 ou A): ").strip()

    if selection.upper() == "A":
        selected = comp_list
    else:
        selected = []
        for s in selection.split(","):
            try:
                idx = int(s.strip()) - 1
                if 0 <= idx < len(comp_list):
                    selected.append(comp_list[idx])
            except ValueError:
                pass

    if not selected:
        print("[ERR] Aucun composant selecte.")
        return

    print()
    last_n = input("Nombre de fichiers par composant (Enter = tous): ").strip()
    last_n = int(last_n) if last_n.isdigit() else None

    level = input("Filtrer par niveau (ERROR/WARNING/INFO/DEBUG ou Enter): ").strip().upper()
    level = level if level in ("ERROR", "WARNING", "INFO", "DEBUG") else None

    trace = input("Filtrer par trace_id (Enter = tous): ").strip()
    trace = trace if trace else None

    config = {
        "components": selected,
        "last_n": last_n,
        "level": level,
        "trace": trace,
    }
    run_aggregator(config)


def run_aggregator(config):
    """Execute l'agregation avec la config donnee"""
    print()
    print("[INFO] Collecte des logs...")

    files = collect_log_files(config["components"], config.get("last_n"))
    if not files:
        print("[WARN] Aucun fichier de log trouve.")
        print(f"  Repertoire logs: {LOGS_DIR}")
        print("  Verifier que les terminaux sont lancés.")
        return

    print(f"[INFO] {len(files)} fichier(s) collecte(s)")
    for f in files:
        print(f"  - {f.name} ({f.stat().st_size} bytes)")

    print("[INFO] Parsing...")
    entries = read_and_parse_logs(files, config.get("level"), config.get("trace"))

    if not entries:
        print("[WARN] Aucune entree apres filtrage.")
        return

    print(f"[INFO] {len(entries)} entrees parsees")

    # Timeline causale
    traces, ungrouped = build_causal_timeline(entries)
    print(f"[INFO] {len(traces)} trace(s) causale(s) identifiee(s)")

    # Alertes
    alerts = check_alerts(entries)
    if alerts:
        print(f"[ALERT] {len(alerts)} alerte(s) detectee(s):")
        for a in alerts:
            print(
                f"  [{a['severity']}] {a['type']} — "
                f"{a['duration_ms']:.0f}ms (seuil: >{a['threshold_ms']}ms)"
            )

    # Generer rapport
    print("[INFO] Generation rapport...")
    report = generate_markdown(entries, traces, ungrouped, alerts, config)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"log_report_{timestamp}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[OK] Rapport sauvegarde: {output_file}")
    print()
    print("=" * 60)
    if alerts:
        print("  ALERTES")
        for a in alerts[:5]:
            print(f"  [{a['severity']}] {a['type']} {a['duration_ms']:.0f}ms")
    print(f"  Traces: {len(traces)} | Entrees: {len(entries)} | Alertes: {len(alerts)}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Log Aggregator — Aristobot3 Logging Infrastructure",
        epilog="Sans arguments, lance le mode interactif."
    )
    parser.add_argument(
        "--components", type=str,
        help="Composants separes par virgule (ex: webhook,trading,exchange)"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Tous les composants"
    )
    parser.add_argument(
        "--last", type=int,
        help="N fichiers par composant (chaque fichier = 2 minutes)"
    )
    parser.add_argument(
        "--level", type=str,
        choices=["ERROR", "WARNING", "INFO", "DEBUG"],
        help="Filtrer par niveau"
    )
    parser.add_argument(
        "--trace", type=str,
        help="Filtrer par trace_id (flow complet)"
    )

    args = parser.parse_args()

    # Mode interactif si pas d'arguments
    if not any([args.components, args.all, args.last, args.level, args.trace]):
        interactive_mode()
        return

    # Mode script
    if args.all:
        selected = list(COMPONENTS.keys())
    elif args.components:
        selected = [c.strip() for c in args.components.split(",")]
        invalid = [c for c in selected if c not in COMPONENTS]
        if invalid:
            print(f"[ERR] Composants inconnus: {invalid}")
            print(f"  Disponibles: {list(COMPONENTS.keys())}")
            sys.exit(1)
    else:
        print("[ERR] Specifier --components ou --all")
        sys.exit(1)

    config = {
        "components": selected,
        "last_n": args.last,
        "level": args.level,
        "trace": args.trace,
    }
    run_aggregator(config)


if __name__ == "__main__":
    main()
