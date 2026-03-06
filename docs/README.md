# Documentation

The documentation for this project is built using [MkDocs](https://www.mkdocs.org/) and [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).
API documentation is automatically generated from Python docstrings using [mkdocstrings](https://mkdocstrings.github.io/).

## Setup

1.  Ensure you have the documentation dependencies installed:
    ```bash
    pip install -r backend/requirements.txt
    ```
    (Note: These are included in the dev container if you rebuild it)

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
