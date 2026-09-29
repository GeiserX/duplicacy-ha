# Usage

## Sensors

Each backup device gets these 21 sensors, each one once the exporter reports its metric. The last six
need exporter 0.5.0 or later; the storage ones also need its storage poller.

| Entity | Description | Unit | Device Class |
|--------|-------------|------|--------------|
| Last successful backup | Timestamp of the most recent successful backup | - | Timestamp |
| Last backup duration | How long the last backup took | seconds | Duration |
| Backup speed | Current upload speed during a running backup | B/s | Data Rate |
| Backup progress | Current backup completion percentage | % | - |
| Bytes uploaded (last) | Bytes uploaded in the last backup | bytes | Data Size |
| New bytes (last) | New bytes detected in the last backup | bytes | Data Size |
| Total files (last) | Number of files processed in the last backup | - | - |
| New files (last) | Number of new files in the last backup | - | - |
| Last exit code | Exit code of the last backup (0 = success, 1 = failure) | - | - |
| Last revision | Revision number of the last backup | - | - |
| Chunks uploaded | Chunks currently being uploaded | - | - |
| Chunks skipped | Chunks skipped (already present) | - | - |
| New chunks (last) | New chunks created in the last backup | - | - |
| Total bytes uploaded | Cumulative bytes uploaded (monotonically increasing) | bytes | Data Size |
| Last successful prune | Timestamp of the most recent successful prune operation | - | Timestamp |
| Files size (last) | Total size of all files in the last backup | bytes | Data Size |
| Chunks size (last) | Total size of the chunks the last backup references, compressed | bytes | Data Size |
| Storage size | Total size of all chunks in the storage (storage poller) | bytes | Data Size |
| Storage chunks | Total number of chunks in the storage (storage poller) | - | - |
| Revisions | Number of revisions for this snapshot ID (storage poller) | - | - |
| Latest revision | Highest revision number for this snapshot ID (storage poller) | - | - |

## Binary sensors

| Entity | Description | Device Class |
|--------|-------------|--------------|
| Backup running | Whether a backup is currently in progress | Running |
| Prune running | Whether a prune operation is currently in progress | Running |

## Example automations

### Alert on backup failure

```yaml
automation:
  - alias: "Duplicacy backup failed"
    trigger:
      - platform: state
        entity_id: sensor.documents_b2_last_exit_code
        to: "1"
    action:
      - service: notify.mobile_app_YOUR_DEVICE_ID
        data:
          title: "Backup Failed"
          message: "Duplicacy backup for 'documents' to B2 has failed."
```

### Alert if no backup in 24 hours

Until the first successful backup the sensor has no timestamp; the `0` default makes the template treat
that as overdue instead of failing.

```yaml
automation:
  - alias: "Duplicacy no backup in 24h"
    trigger:
      - platform: template
        value_template: >
          {{ as_timestamp(now()) - as_timestamp(states('sensor.documents_b2_last_successful_backup'), 0) > 86400 }}
    action:
      - service: notify.mobile_app_YOUR_DEVICE_ID
        data:
          title: "Backup Overdue"
          message: "No successful Duplicacy backup for 'documents' to B2 in the last 24 hours."
```
