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
- **Self-contained HTML** — single report file with inline CSS & JS, no external dependencies
- **Login-gated access** — static login page with SHA-256 hashed filename; report URL is unguessable without credentials
- **Dashboard sections**:
  - Executive summary cards (totals, warnings, alerts)
  - All Resources with search, region/owner dropdowns & column sorting
  - Resources grouped by Owner
  - Resources grouped by Project
  - Expiring Soon (configurable threshold)
  - Already Expired (overdue resources)
  - Incomplete Tags (missing Owner/Created/TTL)
  - No-Delete Missing Project (TaggerCanDelete=NO without TaggerProject)
  - Distribution charts (by service, region, project, owner)
- **COS upload** — publishes login page + hashed report to a COS bucket for static website hosting

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
rm -rf package tc-resource-reporter.zip
mkdir package
pip3 install -t package -r requirements.txt
cd package && zip -r9 ../tc-resource-reporter.zip . -x "*/__pycache__/*" "*/.DS_Store" && cd ..
zip -r9 tc-resource-reporter.zip index.py template.py publisher.py credentials.json services/ policies/ \
  -x "services/__pycache__/*" "*/.DS_Store"
```

> **Important:** Include `credentials.json` in the zip (or set `REPORT_USERNAME` / `REPORT_PASSWORD` env vars in the SCF console).

### 2. Deploy to SCF

| Setting | Value |
|---------|-------|
| Runtime | Python 3.9 |
| Handler | `index.main_handler` |
| Memory | 256 MB |
| Timeout | 300 seconds |

Upload `tc-resource-reporter.zip`.

### 3. Configure Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `COS_REPORT_BUCKET` | **Yes** | — | COS bucket name only (e.g. `my-reports-1234567890`) |
| `COS_REPORT_REGION` | **Yes** | — | COS bucket region (e.g. `ap-singapore`) |
| `COS_REPORT_KEY` | No | `index.html` | Upload path inside the bucket (e.g. `/Report/index.html`). The directory portion becomes the upload prefix for all files. |
| `REPORT_USERNAME` | No* | — | Login username (alternative to `credentials.json`) |
| `REPORT_PASSWORD` | No* | — | Login password (alternative to `credentials.json`) |
| `REPORT_REGIONS` | No | all 15 regions | Comma-separated region list |
| `REPORT_SERVICES` | No | all | Comma-separated service filter |
| `EXPIRY_WARNING_DAYS` | No | `3` | Days before expiry to flag |
| `TIMEZONE_OFFSET` | No | `8` | Hours offset from UTC |
| `REPORT_TITLE` | No | `TC Resource Report` | Dashboard title |

> **Note:** `COS_REPORT_BUCKET` must be the bucket name only — do not include paths.
>
> \* Credentials can be set via env vars **or** by including `credentials.json` in the deployment zip. Env vars take priority.

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

## Authentication

The dashboard is protected by a client-side login gate suitable for COS static hosting (no server needed).

### How it works

1. `index.html` is a **login page** — it prompts for username and password
2. On submit, the browser computes `SHA-256(username + ":" + password)` using the Web Crypto API
3. The browser attempts to fetch `report_<hash>.html` — if the hash matches, the report loads
4. Without valid credentials, the report URL is **unguessable** (64-char hex hash)
5. The report includes a **Logout** button that redirects back to the login page

### Configuring credentials

**Option 1 — `credentials.json`** (bundled in the zip, gitignored):

```json
{
  "username": "admin",
  "password": "your-secure-password"
}
```

**Option 2 — Environment variables** (set in SCF console, takes priority):

| Variable | Value |
|----------|-------|
| `REPORT_USERNAME` | `admin` |
| `REPORT_PASSWORD` | `your-secure-password` |

> When credentials change, the old report file is automatically deleted from COS on the next run.

### Security notes

- This is **not** server-side auth — it's security through an unguessable URL
- If someone captures the full report URL, they can access it directly until the next credential change
- For internal dashboards this provides practical access control without extra infrastructure
- For stronger protection, consider making the COS bucket private and using CDN signed URLs

## COS Static Website Setup

1. Create a COS bucket (e.g., `tc-reports-1234567890`)
2. Enable **Static Website** in bucket settings
3. Set index document to `index.html`
4. The report will be accessible at: `https://tc-reports-1234567890.cos-website.ap-singapore.myqcloud.com`

## Project Structure

```
tc-resource-reporter/
├── index.py              # SCF handler & orchestrator
├── template.py           # HTML templates (login + dashboard)
├── publisher.py          # COS upload logic (login + hashed report)
├── credentials.json      # Login credentials (gitignored)
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
2. `main_handler` loads report credentials and computes `SHA-256(username:password)` for the report filename
3. Resolves SCF credentials and iterates regions × services
4. Each service scanner lists resources via the Tencent Cloud SDK, extracting tag metadata
5. `compute_stats` groups resources by owner, calculates expiry, flags incomplete tags
6. `render_login` generates the login page (`index.html`)
7. `render_report` populates the dashboard template (`report_<hash>.html`)
8. `upload_to_cos` pushes both files and deletes any old report files from previous credential hashes
9. Admin browses the COS static website URL, logs in, and views the dashboard

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
