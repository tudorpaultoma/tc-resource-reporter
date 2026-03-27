# Changelog

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
