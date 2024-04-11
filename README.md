# Airbnb Data Visualization with Streamlit

This project is a Streamlit application designed to fetch and visualize data from a MongoDB collection containing Airbnb listings. It enables users to interactively explore various aspects of the listings, such as price analysis, host analysis, and general property details through an intuitive web interface.

## Features

- **Data Retrieval:** Connects to a MongoDB database to fetch data about Airbnb listings.
- **Interactive Visualizations:** Utilizes Plotly for dynamic and interactive data visualizations.
- **Price Analysis:** Allows users to analyze listing prices across different countries.
- **Host Analysis:** Identifies top hosts based on the number of listings in selected countries.
- **Filtering and Search:** Enables users to filter listings based on specific criteria such as country or property name.

## Prerequisites

Before you can run this application, you'll need to have the following installed:

- Python 3.6 or later
- Streamlit
- Pandas
- Plotly
- Pymongo
- streamlit_option_menu (optional for enhanced navigation)

Configuration
To connect to your MongoDB database, update the connection_string in the Airbnb.py file with your database credentials:

connection_string = "mongodb+srv://your_username:your_password@your_cluster_url"
