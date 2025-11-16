# Testing Commands Quick Reference

## 📋 Available Test Commands

All tests run in isolated Docker containers that **spin up separately** from your development environment.

### Key Features:
✅ **Isolated Environment** - Tests run in a separate container from your dev server
✅ **Fresh Build** - Each test run uses the latest code
✅ **Non-Intrusive** - Your local dev container keeps running
✅ **Auto-Cleanup** - Test container is removed after tests complete

### 1. **Run Unit Tests**
```bash
make test
```
- Spins up a fresh test container with latest code
- Runs all tests in `tests/` directory
- Automatically cleans up after completion
- Your dev container (`localhost:5000`) keeps running

### 2. **Run Tests with Coverage**
```bash
make test-cov
```
- Spins up a fresh test container
- Runs tests with coverage analysis
- Generates HTML coverage report in `htmlcov/`
- Shows coverage percentage in terminal
- Auto-cleanup after completion

### 3. **Run Tests in Watch Mode**
```bash
make test-watch
```
- Spins up a persistent test container
- Watches for file changes on host
- Automatically re-runs tests on save
- Great for TDD (Test-Driven Development)
- Press `Ctrl+C` to stop and cleanup
- Your dev container keeps running independently

## 🚀 Quick Start

### First Time Setup
```bash
# Build the Docker image (development)
make build

# Start the development server
make up
```

### Running Tests (While Dev Server is Running!)
```bash
# Your dev server is running on localhost:5000...

# In another terminal, run tests (they use a separate container)
make test

# Or run with coverage
make test-cov

# Or run in watch mode for TDD
make test-watch
```

### Development Workflow
```bash
# Terminal 1: Development server
make up

# Terminal 2: Test watch mode (auto-runs on file changes)
make test-watch

# Terminal 3: Your editor
vim app/services/watcher_service.py

# Tests auto-run in Terminal 2 when you save!
# Dev server in Terminal 1 keeps running independently!
```

### Before Committing
```bash
# Run all tests with coverage
make test-cov

# Ensure coverage is good (>80%)
# Fix any failing tests
```

## 📊 Expected Output

### make test
```
Running unit tests in isolated Docker container...
Building test container with latest code...
[+] Building 2.3s (12/12) FINISHED
[+] Running 1/1
 ✔ Container weasyprint-sandbox-test  Started
Running tests...
================================ test session starts =================================
platform linux -- Python 3.11.5, pytest-7.4.0, pluggy-1.3.0 -- /usr/local/bin/python3
cachedir: .pytest_cache
rootdir: /app
plugins: cov-4.1.0, mock-3.11.1, asyncio-0.21.1
collected 15 items

tests/test_watcher_service.py::TestWorkspaceChangeHandler::test_initialization PASSED [ 6%]
tests/test_watcher_service.py::TestWorkspaceChangeHandler::test_should_process_debounce PASSED [ 13%]
tests/test_watcher_service.py::TestWorkspaceChangeHandler::test_on_modified_html_file PASSED [ 20%]
...
================================ 15 passed in 5.23s ==================================
✓ Tests passed! Cleaning up...
[+] Running 1/1
 ✔ Container weasyprint-sandbox-test  Removed
✓ Test container stopped
```

### make test-cov
```
Running tests with coverage in isolated Docker container...
Building test container with latest code...
[+] Building 1.8s (12/12) FINISHED
Running tests with coverage...
================================ test session starts =================================
collected 15 items

tests/test_watcher_service.py .............                                    [100%]

---------- coverage: platform linux, python 3.11.5-final-0 ----------
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
app/__init__.py                             3      0   100%
app/services/watcher_service.py            85      4    95%
app/utils/logger.py                        35      2    94%
-----------------------------------------------------------
TOTAL                                     123      6    95%

✓ Coverage report generated in htmlcov/
  Open with: open htmlcov/index.html
[+] Running 1/1
 ✔ Container weasyprint-sandbox-test  Removed
✓ Test container stopped
```

### make test-watch
```
Running tests in watch mode in isolated Docker container...
Building test container with latest code...
Starting watch mode (Ctrl+C to stop)...
File changes will trigger re-runs...

[TODAYS TIME] Running: pytest tests/ -v
...
15 passed in 5.23s

Waiting for file changes...

[File changed detected]
Running tests again...
...
15 passed in 3.12s

Waiting for file changes...
```

