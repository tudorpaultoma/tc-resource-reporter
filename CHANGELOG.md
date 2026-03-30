# Changelog

## v1.1.1 (2026-03-30)

### Fixed
- `COS_REPORT_KEY` is now respected — the directory portion (e.g. `/Report/index.html` → `Report/`) is used as the upload prefix for login + report files
- Files no longer land at bucket root when a key path is configured

## v1.1.0 (2026-03-30)

### Added
- **Login page** — `index.html` is now a login gate; actual report is uploaded as `report_<sha256>.html` where the hash is derived from `SHA-256(username:password)`
- **Logout button** — red button in the report header redirects back to login page
- **Credentials** — configurable via `credentials.json` (gitignored) or `REPORT_USERNAME` / `REPORT_PASSWORD` env vars
- **Automatic cleanup** — old `report_*.html` files in COS are deleted when credentials change
- `credentials.json` and `build_scf.sh` added to `.gitignore`

### Changed
- `publisher.py` rewritten — now uploads two files (login + hashed report) and cleans up stale reports
- `COS_REPORT_KEY` env var removed — the report key is now auto-generated from the credential hash
- Version bumped to 1.1.0

## v1.0.2 (2026-03-27)

### Added
- "By Project" tab — shows only resources with a real `TaggerProject` tag (excludes empty/n/a)
- Project column added to the No-Delete Missing Project tab with red MISSING badge for resources lacking project justification

### Fixed
- CLB `Status` field is numeric (`1` = active) — now translated to human-readable "Active" instead of showing raw `1`
- Unified all state labels across services: `RUNNING`, `ACTIVE`, `AVAILABLE`, `BIND`, `NORMAL`, `Running` → **Active** (green)
- CBS disks: `ATTACHED` → **Attached** (green), `UNATTACHED` → **Unattached** (yellow)
- `STOPPED`, `SHUTDOWN` → **Stopped** (red); `UNBIND`, `DETACHED` → **Detached** (red)
- Mixed-case `Running` (Lighthouse/TKE) now normalised to uppercase before mapping
- `output/` folder added to `.gitignore`

## v1.0.1 (2026-03-27)

### Added
- "No-Delete Missing Project" tab — resources with `TaggerCanDelete=NO` but no `TaggerProject`
- Region dropdown filter on All Resources tab
- Owner dropdown filter on All Resources tab
- Combined AND-logic filtering (search + region + owner)

### Fixed
- CCN `Offset`/`Limit` must be int, not str
- CBS Snapshot attribute is `CreateTime` (not `CreatedTime`)
- TKE tags are nested inside `TagSpecification[].Tags[]` — fixed extraction
- COS publisher auto-splits bucket name if path accidentally included
- Removed `eu-moscow` region — fully unsupported by all APIs
- Cleaned duplicate values in `_state_badge` tuple
- Removed dead `offset`/`limit` variables in EIP scanner (non-paginated API)
- Simplified HAVIP scanner — API does not expose tags directly

### Changed
- Regions: 16 → 15 (removed `eu-moscow`)
- Memory recommendation: 512 MB → 256 MB
- Build process: manual zip instead of `deploy.sh`

## v1.0.0 (2026-03-27)

### Added
- Initial release
- Multi-region resource scanning for: CVM, CLB, CBS, CBS Snapshots, EIP, ENI, HAVIP, NAT Gateway, CCN, TKE, Auto Scaling (groups + launch configs), Lighthouse (instances + snapshots)
- Self-contained static HTML dashboard with dark theme
  - Executive summary cards
  - Tabbed interface: All Resources, By Owner, Expiring Soon, Already Expired, Incomplete Tags, Distribution
  - Client-side search and column sorting
  - Bar-chart distribution visualizations
- COS upload for static website hosting
- Configurable via environment variables (regions, services, expiry threshold, timezone, report title)
- CAM policy template (`policies/reporter-policy.json`)
