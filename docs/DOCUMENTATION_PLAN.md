# Documentation Improvement Plan

This document outlines the plan for improving project documentation, making scripts clearer, and ensuring consistency across all project files.

## Phase 1: Immediate Cleanup ✅ (Completed)

### 1.1 AGENTS.md Improvements ✅
- [x] Update development workflow to reference correct scripts (`./kube/dev.sh`, `./kube/teardown.sh`)
- [x] Remove outdated Docker Compose references (project uses Podman Kube)
- [x] Update troubleshooting section with Podman-specific issues
- [x] Add UV package manager information
- [x] Clean formatting with tables for readability

### 1.2 README.md Improvements ✅
- [x] Rename title from "Full-Stack Application" to "DnD Westmarches Hub"
- [x] Fix all script path references to match actual locations
- [x] Simplify development environment section
- [x] Add quick start section for contributors
- [x] Consolidate deployment documentation with clear options

### 1.3 Script Cleanup ✅
- [x] Add clear header documentation to all kube scripts
- [x] Document `create_from_file.sh` with usage examples
- [x] Improve `generate_docs.sh` with better structure
- [x] Clean up `setup.sh` with checkmarks and better output
- [x] Simplify `run_tests.sh`

### 1.4 Makefile Cleanup ✅
- [x] Remove `-host` targets (Jules-specific, not for general use)
- [x] Add `make help` with all available commands
- [x] Add `make logs` shortcut
- [x] Organize into logical sections with comments

### 1.5 .env.example Updates ✅
- [x] Add missing Discord authentication variables
- [x] Add section comments for clarity
- [x] Mark required vs optional variables

## Phase 2: Documentation Structure (Future Work)

### 2.1 docs/ Directory Organization
- [ ] Review and update `docs/index.md` with accurate project description
- [ ] Update `docs/README.md` to reflect actual MkDocs setup
- [ ] Ensure all API reference docs are generating correctly
- [ ] Add architecture overview diagram

### 2.2 New Documentation Pages
- [ ] **CONTRIBUTING.md** - Contribution guidelines for new developers
- [ ] **DEVELOPMENT.md** - Detailed local development setup
- [ ] **DEPLOYMENT.md** - Production deployment guide (move from README)
- [ ] **API.md** - API usage examples and authentication flow
- [ ] **DATABASE.md** - Database schema and migration guide

## Phase 3: Script Documentation (Future Work)

### 3.1 Add Help Output
Each script should support `--help` flag with:
- Purpose description
- Usage examples
- Environment variable requirements
- Exit codes

### 3.2 Script Standardization
- Use consistent variable naming (`PROJECT_DIR`, `SCRIPT_DIR`)
- Add error handling with descriptive messages
- Add color-coded output for success/failure
- Use `set -euo pipefail` consistently

## Phase 4: Auto-generated Documentation (Future Work)

### 4.1 API Documentation
- [ ] Ensure FastAPI OpenAPI docs are complete
- [ ] Add request/response examples
- [ ] Document authentication requirements per endpoint

### 4.2 Frontend Documentation
- [ ] Add Storybook or similar for component documentation
- [ ] Document Svelte store structure
- [ ] Add route documentation

## Summary of Changes Made

| File | Changes |
|------|---------|
| `AGENTS.md` | Complete rewrite with accurate Podman workflow, tables, troubleshooting |
| `README.md` | Renamed, accurate paths, consolidated deployment options |
| `Makefile` | Removed host targets, added help command, organized sections |
| `.env.example` | Added Discord vars, clear sections, required markers |
| `kube/dev.sh` | Added header docs |
| `kube/deploy.sh` | Added header docs |
| `kube/build.sh` | Added header docs |
| `kube/teardown.sh` | Added header docs |
| `kube/setup_secrets.sh` | Added header docs, improved output |
| `kube/install-quadlet.sh` | Added header docs |
| `setup.sh` | Cleaned up output with checkmarks |
| `run_tests.sh` | Simplified, added header docs |
| `create_from_file.sh` | Added comprehensive usage docs |
| `generate_docs.sh` | Improved structure and output |
