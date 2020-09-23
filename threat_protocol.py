import time
import email, smtplib, ssl
from toolbox import convert_json
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import cv2
import os


### !!! Main function at the bottom


def email_template(threat_dict,file,time,name,email):
	
	subject = "Security Breach: Rasp Pi SS from XXX Store"
	body = f"""Hello {name},

There was a breach at your store. Review attached picture and details.
Time: {time}
Threats detected: {threat_dict}

Best,
JARVIS

"""
	sender_email = "raspberry.pi.webdunia@gmail.com"
	password = 'Webd123!'
	receiver_email = email

	# Create a multipart message and set headers
	message = MIMEMultipart()
	message["From"] = sender_email
	message["To"] = receiver_email
	message["Subject"] = subject
	 # Recommended for mass emails

	# Add body to email
	message.attach(MIMEText(body, "plain"))

	filename = file  # In same directory as script

	# Open PDF file in binary mode
	with open(filename, "rb") as attachment:
	    # Add file as application/octet-stream
	    # Email client can usually download this automatically as attachment
	    part = MIMEBase("application", "octet-stream")
	    part.set_payload(attachment.read())

	# Encode file in ASCII characters to send by email    
	encoders.encode_base64(part)

	# Add header as key/value pair to attachment part
	part.add_header(
	    "Content-Disposition",
	    "attachment; filename=threat_image.png",
	)

	# Add attachment to message and convert message to string
	message.attach(part)
	text = message.as_string()

	# Log in to server using secure context and send email
	context = ssl.create_default_context()
	with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
	    server.login(sender_email, password)
	    server.sendmail(sender_email, receiver_email, text)
	    print('Sent notification Email.')


def send_email(contact_list_json,threat_dict,file,time):
	contact_list = convert_json(contact_list_json)
	keys = [] # Parse list of keys from contact.json file
	for key,value in contact_list.items():
		keys.append(key)

	if keys[0] == 'persons': 
		for person in contact_list[keys[0]]:

			email_template(threat_dict,file,time,person['name'],person['email'])
	else:
		print(f'{contact_list_json} Corrupted')




def save_img(img,time):
	cwd =  os.getcwd()
	file_name = 'threat_' + str(time[4:7]+time[8:11]) +'.png'
	path = os.path.join(cwd,file_name) 
	
	im = cv2.imwrite(file_name,img)
	print('Saved image.')
	return path
	

def del_img(img_path):
	os.remove(img_path)
	print('Removed Image.')


def threat_presence(obj_dict,mode):
	if obj_dict == None:
		return False,{}

	if mode == 'operations':
		return_dict = {}
		for obj in obj_dict:
			if obj == 'person': # Detection of People are negligible during hours of operations
				continue
			if obj != 'person' and obj_dict[obj] > 0:
				return_dict[obj] = obj_dict[obj]
		

		if return_dict != {}:
			threat = True
			return threat,return_dict
		else:
			return False,{}
	
	elif mode == 'night_guard':
		return_dict = {}
		for obj in obj_dict:
			if obj_dict[obj] > 0:
				return_dict[obj] = obj_dict[obj]
				
		
		if return_dict != {}:
			threat = True
			return threat,return_dict
		
		else:
			threat = False
			return threat, return_dict




def exec_threat_protocol_process(threat_dict,img,time):
	print('INFO: Executing Threat Protocol')
	img_path = save_img(img,time) ## Saves image to email and returns path
	send_email('json/contacts.json',threat_dict,img_path,time)
	del_img(img_path) ## Deletes image after email is sent
	print('INFO: Finished executing Threat Protocol')
	
