"""DWD API client for fetching weather data."""

import logging
from typing import Any

import httpx
from pydantic import ValidationError

from .models import CrowdReport, StationData, StationInfo, WarningInfo

logger = logging.getLogger(__name__)


class DWDAPIError(Exception):
    """Base exception for DWD API errors."""

    pass


class DWDClient:
    """Client for interacting with the DWD API."""

    def __init__(self, base_url: str = "https://dwd.api.bund.dev"):
        """Initialize the DWD client.

        Args:
            base_url: Base URL for the DWD API
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self) -> "DWDClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.client.aclose()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def _make_request(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make an HTTP request to the DWD API.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            DWDAPIError: If the request fails
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            raise DWDAPIError(f"Failed to fetch data from {url}: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            raise DWDAPIError(f"Unexpected error fetching data: {e}") from e

    async def get_weather_stations(
        self, station_ids: list[str] | None = None, region: str | None = None
    ) -> list[StationData]:
        """Fetch weather station data.

        Args:
            station_ids: List of specific station IDs to fetch
            region: Region filter (implementation depends on API structure)

        Returns:
            List of station data

        Raises:
            DWDAPIError: If the request fails
        """
        params = {}
        if station_ids:
            params["stationIds"] = ",".join(station_ids)

        try:
            data = await self._make_request("/stationOverviewExtended", params)

            # Handle different response formats
            if isinstance(data, dict):
                if "stations" in data:
                    stations_data = data["stations"]
                else:
                    # Single station response
                    stations_data = [data]
            elif isinstance(data, list):
                stations_data = data
            else:
                raise DWDAPIError(f"Unexpected response format: {type(data)}")

            stations = []
            for station_data in stations_data:
                try:
                    # If the station_data is already a complete StationData object
                    if "station" in station_data:
                        station = StationData.model_validate(station_data)
                    else:
                        # If it's just station info, wrap it in StationData
                        station_info = StationInfo.model_validate(station_data)
                        station = StationData(station=station_info)
                    stations.append(station)
                except ValidationError as e:
                    logger.warning(f"Failed to parse station data: {e}")
                    continue

            return stations

        except Exception as e:
            logger.error(f"Error fetching weather stations: {e}")
            raise DWDAPIError(f"Failed to fetch weather stations: {e}") from e

    async def get_current_warnings(
        self, region: str | None = None, severity: int | None = None
    ) -> list[WarningInfo]:
        """Fetch current weather warnings.

        Args:
            region: Region filter
            severity: Minimum severity level

        Returns:
            List of weather warnings

        Raises:
            DWDAPIError: If the request fails
        """
        try:
            data = await self._make_request("/warnings_nowcast.json")

            warnings = []
            if isinstance(data, dict) and "warnings" in data:
                warnings_data = data["warnings"]
            elif isinstance(data, list):
                warnings_data = data
            else:
                warnings_data = []

            for warning_data in warnings_data:
                try:
                    warning = WarningInfo.model_validate(warning_data)

                    # Apply filters
                    if severity is not None and warning.level < severity:
                        continue
                    if region and region not in warning.regions:
                        continue

                    warnings.append(warning)
                except ValidationError as e:
                    logger.warning(f"Failed to parse warning data: {e}")
                    continue

            return warnings

        except Exception as e:
            logger.error(f"Error fetching warnings: {e}")
            raise DWDAPIError(f"Failed to fetch warnings: {e}") from e

    async def get_crowd_reports(self, region: str | None = None) -> list[CrowdReport]:
        """Fetch user-submitted weather reports.

        Args:
            region: Region filter

        Returns:
            List of crowd-sourced weather reports

        Raises:
            DWDAPIError: If the request fails
        """
        try:
            data = await self._make_request("/crowd_meldungen_overview_v2.json")

            reports = []
            if isinstance(data, dict) and "reports" in data:
                reports_data = data["reports"]
            elif isinstance(data, list):
                reports_data = data
            else:
                reports_data = []

            for report_data in reports_data:
                try:
                    report = CrowdReport.model_validate(report_data)
                    reports.append(report)
                except ValidationError as e:
                    logger.warning(f"Failed to parse crowd report data: {e}")
                    continue

            return reports

        except Exception as e:
            logger.error(f"Error fetching crowd reports: {e}")
            raise DWDAPIError(f"Failed to fetch crowd reports: {e}") from e
