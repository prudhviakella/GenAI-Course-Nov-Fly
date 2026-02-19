# Prerequisites Check — Checkpoint System

## Overview

The enhanced `check_prerequisites.py` now includes a **checkpoint system** that saves progress after each check. This prevents re-running expensive operations (like Docker builds) when fixing issues in later checks.

---

## Key Features

### 1. **Automatic Resume**
- Script automatically resumes from the last successful check
- No need to re-run completed checks
- Saves time on expensive operations (Docker build = 8-12 minutes)

### 2. **Execution Modes**

| Mode | Command | Description |
|------|---------|-------------|
| **Checkpoint (default)** | `python check_prerequisites.py` | Resumes from last checkpoint |
| **Full execution** | `python check_prerequisites.py --full` | Runs all checks from beginning |
| **Resume from specific check** | `python check_prerequisites.py --from-check 5` | Starts from check 5 |
| **List history** | `python check_prerequisites.py --list-checkpoints` | Shows recent runs |

### 3. **Persistent Logging**
- Each run creates a timestamped log file
- Logs stored in `.checkpoints/logs/`
- Full execution history with pass/fail counts

### 4. **Interrupt Recovery**
- Press `Ctrl+C` to interrupt
- Progress automatically saved
- Resume exactly where you left off

---

## Usage Examples

### Example 1: First Run (No Checkpoint)
```bash
$ python check_prerequisites.py

[MODE] No checkpoint found - running all checks

============================================================
  RAY PIPELINE — PREREQUISITES CHECK
  Platform: Darwin 25.2.0
============================================================

[ 1 ] AWS CLI
  [PASS] Installed: aws-cli/2.31.15

[ 2 ] AWS Credentials
  [PASS] Account: 123456789012
  ...
  
[ 8 ] Docker Image — Build & Push to ECR
  [INFO] Building image...
  [PASS] Image pushed to ECR
  
[INFO] Checkpoint saved: Check 8 (Docker Image Build & Push) - PASS
```

**Result**: Checkpoint saved after check 8

---

### Example 2: Resume After Failure

**First run** (fails at check 7):
```bash
$ python check_prerequisites.py

[ 7 ] S3 Bucket Name
  [FAIL] S3BucketName is still the placeholder value
  
[INFO] Checkpoint saved: Check 7 (S3 Bucket Name) - COMPLETED
```

**Fix the issue**:
```bash
# Edit cloudformation-parameters.json
vim 2_cloudformation/cloudformation-parameters.json
# Change S3BucketName to unique value
```

**Re-run** (automatically resumes from check 7):
```bash
$ python check_prerequisites.py

[MODE] Checkpoint found from 2 minutes ago
       Last completed: Check 6 (API Keys → Secrets Manager) - PASS
       Resuming from: Check 7
       Tip: Use --full to run all checks from beginning

============================================================
  RAY PIPELINE — PREREQUISITES CHECK
============================================================

[ 1 ] AWS CLI - Skipped (completed in previous run)
[ 2 ] AWS Credentials - Skipped (completed in previous run)
...
[ 6 ] API Keys → Secrets Manager - Skipped (completed in previous run)

[ 7 ] S3 Bucket Name
  [PASS] S3BucketName: ray-pipeline-prudhvi-2026

[ 8 ] Docker Image — Build & Push to ECR - Skipped (completed in previous run)
[ 9 ] AWS Service Quotas
  [PASS] VPC quota OK: 2/5 used
  ...
```

**Result**: Only re-ran checks 7, 9, 10 (saves 8-12 minutes)

---

### Example 3: Full Re-execution

**Force full run** (ignores checkpoint):
```bash
$ python check_prerequisites.py --full

[MODE] Full execution - running all checks from beginning

[ 1 ] AWS CLI
  [PASS] Installed: aws-cli/2.31.15
  
[ 2 ] AWS Credentials
  [PASS] Account: 123456789012
  
... (runs all 10 checks)
```

**When to use**:
- After updating AWS credentials
- After major infrastructure changes
- When troubleshooting checkpoint issues
- Weekly validation runs

---

### Example 4: Resume from Specific Check

**Scenario**: Docker build succeeded, but want to rebuild image
```bash
$ python check_prerequisites.py --from-check 8

[MODE] Resuming from check 8

[ 1 ] AWS CLI - Skipped (completed in previous run)
...
[ 7 ] S3 Bucket Name - Skipped (completed in previous run)

[ 8 ] Docker Image — Build & Push to ECR
  [INFO] Building image...
  [PASS] Image pushed to ECR
```

