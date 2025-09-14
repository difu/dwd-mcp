# dwd-mcp

MCP-DWD is a Model Context Protocol (MCP) server that provides seamless access to open data from the Deutscher Wetterdienst (DWD). It exposes weather observations, forecasts, and warnings through standardized MCP tools, enabling applications and AI agents to query and integrate German weather data reliably.

__Note:__ MCP-DWD is not an official service of the Deutscher Wetterdienst. The community-driven endpoint at dwd.api.bund.dev
 may be used as a data source, but it is maintained independently of DWD.

## Features

### MCP Tools
- **`get_weather_stations`** - Retrieve detailed weather station data with optional filtering by station IDs or region
- **`get_current_warnings`** - Fetch active weather warnings with severity level and region filtering
- **`get_crowd_reports`** - Access user-submitted weather observations and reports

### MCP Resources
- `weather://stations/all` - Complete list of all available weather stations
- `weather://warnings/current` - Active weather warnings in structured format
- `weather://reports/crowd` - User-submitted weather observations

### Data Types
- **Weather Stations**: Station metadata, measurements, coordinates, elevation
- **Weather Warnings**: Severity levels, affected regions, time validity, descriptions
- **Crowd Reports**: User-submitted conditions, temperatures, locations, comments

## Usage

### Starting the Server
```bash
# Run the MCP server
uv run dwd-mcp
```

### Tool Examples
```json
// Get specific weather stations
{
  "name": "get_weather_stations",
  "arguments": {
    "station_ids": ["10637", "10382"],
    "region": "Hessen"
  }
}

// Get severe weather warnings
{
  "name": "get_current_warnings",
  "arguments": {
    "severity": 3,
    "region": "Bayern"
  }
}

// Get crowd-sourced reports
{
  "name": "get_crowd_reports",
  "arguments": {
    "region": "Berlin"
  }
}
```

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

### Code Quality
```bash
# Run linting
uv run ruff check .

# Auto-fix linting issues
uv run ruff check . --fix

# Format code
uv run black .

# Type checking
uv run mypy src/
```

### Project Structure
```
src/dwd_mcp/
├── __init__.py          # Package entry point
├── client.py            # DWD API client
├── models.py            # Pydantic data models
└── server.py            # MCP server implementation
tests/
├── test_client.py       # API client tests
├── test_models.py       # Data model tests
└── test_server.py       # MCP server tests
```

