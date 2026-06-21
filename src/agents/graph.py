import os
from typing import Annotated
from enum import Enum

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langchain_groq import ChatGroq
from langgraph.types import Command

from .utils import (
    search_flights,
    search_hotels,
    get_weather_forecast,
    get_local_news_and_advisories,
)

# Load environment variables
load_dotenv()

# Initialize LLM (using the same model as github-agent)
llm = ChatGroq(model="openai/gpt-oss-120b")

# =====================================================================
# 1. LEAF AGENTS & WRAPPERS (Weather & News)
# =====================================================================

_weather_agent = create_agent(
    model=llm,
    tools=[get_weather_forecast],
    name="weather_agent",
    system_prompt=(
        "You are a weather forecast analyst. Your job is to fetch the weather forecast for the requested "
        "destination and dates using the provided tools, analyze the temperature ranges and rain probabilities, "
        "and provide a clear summary and advice (e.g., whether to carry an umbrella or if outdoor activities "
        "are recommended). Always include the full details in your final message."
    ),
)

_news_agent = create_agent(
    model=llm,
    tools=[get_local_news_and_advisories],
    name="news_agent",
    system_prompt=(
        "You are a local news and safety advisory agent. Your job is to check local news, events, transit status, "
        "and travel advisories for the requested destination using the provided tools, and output a concise "
        "report of any transit updates, events, or safety advisories. Always include the full details in your final message."
    ),
)


@tool(
    "weather_agent",
    description="Fetches weather forecast for a destination and travel dates. Pass destination and dates.",
)
def call_weather_agent(
    task: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    result = _weather_agent.invoke({"messages": [{"role": "user", "content": task}]})
    return Command(update={
        "messages": [ToolMessage(content=result["messages"][-1].content, tool_call_id=tool_call_id)]
    })


@tool(
    "news_agent",
    description="Fetches local news, events, and travel advisories for a destination. Pass destination.",
)
def call_news_agent(
    task: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    result = _news_agent.invoke({"messages": [{"role": "user", "content": task}]})
    return Command(update={
        "messages": [ToolMessage(content=result["messages"][-1].content, tool_call_id=tool_call_id)]
    })


# =====================================================================
# 2. SUB-AGENTS (Flights, Hotels, Trip Planner)
# =====================================================================

_flight_agent = create_agent(
    model=llm,
    tools=[search_flights],
    name="flight_agent",
    system_prompt=(
        "You are a flight search assistant. Your job is to retrieve potential flight options for the requested "
        "origin, destination, and travel dates using the provided tools. Filter and present the best outbound "
        "and inbound options based on convenience and price. Always include the options in your final message."
    ),
)

_hotel_agent = create_agent(
    model=llm,
    tools=[search_hotels],
    name="hotel_agent",
    system_prompt=(
        "You are a hotel search assistant. Your job is to look up accommodation options at the destination city "
        "for the travel dates using the provided tools. Filter and present a range of high-quality options "
        "across different budgets. Always include the options in your final message."
    ),
)

# Trip Planner Agent coordinates Weather and News Agents
_trip_planner_agent = create_agent(
    model=llm,
    tools=[call_weather_agent, call_news_agent],
    name="trip_planner_agent",
    system_prompt=(
        "You are a trip itinerary generator. Your job is to generate a personalized day-by-day travel itinerary "
        "for the user. To do this, you MUST query both the weather_agent and the news_agent to understand "
        "local conditions, events, and advisories. Integrate the weather forecast and local events/advisories "
        "into a logical daily schedule of sightseeing, dining, and activities. Always include the complete "
        "itinerary in your final message."
    ),
)


@tool(
    "flight_agent",
    description="Searches for flights between origin and destination. Pass origin, destination, and dates.",
)
def call_flight_agent(
    task: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    result = _flight_agent.invoke({"messages": [{"role": "user", "content": task}]})
    return Command(update={
        "messages": [ToolMessage(content=result["messages"][-1].content, tool_call_id=tool_call_id)]
    })


@tool(
    "hotel_agent",
    description="Searches for hotel accommodation in destination city. Pass destination and dates.",
)
def call_hotel_agent(
    task: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    result = _hotel_agent.invoke({"messages": [{"role": "user", "content": task}]})
    return Command(update={
        "messages": [ToolMessage(content=result["messages"][-1].content, tool_call_id=tool_call_id)]
    })


@tool(
    "trip_planner_agent",
    description="Generates a customized travel itinerary based on local weather and news. Pass destination and dates.",
)
def call_trip_planner_agent(
    task: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    result = _trip_planner_agent.invoke({"messages": [{"role": "user", "content": task}]})
    return Command(update={
        "messages": [ToolMessage(content=result["messages"][-1].content, tool_call_id=tool_call_id)]
    })


# =====================================================================
# 3. MAIN COORDINATOR AGENT (Traveller Agent)
# =====================================================================

traveller_agent = create_agent(
    model=llm,
    tools=[call_flight_agent, call_hotel_agent, call_trip_planner_agent],
    name="traveller_agent",
    system_prompt=(
        "You are the main Traveller Agent Coordinator. Your role is to communicate with the user, parse their "
        "travel request, and coordinate the planning process.\n\n"
        "To plan a trip, you MUST delegate tasks to the following subagents via tools:\n"
        "1. flight_agent: to search outbound and inbound flight options.\n"
        "2. hotel_agent: to search lodging options.\n"
        "3. trip_planner_agent: to generate the itinerary tailored to weather and local events.\n\n"
        "Once you receive responses from these three agents, synthesize a unified, premium trip proposal containing:\n"
        "- Recommended Outbound & Inbound Flights (airline, times, price)\n"
        "- Recommended Hotels (name, rating, price, location)\n"
        "- Weather Forecast Summary & local advisories\n"
        "- Day-by-Day Itinerary incorporating weather recommendations\n\n"
        "Be professional and display the final proposal using clean, beautiful markdown. Do not perform any flight/hotel "
        "searches yourself—always use the subagents."
    ),
)


if __name__ == "__main__":
    import sys
    
    # Simple interactive command-line mode or default demo run
    query = "Travel from Delhi to Hyderabad from June 25 to June 27, 2026."
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        
    print(f"=== Starting Travel Planner Coordinator ===")
    print(f"User Query: {query}\n")
    
    res = traveller_agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": query,
            }
        ]
    })
    
    print("\n=== Final Traveller Agent Proposal ===\n")
    print(res["messages"][-1].content)
