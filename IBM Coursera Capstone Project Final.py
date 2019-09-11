#!/usr/bin/env python
# coding: utf-8

# In[6]:


from bs4 import BeautifulSoup
import requests
import numpy as np
import pandas as pd
from geopy.geocoders import Nominatim
import folium
import json
from pandas.io.json import json_normalize
from sklearn.cluster import KMeans
import matplotlib.cm as cm
import matplotlib.colors as colors
import statistics
pd.set_option('display.max_columns', None)
from statistics import mode


# In[7]:


url = 'https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_M'
response = requests.get(url)

if response.status_code == 200:
    print('Success!')
elif response.status_code == 404:
    print('Not Found.')
    
print(url)
print(response.headers)


# In[8]:


soup = BeautifulSoup(response.text, 'lxml')
table_body=soup.find('tbody')
trs = table_body.find_all('tr')
rows = []
for tr in trs:
    i = tr.find_all('td')
    if i:
        rows.append(i)


# In[9]:


list_table = []
for row in rows:
    postalcode = row[0].text.strip()
    borough = row[1].text.strip()
    neighborhood = row[2].text.strip()
    if borough != 'Not assigned':             
        if neighborhood == 'Not assigned':
            neighborhood = borough
        list_table.append([postalcode, borough, neighborhood])


# In[10]:


df = pd.DataFrame(list_table, columns=['PostalCode', 'Borough', 'Neighborhood'])
print(df.shape)


# In[11]:


#Drops rows where Borough = 'Not assigned' if any
df.drop(df.loc[df['Borough']=='Not assigned'].index, inplace=True)


# In[12]:


df = df.groupby('PostalCode').agg({'Borough':'first','Neighborhood': ', '.join}).reset_index()


# In[13]:


df.loc[df['PostalCode'] == 'M5A']


# In[14]:


df.shape


# In[15]:


loc_df = pd.read_csv('http://cocl.us/Geospatial_data')


# In[16]:


loc_df.rename(columns={'Postal Code':'PostalCode'},inplace = True)


# In[17]:


df2 = pd.merge(df, loc_df, on="PostalCode", how='left')


# In[18]:


#Toronto Coordinates
address = 'Toronto'

geolocator = Nominatim(user_agent="toronto_explorer")
location = geolocator.geocode(address)
latitude = location.latitude
longitude = location.longitude
print('The geograpical coordinate of Toronto are {}, {}.'.format(latitude, longitude))


# In[19]:


# create map of Toronto using latitude and longitude values
map_toronto = folium.Map(location=[latitude, longitude], zoom_start=11)

# add markers to map
for lat, lng, label in zip(df2['Latitude'], df2['Longitude'], df2['Neighborhood']):
    label = folium.Popup(label, parse_html=True)
    folium.CircleMarker(
        [lat, lng],
        radius=5,
        popup=label,
        color='blue',
        fill=True,
        fill_color='#3186cc',
        fill_opacity=0.7,
        parse_html=False).add_to(map_toronto)  
    
map_toronto


# In[20]:


CLIENT_ID = '23QCEME0X05NQPDAGB1K0WYP3PRWCIJ0ALLDPMBEY1ZXTZPG' # Foursquare ID
CLIENT_SECRET = 'A5YTYTWO5L2D11VOQDEDD3U5YJI1PNQ4C4XPSTVQEU3SHWYV' # your Foursquare Secret
VERSION = '20180605' # Foursquare API version

print('Your credentails:')
print('CLIENT_ID: ' + CLIENT_ID)
print('CLIENT_SECRET:' + CLIENT_SECRET)


# In[21]:


#Exploring the Woburn Neighborhood
df2.loc[3, 'Neighborhood']


# In[22]:


neighborhood_latitude = df2.loc[3, 'Latitude'] # neighborhood latitude value
neighborhood_longitude = df2.loc[3, 'Longitude'] # neighborhood longitude value

neighborhood_name = df2.loc[3, 'Neighborhood'] # neighborhood name

print('Latitude and longitude values of {} are {}, {}.'.format(neighborhood_name, 
                                                               neighborhood_latitude, 
                                                               neighborhood_longitude))


# In[23]:


#Getting the top 100 venues that are in Woburn within a radius of 500 meters.


# In[24]:


radius = 500
LIMIT = 100

url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
    CLIENT_ID, 
    CLIENT_SECRET, 
    VERSION, 
    neighborhood_latitude, 
    neighborhood_longitude, 
    radius, 
    LIMIT)


# In[25]:


results = requests.get(url).json()
results


# In[26]:


# function that extracts the category of the venue
def get_category_type(row):
    try:
        categories_list = row['categories']
    except:
        categories_list = row['venue.categories']
        
    if len(categories_list) == 0:
        return None
    else:
        return categories_list[0]['name']


# In[27]:


venues = results['response']['groups'][0]['items']
    
nearby_venues = json_normalize(venues) # flatten JSON

# filter columns
filtered_columns = ['venue.name', 'venue.categories', 'venue.location.lat', 'venue.location.lng']
nearby_venues =nearby_venues.loc[:, filtered_columns]

