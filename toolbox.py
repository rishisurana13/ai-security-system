import json
import time
import cv2
import os

def clear_dict(obj_dict):
	# Reset all vals in pydict to 0
    for obj in obj_dict:
        obj_dict[obj] = 0
    return obj_dict

def del_file(img_path):
	os.remove(img_path)
	print(f'Removed file {img_path}.')

def threat_presence(obj_dict,mode):
	# If any object in label map is detected, threat = True. 
	# Exception is person, whose presence is negligible during working hours.
	if obj_dict == None:
		return False,{}

	if mode == 'operations':
		return_dict = {}
		for obj in obj_dict:
			if obj == 'person': # Detection of People are negligible during hours of operations
				continue
			if obj != 'person' and obj_dict[obj] > 0:
				# Adds other objects (except person) to return_dict with all detected threat objects. 
				return_dict[obj] = obj_dict[obj]

		if return_dict != {}:
			# If its not empty and other key-vals are present, then threat must be true. 
			threat = True
			return threat,return_dict
		else:
			return False,{}
	
	elif mode == 'night_guard':
		# In Night guard mode if even a person is detected then a threat is considered to be true.
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

def time_diff(t1,t2):
	# t1 = 18:20 t2 = 13:30 == 
	if len(t1) == 5 and len(t2) == 5:
		t1_h = int(t1[:2])
		t2_h = int(t2[:2])

		t1_m = int(t1[3:])
		t2_m = int(t2[3:])
		if t1_h - t2_h == 0:
			td = t1_m - t2_m
			return td 

		elif t1_h - t2_h == 1:
			rem = 60 - t2_m
			td = rem + (t1_m)
			return td
		elif t1_h - t2_h > 1:
			td_h2m = (t1_h - t2_h - 1) * 60
			rem = 60 - t2_m
			td = td_h2m + rem + t1_m
			return td
		elif t1_h - t2_h < 0:
			td_h2m = (t1_h - t2_h - 1) * 60
			rem = 60 - t2_m
			td = td_h2m + rem + t1_m
			return td


	### returns time diff in minutes
	else:
		t1_h = int(t1[11:13]) # t1_h is t1 hour val
		t1_m = int(t1[14:16]) # t2_m is t2 minute val

		t2_h = int(t2[11:13])
		t2_m = int(t2[14:16])

		if t1_h - t2_h == 0:
			td = t1_m - t2_m
			return td # returns int denoting minutes

		elif t1_h - t2_h == 1:
			rem = 60 - t2_m
			td = rem + (t1_m)
			return td

def td_h(start_time):
	# Returns time diff between hour vals
	# I.E start time = 2.59 pm and ctime = 3.00 pm, td_h = 1
	ctime = time.ctime()
	ctime_h = int(ctime[11:13])
	start_time_h = int(start_time[11:13])
	if ctime_h == 00 and start_time_h == 11:
		ctime_h == 12
	td_h = ctime_h - start_time_h
	return td_h


def gen_vid_writer(video):
	# The main purpose of this function is to return vid writers with 
	# appropriate file name since there is 1 clip per hour i.e. nov24_14.avi (nov 24 2:00:00pm - 2:59:59 pm (2 pm = 1400/14 hrs))
	# This is so files can be uploaded to s3 in an hourly interval.
	video_res = (int(video.get(3)),int(video.get(4)))
	path = 'saved_videos/general'
	path_threat = 'saved_videos/threat'
	ctime = time.ctime()
	filename = time.strftime("%b%d_%H") + '.avi'

	fourcc = cv2.VideoWriter_fourcc(*'XVID')
	vidout = cv2.VideoWriter(f'saved_videos/general/{filename}', fourcc, 10.4, (video_res))

	filename_threat = time.strftime("%b%d_%H%M") + '_threat.avi'
	vidout_threat = cv2.VideoWriter(f'saved_videos/threat/{filename_threat}', fourcc, 10.4, (video_res))
	return vidout, vidout_threat


def upload_to_s3_dir(vid_dir):
	bucket_name = 'deeplens-objectdetection-output'
	subdir_list = os.listdir(vid_dir)
	if '.DS_Store' in subdir_list:
			subdir_list.remove('.DS_Store')
	for subdir in subdir_list:
		o_path = os.path.join(vid_dir,subdir)
		vidlist = os.listdir(o_path)
		if '.DS_Store' in vidlist:
			vidlist.remove('.DS_Store')
		
		if vidlist != []:
			for vid in vidlist:
				path = os.path.join(vid_dir,subdir,vid)
				print(f'Uploading {path}')
				# client = boto3.client('s3')
				# client.put_object(Body=path, Bucket=bucket_name, Key=path)
				print(f'Uploaded {path}')
				del_file(path)
		else:
			print(f'{vid_dir} is empty')

