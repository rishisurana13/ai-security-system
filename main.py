from toolbox import td_h, modify_json_file, parse_json, time_diff
import time
import threading
from threat_protocol import exec_threat_protocol_process

def main(threat,threat_dict,frame):
	# Intiialize all variables.
	t_diff = 0
	ctime = time.ctime()
	json_file = 'json/notification_log.json'
	last_notified,notif_count = parse_json(json_file,"last_notified","notification_count")
	notif_count = int(notif_count)
##########
	# 0 is default val of last notified. In the event a notif has already been sent then time diff (td) can be calculated. 
	if last_notified != "0":
		t_diff = time_diff(ctime,last_notified) # returns an int - total minutes
	
	# If time difference more than 5 minutes execute following block below. 
	if t_diff > 5:
		notif_count = "0"
		last_notified = "0"
		# Resets notification log file if it has been 5 minutes since a notif has been sent.
		reset_json_file('json/notification_log.json',"last_notified","notification_count")
		print(f'INFO: Reset {json_file}, as vigilance period has elapsed.')

	if threat == True:
		# This is for the first notification being sent when a threat is True. 
		if notif_count < 1:
			notif_count +=1
			last_notified = ctime
			modify_json_file(json_file,"last_notified","notification_count",last_notified,notif_count)
			# Execute threat protocol in new thread.
			t2 = threading.Thread(target=exec_threat_protocol_process,args=(threat_dict,frame,ctime))
			t2.start()
			
		
		# If more than one has been sent and time diff more than 2 mins and less than 3 mins.
		# This helps in reducing wasted threads. 
		elif notif_count >= 1 and notif_count < 3 and t_diff >= 2 and t_diff < 3: 
			notif_count +=1
			last_notified = ctime
			modify_json_file(json_file,"last_notified","notification_count",last_notified,notif_count)
			t2 = threading.Thread(target=exec_threat_protocol_process,args=(threat_dict,frame,ctime))
			t2.start()
			
		
		else:
			pass
	