# filter the category for each row
nearby_venues['venue.categories'] = nearby_venues.apply(get_category_type, axis=1)

# clean columns
nearby_venues.columns = [col.split(".")[-1] for col in nearby_venues.columns]

nearby_venues.head()


# In[28]:


#Looking at all Neighborhoods in Toronto

def getNearbyVenues(names, latitudes, longitudes, radius=500):
    
    venues_list=[]
    for name, lat, lng in zip(names, latitudes, longitudes):
        print(name)
            
        # create the API request URL
        url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
            CLIENT_ID, 
            CLIENT_SECRET, 
            VERSION, 
            lat, 
            lng, 
            radius, 
            LIMIT)
            
        # make the GET request
        results = requests.get(url).json()["response"]['groups'][0]['items']
        
        # return only relevant information for each nearby venue
        venues_list.append([(
            name, 
            lat, 
            lng, 
            v['venue']['name'], 
            v['venue']['location']['lat'], 
            v['venue']['location']['lng'],  
            v['venue']['categories'][0]['name']) for v in results])

    nearby_venues = pd.DataFrame([item for venue_list in venues_list for item in venue_list])
    nearby_venues.columns = ['Neighborhood', 
                  'Neighborhood Latitude', 
                  'Neighborhood Longitude', 
                  'Venue', 
                  'Venue Latitude', 
                  'Venue Longitude', 
                  'Venue Category']
    
    return(nearby_venues)


# In[29]:


toronto_venues= getNearbyVenues(names=df2['Neighborhood'],
                                   latitudes=df2['Latitude'],
                                   longitudes=df2['Longitude'])


# In[30]:


##Analyzing all the Toronto Neighborhoods
# one hot encoding
toronto_onehot = pd.get_dummies(toronto_venues[['Venue Category']], prefix="", prefix_sep="")

# add neighborhood column back to dataframe
toronto_onehot['Neighborhood'] = toronto_venues['Neighborhood'] 

# move neighborhood column to the first column
fixed_columns = [toronto_onehot.columns[-1]] + list(toronto_onehot.columns[:-1])
toronto_onehot = toronto_onehot[fixed_columns]

toronto_onehot.head()


# In[31]:


post1 = []
for col in toronto_onehot.columns:
    if ('Restaurant') in col:
        post1.append(col)


toronto_onehot['Total_Restaurant']=0

for i in post1:
    toronto_onehot['Total_Restaurant'] += toronto_onehot[i]





# In[32]:


toronto_onehot['Total_Restaurant'].sum()


# In[33]:


toronto_onehot2=toronto_onehot[['Total_Restaurant','Neighborhood']]


# In[34]:


#Group rows by neighborhood and by taking the mean of the frequency of occurrence of each category
toronto_grouped1 = toronto_onehot2.groupby('Neighborhood').agg({'Total_Restaurant':np.mean}).reset_index()
toronto_grouped2 = toronto_onehot2.groupby('Neighborhood').agg({'Total_Restaurant':np.sum}).reset_index()
toronto_grouped1 = toronto_grouped1.sort_values(by='Total_Restaurant', ascending=False)
toronto_grouped1['Total_Restaurant_Frequency']=toronto_grouped1['Total_Restaurant']
toronto_grouped1 = toronto_grouped1.drop(columns=['Total_Restaurant'])
toronto_grouped_final= toronto_grouped1.join(toronto_grouped2.set_index('Neighborhood'), on='Neighborhood')
toronto_grouped_final.head()


# In[35]:


toronto_merged = df2


toronto_merged.head() # check the last columns!


# In[36]:


toronto_merged_final = toronto_merged.join(toronto_grouped_final.set_index('Neighborhood'), on='Neighborhood')
toronto_merged_final=toronto_merged_final[['Borough','Neighborhood','PostalCode','Latitude','Longitude','Total_Restaurant','Total_Restaurant_Frequency']]
toronto_merged_final=toronto_merged_final.sort_values(by='Total_Restaurant', ascending=False)


# In[37]:


toronto_merged_final.head()


# In[38]:


toronto_merged_final=toronto_merged_final[['Borough','Neighborhood','PostalCode','Latitude','Longitude','Total_Restaurant','Total_Restaurant_Frequency']]
toronto_merged_final=toronto_merged_final.sort_values(by='Total_Restaurant', ascending=False)


# In[39]:


lat_group=list(toronto_merged_final['Latitude'])
lat_list=list(map(str, lat_group))
lon_group=list(toronto_merged_final['Longitude'])
lon_list = list(map(str, lon_group))


# In[40]:


#Obtaining AVG Temperature List
lst_temp=[]
final_lst_temp=[]

for lat, lon in zip(lat_list, lon_list):
    api_address='http://api.openweathermap.org/data/2.5/forecast?lat='+lat+'&lon='+lon+'&units=imperial&APPID=aee82abb5cd39bd3aef65599bde034fa'
    json_data= requests.get(api_address).json()
    
    for i in range(0,40):
        temp_data=json_data['list'][i]['main']['temp']
        lst_temp.append(temp_data)
    temp_avg=statistics.mean(lst_temp)
    final_lst_temp.append(temp_avg)

