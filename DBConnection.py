# Copyright © Jaehyuk,Kim(a.k.a. SangDdung) 2019~
# 한신대학교 생활코딩 대회
# MySql 데이터베이스 처리 클래스

import pymysql

class MysqlDB():
	
	# 생성자 : 데이터베이스 정보 정의 및 연결
	def __init__(self):
		# DB 연결
		self.db = pymysql.connect(host='localhost',
											 port=3306,
											 user='root',
											 passwd='********',
											 db='bus_info_system',
											 charset='utf8')
		self.cursor = self.db.cursor()
		
		print("[I] 데이터베이스 처리 클래스를 로드하였습니다.")
	
	def is_login_success(self, id, pw):
		try:
			input_pw = self.get_password_by_id(id)
			if (pw==input_pw):
				return True
			return False
		except:
			return False
	
	def get_password_by_id(self, id):
		self.cursor.execute("SELECT password FROM accounts WHERE id='" + id + "'")
		result = self.cursor.fetchall()[0][0]
		return result
	
	def update_password_by_id(self, id, new_pw):
		self.cursor.execute("UPDATE accounts SET password='"+new_pw+"' WHERE id='"+id+"'")
		self.db.commit()
	
	def get_regi_bus_info(self, id):
		try:
			self.cursor.execute("SELECT * FROM regi_bus WHERE id='" + id + "'")
			result = self.cursor.fetchall()[0]
			print("[i] 등록 정보 : " + str(result))
		except:
			return ()
		return result
	
	def set_regi_bus_info(self, id, name, bus_id, bus_name, station_id):
		regi_info = self.get_regi_bus_info(id)
		
		if(len(regi_info)==0):
			self.cursor.execute("INSERT INTO regi_bus (id, name, bus_id, bus_name, station_id) VALUES ('"+id+"','"+name+"','"+bus_id+"','"+bus_name+"','"+station_id+"');")
		else:
			self.cursor.execute("UPDATE regi_bus SET name='"+name+"', bus_id='"+bus_id+"', bus_name='"+bus_name+"', station_id='"+station_id+"' WHERE id='"+id+"'")
		self.db.commit()
	
	def delete_bus_info(self, id):
		self.cursor.execute("DELETE FROM regi_bus WHERE id='"+id+"'")
		self.db.commit()
	
	def get_save_bus_name_list(self, id):
		try:
			self.cursor.execute("SELECT name FROM save_bus WHERE id='" + id + "'")
			return self.cursor.fetchall()
		except:
			return ((),)
		
	def get_save_bus_info(self, id, name):
		try:
			self.cursor.execute("SELECT * FROM save_bus WHERE id='" + id + "' AND name='" + name + "'")
			return self.cursor.fetchall()[0]
		except:
			return ()
		
	def is_valid_name(self, id, name):
		self.cursor.execute("SELECT name FROM save_bus WHERE id='" + id + "'")
		try:
			db_names = self.cursor.fetchall()
		except:
			db_names = ((),)
		for db_name in db_names:
			if(name==db_name[0]):
				return False
		return True
	
	def put_save_bus_info(self, id, name, bus_id, bus_name, station_id):
		self.cursor.execute("INSERT INTO save_bus (id, name, bus_id, bus_name, station_id) VALUES ('"+id+"','"+name+"','"+bus_id+"','"+bus_name+"','"+station_id+"');")
		self.db.commit()
