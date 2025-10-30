import streamlit as st
import pandas as pd
import json
import datetime
import re


# Page configuration
st.set_page_config(
    page_title="AgriClimate Intelligence - Tamil Nadu",
    page_icon="🌾",
    layout="wide"
)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []



# Load datasets
@st.cache_data
def load_datasets():
    """Load CSV datasets from data.gov.in"""
    try:
        rainfall_df = pd.read_csv('data/rainfall_data.csv')
        crop_df = pd.read_csv('data/crop_production.csv')
        return rainfall_df, crop_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None

@st.cache_data
def load_metadata():
    """Load dataset metadata"""
    try:
        with open('data/dataset.json', 'r') as f:
            return json.load(f)
    except:
        return {
            "rainfall_data": {
                "title": "District-wise Rainfall Data - Tamil Nadu (2017-18)",
                "source": "India Meteorological Department",
                "years_covered": "2017-2018",
                "description": "Seasonal and annual rainfall for 32 Tamil Nadu districts"
            },
            "crop_production": {
                "title": "Crop Production Statistics - Tamil Nadu (2012-13)",
                "source": "Ministry of Agriculture & Farmers Welfare",
                "years_covered": "2012-2013",
                "description": "Area, production, and productivity for major crops"
            }
        }

def analyze_question(question, rainfall_df, crop_df):
    question_lower = question.lower().strip()
    response = {"text": "", "data": None, "data_type": None}

    # --- 1️⃣ Handle Greetings / Small Talk (keep as you already have) ---
    greetings = ["hi", "hello", "hey", "good morning", "good evening"]
    if any(re.fullmatch(rf"\b{g}\b", question_lower) for g in greetings):
       response["text"] = "👋 Hello there! How can I help you explore Tamil Nadu’s rainfall or crop data today?"
       return response

    if "how are you" in question_lower:
        response["text"] = "😊 I’m just a chatbot, but I’m doing great! Ready to analyze data for you."
        return response

    if "who made you" in question_lower or "developer" in question_lower:
        response["text"] = "🤖 I was created by **Ishwaree Patil** as part of the *Bharat Digital Fellowship 2026* project!"
        return response
    if "what is your name" in question_lower or "who are you" in question_lower or "your name" in question_lower:
        response["text"] = "🤖 My name is **AgriClimateBot** — your data assistant for Tamil Nadu’s agriculture and climate insights! 🌾☁️"
        return response

    if "bye" in question_lower or "thank" in question_lower:
        response["text"] = "👋 You’re welcome! Have a wonderful day ahead 🌾"
        return response

    # --- 2️⃣ Fallback for unrelated or unusual questions ---
    # Keywords related to data domain
    data_keywords = [
        "rain", "rainfall", "district", "crop", "production", "area",
        "productivity", "yield", "monsoon", "agriculture", "climate"
    ]

    # If none of the relevant keywords appear → respond with chatbot purpose
    if not any(k in question_lower for k in data_keywords):
        response["text"] = (
            "🤖 I’m **AgriClimateBot**, a data assistant built to analyze and explain "
            "**Tamil Nadu’s rainfall and crop production datasets**. 🌾☁️\n\n"
            "I’m not designed for general conversation — but I can help you with agriculture and climate insights!\n\n"
            "💡 Try asking questions like:\n"
            "- Which district received the most rainfall in 2019?\n"
            "- Which crop had the highest productivity?\n"
            "- Compare rainfall between Chennai and Coimbatore.\n"
            "- What is the average rainfall across Tamil Nadu?\n"
        )
        return response
    # --- 3️⃣ Handle "Which district has highest rainfall" ---
    try:
        pattern = r"(which district|where).*?(highest|max(?:imum)?|most).*?(rain|rainfall|precipitation)"
        if re.search(pattern, question_lower):
            if rainfall_df is None or rainfall_df.empty:
                response["text"] = "⚠️ Sorry, I couldn’t find any rainfall data to analyze right now."
                return response

            # Identify possible columns
            district_col = next((c for c in rainfall_df.columns if re.search(r"district|region|zone|place", c, re.I)), None)
            rainfall_col = next((c for c in rainfall_df.columns if re.search(r"rain|precip", c, re.I)), None)

            if not district_col or not rainfall_col:
                response["text"] = "⚠️ Couldn't identify district or rainfall columns in your dataset. Please check column names."
                return response

            # Convert to numeric and clean
            df = rainfall_df[[district_col, rainfall_col]].copy()
            df[rainfall_col] = pd.to_numeric(df[rainfall_col], errors="coerce")
            df = df.dropna(subset=[rainfall_col])

            if df.empty:
                response["text"] = "⚠️ The rainfall data appears empty or invalid after cleaning."
                return response

            # Group and find highest rainfall
            grouped = df.groupby(district_col)[rainfall_col].mean()
            if grouped.empty:
                response["text"] = "⚠️ Unable to compute rainfall statistics due to missing data."
                return response

            top_district = grouped.idxmax()
            max_rainfall = grouped.max()

            response["text"] = (
                f"🌧️ The district with the **highest average rainfall** is **{top_district}**, "
                f"with approximately **{round(max_rainfall, 2)} mm** of rainfall."
            )
            response["data"] = df
            response["data_type"] = "rainfall"
            return response

    except Exception as e:
        response["text"] = f"❌ An unexpected error occurred while analyzing rainfall data: {str(e)}"
        return response

    # --- 4️⃣ Default fallback if no pattern matched ---
    response["text"] = "🤔 I couldn’t understand that question clearly. Could you please rephrase it?"
    return response
      

    # RAINFALL QUERIES
    if any(word in question_lower for word in ['rainfall', 'rain', 'monsoon', 'precipitation', 'weather', 'climate']):
        response['data_type'] = 'rainfall'
        
        district_col = 'District'
        total_rainfall_col = 'Total Actual Rainfall (June\'17 to May\'18) in mm'
        sw_monsoon_col = 'Actual Rainfall in South West Monsoon (June\'17 to September\'17) in mm'
        ne_monsoon_col = 'Actual Rainfall in North East Monsoon (October\'17 to December\'17) in mm'
        
        # Check for specific districts
        districts_mentioned = []
        for district in rainfall_df[district_col].values:
            if str(district).lower() in question_lower:
                districts_mentioned.append(district)
        
        if districts_mentioned:
            data = rainfall_df[rainfall_df[district_col].isin(districts_mentioned)]
            response['data'] = data
            
            if len(districts_mentioned) == 1:
                district_name = districts_mentioned[0]
                district_data = data.iloc[0]
                total_rain = district_data[total_rainfall_col]
                sw_rain = district_data[sw_monsoon_col]
                ne_rain = district_data[ne_monsoon_col]
                
                response['text'] = f"## 🌧️ Rainfall Analysis for {district_name}\n\n"
                response['text'] += f"### Annual Rainfall (2017-18)\n"
                response['text'] += f"- **Total Annual Rainfall**: {total_rain:.1f} mm\n"
                response['text'] += f"- **South West Monsoon** (June-Sept): {sw_rain:.1f} mm\n"
                response['text'] += f"- **North East Monsoon** (Oct-Dec): {ne_rain:.1f} mm\n\n"
                
                # Compare with state average
                state_avg = rainfall_df[rainfall_df[district_col] == 'State Average'][total_rainfall_col].values
                if len(state_avg) > 0:
                    diff = total_rain - state_avg[0]
                    if diff > 0:
                        response['text'] += f"📊 This is **{diff:.1f} mm above** the state average.\n\n"
                    else:
                        response['text'] += f"📊 This is **{abs(diff):.1f} mm below** the state average.\n\n"
                
                response['text'] += "*[Source: India Meteorological Department via data.gov.in]*"
            
            elif len(districts_mentioned) == 2:
                d1, d2 = districts_mentioned[0], districts_mentioned[1]
                r1 = data[data[district_col] == d1][total_rainfall_col].values[0]
                r2 = data[data[district_col] == d2][total_rainfall_col].values[0]
                
                response['text'] = f"## 📊 Rainfall Comparison (2017-18)\n\n"
                response['text'] += f"### {d1} vs {d2}\n\n"
                response['text'] += f"| District | Total Rainfall |\n"
                response['text'] += f"|----------|----------------|\n"
                response['text'] += f"| **{d1}** | {r1:.1f} mm |\n"
                response['text'] += f"| **{d2}** | {r2:.1f} mm |\n\n"
                
                diff = abs(r1 - r2)
                higher = d1 if r1 > r2 else d2
                
                response['text'] += f"**Analysis**: {higher} received **{diff:.1f} mm more** rainfall than the other district.\n\n"
                response['text'] += "*[Source: India Meteorological Department via data.gov.in]*"
            
            else:
                response['text'] = f"## 🌧️ Rainfall Data for Multiple Districts\n\n"
                response['text'] += f"Showing rainfall data for {len(districts_mentioned)} districts.\n\n"
                response['text'] += "*[Source: India Meteorological Department via data.gov.in]*"
        
        elif 'highest' in question_lower or 'maximum' in question_lower or 'most' in question_lower or 'top' in question_lower:
            # Extract number if mentioned
            num = 10
            if 'top 5' in question_lower or '5 highest' in question_lower:
                num = 5
            elif 'top 3' in question_lower or '3 highest' in question_lower:
                num = 3
            
            data = rainfall_df[rainfall_df[district_col] != 'State Average'].nlargest(num, total_rainfall_col)
            response['data'] = data
            
            top_district = data.iloc[0][district_col]
            top_rainfall = data.iloc[0][total_rainfall_col]
            
            response['text'] = f"## 🏆 Top {num} Districts by Rainfall (2017-18)\n\n"
            response['text'] += f"### Highest Rainfall:\n"
            response['text'] += f"**{top_district}** with **{top_rainfall:.1f} mm**\n\n"
            response['text'] += f"### Complete Ranking:\n"
            
            for idx, row in data.head(num).iterrows():
                rank = list(data.index).index(idx) + 1
                response['text'] += f"{rank}. **{row[district_col]}**: {row[total_rainfall_col]:.1f} mm\n"
            
            response['text'] += f"\n*[Source: India Meteorological Department via data.gov.in]*"
        
        elif 'lowest' in question_lower or 'minimum' in question_lower or 'least' in question_lower:
            data = rainfall_df[rainfall_df[district_col] != 'State Average'].nsmallest(10, total_rainfall_col)
            response['data'] = data
            
            bottom_district = data.iloc[0][district_col]
            bottom_rainfall = data.iloc[0][total_rainfall_col]
            
            response['text'] = f"## 📉 Districts with Lowest Rainfall (2017-18)\n\n"
            response['text'] += f"### Lowest Rainfall:\n"
            response['text'] += f"**{bottom_district}** with **{bottom_rainfall:.1f} mm**\n\n"
            response['text'] += f"### Bottom 10 Districts:\n"
            
            for idx, row in data.head(10).iterrows():
                rank = list(data.index).index(idx) + 1
                response['text'] += f"{rank}. **{row[district_col]}**: {row[total_rainfall_col]:.1f} mm\n"
            
            response['text'] += f"\n*[Source: India Meteorological Department via data.gov.in]*"
        
        elif 'average' in question_lower or 'mean' in question_lower:
            state_avg_data = rainfall_df[rainfall_df[district_col] == 'State Average']
            if len(state_avg_data) > 0:
                response['data'] = state_avg_data
                avg_rainfall = state_avg_data[total_rainfall_col].values[0]
                response['text'] = f"## 📊 Tamil Nadu State Average Rainfall (2017-18)\n\n"
                response['text'] += f"**Average Annual Rainfall**: {avg_rainfall:.1f} mm\n\n"
                response['text'] += "*[Source: India Meteorological Department via data.gov.in]*"
            else:
                avg_rainfall = rainfall_df[rainfall_df[district_col] != 'State Average'][total_rainfall_col].mean()
                response['text'] = f"## 📊 Tamil Nadu Average Rainfall (2017-18)\n\n"
                response['text'] += f"**Calculated Average**: {avg_rainfall:.1f} mm (across {len(rainfall_df)-1} districts)\n\n"
                response['text'] += "*[Source: India Meteorological Department via data.gov.in]*"
                response['data'] = rainfall_df.head(15)
        
        else:
            data = rainfall_df.head(15)
            response['data'] = data
            response['text'] = f"## 🌧️ Tamil Nadu Rainfall Data (2017-18)\n\n"
            response['text'] += f"Showing rainfall data for {len(rainfall_df)} districts including seasonal breakdowns.\n\n"
            response['text'] += "**Available Data:**\n"
            response['text'] += "- South West Monsoon (June-September)\n"
            response['text'] += "- North East Monsoon (October-December)\n"
            response['text'] += "- Winter Season (January-February)\n"
            response['text'] += "- Hot Weather Season (March-May)\n\n"
            response['text'] += "*[Source: India Meteorological Department via data.gov.in]*"
    
    # CROP QUERIES
    elif any(word in question_lower for word in ['crop', 'production', 'agriculture', 'farming', 'paddy', 'rice', 'wheat', 'productivity', 'yield', 'area', 'maize', 'ragi', 'jowar', 'bajra']):
        response['data_type'] = 'crops'
        
        crop_col = 'District'
        area_col = 'Area (Ha)'
        production_col = 'Production (Tonnes)'
        productivity_col = 'Productivity. (Tonnes/Ha)'

        
        # Check for specific crops
        crops_mentioned = []
        for crop in crop_df[crop_col].values:
            if str(crop).lower() in question_lower:
                crops_mentioned.append(crop)
        
        if crops_mentioned:
            data = crop_df[crop_df[crop_col].isin(crops_mentioned)]
            response['data'] = data
            
            response['text'] = f"## 🌾 Crop Production Analysis (Tamil Nadu 2012-13)\n\n"
            
            for crop in crops_mentioned[:5]:  # Show max 5 crops
                if crop in data[crop_col].values:
                    crop_data = data[data[crop_col] == crop].iloc[0]
                    
                    response['text'] += f"### {crop}\n"
                    response['text'] += f"- **Area Under Cultivation**: {crop_data[area_col]:.2f} thousand hectares\n"
                    response['text'] += f"- **Total Production**: {crop_data[production_col]:.2f} thousand metric tonnes\n"
                    response['text'] += f"- **Productivity**: {crop_data[productivity_col]:.0f} kg per hectare\n\n"
            
            response['text'] += "*[Source: Ministry of Agriculture & Farmers Welfare via data.gov.in]*"
        
        elif 'production' in question_lower or 'produce' in question_lower or 'top' in question_lower:
            num = 10
            if 'top 5' in question_lower or '5 highest' in question_lower:
                num = 5
            elif 'top 3' in question_lower:
                num = 3
            
            data = crop_df.nlargest(num, production_col)
            response['data'] = data
            
            top_crop = data.iloc[0][crop_col]
            top_production = data.iloc[0][production_col]
            
            response['text'] = f"## 🏆 Top {num} Crops by Production (Tamil Nadu 2012-13)\n\n"
            response['text'] += f"### Highest Production:\n"
            response['text'] += f"**{top_crop}** with **{top_production:.2f} thousand metric tonnes**\n\n"
            response['text'] += f"### Complete Ranking:\n\n"
            
            for idx, row in data.head(num).iterrows():
                rank = list(data.index).index(idx) + 1
                response['text'] += f"{rank}. **{row[crop_col]}**: {row[production_col]:.2f} thousand MT\n"
            
            response['text'] += f"\n*[Source: Ministry of Agriculture & Farmers Welfare via data.gov.in]*"
        
        elif 'productivity' in question_lower or 'yield' in question_lower:
            crop_df_clean = crop_df[crop_df[productivity_col] > 0]
            data = crop_df_clean.nlargest(10, productivity_col)
            response['data'] = data
            
            top_crop = data.iloc[0][crop_col]
            top_productivity = data.iloc[0][productivity_col]
            
            response['text'] = f"## 📈 Top 10 Crops by Productivity (Tamil Nadu 2012-13)\n\n"
            response['text'] += f"### Highest Yield:\n"
            response['text'] += f"**{top_crop}** with **{top_productivity:.0f} kg per hectare**\n\n"
            response['text'] += f"### Complete Ranking:\n\n"
            
            for idx, row in data.head(10).iterrows():
                rank = list(data.index).index(idx) + 1
                response['text'] += f"{rank}. **{row[crop_col]}**: {row[productivity_col]:.0f} kg/ha\n"
            
            response['text'] += f"\n*[Source: Ministry of Agriculture & Farmers Welfare via data.gov.in]*"
        
        elif 'area' in question_lower:
            data = crop_df.nlargest(10, area_col)
            response['data'] = data
            
            response['text'] = f"## 📏 Top 10 Crops by Cultivation Area (Tamil Nadu 2012-13)\n\n"
            
            for idx, row in data.head(10).iterrows():
                rank = list(data.index).index(idx) + 1
                response['text'] += f"{rank}. **{row[crop_col]}**: {row[area_col]:.2f} thousand hectares\n"
            
            response['text'] += f"\n*[Source: Ministry of Agriculture & Farmers Welfare via data.gov.in]*"
        
        else:
            data = crop_df.head(10)
            response['data'] = data
            response['text'] = f"## 🌾 Tamil Nadu Crop Production Statistics (2012-13)\n\n"
            response['text'] += f"Showing production, area, and productivity data for major crops in Tamil Nadu.\n\n"
            response['text'] += f"**Total Crops in Dataset**: {len(crop_df)}\n\n"
            response['text'] += "*[Source: Ministry of Agriculture & Farmers Welfare via data.gov.in]*"
    
    # CORRELATION/COMPARISON QUERIES
    elif any(word in question_lower for word in ['correlate', 'correlation', 'relationship', 'impact', 'affect']):
        response['data_type'] = 'both'
        response['data'] = {
            'rainfall': rainfall_df.head(10),
            'crops': crop_df.head(10)
        }
        
        response['text'] = f"## 🔗 Agriculture & Climate Data Analysis\n\n"
        response['text'] += f"### Available Datasets:\n\n"
        response['text'] += f"**1. Rainfall Data (2017-18)**\n"
        response['text'] += f"- 32 districts in Tamil Nadu\n"
        response['text'] += f"- Seasonal and annual rainfall measurements\n"
        response['text'] += f"- Source: India Meteorological Department\n\n"
        response['text'] += f"**2. Crop Production Data (2012-13)**\n"
        response['text'] += f"- {len(crop_df)} major crops in Tamil Nadu\n"
        response['text'] += f"- Area, production, and productivity metrics\n"
        response['text'] += f"- Source: Ministry of Agriculture & Farmers Welfare\n\n"
        response['text'] += f"**Note**: The datasets cover different time periods (2012-13 for crops, 2017-18 for rainfall), which allows for historical trend analysis.\n\n"
        response['text'] += "*[Sources: IMD & Ministry of Agriculture via data.gov.in]*"
    
    # DEFAULT: Show both datasets
    else:
        response['data_type'] = 'both'
        response['data'] = {
            'rainfall': rainfall_df.head(10),
            'crops': crop_df.head(10)
        }
        
        response['text'] = f"## 🌾 AgriClimate Intelligence System\n\n"
        response['text'] += f"I have access to real data from **data.gov.in**:\n\n"
        response['text'] += f"### 📊 Available Datasets:\n\n"
        response['text'] += f"**1. Rainfall Data (2017-18)**\n"
        response['text'] += f"- 32 districts in Tamil Nadu\n"
        response['text'] += f"- Seasonal rainfall patterns\n"
        response['text'] += f"- Source: India Meteorological Department\n\n"
        response['text'] += f"**2. Crop Production Data (2012-13)**\n"
        response['text'] += f"- {len(crop_df)} crops\n"
        response['text'] += f"- Production, area, and productivity statistics\n"
        response['text'] += f"- Source: Ministry of Agriculture & Farmers Welfare\n\n"
        response['text'] += f"### 💡 You can ask me:\n"
        response['text'] += f"- Which district has the highest rainfall?\n"
        response['text'] += f"- Compare rainfall between Chennai and Coimbatore\n"
        response['text'] += f"- Show top 5 crops by production\n"
        response['text'] += f"- What is paddy production in Tamil Nadu?\n"
        response['text'] += f"- Which crops have the highest productivity?\n\n"
        response['text'] += "*[Data sourced from data.gov.in]*"
    
    return response