---

### Example 5: View Checkpoint History

```bash
$ python check_prerequisites.py --list-checkpoints

================================================================================
  CHECKPOINT HISTORY
================================================================================

1. 2026-02-18 14:32:15
   Log: prerequisites_run_20260218_143215.log
   Results: 22 passed, 1 failed

2. 2026-02-18 14:15:03
   Log: prerequisites_run_20260218_141503.log
   Results: 19 passed, 1 failed

3. 2026-02-18 13:45:22
   Log: prerequisites_run_20260218_134522.log
   Results: 18 passed, 2 failed

================================================================================
```

---

## Checkpoint File Structure

### Directory Layout
```
1_prerequisites/
├── check_prerequisites.py
└── .checkpoints/
    ├── latest_checkpoint.json          # Current checkpoint
    └── logs/
        ├── prerequisites_run_20260218_143215.log
        ├── prerequisites_run_20260218_141503.log
        └── prerequisites_run_20260218_134522.log
```

### Checkpoint JSON Format
```json
{
  "timestamp": "2026-02-18T14:32:15.123456",
  "last_completed_check": 8,
  "check_name": "Docker Image Build & Push",
  "status": "PASS",
  "pass_count": 22,
  "fail_count": 0,
  "log_file": "/path/to/.checkpoints/logs/prerequisites_run_20260218_143215.log",
  "details": {}
}
```

### Log File Format
```
14:32:10 | ============================================================
14:32:10 | Prerequisites Check Started: 2026-02-18 14:32:10
14:32:10 | Platform: Darwin 25.2.0
14:32:10 | ============================================================
14:32:10 | Execution mode: CHECKPOINT RESUME from check 8
14:32:15 | [PASS] Image pushed to ECR
14:32:15 | Checkpoint saved: Check 8 (Docker Image Build & Push) - PASS
14:32:20 | [PASS] VPC quota OK: 2/5 used
14:32:25 | Prerequisites check completed. Passed: 22, Failed: 0
14:32:25 | Log saved to: /path/to/prerequisites_run_20260218_143215.log
```

---

## Time Savings

### Without Checkpoint System
```
First run:        12 minutes  (includes 8min Docker build)
Fix check 7:      12 minutes  (rebuilds Docker image)
Fix check 9:      12 minutes  (rebuilds Docker image again)
---
Total:            36 minutes
```

### With Checkpoint System
```
First run:        12 minutes  (includes 8min Docker build)
Fix check 7:      2 minutes   (skips Docker build)
Fix check 9:      2 minutes   (skips Docker build)
---
Total:            16 minutes  (saves 20 minutes!)
```

---

## Advanced Usage

### Manual Checkpoint Management

**View current checkpoint**:
```bash
cat 1_prerequisites/.checkpoints/latest_checkpoint.json
```

**Clear checkpoint** (force full re-run):
```bash
rm 1_prerequisites/.checkpoints/latest_checkpoint.json
python check_prerequisites.py
```

**View specific log**:
```bash
cat 1_prerequisites/.checkpoints/logs/prerequisites_run_20260218_143215.log
```

**Clean old logs** (keep last 10):
```bash
cd 1_prerequisites/.checkpoints/logs/
ls -t prerequisites_run_*.log | tail -n +11 | xargs rm
```

---

## CI/CD Integration

### GitHub Actions with Checkpoints

```yaml
name: Deploy Ray Pipeline
on: [push]

jobs:
  prerequisites:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Cache checkpoint
        uses: actions/cache@v3
        with:
          path: 1_prerequisites/.checkpoints
          key: prerequisites-${{ github.sha }}
          restore-keys: |
            prerequisites-
      
      - name: Run prerequisites (with checkpoint)
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          PINECONE_API_KEY: ${{ secrets.PINECONE_API_KEY }}
        run: python 1_prerequisites/check_prerequisites.py
      
      - name: Upload logs on failure
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: prerequisite-logs
          path: 1_prerequisites/.checkpoints/logs/*.log
```

---

## Troubleshooting

### Issue: Checkpoint stuck on failing check

**Symptom**:
```
[MODE] Resuming from check 7
[ 7 ] S3 Bucket Name
  [FAIL] S3BucketName is still the placeholder value
```