## 🎯 Test-Driven Development (TDD)

### TDD Workflow with Docker
```bash
# Terminal 1: Start application
make up

# Terminal 2: Watch mode for instant feedback
make test-watch

# Terminal 3: Write tests and code
vim tests/test_new_service.py
vim app/services/new_service.py

# Watch terminal 2 for instant feedback!
```

## 🔍 Running Specific Tests

All commands run in isolated test containers:

### Run specific test file
```bash
# Spin up test container and run specific file
docker compose -f docker-compose.test.yml up -d --build
docker compose -f docker-compose.test.yml exec weasyprint-test pytest tests/test_watcher_service.py -v
docker compose -f docker-compose.test.yml down
```

### Run specific test class
```bash
docker compose -f docker-compose.test.yml up -d --build
docker compose -f docker-compose.test.yml exec weasyprint-test pytest tests/test_watcher_service.py::TestWatcherService -v
docker compose -f docker-compose.test.yml down
```

### Run specific test method
```bash
docker compose -f docker-compose.test.yml up -d --build
docker compose -f docker-compose.test.yml exec weasyprint-test pytest tests/test_watcher_service.py::TestWatcherService::test_start_and_stop -v
docker compose -f docker-compose.test.yml down
```

### Run tests matching a pattern
```bash
docker compose -f docker-compose.test.yml up -d --build
docker compose -f docker-compose.test.yml exec weasyprint-test pytest tests/ -k "watcher" -v
docker compose -f docker-compose.test.yml down
```

### Or use a helper script (recommended for specific tests)
```bash
# Create a quick test runner script
cat > test-specific.sh << 'EOF'
#!/bin/bash
docker compose -f docker-compose.test.yml up -d --build
docker compose -f docker-compose.test.yml exec -T weasyprint-test pytest "$@"
EXIT_CODE=$?
docker compose -f docker-compose.test.yml down
exit $EXIT_CODE
EOF

chmod +x test-specific.sh

# Now run specific tests easily
./test-specific.sh tests/test_watcher_service.py -v
./test-specific.sh tests/test_watcher_service.py::TestWatcherService -v
./test-specific.sh tests/ -k "watcher" -v
```

## 📈 Coverage Reports

### View coverage reports (generated on host)
```bash
# Generate coverage report
make test-cov

# Coverage report is saved to htmlcov/ on your host machine
# Open it directly
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage Tips
- Aim for >80% coverage
- Focus on critical business logic
- Don't obsess over 100% - some code is hard to test
- Use coverage reports to find untested code paths

## 🐛 Debugging Tests

### Run with print statements visible
```bash
docker compose -f docker-compose.test.yml up -d --build
docker compose -f docker-compose.test.yml exec weasyprint-test pytest tests/ -v -s
docker compose -f docker-compose.test.yml down
```

### Run with debugger (pdb)
```bash
docker compose -f docker-compose.test.yml up -d --build
docker compose -f docker-compose.test.yml exec weasyprint-test pytest tests/ -v --pdb
docker compose -f docker-compose.test.yml down
```

### Show local variables on failure
```bash
docker compose -f docker-compose.test.yml up -d --build
docker compose -f docker-compose.test.yml exec weasyprint-test pytest tests/ -v -l
docker compose -f docker-compose.test.yml down
```

### Stop on first failure
```bash
docker compose -f docker-compose.test.yml up -d --build
docker compose -f docker-compose.test.yml exec weasyprint-test pytest tests/ -v -x
docker compose -f docker-compose.test.yml down
```

### Interactive shell for debugging
```bash
# Start test container
docker compose -f docker-compose.test.yml up -d --build

# Open shell in test container
docker compose -f docker-compose.test.yml exec weasyprint-test /bin/bash

# Inside container:
pytest tests/ -v
# or
python3
>>> from app.services.watcher_service import WatcherService
>>> # Test things interactively

# When done
exit

# Clean up
docker compose -f docker-compose.test.yml down
```

## 🔧 Troubleshooting

### Tests not found
```bash
# Rebuild test container
docker compose -f docker-compose.test.yml build --no-cache