# Sidebar
with st.sidebar:
    st.title("🌾 AgriClimate Intelligence")
    st.markdown("### 📊 Data Sources from data.gov.in")
    
    metadata = load_metadata()
    
    for dataset_name, info in metadata.items():
        with st.expander(f"📄 {info['title']}", expanded=False):
            st.write(f"**Source:** {info['source']}")
            st.write(f"**Years:** {info['years_covered']}")
            if 'description' in info:
                st.write(f"**Details:** {info['description']}")
    
    st.markdown("---")
    st.markdown("### 💡 Sample Questions")
    st.markdown("""
    **Rainfall Queries:**
    - Which district has highest rainfall?
    - Compare Chennai and Coimbatore rainfall
    - Show districts with lowest rainfall
    - What is the average rainfall in Tamil Nadu?
    
    **Crop Queries:**
    - Show top 5 crops by production
    - What is paddy production?
    - Which crops have highest productivity?
    - Show crops by cultivation area
    
    **Comparisons:**
    - Top 3 districts and top 3 crops
    - Correlate rainfall with agriculture
    """)
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

# Main content
st.title("🌾 AgriClimate Intelligence System")
st.markdown("*Powered by Tamil Nadu's Agriculture & Climate Data from **data.gov.in***")

# Load data
with st.spinner("Loading datasets from data.gov.in..."):
    rainfall_df, crop_df = load_datasets()

