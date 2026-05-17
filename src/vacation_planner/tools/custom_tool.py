from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import json
import urllib.request
import urllib.parse
import ssl


class WeatherToolInput(BaseModel):
    """Input schema for WeatherTool."""
    city: str = Field(..., description="The city name to get current weather for.")

class WeatherTool(BaseTool):
    name: str = "Get Current Weather"
    description: str = (
        "Fetches the current weather conditions for a given city including temperature, humidity, "
        "wind speed, and weather description. Use this to provide real-time weather data."
    )
    args_schema: Type[BaseModel] = WeatherToolInput

    def _run(self, city: str) -> str:
        try:
            # Use wttr.in API (free, no key needed)
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
            req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
            with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                data = json.loads(response.read().decode())
            
            current = data["current_condition"][0]
            weather_info = (
                f"Current Weather in {city}:\n"
                f"- Temperature: {current['temp_C']}°C ({current['temp_F']}°F)\n"
                f"- Feels Like: {current['FeelsLikeC']}°C ({current['FeelsLikeF']}°F)\n"
                f"- Humidity: {current['humidity']}%\n"
                f"- Weather: {current['weatherDesc'][0]['value']}\n"
                f"- Wind Speed: {current['windspeedKmph']} km/h\n"
                f"- Wind Direction: {current['winddir16Point']}\n"
                f"- Visibility: {current['visibility']} km\n"
                f"- UV Index: {current['uvIndex']}\n"
                f"- Cloud Cover: {current['cloudcover']}%\n"
                f"- Observation Time: {current['observation_time']}\n"
            )
            
            # Add monthly averages if available
            if "weather" in data:
                weather_info += "\nUpcoming 3-Day Forecast:\n"
                for day in data["weather"][:3]:
                    weather_info += (
                        f"  - {day['date']}: {day['mintempC']}°C to {day['maxtempC']}°C, "
                        f"{day['hourly'][4]['weatherDesc'][0]['value']}\n"
                    )
            
            return weather_info
        except Exception as e:
            return f"Unable to fetch weather data for {city}: {str(e)}. Please use your general knowledge about the climate of {city}."