# Check if tests directory is accessible
docker compose -f docker-compose.test.yml up -d
docker compose -f docker-compose.test.yml exec weasyprint-test ls -la tests/
docker compose -f docker-compose.test.yml down
```

### Import errors
```bash
# Rebuild test container to install latest dependencies
docker compose -f docker-compose.test.yml build --no-cache

# Verify app package is importable
docker compose -f docker-compose.test.yml up -d
docker compose -f docker-compose.test.yml exec weasyprint-test python3 -c "from app.services.watcher_service import WatcherService; print('OK')"
docker compose -f docker-compose.test.yml down
```

### Test container won't start
```bash
# Check logs
docker compose -f docker-compose.test.yml logs

# Force rebuild
docker compose -f docker-compose.test.yml build --no-cache
docker compose -f docker-compose.test.yml up -d

# Check status
docker compose -f docker-compose.test.yml ps
```

### Port conflicts
Don't worry! Test containers don't expose any ports, so they never conflict with your dev server running on `localhost:5000`.

### Stale test containers
```bash
# Clean up any stale test containers
docker compose -f docker-compose.test.yml down -v

# Or clean up all stopped containers
docker container prune
```

### Tests are slow
```bash
# Tests run in Docker which may be slower than native
# But ensures consistency across all environments

# You can add pytest-xdist for parallel execution:
# 1. Add to requirements-dev.txt: pytest-xdist>=3.3.0
# 2. Rebuild: docker compose -f docker-compose.test.yml build
# 3. Run with: docker compose -f docker-compose.test.yml exec weasyprint-test pytest tests/ -n auto
```

## 📚 Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [pytest-watch](https://github.com/joeyespo/pytest-watch)

## 💡 Pro Tips

1. **Use watch mode during development** - Instant feedback!
2. **Run coverage before commits** - Maintain quality
3. **Write tests first (TDD)** - Better design
4. **Keep tests fast** - Use mocks for external services
5. **One assertion per test** - Easier debugging
6. **Descriptive test names** - Documentation!

## 🎉 Example Session

```bash
# Start development session
cd /Users/beta/Documents/weasyprint_sandbox

# Build and start container
make up

# Run tests to ensure everything works
make test

# Start watch mode for TDD in another terminal
make test-watch

# Make changes to code - tests run automatically!
vim app/services/watcher_service.py

# Before commit, check coverage
make test-cov

# All good? Commit!
git add .
git commit -m "feat: add new feature with tests"
```

## 🌟 Best Practices

### 1. **Always Run Tests in Docker**
- Ensures consistency across development and production
- No "works on my machine" issues
- Same environment for all developers

### 2. **Use Watch Mode During Development**
- Immediate feedback on code changes
- Faster iteration cycle
- Catch issues early

### 3. **Check Coverage Before Committing**
- Maintain >80% coverage
- Ensure new code is tested
- Use coverage report to find gaps

### 4. **Write Tests First (TDD)**
- Clearer requirements
- Better design
- Higher confidence

### 5. **Keep Tests Fast**
- Use mocks for external services
- Avoid unnecessary sleeps
- Run tests in parallel when possible

## 🐳 Why Isolated Test Containers?

### Benefits
✅ **No Interference** - Dev server keeps running while tests run
✅ **Fresh Environment** - Each test run starts with latest code
✅ **True Isolation** - Tests can't affect your development database/state
✅ **Parallel Development** - Test while you develop
✅ **CI/CD Simulation** - Same environment as production tests
✅ **Auto-Cleanup** - Test containers are removed after completion

### How It Works
1. **make test** spins up `docker-compose.test.yml`
2. Builds a fresh container with your latest code
3. Runs tests in isolation
4. Reports results
5. Automatically removes the test container
6. Your dev container (`docker-compose.yml`) keeps running!

### Architecture
```
┌─────────────────────────────────────┐
│  Your Host Machine                  │
│                                     │
│  ┌────────────────────────────┐   │
│  │  Dev Container (port 5000) │   │  ← make up
│  │  - Running server          │   │  ← Keeps running!
│  │  - Live file watching      │   │
│  └────────────────────────────┘   │
│                                     │
│  ┌────────────────────────────┐   │
│  │  Test Container (no ports) │   │  ← make test
│  │  - Runs tests              │   │  ← Spins up
│  │  - Uses latest code        │   │  ← Runs tests
│  │  - Auto-removed            │   │  ← Cleans up
│  └────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