if rainfall_df is None or crop_df is None:
    st.error("⚠️ Could not load datasets. Please ensure CSV files are in the 'data/' folder.")
    st.info("""
    **Required files:**
    - `data/rainfall_data.csv`
    - `data/crop_production.csv`
    - `data/dataset_sources.json`
    """)
    st.stop()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📍 Districts", len(rainfall_df)-1)  # Excluding state average
with col2:
    st.metric("🌾 Crops", len(crop_df))
with col3:
    st.metric("📊 Data Points", len(rainfall_df) + len(crop_df))

st.success("✅ All datasets loaded successfully from data.gov.in")
# Chat input
# --- Chat input ---
user_question = st.chat_input("💬 Ask about Tamil Nadu's agriculture and climate data...")

if user_question:
    # --- Timestamp for user message ---
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- Save user's message ---
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_question,
        "time": current_time
    })

    # --- Display user message (no timestamp here) ---
    with st.chat_message("user"):
        st.markdown(f"**🧑‍💻 You:** {user_question}")

    # --- Process and display bot's response ---
    with st.chat_message("assistant"):
        with st.spinner("🔍 Analyzing data from data.gov.in..."):
            result = analyze_question(user_question, rainfall_df, crop_df)
            bot_text = result["text"]

            # --- Timestamp for bot reply ---
            response_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # --- Save bot message ---
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": bot_text,
                "data": result.get("data"),
                "time": response_time
            })

            # --- Display bot reply ---
            st.markdown(f"**🤖 AgriClimateBot:**\n\n{bot_text}")

            # --- Show retrieved data ---
            if result.get("data") is not None:
                with st.expander("📊 View Retrieved Data from data.gov.in", expanded=False):
                    if isinstance(result["data"], dict):
                        st.subheader("🌧️ Rainfall Data")
                        st.dataframe(result["data"]["rainfall"], use_container_width=True)
                        st.caption("📍 Source: India Meteorological Department via data.gov.in")

                        st.subheader("🌾 Crop Production Data")
                        st.dataframe(result["data"]["crops"], use_container_width=True)
                        st.caption("📍 Source: Ministry of Agriculture & Farmers Welfare via data.gov.in")
                    else:
                        st.dataframe(result["data"], use_container_width=True)
                        if result.get("data_type") == "rainfall":
                            st.caption("📍 Source: India Meteorological Department via data.gov.in")
                        elif result.get("data_type") == "crops":
                            st.caption("📍 Source: Ministry of Agriculture & Farmers Welfare via data.gov.in")

# --- Conversation History (Collapsible Section) ---
with st.expander("💬 Conversation History", expanded=False):
    if len(st.session_state.chat_history) == 0:
        st.info("No chat history yet.")
    else:
        for msg in st.session_state.chat_history:
            role_label = "🧑‍💻 You" if msg["role"] == "user" else "🤖 AgriClimateBot"
            st.markdown(
                f"<div style='padding:8px; margin-bottom:5px; border-radius:10px; background-color:#1e2128;'>"
                f"<b>{role_label}</b> <span style='color:gray;'>({msg['time']})</span><br>{msg['content']}</div>",
                unsafe_allow_html=True
            )

st.markdown("""
<style>
footer {visibility: visible;}
.footer-fixed {
    position: relative;
    bottom: 0;
    width: 100%;
    text-align: center;
    padding: 10px;
    background-color: rgba(0, 0, 0, 0.6);
    color: white;
    border-top: 1px solid #333;
    margin-top: 2rem;
}
.main {
    padding-bottom: 80px; /* prevent footer overlap */
}
</style>
""", unsafe_allow_html=True)
