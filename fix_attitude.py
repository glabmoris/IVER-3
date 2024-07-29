import sys
import os
import re
from exif import Image

if len(sys.argv) != 2:
	sys.stderr.write("Usage: fix-attitude.py picture-directory\n")
	sys.exit(1)

workdir = sys.argv[1]

sys.stderr.write(f"[*] Processing files in {workdir}\n")

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
			d = float(values.group(11)) #Dont know nor care what that is
			altitude = float(values.group(13))
			roll = float(values.group(15))
			pitch = float(values.group(17))
			s = float(values.group(11)) #Dont know nor care what that is

			img.set("pitch",pitch)

			with open(f"{workdir}/new_{file}", 'wb') as new_image_file:
				new_image_file.write(img.get_file())
		else:
			sys.stderr.write(f"File {file} contains bad EXIF data :{metadata}\n")
