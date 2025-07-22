import streamlit as st
import requests
import time
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(
    page_title="Nationalparkprojekt Dummy App",
    page_icon="📊",
    layout="wide"
)


def upload_page():
    st.title("File Upload")

    uploaded_file = st.file_uploader("Select a file", type=["txt", "csv"])

    if uploaded_file:
        if st.button("Start Processing"):
            with st.spinner("Uploading file..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                res = requests.post("http://localhost:8000/upload/", files=files)
                if res.status_code != 200:
                    st.error("Upload failed.")
                    st.stop()
                session_id = res.json()["session_id"]

            st.success("File uploaded. Processing...")

            status_text = st.empty()
            progress_bar = st.progress(0)

            step_map = {
                "starting": 0,
                "loaded": 0.2,
                "preprocessed": 0.4,
                "main_process": 0.6,
                "postprocess": 0.8,
                "done": 1.0
            }

            done = False
            while not done:
                time.sleep(1.5)
                res = requests.get(f"http://localhost:8000/progress/{session_id}")
                if res.status_code != 200:
                    st.error("Error fetching progress.")
                    break

                data = res.json()
                status = data["status"]
                message = data["message"]
                done = status == "done"

                progress_bar.progress(step_map.get(status, 0.0))
                status_text.write(f"**Status:** {message}")

            st.success("Processing complete.")


def overview_page():
    st.subheader("Current Forecast:")

    try:
        response = requests.post("http://localhost:8000/prognose")
        if response.status_code == 200:
            forecast_result = response.json()

            # Create columns for better layout
            cols = st.columns(len(forecast_result))

            for i, (location, data) in enumerate(forecast_result.items()):
                with cols[i]:
                    st.metric(
                        label=location,
                        value=f"{int((data[0] + data[1]) / 2)} ± {int((data[1] - data[0]) / 2)}"
                    )

            # Show raw data (optional)
            with st.expander("Show raw data"):
                st.json(forecast_result)

        else:
            st.error("Error retrieving forecast")

    except requests.RequestException:
        st.error("Connection to server failed")
        return


def forecast_page():
    st.title("Forecast Time Series")

    # Get available locations
    try:
        locations_response = requests.get("http://localhost:8000/locations")
        if locations_response.status_code == 200:
            available_locations = locations_response.json()
        else:
            st.error("Error retrieving locations")
            return
    except requests.RequestException:
        st.error("Connection to server failed")
        return

    # User input section
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Location Selection")
        selected_locations = st.multiselect(
            "Select locations:",
            available_locations,
            default=available_locations
        )

    with col2:
        st.subheader("Time Period Selection")
        start_date = st.date_input(
            "Start date:",
            value=datetime.date.today() - datetime.timedelta(days=7)
        )
        end_date = st.date_input(
            "End date:",
            value=datetime.date.today()
        )

    if not selected_locations:
        st.warning("Please select at least one location.")
        return

    if start_date > end_date:
        st.error("Start date must be before end date.")
        return

    # Fetch data button
    if st.button("Retrieve forecast"):
        with st.spinner("Loading forecast data..."):
            try:
                # Prepare request body
                request_body = {
                    "locations": selected_locations,
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }

                response = requests.post(
                    "http://localhost:8000/prognose_range",
                    json=request_body
                )

                if response.status_code == 200:
                    forecast_data = response.json()

                    # Create the plot
                    fig = make_subplots(
                        rows=len(selected_locations),
                        cols=1,
                        subplot_titles=selected_locations,
                        shared_xaxes=True,
                        vertical_spacing=0.1
                    )

                    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

                    for i, location in enumerate(selected_locations):
                        if location in forecast_data:
                            location_data = forecast_data[location]
                            dates = []
                            values_0 = []
                            values_1 = []

                            # Convert data to lists for plotting
                            for date_str, values in location_data.items():
                                dates.append(datetime.datetime.fromisoformat(date_str).date())
                                values_0.append(values[0])
                                values_1.append(values[1])

                            # Sort by date
                            sorted_data = sorted(zip(dates, values_0, values_1))
                            dates, values_0, values_1 = zip(*sorted_data)

                            # Add traces for each value index
                            fig.add_trace(
                                go.Scatter(
                                    x=dates,
                                    y=values_0,
                                    mode='lines+markers',
                                    name=f'{location} - Index 0',
                                    line=dict(color=colors[i % len(colors)]),
                                    marker=dict(size=6)
                                ),
                                row=i + 1, col=1
                            )

                            fig.add_trace(
                                go.Scatter(
                                    x=dates,
                                    y=values_1,
                                    mode='lines+markers',
                                    name=f'{location} - Index 1',
                                    line=dict(color=colors[i % len(colors)]),
                                    marker=dict(size=6, symbol='square')
                                ),
                                row=i + 1, col=1
                            )

                    # Update layout
                    fig.update_layout(
                        height=400 * len(selected_locations),
                        title_text="Forecast Time Series",
                        showlegend=True,
                        hovermode='x unified'
                    )

                    # Update x-axis for all subplots
                    fig.update_xaxes(title_text="Date", row=len(selected_locations), col=1)

                    # Update y-axis for all subplots
                    for i in range(len(selected_locations)):
                        fig.update_yaxes(title_text="Value", row=i + 1, col=1)

                    st.plotly_chart(fig, use_container_width=True)

                    # Show raw data in expander
                    with st.expander("Show raw data"):
                        st.json(forecast_data)

                else:
                    st.error(f"Error retrieving forecast: {response.status_code}")

            except requests.RequestException as e:
                st.error(f"Connection to server failed: {e}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")


st.title("Data Processing App")
tab1, tab2, tab3 = st.tabs(["👁️ Overview", "📈 Forecast Time Series", "📁 File Upload"])

with tab1:
    overview_page()

with tab2:
    forecast_page()

with tab3:
    upload_page()