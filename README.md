## IBM Coursera Capstone Project




This project utilizes clustering algorithms, venue data from the Foursquare API, and weather data from the OpenWeatherMap API in order to help restaurant owners decide which New York or Toronto neighborhoods they should consider opening up a restaurant in. Web scrapping was used to obtain neighborhood postal codes from Wikipedia and Geopy was used to determine the corresponding latitudes and longitude values for these neighborhood postal codes. I've broken up the thought process behind the project below and listed any limitations or improvements that can be made to the project. 

1.) Industrial Organization, a field of economics that focuses on the theory of the firm, suggests that firms in similar industries will start to aggregate around a pareto optimal focal point in any geospatial plane in order to reduce transportation costs for customers and thus maximize customer acquisition. For this reason, we are interested in neighborhoods that showcase relatively high frequencies of restaurant venues as this will serve as an indicator of a prime location to open up shop.

2.) Many studies indicate that the weather has a tremendous effect on the restaurant business by ultimately influencing customer behavior. Temperature, humidity, and outside weather conditions (rain, clear sky, etc.) can all have an effect on overall restaurant revenues, so it is important that we incorporate weather data. Since different restaurants have different sensitives to the weather (i.e. ice cream shops would favor higher temperatures; hot-pot restaurants would favor lower temperatures), we will let the restaurant owner decide what temperature and humidity ranges are most suitable for them. Rain and snow, however, seems to always have a negative impact on the restaurant business so we will favor locations that show the highest frequency for the "clear skies" weather condition.

3.) Standard clustering algorithms based off the calculation of Euclidean distance were used to group similar neighborhoods together. This gave us more insight into what type of restaurants aggregated together at which particular neighborhoods. This would give the restaurant owner more detailed information and would dramatically cut down the list of potential locations he/she would need to consider. In the future, we can consider implementing more advanced algorithms such as DBSCAN (Density-Based Spatial Clustering of Applications with Noise).

4.) There are many other factors that should be considered when opening up a restaurant such as the area's demographics, per-capita income, rent per square footage, market saturation, the type of restaurant being opened, local supplier costs, differences in inspection standards, currency fluctuations and current business cycle positions between countries. Moreover, the 5-day weather forecast API option was the most extensive forecast coverage I was able to use that was cost-free. It definitely would've been better to use a year's worth of weather data, but the cost associated with this type of API access was beyond the budget for the course.
