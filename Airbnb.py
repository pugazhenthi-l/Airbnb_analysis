import pymongo
from pymongo import MongoClient
import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import plotly.express as px
from bson.decimal128 import Decimal128
from urllib.parse import quote_plus
from PIL import Image

username = quote_plus('pugazh')
password = quote_plus('TUxgwwDe2ZsqS1Sz')  # URL encoding the password, useful if special characters were present

connection_string = f"mongodb+srv://{username}:{password}@airbnb.ncjevdt.mongodb.net/"

client = MongoClient(connection_string)

db = client.get_database("sample_airbnb")
col = db["listingsAndReviews"]
data = []

for i in col.find():
    data.append({
        'ID': i['_id'],
        'Name': i['name'],
        'Description': i['description'],
        'Country': i['address']['country'],
        'Longitude': i['address']['location']['coordinates'][0],
        'Latitude': i['address']['location']['coordinates'][1],
        'Price': i['price'],
        'Cleaning Fees': i.get('cleaning_fee', 0),
        'Amenities': i['amenities'],
        'Property_Type': i['property_type'],
        'Room_Type': i['room_type'],
        'Bedroom Count': i.get('bedrooms', 0),
        'Total Beds': i.get('beds', 0),
        'Listing URL': i['listing_url'],
        'Availability_365': i['availability']['availability_365'],
        'Availability_90': i['availability']['availability_90'],
        'Availability_60': i['availability']['availability_60'],
        'Availability_30': i['availability']['availability_30'],
        'Minimum_Nights': i['minimum_nights'],
        'Maximum_Nights': i['maximum_nights'],
        'Host_id': i['host']['host_id'],
        'Host ID': i['host']['host_id'],
        'Host Name': i['host']['host_name'],
        'Host Location': i['host']['host_location'],
        'Total Host Listing count': i['host']['host_total_listings_count'],       
        'Number of Reviews': i['number_of_reviews'],
        'Review_count': i['review_scores'].get('review_scores_rating'),
        'Review_score': i['review_scores'].get('review_scores_value')
    })
dataf = pd.DataFrame(data)
duplicate_rows = dataf[dataf.duplicated(subset=['ID'])]  
dataf.reset_index(drop=True,inplace=True)

csv_file_path = 'Airbnb_data_Analysis.csv'
dataf.to_csv(csv_file_path, index=False)


def extract_countries():
    countries = [doc['address']['country'] for doc in col.find({}, {"address.country": 1})]
    unique_countries = sorted(set(countries))
    return unique_countries

def list_property():
    properties=[doc['property_type'] for doc in col.find({},{"property_type":1})]
    unique_properties=sorted(set(properties))
    return unique_properties

def amenities():
    stage1={"$unwind":"$amenities"}
    stage2={"$project":{"_id":0,"amenity":"$amenities"}}
    result=[i['amenity'] for i in col.aggregate([stage1,stage2])]
    return result

def max_nights(days, col,country,pt):
    stage1 = {"$match": {"minimum_nights": str(days),"address.country":country,"property_type":pt}}  # Ensure days is converted to string
    stage2 = {"$project": {"_id": 0, "name": 1, "property_type": 1, "room_type": 1,"price":1,
                           "country": "$address.country","review_scores_value":{
                "$ifNull": ["$review_scores.review_scores_value", "No Rating"]}}}
    result = [i for i in col.aggregate([stage1, stage2])]
    return result

def amen_based(col, selected_amenity,country,pt):
    stage1 = {"$match": {"amenities": selected_amenity,"address.country":country,"property_type":pt}}
    stage2 = {
        "$project": {
            "_id": 0,"name": 1,"property_type": 1,"room_type": 1,"price": 1,"country": "$address.country",
            "review_scores_value": {"$ifNull": ["$review_scores.review_scores_value", "No Rating"]}}}
    result = [i for i in col.aggregate([stage1, stage2])]
    return result


