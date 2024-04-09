import pymongo
from pymongo import MongoClient
import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import plotly.express as px
from bson.decimal128 import Decimal128
from urllib.parse import quote_plus

username = quote_plus('pugazh')
password = quote_plus('Lp573kH6XXdHxP75')  # URL encoding the password, useful if special characters were present

connection_string = f"mongodb+srv://{username}:{password}@airbnb.p0q2gkx.mongodb.net/"

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

st.set_page_config(page_title="Airbnb",
                   layout="wide",
                   page_icon="hotel")


st.markdown("<h1 style='text-align: center;font-size: 35px;'>Accurate Airbnb Analytics and Visualization for Unveiling Trends & Insights</h1>",
            unsafe_allow_html=True)

choropleth_data = dataf[['Country', 'Latitude', 'Longitude']].copy()
choropleth_data.dropna(subset=['Country', 'Latitude', 'Longitude'], inplace=True)
with st.sidebar:
    st.markdown("<h1 style='text-align: center;font-size: 30px;color: red;'>Airbnb Analyis</h1>",
            unsafe_allow_html=True)
    st.image("data:image/jpeg;base64,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")
       
    st.download_button(label="Download data as csv",
                        data=open(csv_file_path, 'rb').read(),
                        file_name='Airbnb_data_analysis.csv',
                        mime='text/csv')
    st.link_button("Tableau Dashboard","https://public.tableau.com/app/profile/jeriyl.florence/viz/Airbnbanalysistry/Dashboard1?publish=yes")
     
fig = px.scatter_geo(choropleth_data, locations="Country",
                    hover_name="Country", 
                    locationmode='country names',
                    projection="natural earth",
                    title="Airbnb Across the World")
                    
st.sidebar.plotly_chart(fig,use_container_width=True)
 

selected=option_menu(menu_title="Airbnb Analysis",
                    options=["Property","Locations","Analysis"],
                    #icons=["window-dash","cash-coin","currency-exchange","search"],
                    default_index=0,
                    orientation="horizontal")
                    
if selected == "Property":   
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
            list1=st.selectbox("Key Features",["Number of Nights","Availability of Days","Amenities"])
        
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
               
if selected == "Locations":
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
          

if selected == "Analysis":
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
            