final_lst_temp[0:5]


# In[41]:


#Obtaining AVG Humidity List
lst_hum=[]
final_lst_hum=[]

for lat, lon in zip(lat_list, lon_list):
    api_address='http://api.openweathermap.org/data/2.5/forecast?lat='+lat+'&lon='+lon+'&units=imperial&APPID=aee82abb5cd39bd3aef65599bde034fa'
    json_data= requests.get(api_address).json()
    
    for i in range(0,40):
        hum_data=json_data['list'][i]['main']['humidity']
        lst_hum.append(hum_data)
    hum_avg=statistics.mean(lst_hum)
    final_lst_hum.append(hum_avg)

final_lst_hum[0:5]


# In[42]:


final_np_temp = np.asarray(final_lst_temp)


# In[43]:


final_np_hum=np.asarray(final_lst_hum)


# In[44]:


toronto_merged_final['Average 5-Day Temperature']= final_np_temp


# In[45]:


toronto_merged_final['Average 5-Day Humidity'] = final_np_hum


# In[46]:


toronto_merged_final.head()


# In[47]:


json_data['list'][i]['weather'][0]['description']


# In[48]:


#Obtaining most frequent weather condition
lst_con=[]
final_lst_con=[]
from collections import Counter

for lat, lon in zip(lat_list, lon_list):
    api_address='http://api.openweathermap.org/data/2.5/forecast?lat='+lat+'&lon='+lon+'&units=imperial&APPID=aee82abb5cd39bd3aef65599bde034fa'
    json_data= requests.get(api_address).json()
    
    for i in range(0,40):
        con_data=json_data['list'][i]['weather'][0]['description']
        lst_con.append(con_data)
        c = Counter(lst_con)
        common_list = c.most_common(i)
        
    if common_list[0][1] > common_list[1][1]:
        final_lst_con.append(common_list[0][0])
    elif common_list[0][1] == common_list[1][1]:
        final_lst_con.append(common_list[0][0] +' & '+ common_list[1][0])
    elif common_list[0][1] == common_list[1][1] == common_list[2][1]:
        final_lst_con.append(common_list[0][0] +' & '+ common_list[1][0] +' & '+ common_list[3][0])
    elif common_list[0][1] == common_list[1][1] == common_list[2][1]==common_list[3][1]:
        final_lst_con.append(common_list[0][0] +' & '+ common_list[1][0] +' & '+ common_list[3][0]+' & '+ common_list[4][0])
    elif common_list[0][1] == common_list[1][1] == common_list[2][1] == common_list[3][1] == common_list[4][1]:
        final_lst_con.append(common_list[0][0] +' & '+ common_list[1][0] +' & '+ common_list[2][0] +' & '+ common_list[3][0]+' & '+ common_list[4][0])
    elif common_list[0][1] == common_list[1][1] == common_list[2][1] == common_list[3][1] == common_list[4][1] == common_list[5][1]:
        final_lst_con.append(common_list[0][0] +' & '+ common_list[1][0] +' & '+ common_list[3][0] +' & '+ common_list[4][0] +' & '+ common_list[5][0] +' & '+ common_list[6][0])
    elif common_list[0][1] == common_list[1][1] == common_list[2][1] == common_list[3][1] == common_list[4][1] == common_list[5][1] == common_list[5][1]:
        final_lst_con.append(common_list[0][0] +' & '+ common_list[1][0] +' & '+ common_list[3][0] +' & '+ common_list[4][0] +' & '+ common_list[5][0] +' & '+ common_list[6][0])
    elif common_list[0][1] == common_list[1][1] == common_list[2][1] == common_list[3][1] == common_list[4][1] == common_list[5][1] == common_list[5][1] == common_list[6][1]:
        final_lst_con.append(common_list[0][0] +' & '+ common_list[1][0] +' & '+ common_list[3][0] +' & '+ common_list[4][0] +' & '+ common_list[5][0] +' & '+ common_list[6][0] +' & '+ common_list[7][0]


# In[49]:


len(final_lst_con)


# In[50]:


final_np_con = np.asarray(final_lst_con)


# In[51]:


toronto_merged_final['Most Frequent Weather Condition']= final_np_con


# In[52]:


toronto_merged_final.head()


# In[53]:


#Frequency of Clear Sky Condition

lst_con2=[]
final_lst_con2=[]
from collections import Counter

for lat, lon in zip(lat_list, lon_list):
    api_address='http://api.openweathermap.org/data/2.5/forecast?lat='+lat+'&lon='+lon+'&units=imperial&APPID=aee82abb5cd39bd3aef65599bde034fa'
    json_data= requests.get(api_address).json()
    
    for i in range(0,40):
        con_data=json_data['list'][i]['weather'][0]['description']
        lst_con2.append(con_data)
    lst_con2_count = lst_con2.count('clear sky')/40
    final_lst_con2.append(lst_con2_count)
    lst_con2=[]


# In[54]:


len(final_lst_con2)


# In[55]:


final_np_con2 = np.asarray(final_lst_con2)


# In[56]:


toronto_merged_final['Clear Sky condition frequency']= final_np_con2


# In[57]:


toronto_merged_final.head()


# In[58]:


### New York


# In[59]:


import numpy as np # library to handle data in a vectorized manner
import wget
import json

import pandas as pd # library for data analsysis
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

import json # library to handle JSON files

#!conda install -c conda-forge geopy --yes # uncomment this line if you haven't completed the Foursquare API lab
from geopy.geocoders import Nominatim # convert an address into latitude and longitude values

import requests # library to handle requests
from pandas.io.json import json_normalize # tranform JSON file into a pandas dataframe

# Matplotlib and associated plotting modules
import matplotlib.cm as cm
import matplotlib.colors as colors

# import k-means from clustering stage
from sklearn.cluster import KMeans

#!conda install -c conda-forge folium=0.5.0 --yes # uncomment this line if you haven't completed the Foursquare API lab
import folium # map rendering library

print('Libraries imported.')


# In[60]:


import os
os.chdir('/Users/Jeffrey.Lu@ibm.com/Desktop')


# In[61]:


with open('newyork_data.json') as json_data:
    newyork_data = json.load(json_data)


# In[62]:


newyork_data


# In[63]:


# define the dataframe columns
column_names = ['Borough', 'Neighborhood', 'Latitude', 'Longitude'] 

# instantiate the dataframe
neighborhoods = pd.DataFrame(columns=column_names)


# In[64]:


neighborhoods_data = newyork_data['features']


# In[65]:


neighborhoods_data[0]


# In[66]:


for data in neighborhoods_data:
    borough = neighborhood_name = data['properties']['borough'] 
    neighborhood_name = data['properties']['name']
        
    neighborhood_latlon = data['geometry']['coordinates']
    neighborhood_lat = neighborhood_latlon[1]
    neighborhood_lon = neighborhood_latlon[0]
    
    neighborhoods = neighborhoods.append({'Borough': borough,
                                          'Neighborhood': neighborhood_name,
                                          'Latitude': neighborhood_lat,
                                          'Longitude': neighborhood_lon}, ignore_index=True)


# In[67]:


neighborhoods.head()


# In[68]:


#Making sure we have 5 boroughs in the data set
print('The dataframe has {} boroughs and {} neighborhoods.'.format(
        len(neighborhoods['Borough'].unique()),
        neighborhoods.shape[0]
    )
)


# In[69]:


neighborhood_latitude = neighborhoods.loc[0, 'Latitude'] # neighborhood latitude value
neighborhood_longitude = neighborhoods.loc[0, 'Longitude'] # neighborhood longitude value

neighborhood_name = neighborhoods.loc[0, 'Neighborhood'] # neighborhood name

print('Latitude and longitude values of {} are {}, {}.'.format(neighborhood_name, 
                                                               neighborhood_latitude, 
                                                               neighborhood_longitude))


# In[70]:


radius = 500
LIMIT = 100

url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
    CLIENT_ID, 
    CLIENT_SECRET, 
    VERSION, 
    neighborhood_latitude, 
    neighborhood_longitude, 
    radius, 
    LIMIT)


