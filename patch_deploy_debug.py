with open('.github/workflows/deploy.yml', 'r') as f:
    content = f.read()

old_alembic = """      - name: Run Alembic Migrations
        if: github.event_name == 'pull_request'
        working-directory: backend
        run: |
          pip install uv
          uv sync --group dev
          DATABASE_URL="${{ steps.create_neon_branch.outputs.db_url_with_pooler }}" uv run alembic upgrade head"""

new_alembic = """      - name: Run Alembic Migrations
        if: github.event_name == 'pull_request'
        working-directory: backend
        env:
          NEON_DB_URL: ${{ steps.create_neon_branch.outputs.db_url }}
          NEON_DB_URL_POOLER: ${{ steps.create_neon_branch.outputs.db_url_with_pooler }}
        run: |
          echo "Debugging outputs:"
          echo "db_url_with_pooler: $NEON_DB_URL_POOLER"
          echo "db_url: $NEON_DB_URL"

          # Fallback to db_url if db_url_with_pooler is empty
          URL="$NEON_DB_URL_POOLER"
          if [ -z "$URL" ]; then
            URL="$NEON_DB_URL"
          fi

          if [ -z "$URL" ]; then
            echo "ERROR: Database URL is still empty. Neon action might have failed silently or returned different output keys."
            # Force exit 1 manually to fail CI
            python -c "import sys; sys.exit(1)"
          fi

          pip install uv
          uv sync --group dev
          DATABASE_URL="$URL" uv run alembic upgrade head"""

content = content.replace(old_alembic, new_alembic)

with open('.github/workflows/deploy.yml', 'w') as f:
    f.write(content)
