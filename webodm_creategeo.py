import sys
import os
import re
from exif import Image
import pandas as pd

if len(sys.argv) != 2:
	sys.stderr.write("Usage: extract-exif.py picture-directory\n")
	sys.exit(1)

workdir = sys.argv[1]

sys.stderr.write(f"[*] Processing files in {workdir}\n")

# List to store extracted data
data = []

for file in os.listdir(workdir):
	with open(f"{workdir}/{file}", 'rb') as image_file:
		img = Image(image_file)

		#IVER-3 encodes a metadata string as EXIF code 37510 (User Comment)
		#It looks like: 315739229.04,La,49.29684,N,Ln,67.681939,W,H,276.6,D,21.4,A,24.57,R,0,P,-2.3,S,2.6,*
		metadata = img.user_comment

		# Extract values using regex kungfu...
		values = re.search("^([+-]?([0-9]*[.])?[0-9]+),La,([+-]?([0-9]*[.])?[0-9]+),([NS]{1}),Ln,([+-]?([0-9]*[.])?[0-9]+),([WE]{1}),H,([+-]?([0-9]*[.])?[0-9]+),D,([+-]?([0-9]*[.])?[0-9]+),A,([+-]?([0-9]*[.])?[0-9]+),R,([+-]?([0-9]*[.])?[0-9]+),P,([+-]?([0-9]*[.])?[0-9]+),S,([+-]?([0-9]*[.])?[0-9]+)",metadata)
		if values:
			timestamp = values.group(1) #I haven't checked what the time basis would be for this
			latitude = float(values.group(3))
			n_or_s = values.group(5)

			if n_or_s == 'S':
				latitude = -latitude

			longitude = float(values.group(6))
			w_or_e = values.group(8)

			if w_or_e == 'W':
				longitude = -longitude

			heading = float(values.group(9))
			d = float(values.group(11)) # Does D stand for Depth ? Validate this
			altitude = float(values.group(13))
			roll = float(values.group(15))
			pitch = float(values.group(17))
			s = float(values.group(11)) #What's this...

			data.append([file,latitude,longitude,altitude,heading,pitch,roll])
		else:
			sys.stderr.write(f"File {file} contains bad EXIF data :{metadata}\n")
            
# Convert the list to a DataFrame
df = pd.DataFrame(data, columns=['File', 'Latitude', 'Longitude', 'Altitude', 'Heading', 'Pitch', 'Roll'])

#Sorting the dataframe based on Filename
# Had to create this function, since the normal sort sorts WP13_1067,WP13_1068,WP13_1069,WP13_107

def extract_numeric(filename):
    numbers = re.findall(r'\d+', filename)# Find all numbers in the filename and stores in a list eg.['WP13','1067']          
    return int(numbers[-1]) if numbers else 0 # Returns the number after WP13, which is the image number

df['Sort_Key'] = df['File'].apply(extract_numeric)# Stores the image number in a temporary column
df_sorted = df.sort_values(by='Sort_Key')# Sorts the dataframe based on the image number
df_sorted = df_sorted.drop(columns='Sort_Key')# Drops the image number column


#Transforming Positive Altitude to Negative Altitude
df_sorted['Altitude'] = df_sorted['Altitude'] * -1

#Adding Vertical Accuracy and Horizontal Accuracy
df_sorted["VA"] = 0.02
df_sorted["HA"] = 0.02

#Projection String
first_line = "+proj=utm +zone=19 +ellps=WGS84 +datum=WGS84 +units=m +no_defs\n"

# Write the first line and then the DataFrame without headers
with open('geo.txt', 'w') as f:
    f.write(first_line)  # First Line is the Projection String
    df_sorted.to_csv(f, index=False, header=False, sep=',')  # Appending the DataFrame content to geo.txt file
