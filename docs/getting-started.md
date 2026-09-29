# Getting started

## Prerequisites

- Home Assistant 2024.1 or later.
- A running instance of [duplicacy-exporter](https://github.com/GeiserX/duplicacy-exporter) that
  exposes `/metrics` (Prometheus format) and `/health`, reachable from Home Assistant.
- [HACS](https://hacs.xyz), for the HACS path.

## Install with HACS

1. Open HACS in Home Assistant.
2. Open the three-dot menu in the top right and select **Custom repositories**.
3. Add `https://github.com/GeiserX/duplicacy-ha` with category **Integration**.
4. Search for "Duplicacy Backup Monitor" and install it.
5. Restart Home Assistant.

## Install manually

1. Copy the `custom_components/duplicacy` directory into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Configure

1. Go to **Settings > Devices & services > Add integration**.
2. Search for **Duplicacy Backup Monitor**.
3. Enter the URL of your duplicacy-exporter (default: `http://localhost:9750`).
4. The integration verifies the connection and creates all entities.

A separate device is created for each backup job, identified by snapshot ID and storage target. Each
device gets the sensors and binary sensors listed on [Usage](usage.md). A sensor appears once the
exporter reports its metric, so the storage sensors only show up when the exporter's storage poller is
on, and webhook-mode devices have no revision or prune sensors.

## Removing old devices

If a backup is no longer reported by the exporter (for example a renamed job, or
the combined device replaced by per-folder devices in exporter 0.5.0+), its
device becomes stale. Open the device page and use **Delete** to remove it.
Devices that are still being reported can't be deleted, they would just be
re-created on the next update.
