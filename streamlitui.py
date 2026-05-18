import ssl
import os

# Fix SSL certificate issues in corporate proxy environments
os.environ["PYTHONHTTPSVERIFY"] = "0"
os.environ["SSL_VERIFY"] = "false"

_original_create_default_context = ssl.create_default_context
def _create_unverified_context(*args, **kwargs):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx
ssl.create_default_context = _create_unverified_context
ssl._create_default_https_context = _create_unverified_context

import streamlit as st
import pandas as pd
import re
from io import StringIO
from datetime import datetime
from src.vacation_planner.crew import VacationPlanner # Replace path 1


def parse_markdown_table(md_content):
    """Parse a markdown table from content into a pandas DataFrame."""
    lines = md_content.strip().split('\n')
    table_lines = [l for l in lines if '|' in l and l.strip().startswith('|')]
    if len(table_lines) < 3:
        return None
    # Remove separator line (contains ---)
    header = table_lines[0]
    data_lines = [l for l in table_lines[1:] if not re.match(r'^\|[\s\-:|]+\|$', l.strip())]
    # Parse header
    cols = [c.strip() for c in header.strip('|').split('|')]
    # Parse rows
    rows = []
    for line in data_lines:
        cells = [c.strip() for c in line.strip('|').split('|')]
        if len(cells) == len(cols):
            rows.append(cells)
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=cols)
    return df


def extract_numeric(series):
    """Extract numeric values from a string series for sorting."""
    return pd.to_numeric(series.str.replace(r'[^\d.]', '', regex=True), errors='coerce')

# Comprehensive list of world cities for autocomplete suggestions
WORLD_CITIES = [
    "Abu Dhabi", "Accra", "Addis Ababa", "Adelaide", "Agra", "Ahmedabad", "Alexandria", "Algiers",
    "Amman", "Amsterdam", "Anchorage", "Ankara", "Antalya", "Antwerp", "Athens", "Atlanta",
    "Auckland", "Austin", "Baghdad", "Baku", "Bali", "Baltimore", "Bangalore", "Bangkok",
    "Barcelona", "Basel", "Beijing", "Beirut", "Belfast", "Belgrade", "Belize City", "Bergen",
    "Berlin", "Bern", "Bogota", "Bologna", "Boston", "Brasilia", "Bratislava", "Brisbane",
    "Brussels", "Bucharest", "Budapest", "Buenos Aires", "Buffalo", "Cairo", "Calgary",
    "Cancun", "Cape Town", "Caracas", "Cardiff", "Cartagena", "Casablanca", "Charlotte",
    "Chennai", "Chicago", "Christchurch", "Cincinnati", "Cleveland", "Colombo", "Copenhagen",
    "Corfu", "Cork", "Dallas", "Damascus", "Dar es Salaam", "Delhi", "Denver", "Detroit",
    "Dhaka", "Doha", "Dominica", "Dresden", "Dubai", "Dublin", "Dubrovnik", "Durban",
    "Dusseldorf", "Edinburgh", "Edmonton", "Eindhoven", "Fes", "Florence", "Fort Lauderdale",
    "Frankfurt", "Fukuoka", "Galle", "Geneva", "Genoa", "Glasgow", "Goa", "Gothenburg",
    "Granada", "Guadalajara", "Guangzhou", "Guatemala City", "Hamburg", "Hanoi", "Havana",
    "Helsinki", "Ho Chi Minh City", "Hobart", "Hong Kong", "Honolulu", "Houston", "Hyderabad",
    "Ibiza", "Indianapolis", "Innsbruck", "Istanbul", "Jacksonville", "Jaipur", "Jakarta",
    "Jeddah", "Jerusalem", "Johannesburg", "Kabul", "Kampala", "Karachi", "Kathmandu",
    "Kiev", "Kigali", "Kochi", "Kolkata", "Krakow", "Kuala Lumpur", "Kuwait City", "Kyoto",
    "Lagos", "Lahore", "Las Vegas", "Lausanne", "Leeds", "Lima", "Lisbon", "Liverpool",
    "Ljubljana", "London", "Los Angeles", "Lucerne", "Luxor", "Lyon", "Macau", "Madrid",
    "Malaga", "Male", "Mallorca", "Manchester", "Manila", "Marrakech", "Marseille", "Mecca",
    "Medina", "Melbourne", "Memphis", "Mexico City", "Miami", "Milan", "Milwaukee",
    "Minneapolis", "Minsk", "Monaco", "Monterrey", "Montevideo", "Montreal", "Moscow",
    "Mumbai", "Munich", "Muscat", "Mysore", "Nagoya", "Nairobi", "Nanjing", "Naples",
    "Nashville", "Nassau", "New Orleans", "New York", "Nice", "Nicosia", "Nuremberg",
    "Oakland", "Okinawa", "Oman", "Orlando", "Osaka", "Oslo", "Ottawa", "Oxford",
    "Palermo", "Palm Beach", "Panama City", "Paris", "Pattaya", "Perth", "Philadelphia",
    "Phnom Penh", "Phoenix", "Phuket", "Pittsburgh", "Portland", "Porto", "Prague",
    "Pune", "Queenstown", "Quito", "Rabat", "Raleigh", "Reykjavik", "Riga", "Rio de Janeiro",
    "Riyadh", "Rome", "Rotterdam", "Sacramento", "Salzburg", "San Antonio", "San Diego",
    "San Francisco", "San Jose", "San Juan", "San Sebastian", "Santiago", "Santo Domingo",
    "Sao Paulo", "Sapporo", "Sarajevo", "Savannah", "Seattle", "Seoul", "Seville",
    "Shanghai", "Shenzhen", "Siem Reap", "Singapore", "Sofia", "Split", "St. Petersburg",
    "Stockholm", "Strasbourg", "Stuttgart", "Surabaya", "Sydney", "Taipei", "Tallinn",
    "Tampa", "Tangier", "Tashkent", "Tbilisi", "Tehran", "Tel Aviv", "The Hague",
    "Thessaloniki", "Thiruvananthapuram", "Tirana", "Tokyo", "Toronto", "Toulouse",
    "Tripoli", "Tunis", "Turin", "Udaipur", "Ulaanbaatar", "Utrecht", "Valencia",
    "Vancouver", "Venice", "Verona", "Victoria", "Vienna", "Vilnius", "Warsaw",
    "Washington DC", "Wellington", "Windhoek", "Winnipeg", "Wuhan", "Xi'an", "Yangon",
    "Yerevan", "Yokohama", "Zagreb", "Zanzibar", "Zurich"
]