**Solution**:
1. Fix the issue (edit `cloudformation-parameters.json`)
2. Re-run: `python check_prerequisites.py`
3. Script automatically retries check 7

---

### Issue: Want to force rebuild Docker image

**Symptom**: Image exists in ECR but want to rebuild with code changes

**Solution**:
```bash
# Option 1: Re-run just Docker build
python check_prerequisites.py --from-check 8

# Option 2: Full re-run
python check_prerequisites.py --full
```

---

### Issue: Checkpoint corrupted

**Symptom**:
```
Error loading checkpoint: Invalid JSON
```

**Solution**:
```bash
# Delete checkpoint and start fresh
rm 1_prerequisites/.checkpoints/latest_checkpoint.json
python check_prerequisites.py
```

---

### Issue: Need to debug a specific check

**Symptom**: Check 5 (AWS Permissions) failing, want detailed output

**Solution**:
```bash
# Run from check 5 and view log
python check_prerequisites.py --from-check 5

# View detailed log
cat 1_prerequisites/.checkpoints/logs/prerequisites_run_*.log | tail -50
```

---

## Best Practices

### Development Workflow

1. **First deployment**:
   ```bash
   python check_prerequisites.py --full
   ```
   Run all checks, creates baseline

2. **Iterative fixes**:
   ```bash
   python check_prerequisites.py
   ```
   Let checkpoints save time

3. **Code changes**:
   ```bash
   python check_prerequisites.py --from-check 8
   ```
   Rebuild Docker image only

4. **Weekly validation**:
   ```bash
   python check_prerequisites.py --full
   ```
   Verify entire setup

### Checkpoint Hygiene

**Keep logs for 30 days**:
```bash
# Add to crontab or run manually
find 1_prerequisites/.checkpoints/logs/ -name "*.log" -mtime +30 -delete
```

**Monitor disk usage**:
```bash
du -sh 1_prerequisites/.checkpoints/
# Typical size: 1-5 MB
```

**Backup checkpoints** (optional):
```bash
tar -czf checkpoints_backup.tar.gz 1_prerequisites/.checkpoints/
```

---

## Command Reference

| Command | Alias | Description |
|---------|-------|-------------|
| `python check_prerequisites.py` | - | Resume from checkpoint (default) |
| `python check_prerequisites.py --full` | `-f` | Run all checks from beginning |
| `python check_prerequisites.py --from-check N` | - | Resume from specific check (1-10) |
| `python check_prerequisites.py --list-checkpoints` | `-l` | Show checkpoint history |

---

## Comparison: Before vs After

### Before (No Checkpoints)
```
❌ Re-runs all checks every time
❌ Docker build repeated (8-12 min each time)
❌ No execution history
❌ No interrupt recovery
❌ Manual tracking of what failed
```

### After (With Checkpoints)
```
✅ Resumes from last successful check
✅ Docker build only once (saves 8-12 min per fix)
✅ Full execution history with logs
✅ Interrupt recovery (Ctrl+C safe)
✅ Automatic tracking of progress
```

---

## FAQ

**Q: Will checkpoints work across different terminals?**  
A: Yes. Checkpoints are file-based and work across any terminal session.

**Q: What if I update AWS credentials?**  
A: Run `python check_prerequisites.py --full` to re-validate all checks.

**Q: Can I delete `.checkpoints/` directory?**  
A: Yes. It will be recreated on next run. You'll lose history but no harm.

**Q: What happens if check 8 fails after 5 minutes?**  
A: Checkpoint saves progress. Next run resumes from check 8, retries the build.

**Q: Can multiple users share checkpoints?**  
A: No. Checkpoints are local to each machine. Each user maintains their own.

**Q: Does checkpoint slow down execution?**  
A: No. Checkpoint save is <10ms. Negligible overhead.

---

## Summary

The checkpoint system transforms the prerequisites workflow:

| Metric | Before | After |
|--------|--------|-------|
| **Average fix time** | 12 minutes | 2 minutes |
| **Docker rebuilds** | Every run | Once per change |
| **Interrupt recovery** | Start over | Resume instantly |
| **Execution history** | None | Full logs |
| **Developer experience** | Frustrating | Smooth |

**Key takeaway**: Checkpoints save 10+ minutes per iteration when fixing issues. Essential for iterative development!

---

**Last updated**: February 18, 2026  
**Version**: 2.0.0 (Checkpoint System)