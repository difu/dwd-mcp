"""MCP server for DWD weather data."""

import asyncio
import logging
from typing import Any

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import AnyUrl, Resource, TextContent, Tool

from .client import DWDAPIError, DWDClient

logger = logging.getLogger(__name__)

# Initialize the MCP server
app = Server("dwd-mcp")

# Global client instance
dwd_client: DWDClient | None = None


@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="get_weather_stations",
            description=(
                "Get weather station data from the German Weather Service (DWD)"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "station_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of specific station IDs to fetch data for",
                    },
                    "region": {
                        "type": "string",
                        "description": "Region filter (optional)",
                    },
                },
                "additionalProperties": False,
            },
        ),
        Tool(
            name="get_current_warnings",
            description="Get current weather warnings from the German Weather Service",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "Region filter (optional)",
                    },
                    "severity": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 4,
                        "description": "Minimum warning severity level (1-4)",
                    },
                },
                "additionalProperties": False,
            },
        ),
        Tool(
            name="get_crowd_reports",
            description=(
                "Get user-submitted weather reports from the German Weather Service"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "Region filter (optional)",
                    },
                },
                "additionalProperties": False,
            },
        ),
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    global dwd_client

    if dwd_client is None:
        dwd_client = DWDClient()

    try:
        if name == "get_weather_stations":
            station_ids = arguments.get("station_ids")
            region = arguments.get("region")

            stations = await dwd_client.get_weather_stations(
                station_ids=station_ids, region=region
            )

            if not stations:
                return [TextContent(type="text", text="No weather stations found.")]

            # Format the response
            result_lines = ["# Weather Stations\n"]

            for station in stations:
                result_lines.append(
                    f"## Station: {station.station.station_name or 'Unknown'}"
                )
                result_lines.append(f"- **ID**: {station.station.station_id}")

                if station.station.latitude and station.station.longitude:
                    result_lines.append(
                        f"- **Location**: {station.station.latitude:.4f}°N, "
                        f"{station.station.longitude:.4f}°E"
                    )

                if station.station.elevation:
                    result_lines.append(
                        f"- **Elevation**: {station.station.elevation}m"
                    )

                if station.station.state:
                    result_lines.append(f"- **State**: {station.station.state}")

                if station.measurements:
                    result_lines.append("- **Current Measurements**:")
                    for measurement in station.measurements:
                        value_str = (
                            f"{measurement.value} {measurement.unit}"
                            if measurement.value is not None and measurement.unit
                            else str(measurement.value) if measurement.value is not None
                            else "N/A"
                        )
                        result_lines.append(f"  - {measurement.parameter}: {value_str}")

                if station.last_updated:
                    result_lines.append(f"- **Last Updated**: {station.last_updated}")

                result_lines.append("")

            return [TextContent(type="text", text="\n".join(result_lines))]

        elif name == "get_current_warnings":
            region = arguments.get("region")
            severity = arguments.get("severity")

            warnings = await dwd_client.get_current_warnings(
                region=region, severity=severity
            )

            if not warnings:
                return [TextContent(type="text", text="No weather warnings found.")]

            result_lines = ["# Current Weather Warnings\n"]

            for warning in warnings:
                result_lines.append(f"## {warning.headline}")
                result_lines.append(f"- **ID**: {warning.warning_id}")
                result_lines.append(f"- **Level**: {warning.level}")
                result_lines.append(f"- **Type**: {warning.type}")
                result_lines.append(f"- **Start**: {warning.start_time}")

                if warning.end_time:
                    result_lines.append(f"- **End**: {warning.end_time}")

                if warning.regions:
                    result_lines.append(f"- **Regions**: {', '.join(warning.regions)}")

                result_lines.append(f"- **Description**: {warning.description}")
                result_lines.append("")

            return [TextContent(type="text", text="\n".join(result_lines))]

        elif name == "get_crowd_reports":
            region = arguments.get("region")

            reports = await dwd_client.get_crowd_reports(region=region)

            if not reports:
                return [TextContent(type="text", text="No crowd reports found.")]

            result_lines = ["# User-Submitted Weather Reports\n"]

            for report in reports:
                result_lines.append(f"## Report {report.report_id}")
                result_lines.append(
                    f"- **Location**: {report.latitude:.4f}°N, {report.longitude:.4f}°E"
                )
                result_lines.append(f"- **Condition**: {report.weather_condition}")

                if report.temperature:
                    result_lines.append(f"- **Temperature**: {report.temperature}°C")

                result_lines.append(f"- **Time**: {report.timestamp}")

                if report.user_comment:
                    result_lines.append(f"- **Comment**: {report.user_comment}")

                result_lines.append("")

            return [TextContent(type="text", text="\n".join(result_lines))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except DWDAPIError as e:
        logger.error(f"DWD API error: {e}")
        return [TextContent(type="text", text=f"Error fetching data: {e}")]
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return [TextContent(type="text", text=f"Unexpected error: {e}")]


@app.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available resources."""
    return [
        Resource(
            uri=AnyUrl("weather://stations/all"),
            name="All Weather Stations",
            description="Complete list of all available weather stations",
            mimeType="application/json",
        ),
        Resource(
            uri=AnyUrl("weather://warnings/current"),
            name="Current Weather Warnings",
            description="Active weather warnings",
            mimeType="application/json",
        ),
        Resource(
            uri=AnyUrl("weather://reports/crowd"),
            name="Crowd Weather Reports",
            description="User-submitted weather observations",
            mimeType="application/json",
        ),
    ]


@app.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a resource by URI."""
    global dwd_client

    if dwd_client is None:
        dwd_client = DWDClient()

    try:
        if uri == "weather://stations/all":
            stations = await dwd_client.get_weather_stations()
            return "\n".join([station.json(indent=2) for station in stations])

        elif uri == "weather://warnings/current":
            warnings = await dwd_client.get_current_warnings()
            return "\n".join([warning.json(indent=2) for warning in warnings])

        elif uri == "weather://reports/crowd":
            reports = await dwd_client.get_crowd_reports()
            return "\n".join([report.json(indent=2) for report in reports])

        else:
            raise ValueError(f"Unknown resource URI: {uri}")

    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}")
        raise


async def main() -> None:
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="dwd-mcp",
                server_version="0.1.0",
                capabilities=app.get_capabilities({}, {}),  # type: ignore[arg-type]
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