# In[71]:


results = requests.get(url).json()
results


# In[72]:


# function that extracts the category of the venue
def get_category_type(row):
    try:
        categories_list = row['categories']
    except:
        categories_list = row['venue.categories']
        
    if len(categories_list) == 0:
        return None
    else:
        return categories_list[0]['name']


# In[73]:


venues = results['response']['groups'][0]['items']
    
nearby_venues = json_normalize(venues) # flatten JSON

# filter columns
filtered_columns = ['venue.name', 'venue.categories', 'venue.location.lat', 'venue.location.lng']
nearby_venues =nearby_venues.loc[:, filtered_columns]

# filter the category for each row
nearby_venues['venue.categories'] = nearby_venues.apply(get_category_type, axis=1)

# clean columns
nearby_venues.columns = [col.split(".")[-1] for col in nearby_venues.columns]

nearby_venues.head()


# In[74]:


newyork_data = neighborhoods
newyork_data.head()


# In[75]:


#Looking at all Neighborhoods in New York

def getNearbyVenues(names, latitudes, longitudes, radius=500):
    
    venues_list=[]
    for name, lat, lng in zip(names, latitudes, longitudes):
        print(name)
            
        # create the API request URL
        url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
            CLIENT_ID, 
            CLIENT_SECRET, 
            VERSION, 
            lat, 
            lng, 
            radius, 
            LIMIT)
            
        # make the GET request
        results = requests.get(url).json()["response"]['groups'][0]['items']
        
        # return only relevant information for each nearby venue
        venues_list.append([(
            name, 
            lat, 
            lng, 
            v['venue']['name'], 
            v['venue']['location']['lat'], 
            v['venue']['location']['lng'],  
            v['venue']['categories'][0]['name']) for v in results])

    nearby_venues = pd.DataFrame([item for venue_list in venues_list for item in venue_list])
    nearby_venues.columns = ['Neighborhood', 
                  'Neighborhood Latitude', 
                  'Neighborhood Longitude', 
                  'Venue', 
                  'Venue Latitude', 
                  'Venue Longitude', 
                  'Venue Category']
    
    return(nearby_venues)


