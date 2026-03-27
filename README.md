# TC Resource Reporter

A Tencent Cloud SCF function that generates a **static HTML dashboard** of all tagged cloud resources and uploads it to a COS bucket for admin browsing.

Part of the TC resource management suite:
| Tool | Purpose | Trigger |
|------|---------|---------|
| [tc-tagger-function](https://github.com/tudorpaultoma/tc-tagger-function) | Tag new resources on creation | COS (CloudAudit) |
| [tc-tag-enforcer](https://github.com/tudorpaultoma/tc-tag-enforcer) | Enforce tags on existing resources | Timer |
| [tc-resource-cleaner](https://github.com/tudorpaultoma/tc-resource-cleaner) | Delete expired resources | Timer |
| [tc-cvm-tag-shutdown](https://github.com/tudorpaultoma/tc-cvm-tag-shutdown) | Auto-stop/start/terminate CVMs | Timer |
| **tc-resource-reporter** (this) | Daily resource dashboard | Timer |

## Features

- **Multi-region scanning** — scans 15 Tencent Cloud regions
- **16 resource types** — CVM, CLB, CBS, CBS Snapshots, EIP, ENI, HAVIP, NAT Gateway (public + private), CCN, TKE, Auto Scaling Groups, Auto Scaling Launch Configs, Lighthouse Instances, Lighthouse Snapshots
- **Self-contained HTML** — single `index.html` with inline CSS & JS, no external dependencies
- **Dashboard sections**:
  - Executive summary cards (totals, warnings, alerts)
  - All Resources with search, region/owner dropdowns & column sorting
  - Resources grouped by Owner
  - Expiring Soon (configurable threshold)
  - Already Expired (overdue resources)
  - Incomplete Tags (missing Owner/Created/TTL)
  - No-Delete Missing Project (TaggerCanDelete=NO without TaggerProject)
  - Distribution charts (by service, region, project, owner)
- **COS upload** — publishes directly to a COS bucket for static website hosting

## Supported Services

| Service | Resource Types |
|---------|---------------|
| CVM | Instances |
| CLB | Load Balancers |
| CBS | Disks, Snapshots |
| VPC | EIP, ENI, HAVIP, NAT Gateway, CCN |
| TKE | Clusters |
| Auto Scaling | Groups, Launch Configurations |
| Lighthouse | Instances, Snapshots |

## Regions

15 regions scanned by default (eu-moscow excluded — fully unsupported):

```
ap-guangzhou, ap-shanghai, ap-nanjing, ap-beijing,
ap-chengdu, ap-chongqing, ap-hongkong, ap-singapore,
ap-jakarta, ap-seoul, ap-tokyo, ap-bangkok,
eu-frankfurt, na-siliconvalley, na-ashburn
```

## Quick Start

### 1. Build Deployment Package

```bash
pip install -t build/ -r requirements.txt
cp -f index.py publisher.py template.py build/
cp -rf services/ build/services/
cp -rf policies/ build/policies/
cd build && zip -qr ../scf-resource-reporter.zip . -x '*.pyc' '*__pycache__*'
```

### 2. Deploy to SCF

| Setting | Value |
|---------|-------|
| Runtime | Python 3.9 |
| Handler | `index.main_handler` |
| Memory | 256 MB |
| Timeout | 300 seconds |

Upload `scf-resource-reporter.zip`.

### 3. Configure Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `COS_REPORT_BUCKET` | **Yes** | — | COS bucket name only (e.g. `my-reports-1234567890`) |
| `COS_REPORT_REGION` | **Yes** | — | COS bucket region (e.g. `ap-singapore`) |
| `COS_REPORT_KEY` | No | `index.html` | Object key for the report |
| `REPORT_REGIONS` | No | all 15 regions | Comma-separated region list |
| `REPORT_SERVICES` | No | all | Comma-separated service filter |
| `EXPIRY_WARNING_DAYS` | No | `3` | Days before expiry to flag |
| `TIMEZONE_OFFSET` | No | `8` | Hours offset from UTC |
| `REPORT_TITLE` | No | `TC Resource Report` | Dashboard title |

> **Note:** `COS_REPORT_BUCKET` must be the bucket name only — do not include paths. Use `COS_REPORT_KEY` for the object path.

### 4. Set Timer Trigger

Recommended: daily at 8 AM UTC+8

```
0 0 8 * * * *
```

### 5. IAM Policy

Attach `policies/reporter-policy.json` to the SCF execution role. The role requires:
- **Read-only** access to CVM, CLB, CBS, VPC, TKE, AS, Lighthouse, Tag APIs
- **Write** access to the target COS bucket
- **Note:** EIP uses `vpc:DescribeAddresses` (not `cvm:DescribeAddresses`)

## COS Static Website Setup

1. Create a COS bucket (e.g., `tc-reports-1234567890`)
2. Enable **Static Website** in bucket settings
3. Set index document to `index.html`
4. The report will be accessible at: `https://tc-reports-1234567890.cos-website.ap-singapore.myqcloud.com`

## Project Structure

```
tc-resource-reporter/
├── index.py              # SCF handler & orchestrator
├── template.py           # HTML template (inline CSS/JS)
├── publisher.py          # COS upload logic
├── services/
│   ├── __init__.py
│   ├── cvm.py
│   ├── clb.py
│   ├── cbs.py
│   ├── snapshot.py
│   ├── eip.py
│   ├── eni.py
│   ├── havip.py
│   ├── nat.py
│   ├── ccn.py
│   ├── tke.py
│   ├── autoscaling.py
│   └── lighthouse.py
├── policies/
│   └── reporter-policy.json
├── requirements.txt
├── CHANGELOG.md
├── README.md
└── LICENSE
```

## How It Works

1. **Timer trigger** fires daily
2. `main_handler` resolves SCF credentials and iterates regions × services
3. Each service scanner lists resources via the Tencent Cloud SDK, extracting tag metadata
4. `compute_stats` groups resources by owner, calculates expiry, flags incomplete tags
5. `render_report` populates the HTML template with data
6. `upload_to_cos` pushes `index.html` to the configured COS bucket
7. Admin browses the COS static website URL

## Tags Used

The reporter reads these tags (set by tc-tagger-function / tc-tag-enforcer):

| Tag | Purpose |
|-----|---------|
| `TaggerOwner` | Resource creator/owner |
| `TaggerCreated` | Creation timestamp |
| `TaggerTTL` | Time-to-live in days |
| `TaggerCanDelete` | Whether auto-deletion is allowed |
| `TaggerProject` | Project assignment |
| `TaggerAutoOff` | CVM auto-shutdown flag |
| `TaggerAutoStart` | CVM auto-start flag |

## License

GPL-3.0 — see [LICENSE](LICENSE)