def upload_to_s3_file(file_path):
	# bucket_name = 'deeplens-objectdetection-output'
	# client = boto3.client('s3')
	# img = open(file_path, 'rb').read() 
	# client.put_object(Body=img, Bucket=bucket_name, Key=file_path)
	pass


	



# x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x
# next 3 functions apply ONLY for notif tracking
# Simple JSON parse/modify helper functions
def parse_json(filename, param1,param2):
	with open(filename) as file:
		data = json.load(file)
		d1 = data[param1]
		d2 = data[param2]
		return d1,d2

def modify_json_file(filename,param1,param2,inp1,inp2):
	inp1 = str(inp1)
	inp2 = str(inp2)
	with open(filename,'w') as file:
		inp_data = {param1:inp1,param2:inp2}
		json.dump(inp_data,file,indent=4)
		

def reset_json_file(filename,param1,param2):
	with open(filename,'w') as file:
		inp_data = {param1:"0",param2:"0"}
		json.dump(inp_data,file,indent=4)
		print(f'Success: Reset {filename}')

# x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x

def convert_json(filename):
	# convert json to a python dict
	config_dict = {}
	with open(filename) as file:
		data = json.load(file)
		for d in data:
			config_dict[d] = data[d]
		return config_dict

def modify_json(filename,config_dict):
	# input a python dict, convert to json and output to json file
	with open(filename,'w') as file:
		json.dump(config_dict,file,indent=4)
	print(f'Added change on {filename}')

def modify_json_field(filename,key,val):
	data = convert_json(filename)
	data[key] = val
	if data["user_override"] == "False":
		with open(filename,'w') as file:
			json.dump(data,file,indent=4)
		print(f'Reset {key} in config.json')
	else:
		pass


# -x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x

def determine_mode(hr,op_time,cl_time,config,filename):
	# Static function to determine current mode.
	# current mode = 0 by default.
	# hr is current hour of the day (24 hr format)
	# op_time = opening time, cl_time = closing time
	# two modes available: operations and night guard
	
	if hr >= op_time and hr < cl_time:
			if config["current_mode"] != "operations": 
				config["current_mode"] = "operations"
				
				modify_json(filename,config)
				# if hr is during between opening and closing hours return operations for mode.
			return 'operations'	
	
	elif hr >= cl_time:
		if hr >= cl_time and hr <= 23:
			if config["current_mode"] != "night_guard": 
				config["current_mode"] = "night_guard"
				
				modify_json(filename,config)
			return 'night_guard'
		if hr >= 0 and hr <= op_time:
			if config["current_mode"] != "night_guard":
				conig["current_mode"] = "night_guard"
				modify_json(filename,config)
			return 'night_guard'

			
			

def output_mode():
	# Determines mode by considering a range of factors like opening/closing hours, and weekday or weekend. 
	# User override is possible so user can manually set the mode.
	file = 'json/config.json'
	weekdays = ['Mon','Tue','Wed','Thu','Fri']
	config = convert_json(file)
	today = time.strftime("%a")
	hr = int(time.strftime("%H")) # current hour
	curr_date = time.strftime("%d/%m/%y")
	curr_time = time.strftime('%H:%M')
	op_time = int(config["weekday-opening"][:2])
	cl_time = int(config["weekday-closing"][:2])
	
	
	if config['user_override'] == 'False':

		if today in weekdays:
			mode = determine_mode(hr,op_time,cl_time,config,file)
			return mode
		
		elif today == 'Sat':
			op_time = int(config["weekend-opening"][:2])
			cl_time = int(config["weekend-closing"][:2])
			mode = determine_mode(hr,op_time,cl_time,config,file)
			return mode
		
		elif today == 'Sun':
			return 'night_guard'

	elif config['user_override'] == "True":
		
		curr_mode = config['current_mode']
		expire_date = config['mode_until_date']
		expire_time = config['mode_until_time']
		td = time_diff(expire_time,curr_time)
		

		if curr_date == expire_date:
			if td <= 0:
				mode = determine_mode(hr,op_time,cl_time,config,file)
				config["user_override"] = "False"
				config["current_mode"] = mode
				config["mode_until_date"] = "0"
				config["mode_until_time"] = "0"
				modify_json(file,config)
				return mode
			else:
				return curr_mode
		else:			
				return curr_mode
		



