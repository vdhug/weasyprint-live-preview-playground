# Testing Commands Quick Reference

## 📋 Available Test Commands

### 1. **Run Unit Tests Locally**
```bash
make test-unit
```
- Runs all tests in `tests/` directory
- Installs dev dependencies if needed
- Shows verbose output

### 2. **Run Tests with Coverage**
```bash
make test-cov
```
- Runs tests with coverage analysis
- Generates HTML coverage report
- Shows coverage percentage in terminal
- Opens `htmlcov/index.html` for detailed view

### 3. **Run Tests in Watch Mode**
```bash
make test-watch
```
- Automatically re-runs tests when files change
- Great for TDD (Test-Driven Development)
- Press `Ctrl+C` to stop

### 4. **Run Tests in Docker Container**
```bash
make test-docker
```
- Runs tests inside the Docker container
- Ensures environment consistency
- Useful for CI/CD pipelines

### 5. **Test PDF Generation** (Legacy)
```bash
make test
```
- Quick test to verify PDF generation works
- Runs inside Docker container

## 🚀 Quick Start

### First Time Setup
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Or let make do it for you
make test-unit
```

### Development Workflow
```bash
# 1. Write your test
vim tests/test_watcher_service.py

# 2. Run tests in watch mode
make test-watch

# 3. Make changes to code
vim app/services/watcher_service.py

# 4. Tests auto-run on save!
```

### Before Committing
```bash
# Run all tests with coverage
make test-cov

# Ensure coverage is good (>80%)
# Fix any failing tests
```

## 📊 Expected Output

### test-unit
```
Running unit tests...
================================ test session starts =================================
tests/test_watcher_service.py::TestWorkspaceChangeHandler::test_initialization PASSED [ 10%]
tests/test_watcher_service.py::TestWorkspaceChangeHandler::test_should_process_first_time PASSED [ 20%]
...
================================ 15 passed in 5.23s ==================================
```

### test-cov
```
Running tests with coverage...
================================ test session starts =================================
tests/test_watcher_service.py .............                                    [100%]

---------- coverage: platform darwin, python 3.11.5-final-0 ----------
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
app/__init__.py                             3      0   100%
app/services/watcher_service.py            85      4    95%
app/utils/logger.py                        35      2    94%
-----------------------------------------------------------
TOTAL                                     123      6    95%

✓ Coverage report generated in htmlcov/index.html
  Open with: open htmlcov/index.html
```

### test-watch
```
Running tests in watch mode (Ctrl+C to stop)...
[TODAYS TIME] Running: pytest tests/ -v
...
15 passed in 5.23s

Waiting for file changes...
```

## 🎯 Test-Driven Development (TDD)

### TDD Workflow
```bash
# Terminal 1: Watch mode
make test-watch

# Terminal 2: Write tests first
vim tests/test_new_service.py

# Terminal 3: Implement service
vim app/services/new_service.py

# Watch terminal 1 for instant feedback!
```

## 🔍 Running Specific Tests

### Run specific test file
```bash
pytest tests/test_watcher_service.py -v
```

### Run specific test class
```bash
pytest tests/test_watcher_service.py::TestWatcherService -v
```

### Run specific test method
```bash
pytest tests/test_watcher_service.py::TestWatcherService::test_start_and_stop -v
```

### Run tests matching a pattern
```bash
pytest tests/ -k "watcher" -v
```

## 📈 Coverage Reports

### View coverage in terminal
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

### Generate HTML coverage report
```bash
make test-cov
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
pytest tests/ -v -s
```

### Run with debugger (pdb)
```bash
pytest tests/ -v --pdb
```

### Show local variables on failure
```bash
pytest tests/ -v -l
```

### Stop on first failure
```bash
pytest tests/ -v -x
```

## 🔧 Troubleshooting

### Tests not found
```bash
# Make sure you're in the project root
cd /path/to/weasyprint_sandbox

# Check Python path
python -c "import sys; print(sys.path)"

# Run with explicit path
python -m pytest tests/ -v
```

### Import errors
```bash
# Install the app in development mode
pip install -e .

# Or ensure PYTHONPATH includes app/
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Docker tests fail
```bash
# Rebuild container
make rebuild

# Check if container is running
docker compose ps

# View container logs
make logs
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
# Start development
cd /Users/beta/Documents/weasyprint_sandbox

# Install dependencies
pip install -r requirements-dev.txt

# Run tests once to make sure everything works
make test-unit

# Start watch mode for TDD
make test-watch

# In another terminal, start coding!
# Tests run automatically on save

# Before commit, check coverage
make test-cov

# All good? Commit!
git add .
git commit -m "feat: add new feature with tests"
```