# In[76]:


newyork_venues = getNearbyVenues(names=newyork_data['Neighborhood'],
                                   latitudes=newyork_data['Latitude'],
                                   longitudes=newyork_data['Longitude'])


# In[77]:


# one hot encoding
newyork_onehot = pd.get_dummies(newyork_venues[['Venue Category']], prefix="", prefix_sep="")

# add neighborhood column back to dataframe
newyork_onehot['Neighborhood'] = newyork_venues['Neighborhood'] 

# move neighborhood column to the first column
fixed_columns = [newyork_onehot.columns[-1]] + list(newyork_onehot.columns[:-1])
newyork_onehot = newyork_onehot[fixed_columns]

newyork_onehot.head()


# In[78]:


post2 = []
for col in newyork_onehot.columns:
    if ('Restaurant') in col:
        post2.append(col)



# In[79]:


newyork_onehot['Total_Restaurant']=0

for i in post2:
    newyork_onehot['Total_Restaurant'] += newyork_onehot[i]
    


# In[80]:


newyork_onehot['Total_Restaurant'].sum()


# In[81]:


newyork_onehot2=newyork_onehot[['Total_Restaurant','Neighborhood']]


# In[82]:


#Group rows by neighborhood and by taking the mean of the frequency of occurrence of each category
newyork_grouped1 = newyork_onehot2.groupby('Neighborhood').agg({'Total_Restaurant':np.mean}).reset_index()
newyork_grouped2 = newyork_onehot2.groupby('Neighborhood').agg({'Total_Restaurant':np.sum}).reset_index()
newyork_grouped1 = newyork_grouped1.sort_values(by='Total_Restaurant', ascending=False)
newyork_grouped1['Total_Restaurant_Frequency']=newyork_grouped1['Total_Restaurant']
newyork_grouped1 = newyork_grouped1.drop(columns=['Total_Restaurant'])
newyork_grouped_final= newyork_grouped1.join(newyork_grouped2.set_index('Neighborhood'), on='Neighborhood')
newyork_grouped_final.head()


# In[83]:


newyork_merged = newyork_data


newyork_merged.head() # check the last columns!


# In[84]:


newyork_merged_final = newyork_merged.join(newyork_grouped_final.set_index('Neighborhood'), on='Neighborhood')
newyork_merged_final= newyork_merged_final.sort_values(by='Total_Restaurant', ascending=False)
newyork_merged_final


# In[85]:


lat_group=list(newyork_merged_final['Latitude'])
lat_list=list(map(str, lat_group))
lon_group=list(newyork_merged_final['Longitude'])
lon_list = list(map(str, lon_group))


# In[86]:


#Obtaining AVG Temperature List
lst_temp=[]
final_lst_temp=[]

for lat, lon in zip(lat_list, lon_list):
    api_address='http://api.openweathermap.org/data/2.5/forecast?lat='+lat+'&lon='+lon+'&units=imperial&APPID=aee82abb5cd39bd3aef65599bde034fa'
    json_data= requests.get(api_address).json()
    
    for i in range(0,40):
        temp_data=json_data['list'][i]['main']['temp']
        lst_temp.append(temp_data)
    temp_avg=statistics.mean(lst_temp)
    final_lst_temp.append(temp_avg)

final_lst_temp[0:5]


# In[87]:


#Obtaining AVG Humidity List
lst_hum=[]
final_lst_hum=[]

for lat, lon in zip(lat_list, lon_list):
    api_address='http://api.openweathermap.org/data/2.5/forecast?lat='+lat+'&lon='+lon+'&units=imperial&APPID=aee82abb5cd39bd3aef65599bde034fa'
    json_data= requests.get(api_address).json()
    
    for i in range(0,40):
        hum_data=json_data['list'][i]['main']['humidity']
        lst_hum.append(hum_data)
    hum_avg=statistics.mean(lst_hum)
    final_lst_hum.append(hum_avg)

final_lst_hum[0:5]


# In[88]:


final_np_temp = np.asarray(final_lst_temp)


# In[89]:


final_np_hum=np.asarray(final_lst_hum)


# In[90]:


newyork_merged_final['Average 5-Day Temperature']= final_np_temp


# In[91]:


newyork_merged_final['Average 5-Day Humidity'] = final_np_hum


# In[92]:


newyork_merged_final.head()


# In[93]:


json_data['list'][i]['weather'][0]['description']


# In[94]:


#Obtaining most frequent weather condition
lst_con=[]
final_lst_con=[]
from collections import Counter

