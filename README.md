# Full-Stack Application with FastAPI and Svelte

This is a full-stack application with a FastAPI backend and a Svelte frontend.

## Development Environment Setup

This project uses a container-based development environment powered by Docker and managed by a set of helper scripts. This is the recommended way to work on the project.

**1. Initial Setup**

First, build the development images. This command only needs to be run once, or whenever you change the dependencies in the `Containerfile.dev` files.

```bash
/app/setup.sh
```

**2. Running the Development Environment**

To start the frontend and backend services, run:

```bash
/app/run_dev.sh
```

This will start the services in the background. The backend will be available at `http://localhost:8000` and the frontend at `http://localhost:5173`.

**3. Running Tests**

To run the test suite, use the `run_tests_dev.sh` script.

```bash
# Run all tests
/app/run_tests_dev.sh

# Run only frontend tests
/app/run_tests_dev.sh --frontend

# Run only backend tests
/app/run_tests_dev.sh --backend
```

**4. Stopping the Development Environment**

To stop all running services, run:

```bash
/app/stop_dev.sh
```
