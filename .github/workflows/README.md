# GitHub Actions Workflows

This directory contains GitHub Actions workflows for the asimov-gwdata repository.

## Workflows

### `tests.yml` - Run Tests

Runs the test suite for asimov-gwdata, including tests with the MockGWDataFindServer.

**Triggers:**
- Push to `main` or `master` branches
- Pull requests to `main` or `master` branches
- Manual trigger via workflow_dispatch

**Jobs:**

1. **test** - Runs basic unit tests on Python 3.9, 3.10, 3.11, and 3.12
   - Tests run without requiring external services
   - Uses mock fixtures for offline testing

2. **test-with-mock-server** - Runs tests with MockGWDataFindServer on Python 3.10, 3.11, and 3.12
   - Starts MockGWDataFindServer as a background service
   - Creates test frame files
   - Sets `GWDATAFIND_SERVER=http://localhost:8765`
   - Runs all tests including integration tests with the mock server

3. **test-summary** - Reports test results
   - Runs after both test jobs complete
   - Displays summary of test results

### `documentation.yml` - Build and Deploy Documentation

Builds and deploys the documentation to GitHub Pages.

**Triggers:**
- Push to `main` or `master` branches
- Push of version tags (`v*`)
- Pull requests to `main` or `master` branches
- Manual trigger via workflow_dispatch

**Jobs:**

1. **build** - Builds Sphinx documentation
   - For PRs: builds current version only
   - For main/master/tags: builds all versions with sphinx-multiversion

2. **deploy** - Deploys to GitHub Pages
   - Only runs for pushes to main/master or version tags
   - Deploys built documentation to GitHub Pages

## Testing Locally

To test the workflows locally, you can use [act](https://github.com/nektos/act):

```bash
# Install act
# brew install act  # macOS
# sudo apt install act  # Ubuntu/Debian

# Run the test workflow
act -j test

# Run the test-with-mock-server job
act -j test-with-mock-server
```

## Adding New Workflows

When adding new workflows:

1. Create a new `.yml` file in this directory
2. Follow GitHub Actions syntax and best practices
3. Test locally if possible using `act`
4. Document the workflow in this README
5. Ensure workflows are triggered appropriately
6. Use matrix builds for testing across multiple Python versions

## Best Practices

- **Use matrix builds** for testing across Python versions
- **Separate jobs** for different test types (unit, integration, with/without server)
- **Cache dependencies** when possible to speed up workflows
- **Set appropriate timeouts** to avoid hanging workflows
- **Use `continue-on-error: true`** for non-critical tests
- **Clean up resources** (like background servers) in `if: always()` steps
