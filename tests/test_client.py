"""Tests for the DWD API client."""

from unittest.mock import patch

import pytest

from dwd_mcp.client import DWDAPIError, DWDClient
from dwd_mcp.models import StationData


class TestDWDClient:
    """Tests for DWDClient."""

    @pytest.fixture
    async def client(self):
        """Create a test client."""
        client = DWDClient()
        yield client
        await client.close()

    @pytest.fixture
    def sample_station_response(self):
        """Sample API response for station data."""
        return {
            "stationId": "10382",
            "stationName": "Berlin-Tempelhof",
            "lat": 52.4675,
            "lon": 13.4021,
            "elevation": 48.0,
            "state": "Berlin",
            "lastUpdated": "2024-01-15T12:00:00Z",
        }

    @pytest.fixture
    def sample_warning_response(self):
        """Sample API response for warning data."""
        return {
            "warningId": "WARN001",
            "level": 2,
            "type": "THUNDER",
            "headline": "Thunderstorm Warning",
            "description": "Severe thunderstorms expected",
            "startTime": "2024-01-15T14:00:00Z",
            "endTime": "2024-01-15T20:00:00Z",
            "regions": ["Berlin", "Brandenburg"],
        }

    async def test_get_weather_stations_success(self, client, sample_station_response):
        """Test successful weather station data retrieval."""
        with patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = [sample_station_response]

            stations = await client.get_weather_stations(station_ids=["10382"])

            assert len(stations) == 1
            station = stations[0]
            assert isinstance(station, StationData)
            assert station.station.station_id == "10382"
            assert station.station.station_name == "Berlin-Tempelhof"
            assert station.station.latitude == 52.4675
            assert station.station.longitude == 13.4021

            mock_request.assert_called_once_with(
                "/stationOverviewExtended", {"stationIds": "10382"}
            )

    async def test_get_weather_stations_multiple_ids(
        self, client, sample_station_response
    ):
        """Test weather station data retrieval with multiple station IDs."""
        with patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = [
                sample_station_response,
                sample_station_response,
            ]

            stations = await client.get_weather_stations(station_ids=["10382", "10384"])

            assert len(stations) == 2
            mock_request.assert_called_once_with(
                "/stationOverviewExtended", {"stationIds": "10382,10384"}
            )

    async def test_get_weather_stations_no_params(
        self, client, sample_station_response
    ):
        """Test weather station data retrieval without parameters."""
        with patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = [sample_station_response]

            stations = await client.get_weather_stations()

            assert len(stations) == 1
            mock_request.assert_called_once_with("/stationOverviewExtended", {})

    async def test_get_weather_stations_api_error(self, client):
        """Test handling of API errors."""
        with patch.object(client, "_make_request") as mock_request:
            mock_request.side_effect = DWDAPIError("API Error")

            with pytest.raises(DWDAPIError, match="Failed to fetch weather stations"):
                await client.get_weather_stations()

    async def test_get_current_warnings_success(self, client, sample_warning_response):
        """Test successful warning data retrieval."""
        with patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = [sample_warning_response]

            warnings = await client.get_current_warnings()

            assert len(warnings) == 1
            warning = warnings[0]
            assert warning.warning_id == "WARN001"
            assert warning.level == 2
            assert warning.type == "THUNDER"
            assert warning.headline == "Thunderstorm Warning"

            mock_request.assert_called_once_with("/warnings_nowcast.json")

    async def test_get_current_warnings_with_filters(
        self, client, sample_warning_response
    ):
        """Test warning data retrieval with filters."""
        with patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = [sample_warning_response]

            warnings = await client.get_current_warnings(region="Berlin", severity=2)

            assert len(warnings) == 1
            warning = warnings[0]
            assert "Berlin" in warning.regions
            assert warning.level >= 2

    async def test_get_current_warnings_filtered_out(
        self, client, sample_warning_response
    ):
        """Test warning data retrieval with filters that exclude results."""
        with patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = [sample_warning_response]

            # Filter by severity too high
            warnings = await client.get_current_warnings(severity=4)
            assert len(warnings) == 0

            # Filter by region not in the warning
            warnings = await client.get_current_warnings(region="München")
            assert len(warnings) == 0

    async def test_get_crowd_reports_success(self, client):
        """Test successful crowd reports retrieval."""
        sample_report = {
            "reportId": "CR001",
            "lat": 52.5200,
            "lon": 13.4050,
            "weatherCondition": "sunny",
            "temperature": 22.5,
            "timestamp": "2024-01-15T12:30:00Z",
            "userComment": "Beautiful weather",
        }

        with patch.object(client, "_make_request") as mock_request:
            mock_request.return_value = [sample_report]

            reports = await client.get_crowd_reports()

            assert len(reports) == 1
            report = reports[0]
            assert report.report_id == "CR001"
            assert report.latitude == 52.5200
            assert report.longitude == 13.4050
            assert report.weather_condition == "sunny"
            assert report.temperature == 22.5

            mock_request.assert_called_once_with("/crowd_meldungen_overview_v2.json")

    async def test_make_request_http_error(self, client):
        """Test HTTP error handling in _make_request."""
        with patch.object(client.client, "get") as mock_get:
            # Mock HTTP error by making get itself raise an exception
            mock_get.side_effect = Exception("HTTP 404")

            with pytest.raises(DWDAPIError, match="Unexpected error fetching data"):
                await client._make_request("/test")

    async def test_context_manager(self):
        """Test client as async context manager."""
        async with DWDClient() as client:
            assert client is not None
            # Client should be usable within the context
