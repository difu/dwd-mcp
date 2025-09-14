"""Data models for DWD API responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StationInfo(BaseModel):
    """Weather station information."""

    model_config = ConfigDict(populate_by_name=True)

    station_id: str = Field(alias="stationId")
    station_name: str | None = Field(default=None, alias="stationName")
    latitude: float | None = Field(default=None, alias="lat")
    longitude: float | None = Field(default=None, alias="lon")
    elevation: float | None = Field(default=None, alias="elevation")
    state: str | None = Field(default=None, alias="state")


class WeatherMeasurement(BaseModel):
    """Individual weather measurement."""

    parameter: str
    value: float | None = None
    unit: str | None = None
    timestamp: datetime | None = None
    quality: str | None = None


class StationData(BaseModel):
    """Complete weather station data."""

    model_config = ConfigDict(populate_by_name=True)

    station: StationInfo
    measurements: list[WeatherMeasurement] = Field(default_factory=list)
    last_updated: datetime | None = Field(default=None, alias="lastUpdated")


class WarningInfo(BaseModel):
    """Weather warning information."""

    model_config = ConfigDict(populate_by_name=True)

    warning_id: str = Field(alias="warningId")
    level: int
    type: str
    headline: str
    description: str
    start_time: datetime = Field(alias="startTime")
    end_time: datetime | None = Field(default=None, alias="endTime")
    regions: list[str] = Field(default_factory=list)


class CrowdReport(BaseModel):
    """User-submitted weather report."""

    model_config = ConfigDict(populate_by_name=True)

    report_id: str = Field(alias="reportId")
    latitude: float = Field(alias="lat")
    longitude: float = Field(alias="lon")
    weather_condition: str = Field(alias="weatherCondition")
    temperature: float | None = None
    timestamp: datetime
    user_comment: str | None = Field(default=None, alias="userComment")