for lat, lon in zip(lat_list, lon_list):
    api_address='http://api.openweathermap.org/data/2.5/forecast?lat='+lat+'&lon='+lon+'&units=imperial&APPID=aee82abb5cd39bd3aef65599bde034fa'
    json_data= requests.get(api_address).json()
    
    for i in range(0,40):
        con_data=json_data['list'][i]['weather'][0]['description']
        lst_con.append(con_data)
        c = Counter(lst_con)
        common_list = c.most_common(i)
        
    if common_list[0][1] > common_list[1][1]:
        final_lst_con.append(common_list[0][0])
    elif common_list[0][1] == common_list[1][1]:
        final_lst_con.append(common_list[0][0] +' & '+ common_list[1][0])
    elif common_list[0][1] == common_list[1][1] == common_list[2][1]:
        final_lst_con.append(common_list[0][0] +' & '+ common_list[1][0] +' & '+ common_list[3][0])
    elif common_list[0][1] == common_list[1][1] == common_list[2][1]==common_list[3][1]:
        final_lst_con.append(common_list[0][0] +' & '+ common_list[1][0] +' & '+ common_list[3][0]+' & '+ common_list[4][0])
    elif common_list[0][1] == common_list[1][1] == common_list[2][1] == common_list[3][1] == common_list[4][1]:
        final_lst_con.append(common_list[0][0] +' & '+ common_list[1][0] +' & '+ common_list[2][0] +' & '+ common_list[3][0]+' & '+ common_list[4][0])
    elif common_list[0][1] == common_list[1][1] == common_list[2][1] == common_list[3][1] == common_list[4][1] == common_list[5][1]:
        final_lst_con.append(common_list[0][0] +' & '+ common_list[1][0] +' & '+ common_list[3][0] +' & '+ common_list[4][0] +' & '+ common_list[5][0] +' & '+ common_list[6][0])
    elif common_list[0][1] == common_list[1][1] == common_list[2][1] == common_list[3][1] == common_list[4][1] == common_list[5][1] == common_list[5][1]:
        final_lst_con.append(common_list[0][0] +' & '+ common_list[1][0] +' & '+ common_list[3][0] +' & '+ common_list[4][0] +' & '+ common_list[5][0] +' & '+ common_list[6][0])
    elif common_list[0][1] == common_list[1][1] == common_list[2][1] == common_list[3][1] == common_list[4][1] == common_list[5][1] == common_list[5][1] == common_list[6][1]:
        final_lst_con.append(common_list[0][0] +' & '+ common_list[1][0] +' & '+ common_list[3][0] +' & '+ common_list[4][0] +' & '+ common_list[5][0] +' & '+ common_list[6][0] +' & '+ common_list[7][0])
      
        


# In[95]:


len(final_lst_con)


# In[96]:


final_np_con = np.asarray(final_lst_con)


# In[97]:


newyork_merged_final['Most Frequent Weather Condition']= final_np_con


# In[98]:


newyork_merged_final.head()


# In[99]:


#Frequency of Clear Sky Condition

lst_con2=[]
final_lst_con2=[]
from collections import Counter

for lat, lon in zip(lat_list, lon_list):
    api_address='http://api.openweathermap.org/data/2.5/forecast?lat='+lat+'&lon='+lon+'&units=imperial&APPID=aee82abb5cd39bd3aef65599bde034fa'
    json_data= requests.get(api_address).json()
    
    for i in range(0,40):
        con_data=json_data['list'][i]['weather'][0]['description']
        lst_con2.append(con_data)
    lst_con2_count = lst_con2.count('clear sky')/40
    final_lst_con2.append(lst_con2_count)
    lst_con2=[]


# In[100]:


len(final_lst_con2)


# In[101]:


final_np_con2 = np.asarray(final_lst_con2)


# In[102]:


newyork_merged_final['Clear Sky condition frequency']= final_np_con2


# In[103]:


newyork_merged_final.head()


# In[104]:


## Combining Both Toronto and New York Datasets


# In[105]:


df=toronto_merged_final.append(newyork_merged_final)


# In[106]:


df.drop('PostalCode', axis = 1, inplace= True)


# In[107]:


df


# In[108]:


### Analyzing Neighborhoods in Toronto and New York with Clustering


# In[109]:


newyork_onehot.head()


# In[110]:


newyork_grouped = newyork_onehot.groupby('Neighborhood').mean().reset_index()
newyork_grouped.drop('Total_Restaurant', axis = 1, inplace = True)


# In[111]:


num_top_venues = 5

for hood in newyork_grouped['Neighborhood']:
    print("----"+hood+"----")
    temp = newyork_grouped[newyork_grouped['Neighborhood'] == hood].T.reset_index()
    temp.columns = ['venue','freq']
    temp = temp.iloc[1:]
    temp['freq'] = temp['freq'].astype(float)
    temp = temp.round({'freq': 2})
    print(temp.sort_values('freq', ascending=False).reset_index(drop=True).head(num_top_venues))
    print('\n')


# In[112]:


def return_most_common_venues(row, num_top_venues):
    row_categories = row.iloc[1:]
    row_categories_sorted = row_categories.sort_values(ascending=False)
    
    return row_categories_sorted.index.values[0:num_top_venues]


# In[113]:


num_top_venues = 10

indicators = ['st', 'nd', 'rd']

# create columns according to number of top venues
columns = ['Neighborhood']
for ind in np.arange(num_top_venues):
    try:
        columns.append('{}{} Most Common Venue'.format(ind+1, indicators[ind]))
    except:
        columns.append('{}th Most Common Venue'.format(ind+1))

