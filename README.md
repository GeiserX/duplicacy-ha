<p align="center">
  <img src="docs/images/banner.svg" alt="Duplicacy Backup Monitor" width="900"/>
</p>

# Duplicacy Backup Monitor for Home Assistant

[![Tests](https://github.com/GeiserX/duplicacy-ha/actions/workflows/tests.yml/badge.svg)](https://github.com/GeiserX/duplicacy-ha/actions/workflows/tests.yml)
[![License](https://img.shields.io/github/license/GeiserX/duplicacy-ha)](LICENSE)
[![codecov](https://codecov.io/gh/GeiserX/duplicacy-ha/graph/badge.svg)](https://codecov.io/gh/GeiserX/duplicacy-ha)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)
[![GitHub Stars](https://img.shields.io/github/stars/GeiserX/duplicacy-ha)](https://github.com/GeiserX/duplicacy-ha/stargazers)

A Home Assistant custom integration that monitors [Duplicacy](https://duplicacy.com) backups through the [duplicacy-exporter](https://github.com/GeiserX/duplicacy-exporter) Prometheus exporter: backup status, progress, speed and history on your dashboard.

## Features

- One Home Assistant device per backup job, keyed by snapshot ID and storage target.
- Up to 21 sensors: the last run's summary, live speed and progress, cumulative bytes, prune, and storage size and revisions.
- 2 binary sensors: backup running and prune running.
- Works with both exporter modes, `log_tail` for the Duplicacy CLI and `webhook` for the Web UI.
- Polls the exporter's `/metrics` every 30 seconds; the setup form checks `/health` first.
- Config flow with one field, the exporter URL.

## Quick start

Needs Home Assistant 2024.1 or later and a running duplicacy-exporter.

1. In HACS, open the three-dot menu > **Custom repositories** and add `https://github.com/GeiserX/duplicacy-ha` with category **Integration**.
2. Search for "Duplicacy Backup Monitor", install it, and restart Home Assistant.
3. Go to **Settings > Devices & services > Add integration** and search for **Duplicacy Backup Monitor**.
4. Enter the exporter URL as Home Assistant can reach it; the default `http://localhost:9750` only works when both run on the same network namespace.

Manual install and removing stale devices are in [Getting started](docs/getting-started.md).

## Documentation

- [Getting started](docs/getting-started.md): prerequisites, HACS and manual install, configuration, removing old devices
- [Usage](docs/usage.md): every sensor and binary sensor, example automations

## Related projects

Duplicacy family: [duplicacy-exporter](https://github.com/GeiserX/duplicacy-exporter), [duplicacy-cli-cron](https://github.com/GeiserX/duplicacy-cli-cron), [duplicacy-mcp](https://github.com/GeiserX/duplicacy-mcp), [duplicacy-container](https://github.com/GeiserX/duplicacy-container). Other Home Assistant integrations: [cashpilot-ha](https://github.com/GeiserX/cashpilot-ha), [genieacs-ha](https://github.com/GeiserX/genieacs-ha), [pumperly-ha](https://github.com/GeiserX/pumperly-ha).

## License

[GPL-3.0-or-later](LICENSE)
