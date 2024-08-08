import streamlit as st
import anthropic
from collections import Counter
import plotly.graph_objects as go

# Set up the Anthropic client using Streamlit secrets
client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
MODEL = "claude-3-5-sonnet-20240620"


def parse_supplement_list(response_content):
    if isinstance(response_content, list) and len(response_content) > 0:
        if hasattr(response_content[0], "text"):
            text_content = response_content[0].text
        else:
            text_content = str(response_content[0])
    elif isinstance(response_content, str):
        text_content = response_content
    else:
        raise ValueError(f"Unexpected response type: {type(response_content)}")

    return [item.strip() for item in text_content.split(",") if item.strip()]


def get_supplement_information(user_info):
    prompt = f"""
    Given the following user information:
    {user_info}
    
    Provide a list of 5 supplements that have been studied in scientific literature for potential health benefits related to this person's profile. 
    Include only supplements with peer-reviewed research support.
    Format your response as a comma-separated list of supplement names only.
    Do not include any health claims or recommendations.
    """

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=300,
            temperature=1,
            messages=[{"role": "user", "content": prompt}],
        )

        if st.session_state.debug_mode:
            st.write(f"Debug - Raw API response: {response.content}")
        return parse_supplement_list(response.content)
    except Exception as e:
        st.error(
            f"An error occurred while fetching supplement information: {str(e)}"
        )
        return []


def create_supplement_chart(supplement_counts, total_queries):
    supplements = list(supplement_counts.keys())
    percentages = [
        round(count / total_queries * 100)
        for count in supplement_counts.values()
    ]

    # Sort supplements and percentages by percentage in descending order
    sorted_data = sorted(
        zip(supplements, percentages), key=lambda x: x[1], reverse=True
    )
    sorted_supplements, sorted_percentages = zip(*sorted_data)

    fig = go.Figure(
        go.Bar(
            x=sorted_percentages,
            y=sorted_supplements,
            orientation="h",
            text=[f"{p}%" for p in sorted_percentages],
            textposition="inside",
            insidetextanchor="end",
            textfont=dict(color="white"),
            marker=dict(
                color="#1f77b4"
            ),  # Set bar color to match the original blue
        )
    )

    fig.update_layout(
        xaxis_title="Percentage of Queries (%)",
        yaxis_title="",
        xaxis=dict(
            range=[0, 100], dtick=20
        ),  # Set x-axis range from 0 to 100% with ticks every 20%
        height=400
        + (
            len(supplements) * 20
        ),  # Adjust height based on number of supplements
        margin=dict(l=0, r=10, t=30, b=0),
        yaxis=dict(
            autorange="reversed"
        ),  # This will put the highest percentage at the top
    )

    return fig


def main():
    st.title("AI-Powered Supplement Information Tool")

    st.write(
        """
    This tool provides information about supplements that have been studied in scientific literature. 
    It does not make recommendations or provide medical advice. 
    Always consult with a qualified healthcare professional before starting any supplement regimen.
    """
    )

    # User input
    age = st.number_input("Age", min_value=18, max_value=120, value=30)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])

    # Dietary preference
    diet = st.selectbox(
        "Dietary Preference",
        ["Omnivore", "Vegetarian", "Vegan", "Pescatarian"],
    )

    activity_level = st.selectbox(
        "Activity Level", ["Sedentary", "Moderately Active", "Very Active"]
    )

    # Tabbed interface for height and weight
    tab1, tab2 = st.tabs(["Imperial", "Metric"])

    with tab1:
        weight_lbs = st.number_input(
            "Weight (lbs)", min_value=66, max_value=660, value=154
        )
        height_ft = st.number_input(
            "Height (ft)", min_value=3, max_value=8, value=5
        )
        height_in = st.number_input(
            "Height (in)", min_value=0, max_value=11, value=7
        )
    with tab2:
        weight_kg = st.number_input(
            "Weight (kg)", min_value=30, max_value=300, value=70
        )
        height_cm = st.number_input(
            "Height (cm)", min_value=100, max_value=250, value=170
        )

    # Use metric values for calculation (convert imperial if necessary)
    if tab1.selected:
        weight = weight_kg
        height = height_cm
    else:
        weight = round(weight_lbs * 0.45359237, 1)
        height = round((height_ft * 30.48) + (height_in * 2.54), 1)

    health_interests = st.text_area(
        "Any specific health interests? (This is not for diagnosis or treatment)"
    )

    if st.button("Get Supplement Information"):
        user_info = f"Age: {age}, Gender: {gender}, Weight: {weight}kg, Height: {height}cm, Activity Level: {activity_level}, Dietary Preference: {diet}, Health Interests: {health_interests}"

        with st.spinner("Fetching and analyzing supplement information..."):
            all_supplements = []
            num_queries = 5
            for _ in range(num_queries):
                supplements = get_supplement_information(user_info)
                all_supplements.extend(supplements)
                if st.session_state.debug_mode:
                    st.write(f"Debug - API response: {supplements}")

            if all_supplements:
                # Count occurrences of each supplement
                supplement_counts = Counter(all_supplements)
                if st.session_state.debug_mode:
                    st.write(
                        f"Debug - Supplement counts: {dict(supplement_counts)}"
                    )

                st.subheader(
                    "Supplement Mention Frequency in Scientific Literature"
                )
                fig = create_supplement_chart(supplement_counts, num_queries)
                st.plotly_chart(fig)

                st.write(
                    "This chart shows how often each supplement was mentioned across multiple queries to the AI model."
                )
                st.write(
                    "Remember: Mention frequency in scientific literature does not imply effectiveness or safety for your specific situation."
                )
            else:
                st.error(
                    "Unable to fetch supplement information. Please try again later."
                )

        st.caption(
            """
        Disclaimer: This information is for educational purposes only and does not constitute medical advice. 
        The mentions of supplements are based on AI analysis of scientific literature and may not be comprehensive or up-to-date. 
        Individual responses to supplements can vary greatly. 
        Always consult with a qualified healthcare provider before starting any new supplement regimen.
        """
        )

    # Sidebar information
    st.sidebar.title("About")
    st.sidebar.info(
        """
    Max Ghenis built this app using the Claude 3.5 Sonnet API.
    
    No user data is collected or stored.
    
    For questions or feedback, please contact me at mghenis@gmail.com.
    """
    )

    # Initialize debug_mode in session state if it doesn't exist
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False

    # Debug mode switch
    st.session_state.debug_mode = st.sidebar.checkbox(
        "Debug Mode", value=st.session_state.debug_mode
    )


if __name__ == "__main__":
    main()