# create a new dataframe
neighborhoods_venues_sorted = pd.DataFrame(columns=columns)
neighborhoods_venues_sorted['Neighborhood'] = newyork_grouped['Neighborhood']

for ind in np.arange(newyork_grouped.shape[0]):
    neighborhoods_venues_sorted.iloc[ind, 1:] = return_most_common_venues(newyork_grouped.iloc[ind, :], num_top_venues)

neighborhoods_venues_sorted.head()


# In[114]:


# set number of clusters
kclusters = 10

newyork_grouped_clustering = newyork_grouped.drop('Neighborhood', 1)

# run k-means clustering
kmeans = KMeans(n_clusters=kclusters, random_state=0).fit(newyork_grouped_clustering)

# check cluster labels generated for each row in the dataframe
kmeans.labels_[0:10] 


# In[115]:


# add clustering labels
neighborhoods_venues_sorted.insert(0, 'Cluster Labels', kmeans.labels_)

newyork_merged = newyork_data

# merge toronto_grouped with toronto_data to add latitude/longitude for each neighborhood
newyork_merged = newyork_merged.join(neighborhoods_venues_sorted.set_index('Neighborhood'), on='Neighborhood')

newyork_merged.head() # check the last columns!


# In[116]:


# create map
map_clusters = folium.Map(location=[latitude, longitude], zoom_start=11)

# set color scheme for the clusters
x = np.arange(kclusters)
ys = [i + x + (i*x)**2 for i in range(kclusters)]
colors_array = cm.rainbow(np.linspace(0, 1, len(ys)))
rainbow = [colors.rgb2hex(i) for i in colors_array]

# add markers to the map
markers_colors = []
for lat, lon, poi, cluster in zip(newyork_merged['Latitude'], newyork_merged['Longitude'], newyork_merged['Neighborhood'], newyork_merged['Cluster Labels'].fillna(0)):
    label = folium.Popup(str(poi) + ' Cluster ' + str(cluster), parse_html=True)
    folium.CircleMarker(
        [lat, lon],
        radius=5,
        popup=label,
        color=rainbow[int(cluster-1)],
        fill=True,
        fill_color=rainbow[int(cluster-1)],
        fill_opacity=0.7).add_to(map_clusters)
       
map_clusters


# In[117]:


newyork_merged.head()


# In[118]:


newyork_merged.loc[newyork_merged['Cluster Labels'] == 0, newyork_merged.columns[[1] + list(range(5, newyork_merged.shape[1]))]]


# In[119]:


newyork_merged['Borough-Neighborhood']= list(zip(newyork_merged['Borough'], newyork_merged['Neighborhood']))


# In[120]:


newyork_merged.head()


# In[121]:


#Cluster 1 New York
newyork_merged.loc[newyork_merged['Cluster Labels'] == 0, newyork_merged.columns[[1] + list(range(5, newyork_merged.shape[1]))]]


# In[122]:


#Cluster 2 New York
newyork_merged.loc[newyork_merged['Cluster Labels'] == 1, newyork_merged.columns[[1] + list(range(5, newyork_merged.shape[1]))]]


# In[123]:


#Cluster 3 New York
newyork_merged.loc[newyork_merged['Cluster Labels'] == 2, newyork_merged.columns[[1] + list(range(5, newyork_merged.shape[1]))]]


# In[124]:


#Cluster 4 New York
newyork_merged.loc[newyork_merged['Cluster Labels'] == 3, newyork_merged.columns[[1] + list(range(5, newyork_merged.shape[1]))]]


# In[125]:


#Cluster 5 New York
newyork_merged.loc[newyork_merged['Cluster Labels'] == 4, newyork_merged.columns[[1] + list(range(5, newyork_merged.shape[1]))]]


# In[126]:


#Cluster 6 New York
newyork_merged.loc[newyork_merged['Cluster Labels'] == 5, newyork_merged.columns[[1] + list(range(5, newyork_merged.shape[1]))]]


# In[127]:


#Cluster 7 New York
newyork_merged.loc[newyork_merged['Cluster Labels'] == 6, newyork_merged.columns[[1] + list(range(5, newyork_merged.shape[1]))]]


# In[128]:


#Cluster 8 New York
newyork_merged.loc[newyork_merged['Cluster Labels'] == 7, newyork_merged.columns[[1] + list(range(5, newyork_merged.shape[1]))]]


# In[129]:


#Cluster 9 New York
newyork_merged.loc[newyork_merged['Cluster Labels'] == 8, newyork_merged.columns[[1] + list(range(5, newyork_merged.shape[1]))]]


# In[130]:


#Cluster 10 New York
newyork_merged.loc[newyork_merged['Cluster Labels'] == 9, newyork_merged.columns[[1] + list(range(5, newyork_merged.shape[1]))]]


# In[131]:


## Toronto Cluster


# In[132]:


toronto_onehot.head()


# In[133]:


toronto_grouped = toronto_onehot.groupby('Neighborhood').mean().reset_index()
toronto_grouped.drop('Total_Restaurant', axis = 1, inplace = True)


# In[134]:


num_top_venues = 10

