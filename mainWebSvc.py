# Copyright © Jaehyuk,Kim(a.k.a. SangDdung) 2019~
# 한신대학교 생활코딩 대회
# 메인

import os
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, session
import pymysql
from OpenApi import OpenApi
from DBConnection import MysqlDB


print("------------------------------------");
print("|        HANSHIN UNIVERSITY        |");
print("|      Programming Hackathon       |");
print("------------------------------------");
print("|         TEAM 짜요타요            |");
print("|      버스도착정보알림시스템      |");
print("------------------------------------");
print("[I] 공공 API정보 처리 클래스를 로드하였습니다.")

# Flask 모듈
app = Flask(__name__)
app.secret_key = os.urandom(24)

# OpenAPI 모듈
openapi = OpenApi('********')

# DB 연결
my_db = MysqlDB()


# 로그인 세션 체크
def login_state_check():
	if 'id' in session:
		return True
	else:
		return False

@app.route("/")
def index():
	if not login_state_check(): return render_template('login.html')
	regi_info = my_db.get_regi_bus_info(session['id'])
	if(len(regi_info)==0):
		device_regi_status = False
		return render_template('main.html', device_id=session['id'], device_regi_status=device_regi_status)
	else:
		device_regi_status = True
		bus_time = openapi.find_bus_arrive(regi_info[4], regi_info[2])[0]
		if(int(bus_time[0])<0):
			bus_time_str = "정보가 존재하지 않습니다."
		else:
			print("[i] 버스 도착 정보 : "+str(bus_time))
			if(bus_time[1] is None):
				bus_time_str = str(bus_time[0]) + "분"
			else:
				bus_time_str = str(bus_time[0]) + "분, " + str(bus_time[1]) + "분"
		return render_template('main.html', device_id=session['id'], device_regi_status=device_regi_status, name=regi_info[1], bus_name=regi_info[3], bus_time_str=bus_time_str)
	
		
@app.route("/login", methods = ['POST', 'GET'])
def login():
	err_msg = "로그인에 실패하였습니다.<br>아이디와 비밀번호를 확인하세요."
	
	if request.method == 'POST':	# 로그인 메소드 : POST
		if(my_db.is_login_success(request.form['id'],request.form['pw'])):
			# 로그인 성공
			session['id'] = request.form['id']
			return redirect("/")
		else:
			# 로그인 실패
			return render_template('dialog/error.html', err_msg=err_msg, redirect_page="/")
	else:		# 로그인 메소드 : GET
		if(my_db.is_login_success(request.args.get('id'),request.args.get('pw'))):
			# 로그인 성공
			session['id'] = request.args.get('id')
			return redirect("/")
		else:
			# 로그인 실패
			return render_template('dialog/error.html', err_msg=err_msg, redirect_page="/")
		
@app.route("/logout")
def logout():
	if not login_state_check(): return render_template('login.html')
	session.pop('id', None)
	return redirect("/")
	
@app.route("/station_search")
def station_search():
	if not login_state_check(): return render_template('login.html')
	db_names = my_db.get_save_bus_name_list(session['id'])
	return render_template('bus_search.html', db_names=db_names)

@app.route("/station_select", methods = ['POST', 'GET'])
def station_select():
	if not login_state_check(): return render_template('login.html')
	print("[i] 선택된 정류소 이름 : "+request.args.get('station_name'))
	station_info = openapi.find_station_id_by_name(request.args.get('station_name'))
	return render_template('station_list.html', station_info=station_info)
	
@app.route("/bus_select", methods = ['POST', 'GET'])
def bus_select():
	if not login_state_check(): return render_template('login.html')
	bus_info = openapi.find_bus_name_by_station_id(request.args.get('station_id'))
	return render_template('bus_list.html',bus_info=bus_info, station_id=request.args.get('station_id'))

@app.route("/bus_select_confirm", methods = ['POST', 'GET'])
def bus_select_confirm():
	if not login_state_check(): return render_template('login.html')
	
	if(request.args.get('select_name')):
		result = my_db.get_save_bus_info(session['id'], request.args.get('select_name'))
		station_id = result[4]
		bus_id = result[2]
		bus_name = result[3]
		name = request.args.get('select_name')
	else:
		station_id = request.args.get('station_id')
		bus_id = request.args.get('bus_id')
		bus_name = request.args.get('bus_name')
		name = ""
	
	check_bus_time = int(openapi.find_bus_arrive(station_id, bus_id)[0][0])
		
	if(check_bus_time<0):
		if(check_bus_time==-2):
			err_msg = "버스 정보가 존재하지 않습니다.<br>폐선된 노선이거나 해당 정류소에서 정보조회가 불가능한 버스입니다."
			return render_template('dialog/error.html', err_msg=err_msg, redirect_page="/")
		if(check_bus_time==-3):
			err_msg = "현재 버스 도착 정보가 존재하지 않습니다.<br>나중에 다시 시도하여 주십시오."
			return render_template('dialog/error.html', err_msg=err_msg, redirect_page="/")
	return render_template('bus_confirm.html',bus_id=bus_id, station_id=station_id, bus_name=bus_name, name=name)
	