st.set_page_config(page_title="Dream Vacation Planner — AI Trip Genie", page_icon="✈️")

# Add Open Graph meta tags for URL preview/thumbnail
st.markdown("""
<meta property="og:title" content="Dream Vacation Planner — AI Trip Genie" />
<meta property="og:description" content="Transform dreams into travel plans with an AI-powered itinerary designer." />
<meta property="og:type" content="website" />
<meta property="og:image" content="https://img.icons8.com/color/96/000000/vacation.png" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="Dream Vacation Planner — AI Trip Genie" />
<meta name="twitter:description" content="Transform dreams into travel plans with an AI-powered itinerary designer." />
""", unsafe_allow_html=True)

# Enhanced CSS styling
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3rem;
    font-weight: bold;
    text-align: center;
    margin-bottom: 0;
}
.subtitle {
    color: #666;
    text-align: center;
    font-size: 1.2rem;
    margin-bottom: 2rem;
}
.feature-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem;
    border-radius: 15px;
    margin: 1rem 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    transition: transform 0.3s ease;
}
.feature-card:hover {
    transform: translateY(-5px);
}
.vacation-container {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    padding: 2rem;
    border-radius: 15px;
    margin: 1rem 0;
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">✈️ Dream Vacation Planner</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Your AI travel concierge for unforgettable adventures — curated just for you.</p>', unsafe_allow_html=True)

# Enhanced input form
st.markdown("### 🌍 Where would you like to go?")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    with st.form("vacation_form"):
        source_city = st.selectbox(
            "Source City",
            options=WORLD_CITIES,
            index=None,
            placeholder="Type to search (e.g., Mum, Par, New)...",
            help="Start typing at least 3 letters to see suggestions"
        )
        destination = st.selectbox(
            "Destination",
            options=WORLD_CITIES,
            index=None,
            placeholder="Type to search (e.g., Lon, Tok, Rom)...",
            help="Start typing at least 3 letters to see suggestions"
        )
        number_of_days = st.number_input("Number of Days", min_value=1, max_value=30, value=5, help="How many days is your trip?")
        
        submitted = st.form_submit_button("🚀 Plan My Dream Vacation", type="primary", use_container_width=True)

# Add some popular destinations as quick options
st.markdown("#### 🔥 Popular Destinations")
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🗼 Paris", use_container_width=True):
        st.session_state.destination = "Paris"
with col2:
    if st.button("🗾 Tokyo", use_container_width=True):
        st.session_state.destination = "Tokyo"
with col3:
    if st.button("🏛️ Rome", use_container_width=True):
        st.session_state.destination = "Rome"
with col4:
    if st.button("🏖️ Bali", use_container_width=True):
        st.session_state.destination = "Bali"

# Handle quick destination selection
if 'destination' in st.session_state:
    destination = st.session_state.destination
    submitted = True
    number_of_days = 5  # Default for quick selections
    source_city = "New York"  # Default source for quick selections
    del st.session_state.destination

if submitted and destination:
    if not source_city:
        st.warning("⚠️ Please enter a source city!")
    else:
        with st.spinner("🌍 Planning your amazing vacation... This may take a few minutes."):
            try:
                inputs = {
                    "topic": destination,
                    "source_city": source_city,
                    "current_year": str(datetime.now().year),
                    "number_of_days": str(number_of_days)
                }
                
                # Progress indicators
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text('🔍 Researching destination...')
                progress_bar.progress(10)
                
                # Run the crew
                result = VacationPlanner().crew().kickoff(inputs=inputs)
                
                progress_bar.progress(100)
                status_text.text('✅ Complete!')
                
                st.balloons()
                
                # Store results in session state so they persist across reruns
                st.session_state.plan_ready = True
                st.session_state.plan_destination = destination
                st.session_state.plan_source_city = source_city
                st.session_state.plan_number_of_days = number_of_days
                # Store weather output
                weather_output = None
                if hasattr(result, 'tasks_output') and len(result.tasks_output) > 2:
                    weather_output = result.tasks_output[2].raw
                st.session_state.plan_weather = weather_output
                
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")
                st.info("🛠️ Please check your AWS credentials and API keys")

elif submitted:
    st.warning("⚠️ Please enter a destination to start planning!")

# Display results from session state (persists across reruns/sort changes)
if st.session_state.get('plan_ready'):
    dest = st.session_state.plan_destination
    src = st.session_state.plan_source_city
    days = st.session_state.plan_number_of_days
    
    st.success(f"🎉 Your {src} → {dest} vacation plan is ready!")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Overview Report", 
        "🌤️ Weather & Best Time", 
        "🗓️ Day-by-Day Itinerary",
        "🏨 Hotels & Stays",
        "🍽️ Restaurants & Cafes",
        "🎯 Activities"
    ])
    
    with tab1:
        if os.path.exists("report.md"):
            with open("report.md", "r", encoding="utf-8") as f:
                report_content = f.read()
            st.markdown(f"## 🗺️ Your {dest} Adventure Plan")
            st.markdown(report_content)
            st.download_button(
                label="💾 Download Overview",
                data=report_content,
                file_name=f"{dest}_vacation_plan.md",
                mime="text/markdown"
            )
    
    with tab2:
        st.markdown(f"## 🌤️ Weather & Best Time to Visit {dest}")
        weather_data = st.session_state.get('plan_weather')
        if weather_data:
            st.markdown(weather_data)
        else:
            st.info("Weather data not available.")
    
    with tab3:
        if os.path.exists("detailed_itinerary.md"):
            with open("detailed_itinerary.md", "r", encoding="utf-8") as f:
                itinerary_content = f.read()
            st.markdown(f"## 🗓️ {days}-Day Itinerary: {src} → {dest}")
            st.markdown(itinerary_content)
            st.download_button(
                label="💾 Download Itinerary",
                data=itinerary_content,
                file_name=f"{dest}_{days}day_itinerary.md",
                mime="text/markdown"
            )
    
    with tab4:
        st.markdown(f"## 🏨 Best Hotels & Stays in {dest}")
        if os.path.exists("hotels.md"):
            with open("hotels.md", "r", encoding="utf-8") as f:
                hotels_content = f.read()
            
            df_hotels = parse_markdown_table(hotels_content)
            if df_hotels is not None:
                sort_option = st.selectbox(
                    "Sort by:",
                    ["Best Reviewed (Google Rating)", "Price: Low to High", "Price: High to Low"],
                    key="hotel_sort"
                )
                # Apply live sorting
                if sort_option == "Best Reviewed (Google Rating)":
                    sort_col = [c for c in df_hotels.columns if 'rating' in c.lower() and 'google' in c.lower()]
                    if sort_col:
                        df_hotels['_sort'] = extract_numeric(df_hotels[sort_col[0]])
                        df_hotels = df_hotels.sort_values('_sort', ascending=False).drop('_sort', axis=1)
                elif sort_option == "Price: Low to High":
                    sort_col = [c for c in df_hotels.columns if 'price' in c.lower()]
                    if sort_col:
                        df_hotels['_sort'] = extract_numeric(df_hotels[sort_col[0]])
                        df_hotels = df_hotels.sort_values('_sort', ascending=True).drop('_sort', axis=1)
                elif sort_option == "Price: High to Low":
                    sort_col = [c for c in df_hotels.columns if 'price' in c.lower()]
                    if sort_col:
                        df_hotels['_sort'] = extract_numeric(df_hotels[sort_col[0]])
                        df_hotels = df_hotels.sort_values('_sort', ascending=False).drop('_sort', axis=1)
                
                st.dataframe(df_hotels.reset_index(drop=True), use_container_width=True, hide_index=True)
            else:
                st.markdown(hotels_content)
            
            st.download_button(
                label="💾 Download Hotels List",
                data=hotels_content,
                file_name=f"{dest}_hotels.md",
                mime="text/markdown"
            )
        else:
            st.info("Hotel data not available yet.")
    
    with tab5:
        st.markdown(f"## 🍽️ Best Restaurants & Cafes in {dest}")
        if os.path.exists("restaurants.md"):
            with open("restaurants.md", "r", encoding="utf-8") as f:
                restaurants_content = f.read()
            
            df_restaurants = parse_markdown_table(restaurants_content)
            if df_restaurants is not None:
                sort_option_rest = st.selectbox(
                    "Sort by:",
                    ["Best Reviewed (Google Rating)", "Cost: Low to High", "Cost: High to Low"],
                    key="restaurant_sort"
                )
                # Apply live sorting
                if sort_option_rest == "Best Reviewed (Google Rating)":
                    sort_col = [c for c in df_restaurants.columns if 'rating' in c.lower() and 'google' in c.lower()]
                    if sort_col:
                        df_restaurants['_sort'] = extract_numeric(df_restaurants[sort_col[0]])
                        df_restaurants = df_restaurants.sort_values('_sort', ascending=False).drop('_sort', axis=1)
                elif sort_option_rest == "Cost: Low to High":
                    sort_col = [c for c in df_restaurants.columns if 'cost' in c.lower()]
                    if sort_col:
                        df_restaurants['_sort'] = extract_numeric(df_restaurants[sort_col[0]])
                        df_restaurants = df_restaurants.sort_values('_sort', ascending=True).drop('_sort', axis=1)
                elif sort_option_rest == "Cost: High to Low":
                    sort_col = [c for c in df_restaurants.columns if 'cost' in c.lower()]
                    if sort_col:
                        df_restaurants['_sort'] = extract_numeric(df_restaurants[sort_col[0]])
                        df_restaurants = df_restaurants.sort_values('_sort', ascending=False).drop('_sort', axis=1)
                
                st.dataframe(df_restaurants.reset_index(drop=True), use_container_width=True, hide_index=True)
            else:
                st.markdown(restaurants_content)
            
            st.download_button(
                label="💾 Download Restaurants List",
                data=restaurants_content,
                file_name=f"{dest}_restaurants.md",
                mime="text/markdown"
            )
        else:
            st.info("Restaurant data not available yet.")
    
    with tab6:
        st.markdown(f"## 🎯 Activities & Entertainment in {dest}")
        if os.path.exists("activities.md"):
            with open("activities.md", "r", encoding="utf-8") as f:
                activities_content = f.read()
            
            st.markdown(activities_content)
            st.download_button(
                label="💾 Download Activities Guide",
                data=activities_content,
                file_name=f"{dest}_activities.md",
                mime="text/markdown"
            )
        else:
            st.info("Activities data not available yet.")