indicators = ['st', 'nd', 'rd']

# create columns according to number of top venues
columns = ['Neighborhood']
for ind in np.arange(num_top_venues):
    try:
        columns.append('{}{} Most Common Venue'.format(ind+1, indicators[ind]))
    except:
        columns.append('{}th Most Common Venue'.format(ind+1))

# create a new dataframe
neighborhoods_venues_sorted1 = pd.DataFrame(columns=columns)
neighborhoods_venues_sorted1['Neighborhood'] = toronto_grouped['Neighborhood']

for ind in np.arange(toronto_grouped.shape[0]):
    neighborhoods_venues_sorted1.iloc[ind, 1:] = return_most_common_venues(toronto_grouped.iloc[ind, :], num_top_venues)

neighborhoods_venues_sorted1.head()


# In[135]:


# set number of clusters
kclusters = 5

toronto_grouped_clustering = toronto_grouped.drop('Neighborhood', 1)

# run k-means clustering
kmeans = KMeans(n_clusters=kclusters, random_state=0).fit(toronto_grouped_clustering)

# check cluster labels generated for each row in the dataframe
kmeans.labels_[0:10] 


# In[136]:


# add clustering labels
neighborhoods_venues_sorted1.insert(0, 'Cluster Labels', kmeans.labels_)


# merge toronto_grouped with toronto_data to add latitude/longitude for each neighborhood
toronto_merged = toronto_merged.join(neighborhoods_venues_sorted1.set_index('Neighborhood'), on='Neighborhood')

toronto_merged.head() # check the last columns!


# In[137]:


toronto_merged.drop('PostalCode',axis=1, inplace=True)


# In[138]:


# create map
map_clusters = folium.Map(location=[latitude, longitude], zoom_start=11)

# set color scheme for the clusters
x = np.arange(kclusters)
ys = [i + x + (i*x)**2 for i in range(kclusters)]
colors_array = cm.rainbow(np.linspace(0, 1, len(ys)))
rainbow = [colors.rgb2hex(i) for i in colors_array]

# add markers to the map
markers_colors = []
for lat, lon, poi, cluster in zip(toronto_merged['Latitude'], toronto_merged['Longitude'], toronto_merged['Neighborhood'], toronto_merged['Cluster Labels'].fillna(0)):
    label = folium.Popup(str(poi) + ' Cluster ' + str(cluster), parse_html=True)
    folium.CircleMarker(
        [lat, lon],
        radius=5,
        popup=label,
        color=rainbow[int(cluster-1)],
        fill=True,
        fill_color=rainbow[int(cluster-1)],
        fill_opacity=0.7).add_to(map_clusters)
       
map_clusters


# In[139]:


#Toronto Cluster 1
toronto_merged.loc[toronto_merged['Cluster Labels'] == 0, toronto_merged.columns[[1] + list(range(5, toronto_merged.shape[1]))]]


# In[140]:


#Toronto Cluster 2

toronto_merged.loc[toronto_merged['Cluster Labels'] == 1, toronto_merged.columns[[1] + list(range(5, toronto_merged.shape[1]))]]


# In[141]:


#Toronto Cluster 3

toronto_merged.loc[toronto_merged['Cluster Labels'] == 2, toronto_merged.columns[[1] + list(range(5, toronto_merged.shape[1]))]]


# In[142]:


#Toronto Cluster 4

toronto_merged.loc[toronto_merged['Cluster Labels'] == 3, toronto_merged.columns[[1] + list(range(5, toronto_merged.shape[1]))]]


# In[143]:


#Toronto Cluster 5

toronto_merged.loc[toronto_merged['Cluster Labels'] == 4, toronto_merged.columns[[1] + list(range(5, toronto_merged.shape[1]))]]


# In[ ]:





# In[144]:


toronto_merged_final.head()


# In[177]:


#Analyzing Toronto neighborhoods
df_tor=toronto_merged_final.where(toronto_merged_final['Total_Restaurant'] > 10).sort_values(by=['Total_Restaurant_Frequency'], ascending=False)
df_tor


# In[178]:


df_tor5 = df_tor.head()


# In[152]:


#Analyzing New York neighborhoods

df_ny = newyork_merged_final.where(newyork_merged_final['Total_Restaurant'] > 10).sort_values(by=['Total_Restaurant_Frequency'], ascending=False)
df_ny


# In[153]:


df_ny5= df_ny.head()


# In[182]:


import matplotlib.pyplot as plt
plt.bar(df_ny5['Neighborhood'],df_ny5['Total_Restaurant_Frequency'], align='center', alpha=0.7)
plt.ylabel('Total Restaurant Frequency')
plt.title('Top 5 New York Neighborhoods')
fig = plt.figure(1, [20, 8])
fig.autofmt_xdate()
plt.show()


# In[181]:


plt.bar(df_tor5['Neighborhood'],df_tor5['Total_Restaurant_Frequency'], align='center', alpha=0.7)
plt.ylabel('Total Restaurant Frequency')
plt.title('Top 5 Toronto Neighborhoods')
fig = plt.figure(1, [20, 8])
fig.autofmt_xdate()
plt.show()