def room_list(country):
    rooms = [doc['name'] for doc in col.find({"address.country": country}, {"name": 1})]
    unique_rooms = sorted(set(rooms))
    return unique_rooms


def room_info(col, selected_room, country):
    stage1 = {"$match": {"name": selected_room, "address.country": country}}
    stage2 = {
        "$project": {
            "_id": 0, "name": 1, "property_type": 1, "room_type": 1, "price": 1,
            "bedrooms": 1, "beds": 1,'bed_type':1,'extra_people':1,'guests_included':1}}
    result = [i for i in col.aggregate([stage1, stage2])]
    return result


def days(user_data, col,country,pt):
    stage1 = {
        "$match": {
            "$or": [
                {"availability.availability_30": user_data},
                {"availability.availability_60": user_data},
                {"availability.availability_90": user_data},
                {"availability.availability_365": user_data},
                ],"address.country":country,"property_type":pt}}
    stage2 = {"$project": {"_id": 0, "name": 1, "property_type": 1, "room_type": 1,"price":1,
                            "country": "$address.country","review_scores_value":{
                "$ifNull": ["$review_scores.review_scores_value", "No Rating"]}}}
    result = [i for i in col.aggregate([stage1, stage2])]
    return result

def location(country):
    stage1 = {"$match":{"address.country":country}}
    stage2={"$group": {"_id": "$property_type", "count": {"$sum": 1}}}
    stage3 = {
        "$project": {
            "_id": 0,"name": 1,"property_type": 1,"room_type": 1,"price": 1,"country": "$address.country",
            "review_scores_value": {"$ifNull": ["$review_scores.review_scores_value", "No Rating"]}}}
    result = [i for i in col.aggregate([stage1, stage2,stage3])]
    return result

def group_property_types(country):
    pipeline = [
        {"$match": {"address.country": country}},  
        {"$group": {"_id": "$property_type", "count": {"$sum": 1}}}]
    result = list(col.aggregate(pipeline))   
    return result

