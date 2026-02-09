#!/bin/bash
# =============================================================================
# generate_docs.sh - Generate MkDocs Reference Structure
# =============================================================================
# Usage: ./generate_docs.sh
#
# Creates the documentation file structure for MkDocs.
# Run this when adding new backend modules to regenerate reference pages.
#
# After running:
#   1. Update mkdocs.yml nav section if new modules added
#   2. Preview with: make docs-serve
# =============================================================================
set -e

echo "==> Creating documentation structure..."

mkdir -p docs/reference/app/modules

# Create index page
cat > docs/index.md <<'EOF'
# DnD Westmarches Hub Documentation

Welcome to the documentation for DnD Westmarches Hub - a web-based companion app for running West Marches–style campaigns.

## Overview

- **Backend**: FastAPI application with SQLAlchemy ORM
- **Frontend**: SvelteKit with TailwindCSS
- **Infrastructure**: Podman containers with Kube YAML manifests

## Quick Links

- [Getting Started](../README.md)
- [API Reference](reference/app/main.md)
- [Contributing](../AGENTS.md)
EOF

# Helper function to create module doc file
create_doc() {
    local file=$1
    local identifier=$2
    cat > "docs/$file" <<EOF
# ${identifier##*.}

::: app.$identifier
EOF
}

# Create core reference docs
create_doc "reference/app/main.md" "main"
create_doc "reference/app/config.md" "config"
create_doc "reference/app/dependencies.md" "dependencies"

# Create module reference docs
create_doc "reference/app/modules/admin.md" "modules.admin"
create_doc "reference/app/modules/auth.md" "modules.auth"
create_doc "reference/app/modules/campaigns.md" "modules.campaigns"
create_doc "reference/app/modules/characters.md" "modules.characters"
create_doc "reference/app/modules/items.md" "modules.items"
create_doc "reference/app/modules/maps.md" "modules.maps"
create_doc "reference/app/modules/missions.md" "modules.missions"
create_doc "reference/app/modules/oneshot.md" "modules.oneshot"
create_doc "reference/app/modules/sessions.md" "modules.sessions"

echo "==> Documentation structure created!"
echo ""
echo "Next steps:"
echo "  1. Update mkdocs.yml if you added new modules"
echo "  2. Preview: make docs-serve"
echo "  3. Build:   make docs-build"
