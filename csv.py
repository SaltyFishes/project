import urllib.request
import json

#url of external api
crime_url_template ='https://data.police.uk/api/crimes-street/all-crime?lat={lat}&lng={lng}&date={data}'
my_latitude = '51.52369'
my_longitude = '-0.0395857'
my_date = '2018-11'
crime_url = crime_url_template.format(lat = my_latitude, lng = my_longitude, data = my_date)

#open the url as a variable called 'data'
with urllib.request.urlopen(crime_url) as url:
    data = json.loads(url.read().decode())
#create if not exist a csv file
crime_data = open('crime_data.csv', 'w')
count = 0
#write some chosen data into the csv file follow the csv format
for crime in data:
    if count < 300:
        if count == 0:
            header = "ID,category,loc_lat,loc_lon,St_id,St_name,outcome\n"
            crime_data.write(header)
        ID = str(crime["id"])
        cate = str(crime["category"])
        lat = str(crime["location"]["latitude"])
        lon = str(crime["location"]["longitude"])
        stid = str(crime["location"]["street"]["id"])
        stname = str(crime["location"]["street"]["name"])
        out = str(crime["outcome_status"])
        row = "{},{},{},{},{},{},{}\n".format(ID, cate, lat, lon, stid, stname, out)
        crime_data.write(row)
    count += 1
#save and close the csv file
crime_data.close()