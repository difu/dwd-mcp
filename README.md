# dwd-mcp
MCP-DWD is a Model Context Protocol (MCP) server that provides seamless access to open data from the Deutscher Wetterdienst (DWD). It exposes weather observations, forecasts, and warnings through standardized MCP tools, enabling applications and AI agents to query and integrate German weather data reliably.

__Note:__ MCP-DWD is not an official service of the Deutscher Wetterdienst. The community-driven endpoint at dwd.api.bund.dev
 may be used as a data source, but it is maintained independently of DWD.

## Development

This project uses Python with [uv](https://docs.astral.sh/uv/) for package management.

### Setup
```bash
# Install dependencies
uv sync

# Add new dependency
uv add <package>
```

### Testing
```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Run tests in watch mode (verbose)
uv run pytest -v
```

### Project Structure
- Uses pytest for testing with async support (`pytest-asyncio`)
- Coverage reporting available via `pytest-cov`

