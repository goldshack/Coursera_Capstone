#!/usr/bin/env python
# coding: utf-8

# In[11]:


pip install beautifulsoup4


# In[12]:


pip install lxml


# In[13]:


pip install requests


# In[4]:


pip install geopy


# In[2]:


pip install folium


# In[1]:


from bs4 import BeautifulSoup
import requests
import numpy as np
import pandas as pd
from geopy.geocoders import Nominatim
import folium
import json
from pandas.io.json import json_normalize
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt


# In[2]:


url = 'https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_M'
response = requests.get(url)

if response.status_code == 200:
    print('Success!')
elif response.status_code == 404:
    print('Not Found.')
    
print(url)
print(response.headers)


# In[3]:


soup = BeautifulSoup(response.text, 'lxml')
table_body=soup.find('tbody')
trs = table_body.find_all('tr')
rows = []
for tr in trs:
    i = tr.find_all('td')
    if i:
        rows.append(i)


# In[4]:


list_table = []
for row in rows:
    postalcode = row[0].text.strip()
    borough = row[1].text.strip()
    neighborhood = row[2].text.strip()
    if borough != 'Not assigned':             
        if neighborhood == 'Not assigned':
            neighborhood = borough
        list_table.append([postalcode, borough, neighborhood])


# In[5]:


df = pd.DataFrame(list_table, columns=['PostalCode', 'Borough', 'Neighborhood'])
print(df.shape)


# In[6]:


#Drops rows where Borough = 'Not assigned' if any
df.drop(df.loc[df['Borough']=='Not assigned'].index, inplace=True)


# In[7]:


df = df.groupby('PostalCode').agg({'Borough':'first','Neighborhood': ', '.join}).reset_index()


# In[8]:


df.loc[df['PostalCode'] == 'M5A']


# In[11]:


df.shape

