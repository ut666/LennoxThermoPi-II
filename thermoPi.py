from time import sleep
import datetime
import requests
import json
import pprint
from xml.dom import minidom

#login details for the icomfort.com page
username = "XXXXXXXXXXXXX"; #your lennox web username
password = "XXXXXXXXXXXXX"; #your lennox we password
weatherLocation = "XXXXXX, XX"; #accuweather location string ie: "Chicago, IL"

serviceURL = "https://" + username + ":" + password + "@services.myicomfort.com/DBAcessService.svc/";

#Get operations: (XXXX?UserName=username)
validateUser = "ValidateUser";

#Get operations: (XXXX?UserID=username)
userID = "?UserId=";
getBuildingsInfo = "GetBuildingsInfo";
getSystemsInfo = "GetSystemsInfo";

#Get operations: (XXXX?GatewaySN=gatewaysn)
gatewaySN  = "?gatewaysn="
getTStatLookupInfo = "GetTStatLookupInfo";
getTStatInfoList = "GetTStatInfoList";
getGatewayInfo = "GetGatewayInfo";
getTStatScheduleInfo = "GetTStatScheduleInfo";
getGatewaysAlerts = "GetGatewaysAlerts";

#Get operations:
location = "?location=";
getWeatherInfoJSON = "GetWeatherInfoJSON";
getWeatherInfoXML = "GetWeatherInfoXML";
getAccuWeather = "GetAccuWeather";

#Set operations allowed
setTStatInfo = "SetTStatInfo";
setAwayModeNew = "SetAwayModeNew";
setProgramInfoNew = "SetProgramInfoNew";

#makes looking at json responses easier to read
pp = pprint.PrettyPrinter(indent=4)

try:
    while True:
	
		#Create a session to our lennox
		session_url = serviceURL + validateUser + "?UserName=" + username + "&TempUnit=&Cancel_Away=-1";
		
		sessionSuccessful = True;
		try:
			s = requests.session();
		except requests.exceptions.RequestException as e:
			logging.info("ERROR: seesion request failed!");
			sessionSuccessful = False;
			
		if sessionSuccessful == True:			
			#get our cookies
			cookies = s.get(session_url)
			#Get all our systems
			url = serviceURL + getSystemsInfo + userID + username;
			r = s.get(url)
			#pp.pprint(r.json());
			
			try:
				#Iterate over each system
				for system in r.json()["Systems"]:

					#fetch our system serial number
					serailNumber = system["Gateway_SN"];

					#now do a getTStatInfoList request
					url = serviceURL + getTStatInfoList + gatewaySN + serailNumber + "&TempUnit=&Cancel_Away=-1";
					resp = s.get(url);

					#pp.pprint(resp.json());
					
					try:
						#our response object that has all our stats
						statInfo = resp.json()['tStatInfo'][0];
					except requests.exceptions.RequestException as e:
						logging.info("ERROR: unable to fetch 'tStatInfo'!");
				
					try:
						#get the weather
						url = serviceURL + getWeatherInfoXML  + location + weatherLocation + "&langnumber=0&metric=1";
						resp = s.get(url);
						#pp.pprint(resp.text);
						#get the node of interest from the XML (just our temp)
						xmldoc = minidom.parseString(resp.text);
						weatherInfo = xmldoc.getElementsByTagName('Current_temp');
						outdoortemp = weatherInfo[0].firstChild.nodeValue;
					except requests.exceptions.RequestException as e:
						logging.info("ERROR: unable to fetch 'Current_temp'!");

					try:
						#now get the data
						status = statInfo['System_Status'];
						mode = statInfo['Operation_Mode'];
						humid = statInfo['Indoor_Humidity'];
						temp = statInfo['Indoor_Temp'];
						cool = statInfo['Cool_Set_Point'];
						heat = statInfo['Heat_Set_Point'];

						#fetch the current time
						dt = datetime.datetime.now().strftime('%Y, %m, %d, %H, %M');

						
						#log all this to a file
						myFile = open('/var/www/html/thermoPi/data.txt', 'a');
						myFile.write(dt + ', ' + str(temp) + ', '  + str(humid) + ', ' + str(heat) + ', ' + str(cool) + ', ' + str(status) + ', ' + str(outdoortemp) + '\n');
						myFile.close();											
					except requests.exceptions.RequestException as e:
						logging.info("ERROR: unable to write stats to file!");

			except requests.exceptions.RequestException as e:
				logging.info("ERROR: unable to fetch 'Systems'!");

		#sleep for 30 mins
		sleep(60*30) 
		
except KeyboardInterrupt, e:
    logging.info("Stopping...")