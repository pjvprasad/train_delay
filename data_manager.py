import re
import requests
from os import system
try:
	from bs4 import BeautifulSoup
except:
	system("pip install beautifulsoup4")
	from bs4 import BeautifulSoup
import csv
import ast

"""
from bs4 import BeautifulSoup
import requests

headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}
r=requests.get('http://www.transfermarkt.com/arsenalfc/startseite/verein/11/saison_id/2015', headers=headers)
soup = BeautifulSoup(r.content, 'html.parser')
print(soup.prettify())
"""

# <> var , [] opt

# station codes and names
#https://www.cleartrip.com/trains/stations/list[?page=<page_num>]
#div(class="pagination")->children[last] 		aslong as it is <a>
#https://www.cleartrip.com/trains/stations/<station_code>

#average time delay for trains in given station
#https://www.railyatri.in/insights/average-train-delay-at-station/<station_code>[?from_pagination=true&page_num=<page_num>]
# div(class="pages")->a[1]        next page link        as long as a[1].title!="No More Data"
#	if no pages then invalid url

def webfetch_stations_trains(label):
	data={}
	headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
	start_urls={'stations':'https://www.cleartrip.com/trains/stations/list',
				'trains':'https://www.cleartrip.com/trains/list?field=number&sort=up'}
	start_url=start_urls[label]
	try:
		print("opening the {} url".format(label))
		#html=urlopen(start_url)
		r=requests.get(start_url)
	except:
		print("please check network connection")
		return
	#print("reading page into soup")
	soup=BeautifulSoup(r.content,'html.parser')
	print("Scraping Data ",end='')
	while(True):
		table=soup.find_all('table')[0]

		rows=table.find_all('tr')
		#print("extracting table data")
		for row in rows[1:]:
			cols=row.find_all('td')
			data[re.sub('<.*?>','',str(cols[0]))]=re.sub('<.*?>','',str(cols[1]))

		#print("looking for next page link")
		div_lst=soup.find_all('div',{'class':'pagination'})
		if(not len(div_lst)):
			break
		a_lst=div_lst[0].find_all('a',{'class':'next_page'})
		if(not len(a_lst)):
			break

		#print("opnening next page")
		print('.',end='')
		#html=urlopen('https://www.cleartrip.com'+a_lst[0]['href'])
		r=requests.get('https://www.cleartrip.com'+a_lst[0]['href'])
		#print("reading into soup")
		soup=BeautifulSoup(r.content,'html.parser')
	print(label," extracted")
	return data

def webfetch_avg_delays(station):
	print(station)
	headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
	r=requests.get('https://www.railyatri.in/insights/average-train-delay-at-station/'+station,headers=headers)
	soup=BeautifulSoup(r.content,'html.parser')
	data={}
	while(True):

		print("looking for pages div")
		div_lst=soup.find_all('div',{'class':'pages'})
		if(not len(div_lst)):
			break

		print('Extracting data')
		scripts=soup.find_all("script")
		list_str=re.sub('<.*?>','',str(scripts[-7])).split(';')[0].split('=')[1].strip()
		train_delay_lst=ast.literal_eval(list_str)
		for train_delay_dict in train_delay_lst:
			mtch=re.match('([0-9]+) \(([0-9]+).*',train_delay_dict['number'])
			data[mtch.group(1)]=int(mtch.group(2))

		a=div_lst[0].find_all('a')
		print("Looking for next page link")
		if(len(a)==0 or a[1]['title']=="No More Data"):
			break
		print('opening next page')
		r=requests.get('https://www.railyatri.in'+a[1]['href'],headers=headers)
		soup=BeautifulSoup(r.content,'html.parser')
	return data

def update_stations_trains(label):
	data=webfetch_stations_trains(label)
	print(f"updating {label} data ",end='')
	with open(f'{label}.csv','w') as file:
		writer=csv.writer(file)
		for code,name in data.items():
			writer.writerow([code,name])
	print("done")
	return data


def filefetch_stations_trains(label):
	data={}
	print("fetching {} data ".format(label),end='')
	with open('{}.csv'.format(label),'r') as file:
		reader=csv.reader(file)
		for row in reader:
			data[row[0]]=row[1]
	print("done")
	return(data)

def update_avg_delays(stations):
	data={}
	for station,_ in stations.items():
		data[station]=webfetch_avg_delays(station)

	with open("train_delays.csv",'w') as train_delays_file:
		train_delays_writer=csv.writer(train_delays_file)
		for station_code,trains in data.items():
			for train_code,delay in trains.items():
				train_delays_writer.writerow([station_code,train_code,delay])
	print("update successful")
	return(data)

def filefetch_avg_delays():
	data={}
	print("fetching average delays ",end='')
	with open("train_delays.csv",'r') as train_delays_file:
		train_delays_reader=csv.reader(train_delays_file)
		for row in train_delays_reader:
			try:
				data[row[0]][row[1]]=row[2]
			except:
				data[row[0]]={}
	print("done")
	return data

if __name__ == '__main__':
	stations=update_stations_trains('stations')
	update_stations_trains('trains')
	stations=filefetch_stations_trains('stations')
	trains=filefetch_stations_trains('trains')
	#update_avg_delays(stations)
	avg_delays=filefetch_avg_delays()
