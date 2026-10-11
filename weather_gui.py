
import streamlit as st
import requests

st.set_page_config(
    page_title="Weatherly",
    page_icon="🌦️",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #edf5ff, #f5f3ff, #e8fbf5);
}
.block-container {
    max-width: 1100px;
    padding-top: 2rem;
}
.hero {
    background: linear-gradient(120deg, #102f58, #2878b9);
    padding: 28px;
    border-radius: 22px;
    color: white;
    margin-bottom: 24px;
}
.hero h1 { color: white; margin: 0; }
.hero p { color: #e2efff; }
.metric {
    background: white;
    border: 1px solid #dce8f5;
    border-radius: 18px;
    padding: 20px;
    min-height: 115px;
    box-shadow: 0 5px 18px rgba(30,70,120,.06);
}
.label { color: #64748b; font-size: 14px; }
.value { color: #163b70; font-size: 25px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<h1>🌦️ Weatherly</h1>
<p>Your weather, at a glance. Search any city for current conditions and forecast.</p>
</div>
""", unsafe_allow_html=True)

city = st.text_input(
    "📍 Search city",
    placeholder="Enter a city, e.g. Jammu or Delhi"
)

search = st.button("🔍 Get Weather", type="primary", use_container_width=True)


def describe_weather(code, is_day):
    if code == 0:
        return ("☀️", "Clear Sky" if is_day else "Clear Night")
    if code in [1, 2]:
        return ("🌤️", "Partly Cloudy")
    if code == 3:
        return ("☁️", "Cloudy")
    if code in [45, 48]:
        return ("🌫️", "Foggy")
    if code in [51, 53, 55, 56, 57]:
        return ("🌦️", "Drizzle")
    if code in [61, 63, 65, 66, 67, 80, 81, 82]:
        return ("🌧️", "Rainy")
    if code in [71, 73, 75, 77, 85, 86]:
        return ("❄️", "Snowy")
    if code in [95, 96, 99]:
        return ("⛈️", "Thunderstorm")
    return ("🌡️", "Changing Conditions")


def metric_card(label, value):
    st.markdown(
        f'<div class="metric"><div class="label">{label}</div>'
        f'<div class="value">{value}</div></div>',
        unsafe_allow_html=True
    )


if search:
    if not city.strip():
        st.warning("Please enter a city name.")
    else:
        try:
            with st.spinner("Getting the latest weather..."):
                geo = requests.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={"name": city.strip(), "count": 1, "language": "en"},
                    timeout=10
                )
                geo.raise_for_status()
                places = geo.json().get("results", [])

                if not places:
                    st.error("City not found. Check the spelling and try again.")
                    st.stop()

                place = places[0]

                result = requests.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": place["latitude"],
                        "longitude": place["longitude"],
                        "current": (
                            "temperature_2m,relative_humidity_2m,"
                            "apparent_temperature,is_day,precipitation,"
                            "rain,weather_code,wind_speed_10m"
                        ),
                        "hourly": "precipitation_probability",
                        "daily": (
                            "temperature_2m_max,temperature_2m_min,"
                            "precipitation_probability_max,precipitation_sum"
                        ),
                        "forecast_days": 1,
                        "timezone": "auto"
                    },
                    timeout=10
                )
                result.raise_for_status()
                data = result.json()

            current = data["current"]
            hourly = data["hourly"]
            daily = data["daily"]

            icon, condition = describe_weather(
                current["weather_code"], current["is_day"]
            )

            probability = None
            for i, time in enumerate(hourly["time"]):
                if time == current["time"]:
                    probability = hourly["precipitation_probability"][i]
                    break

            st.subheader(
                f"{icon}  {place['name']}, {place.get('country', '')}"
            )
            st.caption(
                f"{condition}  ·  Local observation time: {current['time']}"
            )

            st.markdown("### Current Weather")
            cols = st.columns(4)
            current_metrics = [
                ("🌡️ Temperature", f"{current['temperature_2m']} °C"),
                ("🤗 Feels Like", f"{current['apparent_temperature']} °C"),
                ("💧 Humidity", f"{current['relative_humidity_2m']}%"),
                ("💨 Wind Speed", f"{current['wind_speed_10m']} km/h"),
            ]

            for col, (label, value) in zip(cols, current_metrics):
                with col:
                    metric_card(label, value)

            st.markdown("### 🌧️ Rain & Precipitation")
            cols = st.columns(3)
            rain_metrics = [
                (
                    "Chance of Rain Now",
                    f"{probability}%" if probability is not None else "N/A"
                ),
                ("Rain Right Now", f"{current['rain']} mm"),
                ("Expected Rain Today", f"{daily['precipitation_sum'][0]} mm"),
            ]

            for col, (label, value) in zip(cols, rain_metrics):
                with col:
                    metric_card(label, value)

            if probability is not None:
                st.progress(probability / 100)
                st.caption(
                    f"Forecast probability of precipitation this hour: {probability}%"
                )

            st.markdown("### 📅 Today's Forecast")
            cols = st.columns(3)
            forecast_metrics = [
                ("☀️ Maximum Temperature", f"{daily['temperature_2m_max'][0]} °C"),
                ("🌙 Minimum Temperature", f"{daily['temperature_2m_min'][0]} °C"),
                (
                    "🌧️ Max Rain Probability",
                    f"{daily['precipitation_probability_max'][0]}%"
                ),
            ]

            for col, (label, value) in zip(cols, forecast_metrics):
                with col:
                    metric_card(label, value)

            st.caption("Weather data provided by Open-Meteo.")

        except requests.exceptions.RequestException:
            st.error("Could not fetch weather. Check your internet and try again.")
        except (KeyError, IndexError, ValueError):
            st.error("Weather data could not be processed. Please try again.")

st.markdown("---")
st.caption("Weatherly · Live weather dashboard")