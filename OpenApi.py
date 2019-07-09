# Copyright © Jaehyuk,Kim(a.k.a. SangDdung) 2019~
# 한신대학교 생활코딩 대회
# 공공데이터포털(https://www.data.go.kr/) 공개API 처리 클래스

import requests
from bs4 import BeautifulSoup

# 함수 이름 앞에 get은 하나의 string 값만 반환
# 함수 이름 앞에 find는 리스트 반환
class OpenApi():
	
	# 생성자 : api_key 정의
	def __init__(self, api_key):
		self.api_key = api_key
		
	# 정류소 이름으로 정류소 ID 목록 사전(정류소 ID, 정류소 이름, 정류소 위치) 반환
	# 리턴타입 : dictionary
	def find_station_id_by_name(self, keyword):
		url = 'http://openapi.gbis.go.kr/ws/rest/busstationservice?serviceKey='+self.api_key+'&keyword='+keyword
		
		station_info = {} # 리턴 형식
		
		station_id_list = []
		station_name_list = []
		station_xy_list = []
		
		req = requests.get(url)
		html = req.text
		soup = BeautifulSoup(html, "html.parser")
		
		station = soup.find_all('busstationlist')
		
		for station_element in station:
			station_id_list.append(station_element.stationid.string)
			station_name_list.append(station_element.stationname.string)
			station_xy_list.append((station_element.x.string,station_element.y.string))
		
		station_info['station_id'] = station_id_list
		station_info['station_name'] = station_name_list
		station_info['station_xy'] = station_xy_list
		
		return station_info
		
	# 정류소 ID로 경유 버스 ID 목록 반환
	# 리턴타입 : list
	def find_bus_id_by_station_id(self, station_id):
		url = 'http://openapi.gbis.go.kr/ws/rest/busarrivalservice/station?serviceKey='+self.api_key+'&stationId='+station_id
		
		bus_id_list = []
		
		req = requests.get(url)
		html = req.text
		soup = BeautifulSoup(html, "html.parser")
		
		bus = soup.find_all('busarrivallist')
		
		for bus_element in bus:
			bus_id_list.append(bus_element.routeid.string)
		
		return bus_id_list
	
	# 버스 ID로 버스 번호 문자열 반환
	# 리턴타입 : str
	def get_bus_name_by_bus_id(self, bus_id):
		url = 'http://openapi.gbis.go.kr/ws/rest/busrouteservice/info?serviceKey='+self.api_key+'&routeId='+bus_id
		
		req = requests.get(url)
		html = req.text
		soup = BeautifulSoup(html, "html.parser")
		
		bus_name = soup.find('routename').text
		
		return bus_name
	
	# 정류소 ID로 경유 버스 번호 목록 사전(버스 ID, 버스번호) 반환
	# 리턴타입 : dictionary
	def find_bus_name_by_station_id(self, station_id):
		url = 'http://openapi.gbis.go.kr/ws/rest/busstationservice/route?serviceKey='+self.api_key+'&stationId='+station_id
		
		bus_info = {} # 리턴 형식
		
		bus_id_list = []
		bus_name_list = []
		
		req = requests.get(url)
		html = req.text
		soup = BeautifulSoup(html, "html.parser")
		
		bus = soup.find_all('busroutelist')
		
		for bus_element in bus:
			bus_id_list.append(bus_element.routeid.string)
			bus_name_list.append(bus_element.routename.string)
			
		bus_info['bus_id'] = bus_id_list
		bus_info['bus_name'] = bus_name_list
		
		return bus_info
	
	# 정류소 ID와 버스 ID로 경유 버스 도착 정보 목록 반환
	# 리턴타입 : list
	def find_bus_arrive(self, station_id, bus_id):
		url = 'http://openapi.gbis.go.kr/ws/rest/busarrivalservice?serviceKey='+self.api_key+'&stationId='+station_id+'&routeId='+bus_id
		#print(url)
		bus_time_list = ()
		
		req = requests.get(url)
		html = req.text
		soup = BeautifulSoup(html, "html.parser")
		
		try:
			bus_element = soup.find_all('busarrivalitem')[0]
		except IndexError:
			bus_time_list = ("-2", "버스가 존재하지 않습니다.")
			return (bus_time_list,)
		
		if(bus_element.predicttime1.string==None):
			bus_time_list = ("-3", "버스 도착정보가 존재하지 않습니다.")
			return (bus_time_list,)
		
		bus_time_list = ((bus_element.predicttime1.string,bus_element.predicttime2.string))
		bus_personal_num_list = ((bus_element.plateno1.string[5:],bus_element.plateno2.string[5:]))
		
		
		return (bus_time_list,bus_personal_num_list)
	
	# 정류소 ID로 경유 버스 번호 목록 사전(버스 ID, 버스번호) 반환 : 현재파악되는 버스들 (사용X)
	# 리턴타입 : dictionary
	def find_bus_name_by_station_id_not_used(self, station_id):
		bus_info = {} # 리턴 형식
		
		bus_id_list = self.find_bus_id_by_station_id(station_id)
		bus_name_list = []
		
		for bus_id in bus_id_list:
			bus_name_list.append(self.get_bus_name_by_bus_id(bus_id))
			
		bus_info['bus_id'] = bus_id_list
		bus_info['bus_name'] = bus_name_list
		
		return bus_info