# Enhanced sidebar
with st.sidebar:
    st.markdown("### 🌟 What This App Does")
    
    features = [
        ("🔍 Research destinations", "Finds interesting facts and hidden gems", "#667eea", "#764ba2"),
        ("📋 Create detailed itineraries", "Source to destination day-by-day plans", "#f093fb", "#f5576c"),
        ("🏨 Find best hotels", "Sorted by reviews or price", "#FF6B6B", "#ee5a24"),
        ("🍽️ Recommend restaurants", "With cost for 2 and Google ratings", "#4facfe", "#00f2fe"),
        ("🎯 Discover activities", "Gaming, sports, spa, nightlife & more", "#43e97b", "#38f9d7"),
        ("🌤️ Weather insights", "Best time to visit analysis", "#a18cd1", "#fbc2eb")
    ]
    
    for title, desc, color1, color2 in features:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {color1} 0%, {color2} 100%); 
                    padding: 1rem; border-radius: 10px; margin: 0.5rem 0;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <p style="color: white; margin: 0; font-weight: bold;">{title}</p>
            <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;">{desc}</p>
        </div>
        """, unsafe_allow_html=True)
    
    
    st.markdown("---")
    st.markdown("### 📊 Stats")
    st.metric("Destinations Explored", "1000+")
    st.metric("Happy Travelers", "500+")
    
