# Documentation

The documentation for this project is built using [MkDocs](https://www.mkdocs.org/) and [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).
API documentation is automatically generated from Python docstrings using [mkdocstrings](https://mkdocstrings.github.io/).

## Setup

1.  Ensure you have the documentation dependencies installed. The project uses
    `uv` for dependency management — the docs deps are included in the dev group:
    ```bash
    cd backend && uv sync
    ```
    Alternatively, install standalone with pip:
    ```bash
    pip install mkdocs mkdocs-material "mkdocstrings[python]"
    ```

## Building the Docs

To serve the documentation locally with live reloading:

```bash
mkdocs serve
```

Open [http://localhost:8001](http://localhost:8001) in your browser.

To build the static site (e.g. for deployment):

```bash
mkdocs build
```

The output will be in the `site/` directory.

## Structure

- `mkdocs.yml`: Configuration file.
- `docs/`: Markdown documentation files.
- `docs/reference/`: Auto-generated API reference pages.

## Updating API Docs

If you add new modules, create a new markdown file in `docs/reference/app/modules/` with the following content:

```markdown
# Module Name

::: app.modules.new_module_name
```

Then add it to the `nav` section in `mkdocs.yml`.
