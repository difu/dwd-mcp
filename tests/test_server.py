"""Tests for the MCP server."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from dwd_mcp.models import CrowdReport, StationData, StationInfo, WarningInfo
from dwd_mcp.server import handle_call_tool, handle_list_resources, handle_list_tools


class TestMCPServer:
    """Tests for the MCP server functionality."""

    @pytest.fixture
    def sample_station(self):
        """Create a sample station for testing."""
        station_info = StationInfo(
            stationId="10637",
            stationName="Frankfurt am Main",
            lat=50.1109,
            lon=8.6821,
            elevation=112.0,
            state="Hessen",
        )
        return StationData(
            station=station_info,
            measurements=[],
            lastUpdated=datetime.now(),
        )

    @pytest.fixture
    def sample_warning(self):
        """Create a sample warning for testing."""
        return WarningInfo(
            warningId="WARN001",
            level=2,
            type="THUNDER",
            headline="Thunderstorm Warning",
            description="Severe thunderstorms expected",
            startTime=datetime.now(),
            endTime=datetime.now(),
            regions=["Berlin", "Brandenburg"],
        )

    @pytest.fixture
    def sample_crowd_report(self):
        """Create a sample crowd report for testing."""
        return CrowdReport(
            reportId="CR001",
            lat=52.5200,
            lon=13.4050,
            weatherCondition="sunny",
            temperature=22.5,
            timestamp=datetime.now(),
            userComment="Beautiful weather",
        )

    async def test_list_tools(self):
        """Test that list_tools returns expected tools."""
        tools = await handle_list_tools()

        assert len(tools) == 3

        tool_names = [tool.name for tool in tools]
        assert "get_weather_stations" in tool_names
        assert "get_current_warnings" in tool_names
        assert "get_crowd_reports" in tool_names

        # Check specific tool properties
        station_tool = next(
            tool for tool in tools if tool.name == "get_weather_stations"
        )
        assert "station_ids" in station_tool.inputSchema["properties"]
        assert "region" in station_tool.inputSchema["properties"]

        warning_tool = next(
            tool for tool in tools if tool.name == "get_current_warnings"
        )
        assert "region" in warning_tool.inputSchema["properties"]
        assert "severity" in warning_tool.inputSchema["properties"]

    async def test_list_resources(self):
        """Test that list_resources returns expected resources."""
        resources = await handle_list_resources()

        assert len(resources) == 3

        resource_uris = [str(resource.uri) for resource in resources]
        assert "weather://stations/all" in resource_uris
        assert "weather://warnings/current" in resource_uris
        assert "weather://reports/crowd" in resource_uris

    @patch("dwd_mcp.server.dwd_client")
    async def test_get_weather_stations_tool(self, mock_client, sample_station):
        """Test the get_weather_stations tool."""
        mock_client.get_weather_stations = AsyncMock(return_value=[sample_station])

        result = await handle_call_tool(
            "get_weather_stations", {"station_ids": ["10382"]}
        )

        assert len(result) == 1
        content = result[0].text

        assert "Weather Stations" in content
        assert "Frankfurt am Main" in content
        assert "10637" in content
        assert "50.1109°N" in content
        assert "8.6821°E" in content

        mock_client.get_weather_stations.assert_called_once_with(
            station_ids=["10382"], region=None
        )

    @patch("dwd_mcp.server.dwd_client")
    async def test_get_weather_stations_no_results(self, mock_client):
        """Test get_weather_stations tool with no results."""
        mock_client.get_weather_stations = AsyncMock(return_value=[])

        result = await handle_call_tool("get_weather_stations", {})

        assert len(result) == 1
        assert "No weather stations found" in result[0].text

    @patch("dwd_mcp.server.dwd_client")
    async def test_get_current_warnings_tool(self, mock_client, sample_warning):
        """Test the get_current_warnings tool."""
        mock_client.get_current_warnings = AsyncMock(return_value=[sample_warning])

        result = await handle_call_tool(
            "get_current_warnings", {"region": "Berlin", "severity": 2}
        )

        assert len(result) == 1
        content = result[0].text

        assert "Current Weather Warnings" in content
        assert "Thunderstorm Warning" in content
        assert "WARN001" in content
        assert "Level**: 2" in content
        assert "THUNDER" in content

        mock_client.get_current_warnings.assert_called_once_with(
            region="Berlin", severity=2
        )

    @patch("dwd_mcp.server.dwd_client")
    async def test_get_current_warnings_no_results(self, mock_client):
        """Test get_current_warnings tool with no results."""
        mock_client.get_current_warnings = AsyncMock(return_value=[])

        result = await handle_call_tool("get_current_warnings", {})

        assert len(result) == 1
        assert "No weather warnings found" in result[0].text

    @patch("dwd_mcp.server.dwd_client")
    async def test_get_crowd_reports_tool(self, mock_client, sample_crowd_report):
        """Test the get_crowd_reports tool."""
        mock_client.get_crowd_reports = AsyncMock(return_value=[sample_crowd_report])

        result = await handle_call_tool("get_crowd_reports", {"region": "Berlin"})

        assert len(result) == 1
        content = result[0].text

        assert "User-Submitted Weather Reports" in content
        assert "CR001" in content
        assert "52.5200°N" in content
        assert "13.4050°E" in content
        assert "sunny" in content
        assert "22.5°C" in content

        mock_client.get_crowd_reports.assert_called_once_with(region="Berlin")

    @patch("dwd_mcp.server.dwd_client")
    async def test_get_crowd_reports_no_results(self, mock_client):
        """Test get_crowd_reports tool with no results."""
        mock_client.get_crowd_reports = AsyncMock(return_value=[])

        result = await handle_call_tool("get_crowd_reports", {})

        assert len(result) == 1
        assert "No crowd reports found" in result[0].text

    async def test_unknown_tool(self):
        """Test handling of unknown tool calls."""
        result = await handle_call_tool("unknown_tool", {})

        assert len(result) == 1
        assert "Unknown tool: unknown_tool" in result[0].text

    @patch("dwd_mcp.server.dwd_client")
    async def test_tool_error_handling(self, mock_client):
        """Test error handling in tool calls."""
        from dwd_mcp.client import DWDAPIError

        mock_client.get_weather_stations = AsyncMock(
            side_effect=DWDAPIError("API Error")
        )

        result = await handle_call_tool("get_weather_stations", {})

        assert len(result) == 1
        assert "Error fetching data: API Error" in result[0].text

    @patch("dwd_mcp.server.dwd_client")
    async def test_tool_unexpected_error_handling(self, mock_client):
        """Test handling of unexpected errors in tool calls."""
        mock_client.get_weather_stations = AsyncMock(
            side_effect=ValueError("Unexpected error")
        )

        result = await handle_call_tool("get_weather_stations", {})

        assert len(result) == 1
        assert "Unexpected error: Unexpected error" in result[0].text
