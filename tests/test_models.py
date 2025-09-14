"""Tests for the data models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from dwd_mcp.models import (
    CrowdReport,
    StationData,
    StationInfo,
    WarningInfo,
    WeatherMeasurement,
)


class TestModels:
    """Tests for data models."""

    def test_station_info_creation(self):
        """Test StationInfo model creation."""
        station = StationInfo(
            stationId="10382",
            stationName="Berlin-Tempelhof",
            lat=52.4675,
            lon=13.4021,
            elevation=48.0,
            state="Berlin",
        )

        assert station.station_id == "10382"
        assert station.station_name == "Berlin-Tempelhof"
        assert station.latitude == 52.4675
        assert station.longitude == 13.4021
        assert station.elevation == 48.0
        assert station.state == "Berlin"

    def test_station_info_minimal(self):
        """Test StationInfo with minimal required fields."""
        station = StationInfo(stationId="10382")

        assert station.station_id == "10382"
        assert station.station_name is None
        assert station.latitude is None
        assert station.longitude is None
        assert station.elevation is None
        assert station.state is None

    def test_weather_measurement_creation(self):
        """Test WeatherMeasurement model creation."""
        measurement = WeatherMeasurement(
            parameter="temperature",
            value=22.5,
            unit="°C",
            timestamp=datetime.now(),
            quality="good",
        )

        assert measurement.parameter == "temperature"
        assert measurement.value == 22.5
        assert measurement.unit == "°C"
        assert isinstance(measurement.timestamp, datetime)
        assert measurement.quality == "good"

    def test_weather_measurement_minimal(self):
        """Test WeatherMeasurement with minimal fields."""
        measurement = WeatherMeasurement(parameter="humidity")

        assert measurement.parameter == "humidity"
        assert measurement.value is None
        assert measurement.unit is None
        assert measurement.timestamp is None
        assert measurement.quality is None

    def test_station_data_creation(self):
        """Test StationData model creation."""
        station_info = StationInfo(stationId="10382", stationName="Berlin")
        measurement = WeatherMeasurement(parameter="temperature", value=22.5, unit="°C")
        timestamp = datetime.now()

        station_data = StationData(
            station=station_info, measurements=[measurement], lastUpdated=timestamp
        )

        assert station_data.station == station_info
        assert len(station_data.measurements) == 1
        assert station_data.measurements[0] == measurement
        assert station_data.last_updated == timestamp

    def test_station_data_minimal(self):
        """Test StationData with minimal required fields."""
        station_info = StationInfo(stationId="10382")
        station_data = StationData(station=station_info)

        assert station_data.station == station_info
        assert station_data.measurements == []
        assert station_data.last_updated is None

    def test_warning_info_creation(self):
        """Test WarningInfo model creation."""
        start_time = datetime.now()
        end_time = datetime.now()

        warning = WarningInfo(
            warningId="WARN001",
            level=2,
            type="THUNDER",
            headline="Thunderstorm Warning",
            description="Severe thunderstorms expected",
            startTime=start_time,
            endTime=end_time,
            regions=["Berlin", "Brandenburg"],
        )

        assert warning.warning_id == "WARN001"
        assert warning.level == 2
        assert warning.type == "THUNDER"
        assert warning.headline == "Thunderstorm Warning"
        assert warning.description == "Severe thunderstorms expected"
        assert warning.start_time == start_time
        assert warning.end_time == end_time
        assert warning.regions == ["Berlin", "Brandenburg"]

    def test_warning_info_minimal(self):
        """Test WarningInfo with minimal required fields."""
        start_time = datetime.now()

        warning = WarningInfo(
            warningId="WARN001",
            level=1,
            type="RAIN",
            headline="Rain Warning",
            description="Light rain expected",
            startTime=start_time,
        )

        assert warning.warning_id == "WARN001"
        assert warning.level == 1
        assert warning.type == "RAIN"
        assert warning.headline == "Rain Warning"
        assert warning.description == "Light rain expected"
        assert warning.start_time == start_time
        assert warning.end_time is None
        assert warning.regions == []

    def test_crowd_report_creation(self):
        """Test CrowdReport model creation."""
        timestamp = datetime.now()

        report = CrowdReport(
            reportId="CR001",
            lat=52.5200,
            lon=13.4050,
            weatherCondition="sunny",
            temperature=22.5,
            timestamp=timestamp,
            userComment="Beautiful weather",
        )

        assert report.report_id == "CR001"
        assert report.latitude == 52.5200
        assert report.longitude == 13.4050
        assert report.weather_condition == "sunny"
        assert report.temperature == 22.5
        assert report.timestamp == timestamp
        assert report.user_comment == "Beautiful weather"

    def test_crowd_report_minimal(self):
        """Test CrowdReport with minimal required fields."""
        timestamp = datetime.now()

        report = CrowdReport(
            reportId="CR001",
            lat=52.5200,
            lon=13.4050,
            weatherCondition="sunny",
            timestamp=timestamp,
        )

        assert report.report_id == "CR001"
        assert report.latitude == 52.5200
        assert report.longitude == 13.4050
        assert report.weather_condition == "sunny"
        assert report.temperature is None
        assert report.timestamp == timestamp
        assert report.user_comment is None

    def test_model_alias_support(self):
        """Test that models work with both field names and aliases."""
        # Test using aliases (as would come from API)
        station_dict = {
            "stationId": "10382",
            "stationName": "Berlin-Tempelhof",
            "lat": 52.4675,
            "lon": 13.4021,
            "elevation": 48.0,
            "state": "Berlin",
        }

        station = StationInfo.model_validate(station_dict)

        assert station.station_id == "10382"
        assert station.station_name == "Berlin-Tempelhof"
        assert station.latitude == 52.4675
        assert station.longitude == 13.4021
        assert station.elevation == 48.0
        assert station.state == "Berlin"

    def test_validation_error_missing_required(self):
        """Test validation errors for missing required fields."""
        # StationInfo requires stationId
        with pytest.raises(ValidationError):
            StationInfo()

        # WarningInfo requires multiple fields
        with pytest.raises(ValidationError):
            WarningInfo(warningId="WARN001")

        # CrowdReport requires multiple fields
        with pytest.raises(ValidationError):
            CrowdReport(reportId="CR001")
