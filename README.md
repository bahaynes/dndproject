# Full-Stack Application with FastAPI and Svelte

This is a full-stack application with a FastAPI backend and a Svelte frontend.

## Development Environment Setup

### With Docker (Recommended)

Please refer to the `docker-compose.yml` and the `Containerfile`s in the `frontend` and `backend` directories.

### Without Docker

A streamlined development environment is available for those who prefer not to use Docker.

**1. Setup**

Run the setup script to install all the necessary dependencies for both the frontend and the backend.

```bash
./setup_dev.sh
```

**2. Running Tests**

To run the entire test suite for both frontend and backend, use the following command:

```bash
./run_tests.sh
```

You can also run tests for the frontend or backend individually:

- **Frontend:** `cd frontend && pnpm test`
- **Backend:** `cd backend && pytest`

**3. Running the Application**

To run the application, you can use the `run_app.sh` script:

```bash
./run_app.sh
```

This will build the frontend, apply database migrations, and start the backend server.