def top_10_prop(country):
    pipeline = [
    {"$match": {"address.country": country}},  
    {"$group": {"_id": "$property_type", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
    {"$limit": 5}]  
    result = list(col.aggregate(pipeline))
    return result

def price(country):
    pipeline=[
    {"$match":{"address.country": country}},
    {"$project":{"_id":0,"name":1,"price":1,"cleaning_fee":1,"security_deposit":1}},
    {"$addFields": {"Total": {"$sum": ["$price", "$cleaning_fee", "$security_deposit"]}}}]
    result = list(col.aggregate(pipeline))
    return result

def top_host(country):
    pipeline = [
        {"$match": {"address.country": country}},
        {"$group": {"_id": "$host.host_name", "host_listings_count": {"$sum": "$host.host_total_listings_count"}}},
        {"$sort": {"host_listings_count": -1}},
        {"$limit": 10}]
    result = list(col.aggregate(pipeline))
    return result


#STREAMLIT WEB INTERFACE:


st.set_page_config(page_title="Airbnb",
                   layout="wide",
                   page_icon="love_hotel")


col1, col2, col3 = st.columns([1,6,1])

with col1:
    image = Image.open("guvi.png")

    new_size = (100, 80) 
    resized_image = image.resize(new_size)
    st.image(resized_image)

with col3:
    image = Image.open("airbnb.png")

    new_size = (100, 60)
    resized_image = image.resize(new_size)
    st.image(resized_image)


st.markdown("<h1 style='text-align: center;font-size: 35px;'>Airbnb Insight: A Comprehensive Geospatial Analysis and Visualization Suite</h1>",
            unsafe_allow_html=True)

 
col1,col2,col3=st.columns([1,6,2])
with col2:
    st.download_button(label="Download data as csv",
                        data=open(csv_file_path, 'rb').read(),
                        file_name='Airbnb_data_analysis.csv',
                        mime='text/csv')
with col3:
    st.link_button("Tableau Dashboard","https://public.tableau.com/app/profile/pugazhenthi6838/viz/Airbnbanalysistry_17127763660380/Dashboard1")


selected = option_menu(
    menu_title="Explore Airbnb Gems",
    options=["Discover Properties", "Unlock Locations", "Dive into Data"],
    default_index=0,  # Default to "Discover Properties"
    orientation="horizontal",
    styles={
        "container": {"padding": "5!important", "background-color": "#fafafa"},
        "nav-link": {"font-size": "20px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "#08d15d"},
    }
)


if selected == "Discover Properties":
    st.subheader("Property Highlights")
    st.write("Explore a curated selection of Airbnb properties with unique amenities, locations, and styles.")  
    col1,col2,col3,col4=st.columns(4)
    with col4:
        on = st.toggle('Amenities')
    if on:
        with col1:
            amenities=st.radio("Choose Your Amneities",["Wifi","Pets Allowed","Family/kid friendly","Hot water","Pool",
                                                        "Hot tub","TV","Laptop friendly workspace","BBQ grill","Air conditioning","Kitchen","Gym"])                    
        with col2:
            countries_list = extract_countries()
            selected_country = st.selectbox("Select a country", countries_list)
        with col3:
            property_list=list_property()
            selected_property=st.selectbox("Select a Property Type",property_list)
        amen_data = amen_based(col, amenities,selected_country,selected_property)
        amenitydf = pd.DataFrame(amen_data)
        amenitydf.index = amenitydf.index + 1
        st.dataframe(amenitydf)

    else:    
        
        col1,col2,col3,col4=st.columns(4)
        with col1:
            list1=st.selectbox("Key Features",["Number of Nights","Availability of Days"])
        
        if list1=="Number of Nights":    
            with col1:
                num_nights=st.slider("Number Of Nights",min_value=1,max_value=50)
                
            with col2:
                countries_list = extract_countries()
                selected_country = st.selectbox("Select a country", countries_list)
            with col3:
                property_list=list_property()
                selected_property=st.selectbox("Select a Property Type",property_list)
                    
            night_data = max_nights(num_nights, col,selected_country,selected_property)
            nightdf = pd.DataFrame(night_data)
            nightdf.index=nightdf.index+1  
            st.dataframe(nightdf) 
            
        if list1=="Availability of Days":
            with col1:
                day_count=st.selectbox("Number of days",["30","60","90","365"])
                
            with col2:
                countries_list = extract_countries()
                selected_country = st.selectbox("Select a country", countries_list)
            with col3:
                property_list=list_property()
                selected_property=st.selectbox("Select a Property Type",property_list)
           
            day_count_int=int(day_count)
            days_data = days(day_count_int, col,selected_country,selected_property)
            daysdf = pd.DataFrame(days_data)
            daysdf.index=daysdf.index+1
            if not daysdf.empty:
                st.dataframe(daysdf)
            else:
                st.error("Unable to find a match")
                st.warning("Please try with a different property type or country")
               
if selected == "Unlock Locations":
    st.subheader("Location Insights")
    st.write("Unlock the secrets of popular Airbnb destinations. Dive into location trends, hidden gems, and more.")    
    col1,col2,col3=st.columns(3)
    with col1:
        countries_list = extract_countries()
        selected_country = st.selectbox("Select a country", countries_list)
        property_type=list_property()
    property_types = group_property_types(selected_country)
    
    if property_types:
        df = pd.DataFrame(property_types)
        df.index=df.index+1
        df.columns = ["Property Type", "Count"]
        if st.button("Data Frame"):
            st.dataframe(df)
        fig = px.bar(df,title="Number of properties in each Countries", x="Property Type", y="Count",color="Property Type")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for the selected country.")
    with col2:
        if st.button("Total Airbnb Listing"):
            room_type_counts = dataf['Room_Type'].value_counts().reset_index()
            room_type_counts.columns = ['Room Type', 'Total Listings']

            fig = px.pie(room_type_counts, values='Total Listings', names='Room Type', title='Total Airbnb Listings in Each Room Type')
            st.plotly_chart(fig)









if selected == "Dive into Data":
    st.subheader("Data Deep Dive")
    st.write("Get analytical. Examine pricing patterns, availability fluctuations, and other compelling data insights.")
    list1=st.selectbox("Key Features",["Price Analysis","Top 5 Properties","Room Analysis","Host Analysis"])
    if list1 =="Top 5 Properties":
        col1,col2,col3=st.columns(3)
        with col1:
            countries_list = extract_countries()
            selected_country = st.selectbox("Select a country", countries_list)
            property_type=list_property()
    
        property_types = top_10_prop(selected_country)
        if property_types:
            df = pd.DataFrame(property_types)
            df.index=df.index+1
            df.columns = ["Property Type", "Count"]  

            fig = px.bar(df,title="Top 5 properties in each Countries", x="Property Type", y="Count",color="Property Type")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data available for the selected country.")

    if list1=="Room Analysis":
        col1,col2,col3=st.columns(3)
        with col1:
            countries_list = extract_countries()
            selected_country = st.selectbox("Select a country", countries_list)
            if selected_country:
                with col2:
                    room_names=room_list(selected_country)
                    selected_room=st.selectbox("Select a property",room_names)
                
        
        prop_names=room_info(col, selected_room,selected_country)
        df=pd.DataFrame(prop_names)
        df.index=df.index+1
        df.columns=["Property Name","Property Type","Room Type","Bed Type","Bedrooms","Beds","Price","Extra People","Guests"]
        sunburst_data = df[["Room Type", "Bedrooms", "Beds"]].dropna()
        fig = px.sunburst(sunburst_data, path=["Room Type", "Bedrooms", "Beds"], values="Beds")
        st.plotly_chart(fig)
        st.dataframe(df)        
        
    if list1=="Price Analysis":
        col1,col2,col3=st.columns(3)
        with col1:
            countries_list = extract_countries()
            selected_country = st.selectbox("Select a country", countries_list)
            if selected_country:  
                price_analysis=price(selected_country)
                price_analysis = [{k: float(str(v)) if isinstance(v, Decimal128) else v for k, v in row.items()} for row in price_analysis]
                df=pd.DataFrame(price_analysis)
                df = df.dropna()
                df.columns=["Name","Price","Security Deposit","Total","Cleaning Fees"]
        with col2:
            selected_name = st.selectbox("Select a Property Name", sorted(df["Name"].unique()))
            filtered_data = df[df["Name"] == selected_name]
        pie_data = pd.DataFrame({
            "Category": ["Price", "Security Deposit", "Cleaning Fees"],
            "Value": [filtered_data["Price"].values[0], filtered_data["Security Deposit"].values[0], filtered_data["Cleaning Fees"].values[0]]
        })
        fig1 = px.pie(pie_data, values="Value", names="Category", title=f"Breakdown for {selected_name}",hole=0.4)
        st.plotly_chart(fig1)
        st.dataframe(df)

    if list1 == "Host Analysis":
        col1,col2,col3=st.columns(3)
        df = pd.DataFrame(list(col.find({}, {"host.host_name": 1})))
        with col1:
            countries_list = extract_countries()
            selected_country = st.selectbox("Select a country", countries_list)

        if selected_country:
            host_analysis = top_host(selected_country)
            df_filtered = pd.DataFrame(host_analysis)
            df_filtered.columns = ["Host Name", "Total Listing"]
            df_filtered.index=df_filtered.index+1
            fig=px.bar(df_filtered,title="Top 10 Host based on Listing Count",x="Host Name",y="Total Listing",color="Host Name")
            st.plotly_chart(fig, use_container_width=True)
            