@app.route("/bus_regist", methods = ['POST', 'GET'])
def bus_regist():
	if not login_state_check(): return render_template('login.html')
	info_msg = "등록이 완료되었습니다."
	
	my_id = session['id']
	name = request.form['name']
	bus_id = request.form['bus_id']
	bus_name = request.form['bus_name']
	station_id = request.form['station_id']
	if(request.form.get('save_tf')):
		print("[i] 저장 시퀀스 동작")
		if not (my_db.is_valid_name(session['id'], name)):
			err_msg = "저장 리스트에 별명이 중복된 항목이 있습니다.<br>다른 별명으로 시도하여 주십시오."
			return render_template('dialog/error.html', err_msg=err_msg, redirect_page="/")
		my_db.put_save_bus_info(my_id, name, bus_id, bus_name, station_id)
		
	my_db.set_regi_bus_info(my_id, name, bus_id, bus_name, station_id)
	return render_template('dialog/info.html', info_msg=info_msg, redirect_page="/")

@app.route("/bus_delete")
def bus_delete():
	if not login_state_check(): return render_template('login.html')
	my_db.delete_bus_info(session['id'])
	
	return redirect("/") 

@app.route("/pw_reset")
def pw_reset():
	if not login_state_check(): return render_template('login.html')
	return render_template("pw_reset.html", device_id=session['id']) 

@app.route("/pw_reset_proc", methods = ['POST', 'GET'])
def pw_reset_proc():
	if not login_state_check(): return render_template('login.html')
	
	input_pw = my_db.get_password_by_id(session['id'])
			
	if not (request.form['now_pw']==input_pw):
		err_msg = "현재 비밀번호가 맞지 않습니다.<br>다시 시도하여 주십시오."
		return render_template('dialog/error.html', err_msg=err_msg, redirect_page="/pw_reset")
	
	if not (request.form['next_pw']==request.form['next_pw2']):
		err_msg = "새로 설정할 비밀번호 확인이 맞지 않습니다.<br>다시 시도하여 주십시오."
		return render_template('dialog/error.html', err_msg=err_msg, redirect_page="/pw_reset")
	
	my_db.update_password_by_id(session['id'],request.form['next_pw'])
	
	info_msg = "비밀변호 변경이 완료되었습니다."
	return render_template('dialog/info.html', info_msg=info_msg, redirect_page="/")

@app.route("/bus_time", methods = ['POST', 'GET'])
def bus_time():
	try:
		device_id = request.args.get('id')

		regi_info = my_db.get_regi_bus_info(device_id)
		station_id = regi_info[4]
		bus_id = regi_info[2]
		bus_name = regi_info[3]
		
		retstr = ""
		bus_arrive_info = openapi.find_bus_arrive(station_id, bus_id)
		if(int(bus_arrive_info[0][0])<0):
			return "ERROR"
		retstr += bus_name + "|"
		retstr += bus_arrive_info[0][0] + ","
		if(bus_arrive_info[0][1] is None):	#	두번째 버스정보가 존재하지 않으면
			retstr += "-1" + "|" # -1분으로 설정
		else:
			retstr += bus_arrive_info[0][1] + "|"
		retstr += bus_arrive_info[1][0] + ","
		retstr += bus_arrive_info[1][1] + "|"
	except:
		return "ERROR"
	
	return retstr

@app.route("/bus_time_skagen", methods = ['POST', 'GET'])
def bus_time_skagen():
	device_id = request.args.get('id')
	
	regi_info = my_db.get_regi_bus_info(device_id)
	station_id = regi_info[4]
	bus_id = regi_info[2]
	
	return str(int(openapi.find_bus_arrive(station_id, bus_id)[0][0]))
	
@app.before_request
def make_session_permanent():
	session.permanent = True
	# 세션 타임아웃 5분으로 설정
	app.permanent_session_lifetime = timedelta(minutes=5)
	
if __name__ == "__main__":
	print("[I] Flask 웹서버를 시작합니다.")
	app.run(host="0.0.0.0")
