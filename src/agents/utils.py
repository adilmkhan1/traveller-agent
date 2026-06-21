import json
from langchain.tools import tool

# Mock Database
MOCK_FLIGHTS = {
    ("DEL", "HYD"): [
        {"flight_no": "AI-101", "airline": "Air India", "departure": "07:00", "arrival": "09:15", "price": 4500},
        {"flight_no": "6E-502", "airline": "IndiGo", "departure": "13:30", "arrival": "15:45", "price": 4200},
        {"flight_no": "UK-829", "airline": "Vistara", "departure": "18:45", "arrival": "21:00", "price": 5100}
    ],
    ("HYD", "DEL"): [
        {"flight_no": "AI-102", "airline": "Air India", "departure": "10:15", "arrival": "12:30", "price": 4600},
        {"flight_no": "6E-503", "airline": "IndiGo", "departure": "16:45", "arrival": "19:00", "price": 4100},
        {"flight_no": "UK-830", "airline": "Vistara", "departure": "21:45", "arrival": "00:05", "price": 5200}
    ]
}

MOCK_HOTELS = {
    "Hyderabad": [
        {"name": "Taj Falaknuma Palace", "rating": "5 Star", "price_per_night": 25000, "location": "Falaknuma"},
        {"name": "Novotel Hyderabad Convention Centre", "rating": "5 Star", "price_per_night": 9000, "location": "Hitec City"},
        {"name": "ITC Kohenur", "rating": "5 Star", "price_per_night": 15000, "location": "Madhapur"},
        {"name": "Lemon Tree Premier", "rating": "4 Star", "price_per_night": 6000, "location": "Gachibowli"}
    ]
}

MOCK_WEATHER = {
    "Hyderabad": [
        {"date": "2026-06-25", "forecast": "Partly Cloudy", "temp_range": "28°C - 36°C", "rain_prob": "20%"},
        {"date": "2026-06-26", "forecast": "Scattered Showers", "temp_range": "26°C - 33°C", "rain_prob": "60%"},
        {"date": "2026-06-27", "forecast": "Sunny and Clear", "temp_range": "29°C - 37°C", "rain_prob": "10%"}
    ]
}

MOCK_NEWS = {
    "Hyderabad": [
        {"headline": "Local Metro extends operating hours for the weekend", "category": "Transit"},
        {"headline": "Monsoon showers bring relief, civic authorities issue minor water-logging advisory in low areas", "category": "Advisory"},
        {"headline": "Annual Food and Haleem Festival begins in Old City", "category": "Event"}
    ]
}


@tool("search_flights")
def search_flights(origin: str, destination: str, departure_date: str, return_date: str) -> str:
    """
    Search for flights between origin and destination for specified departure and return dates.
    Returns a JSON string of available flight options.
    """
    # Standardize input keys to upper case
    origin_key = origin.strip().upper()
    dest_key = destination.strip().upper()

    outbound = MOCK_FLIGHTS.get((origin_key, dest_key), [
        {"flight_no": f"FL-{origin_key}{dest_key}-99", "airline": "Generic Air", "departure": "09:00", "arrival": "11:30", "price": 6000}
    ])
    
    inbound = MOCK_FLIGHTS.get((dest_key, origin_key), [
        {"flight_no": f"FL-{dest_key}{origin_key}-98", "airline": "Generic Air", "departure": "15:00", "arrival": "17:30", "price": 6000}
    ])

    return json.dumps({
        "status": "success",
        "search_parameters": {
            "origin": origin_key,
            "destination": dest_key,
            "departure_date": departure_date,
            "return_date": return_date
        },
        "outbound_flights": outbound,
        "inbound_flights": inbound
    }, indent=2)


@tool("search_hotels")
def search_hotels(destination: str, check_in_date: str, check_out_date: str) -> str:
    """
    Search for hotels in a destination city for the specified check-in and check-out dates.
    Returns a JSON string of available hotel options.
    """
    dest = destination.strip().title()
    hotels = MOCK_HOTELS.get(dest, [
        {"name": f"Comfort Inn {dest}", "rating": "3 Star", "price_per_night": 4500, "location": "Downtown"}
    ])

    return json.dumps({
        "status": "success",
        "search_parameters": {
            "destination": dest,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date
        },
        "hotels": hotels
    }, indent=2)


@tool("get_weather_forecast")
def get_weather_forecast(destination: str, start_date: str, end_date: str) -> str:
    """
    Get weather forecast for a destination city between start_date and end_date.
    Returns a JSON string with weather details per day.
    """
    dest = destination.strip().title()
    forecast = MOCK_WEATHER.get(dest, [
        {"date": start_date, "forecast": "Pleasant", "temp_range": "22°C - 30°C", "rain_prob": "15%"},
        {"date": end_date, "forecast": "Pleasant", "temp_range": "22°C - 30°C", "rain_prob": "15%"}
    ])

    return json.dumps({
        "status": "success",
        "destination": dest,
        "forecast": forecast
    }, indent=2)


@tool("get_local_news_and_advisories")
def get_local_news_and_advisories(destination: str) -> str:
    """
    Get current local news, events, and transit/safety advisories for a destination city.
    Returns a JSON string of news articles and advisories.
    """
    dest = destination.strip().title()
    news = MOCK_NEWS.get(dest, [
        {"headline": f"Annual tourism drive launched in {dest}", "category": "General"},
        {"headline": f"No active alerts in {dest}", "category": "Advisory"}
    ])

    return json.dumps({
        "status": "success",
        "destination": dest,
        "news_and_advisories": news
    }, indent=2)
