"""Prompts: guided workflows users can invoke explicitly (FR-MCP-003).

Each prompt is a user message that walks the agent through the server's workflow
(Orient → Retrieve → Contextualize → Link) for a common task.
"""

from __future__ import annotations

from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field


def investigate_fire_activity(
    place: Annotated[str, Field(description="A place name or coordinates, e.g. 'Boise, Idaho'")],
    days: Annotated[int, Field(ge=1, le=5, description="Number of UTC days, 1-5")] = 1,
    date: Annotated[
        str | None,
        Field(
            description="First UTC day (YYYY-MM-DD) for past activity; omit for the most recent days"
        ),
    ] = None,
) -> str:
    """Look up recent or past FIRMS fire detections near a place and explain them with FIRMS's caveats."""
    when = (
        f"the {days} UTC day(s) starting {date}" if date else f"the most recent {days} UTC day(s)"
    )
    return f"""\
I want to know about satellite fire detections near {place} for {when}.

Please:
1. Work out a bounding box for {place} (longitude first: west, south, east, north) and tell \
me the box you used.
2. Call get_fire_detections for that box and window{f" with date {date}" if date else ""} \
(day_range {days}).
3. Report the detections per satellite source with the UTC times of the overpasses; do not \
add counts across sources as a number of fires.
4. Read the caveat entries that matter (get_knowledge_entry) and tell me, in FIRMS's words \
where it matters, what the detections can and cannot tell me — including why fires can be \
missed.
5. Include FIRMS's disclaimer warning and give me the Fire Map link with its description.
If I might be in danger, tell me to follow local emergency services first."""


def explain_detection(
    detection: Annotated[
        str,
        Field(
            description="The detection to explain: a record from get_fire_detections or its attributes as text"
        ),
    ],
) -> str:
    """Explain what one FIRMS detection means, using FIRMS's own documentation."""
    return f"""\
Explain this FIRMS fire detection to me:

{detection}

Please:
1. Identify the sensor and satellite, the acquisition time in UTC, and the processing level \
(URT, RT, NRT, or standard).
2. Use search_knowledge and get_knowledge_entry to find FIRMS's explanations of what a \
detection means on the ground, of the confidence value for this sensor, of fire radiative \
power (FRP) if present, and of the attributes involved. Quote FIRMS where precision matters.
3. Explain the pixel size (scan and track) and that the location is a pixel center, not the \
exact position or size of a fire.
4. Mention the caveats that apply, and give a Fire Map link for the place and day \
(build_fire_map_link).
Do not go beyond what FIRMS's documentation supports; say so when something is uncertain."""


def register_prompts(mcp: FastMCP) -> None:
    mcp.prompt(
        investigate_fire_activity,
        name="investigate_fire_activity",
        title="Investigate fire activity near a place",
    )
    mcp.prompt(explain_detection, name="explain_detection", title="Explain a FIRMS detection")
