
#include <SoftwareSerial.h>

// 디스플레이 헤더파일
#include <Wire.h>                            // I2C control library
#include <LiquidCrystal_I2C.h>          // LCD library

// 와이파이 모듈 헤더파일
#include "ESP8266.h"

LiquidCrystal_I2C lcd(0x27,16,2);

SoftwareSerial esp8266Serial = SoftwareSerial(6, 7);
ESP8266 wifi = ESP8266(esp8266Serial);

const char server_ip[] = "211.201.175.117";
const char device_id[] = "1234";

int PLUS_BUTTON=2;
int MINUS_BUTTON=3;
int OK_BUTTON=4;

int BUZZER=8;

int alarmcount = 0; // 알람멜로디가 10번 반복되면 자동으로 종료
bool alarm = false;
/*
 mode 설정
 0 : 초기화중
 1 : 대기상태(버스 설정되어있으면 대기)
 2 : 버스 설정 상태
 3 : 알람시각 설정 상태
 4 : 알람 울리는 중
*/
int now_mode = 0;

int plus_state = 0;
int minus_state = 0;
int ok_state; // ok 버튼 눌렀을때 1됨
const char spliter[] = "|";
const String ok_flag = "OK";
// 버스 정보 정의
typedef struct BUS_INFO{
  String bus_name;
  
  int bus_personal_num = 0; // 버스 차량번호 4자리
  int bus_time; // 버스 도착시각(분)
} BUS_INFO;

int now_selecting_bus = 0;

//0번째 배열은 첫번째 버스, 1번째 배열은 두번째 버스
BUS_INFO query_bus_info[2];
BUS_INFO selected_bus_info;

int retry_count=0;

int user_alarm_time = 5;

void Error_restart(String errmsg1, String errmsg2){
  
  lcd.clear();
  lcd.print(errmsg1);
  lcd.setCursor(0,1);
  lcd.print(errmsg2);
  
  tone(BUZZER, 1976);
  delay(300);
  tone(BUZZER, 1568);
  delay(1000);
  tone(BUZZER, 1976);
  delay(300);
  tone(BUZZER, 1568);
  delay(1000);
  tone(BUZZER, 1976);
  delay(300);
  tone(BUZZER, 1568);
  delay(1000);
  noTone(BUZZER);
  while(1);
}
void setup()
{
  String is_success ;
  
  Serial.begin(9600);
  Serial.println("initilizing...");
  
  pinMode(PLUS_BUTTON,INPUT);
  pinMode(MINUS_BUTTON,INPUT);
  pinMode(OK_BUTTON,INPUT);
  
  pinMode(BUZZER,OUTPUT);
  
  digitalWrite(PLUS_BUTTON, INPUT_PULLUP);
  digitalWrite(MINUS_BUTTON, INPUT_PULLUP);
  digitalWrite(OK_BUTTON, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(PLUS_BUTTON), btn_Plus_Func, RISING);
  attachInterrupt(digitalPinToInterrupt(MINUS_BUTTON), btn_Minus_Func, RISING);

  lcd.begin();
  lcd.backlight();  // turn on backlight
  lcd.print("initializing....");
  
  esp8266Serial.begin(9600);
  wifi.begin();
  wifi.setTimeout(1000);
  
  // test
  //Serial.print("test: ");
  Serial.println(getStatus(wifi.test()));
   
  // restart
  //Serial.print("restart: ");
  Serial.println(getStatus(wifi.restart()));
  
  // getVersion
  char version[20] = {};
  //Serial.print("getVersion: ");
  Serial.print(getStatus(wifi.getVersion(version, 16)));
  Serial.print(" : ");
  Serial.println(version);
  
  // joinAP
  //Serial.print("setMode: ");
  Serial.println(getStatus(wifi.setMode(ESP8266_WIFI_STATION)));
  
  int try_count = 0;
  
  //Serial.print("joinAP: ");
  do{
    try_count++;
    is_success = getStatus(wifi.joinAP("SangDdung", "cool_201"));
    Serial.println(is_success);
    if(try_count>3)  // 와이파이 연결 3번까지 재시도
      Error_restart("WIFIerror.please","Restart Device.");
  }while(!is_success.equals(ok_flag));
  
  // connect
  try_count = 0;
  //Serial.print("connect: ");
  do{
    try_count++;
    is_success = getStatus(wifi.connect(ESP8266_PROTOCOL_TCP, server_ip, 5000));
    Serial.println(is_success);
    if(try_count>3)  // 서버 연결 3번까지 재시도
      Error_restart("Server not","response.");
  }while(!is_success.equals(ok_flag));
  
  // 현재상태 : 초기화 완료 --> 대기상태
  Serial.println("initializing Success");
  delay(1000);
  
  plus_state = 0;
  minus_state = 0;
  ok_state = 0;
  
  mode_change(1);

}

void loop(){
  switch(now_mode){
    case 0:
      break;
    case 1:
      ok_state = !digitalRead(OK_BUTTON);
      if(ok_state){
        //Serial.println("OK PUSHED at MODE 1(IDLE)");
        mode_change(2);
        delay(500);
      }
      if(plus_state){
        update_bus_info(0);
        delay(200);
        plus_state=0;
      }
      
      if(minus_state){
        clear_bus();
        mode_change(1);
        delay(200);
        minus_state=0;
      }
      if(selected_bus_info.bus_personal_num!=0){
        if(!update_bus_info(1)) retry_count++;
        else retry_count=0;
        if(retry_count>5){
          Error_restart("SERVICE","ERROR!!");
        }
        print_wating_bus_time();
        if(selected_bus_info.bus_time<=user_alarm_time)
            mode_change(4);
      }
      break;
    case 2:
      ok_state = !digitalRead(OK_BUTTON);
      if(ok_state){
        //Serial.println("OK PUSHED at MODE 2(BUS SETTING)");
        if(confirm_bus(now_selecting_bus)){
          mode_change(3);
        }else{
          mode_change(3);
        }
        delay(500);
      }
      if(plus_state){
        select_bus(!now_selecting_bus);
        delay(300);
        plus_state = 0;
      }
      if(minus_state){
        select_bus(!now_selecting_bus);
        delay(300);
        minus_state = 0;
      }
      break;
    case 3:
      ok_state = !digitalRead(OK_BUTTON);
      if(ok_state){
        //Serial.println("OK PUSHED at MODE 2(TIME SETTING)");
        mode_change(1);
        delay(500);
      }
      if(plus_state){
        select_alarm_time(user_alarm_time+1);
        delay(300);
        plus_state = 0;
      }
      if(minus_state){
        select_alarm_time(user_alarm_time-1);
        delay(200);
        minus_state = 0;
      }
      break;
    case 4:
      if(alarm){
        tone(BUZZER,1319);
        delay(500);
        alarm_canceling_check();
        tone(BUZZER,1175);
        delay(200);
        alarm_canceling_check();
        tone(BUZZER,1047);
        delay(500);
        alarm_canceling_check();
        tone(BUZZER,1175);
        delay(200);
        alarm_canceling_check();
        tone(BUZZER,1319);
        delay(1000);
        alarm_canceling_check();
        noTone(BUZZER);
        alarmcount++;
        if(alarmcount>=5) alarm=false;
        if(plus_state || minus_state){
          alarm=false;
          delay(200);
          plus_state = 0; minus_state = 0;
        }
      }else{
        alarmcount = 0;
        mode_change(1);
      }
      break;
  }
}

void alarm_canceling_check(){
  if(plus_state || minus_state){
    alarm=false;
    delay(200);
    plus_state = 0; minus_state = 0;
  }
}

void test_setting(String busname, int bustime[]){
  query_bus_info[0].bus_name = busname;
  query_bus_info[1].bus_name = busname;
  
  query_bus_info[0].bus_personal_num = 1111;
  query_bus_info[1].bus_personal_num = 2222;
  
  query_bus_info[0].bus_time = bustime[0];
  query_bus_info[1].bus_time = bustime[1];
}

void print_wating_bus_time(){
  lcd.clear();
  lcd.print("Waiting " + selected_bus_info.bus_name);
  lcd.setCursor(0,1);
  lcd.print("time:" + String(selected_bus_info.bus_time) + "m/" + String(user_alarm_time)+"m");
}

void mode_change(int mode){
  switch(mode){
    case 0:
      //Serial.println("Mode Changing : 0(initializing)");
      break;
    case 1:
      //Serial.println("Mode Changing : 1(IDLE)");
      if(selected_bus_info.bus_personal_num==0){
        lcd.clear();
        lcd.print("Please");
        lcd.setCursor(0,1);
        lcd.print("select a bus");
      }else{
        print_wating_bus_time();
      }
      break;
    case 2:
      lcd.clear();
      lcd.print("Wait...");
      if(!update_bus_info(0)){
        lcd.clear();
        lcd.print("Error!");
        lcd.setCursor(0,1);
        lcd.print("bus cannotFound!");
        delay(3000);
        clear_bus();
        mode = 1;
        mode_change(1);
        break;
      }
      //Serial.println("Mode Changing : 2(BUS SETTING)");
      //test_setting("700-2", bustime);

      select_bus(0);
      
      break;
    case 3:
      //Serial.println("Mode Changing : 3(TIME SETTING)");
      select_alarm_time(user_alarm_time);
      break;
    case 4:
      //Serial.println("Mode Changing : 4(BUZZING)");

      lcd.clear();
      lcd.print("Bus is comming!!");
      lcd.setCursor(0,1);
      lcd.print("----BUZZING!----");
      
      clear_bus();
      alarm = true;
      break;
  }
  now_mode = mode;
}

void select_bus(int num){
  now_selecting_bus = num;
  //Serial.println(query_bus_info[0].bus_name);
  lcd.clear();
  lcd.print("BUS NUM:" + query_bus_info[0].bus_name);
  lcd.setCursor(0,1);
  if(num==0)
    lcd.print("[1. "+String(query_bus_info[0].bus_time)+"m] 2. "+String(query_bus_info[1].bus_time)+"m");
  else
    lcd.print("1. "+String(query_bus_info[0].bus_time)+"m "+"[2. "+String(query_bus_info[1].bus_time)+"m]");
}

int confirm_bus(int num){
  selected_bus_info.bus_name = query_bus_info[num].bus_name;
  selected_bus_info.bus_personal_num = query_bus_info[num].bus_personal_num;
  selected_bus_info.bus_time = query_bus_info[num].bus_time;
  
  return 1;
}

void clear_bus(){
  selected_bus_info.bus_name = "";
  selected_bus_info.bus_personal_num = 0;
  selected_bus_info.bus_time = 0;
}

void select_alarm_time(int minuate){

  if(minuate>0 && minuate<20)
    user_alarm_time = minuate;
  
  lcd.clear();
  lcd.print("Select alarmTime");
  lcd.setCursor(0,1);
  lcd.print("min:" + String(user_alarm_time) + "min before");
}

void btn_Plus_Func(){
  /*
  switch(now_mode){
    case 0:
      Serial.println("PLUS PUSHED at MODE 0(Initializing)");
      break;
    case 1:
      Serial.println("PLUS PUSHED at MODE 1(IDLE)");

      break;
    case 2:
      Serial.println("PLUS PUSHED at MODE 2(BUS SETTING)");
      break;
    case 3:
      Serial.println("PLUS PUSHED at MODE 3(TIME SETTING)");

      break;
    case 4:
      Serial.println("PLUS PUSHED at MODE 4(BUZZING)");
      break;
  }
  */
  plus_state = 1;
}

void btn_Minus_Func(){
  /*
  switch(now_mode){
    case 0:
      Serial.println("PLUS PUSHED at MODE 0(Initializing)");
      break;
    case 1:
      Serial.println("MINUS PUSHED at MODE 1(IDLE)");

      break;
    case 2:
      Serial.println("MINUS PUSHED at MODE 2(BUS SETTING)");
      break;
    case 3:
      Serial.println("MINUS PUSHED at MODE 3(TIME SETTING)");

      break;
    case 4:
      Serial.println("MINUS PUSHED at MODE 4(BUZZING)");
      break;
  }
  */
  minus_state = 1;
}

int update_bus_info(int type){

  int n = 0; // n번째 버스
  
  char buffer[30] = {};

  getStatus(wifi.connect(ESP8266_PROTOCOL_TCP, server_ip, 5000));
  
  //Serial.println(is_success);
  //if(!is_success.equals("OK"))
  //  return;
  
  // send
  Serial.print("send: ");
  delay(1000);
  getStatus(wifi.send("GET /bus_time?id=1234\r\n\r\n"));
  //Serial.println(is_success);
  //if(!is_success.equals("OK"))
  //  return;
  delay(1000);
  wifi.read(buffer, 30);
  Serial.println((char*)buffer);
  if(buffer[0]=='\0' || buffer[0]=='E') {
    return 0;
  }
  String str = buffer;
  int first = str.indexOf(spliter);
  int second = str.indexOf(spliter,first+1);
  int third = str.indexOf(spliter,second+1);
  if(type==0){
    query_bus_info[0].bus_name = str.substring(0, first);
    query_bus_info[1].bus_name = str.substring(0, first);
  }
  
  String timestr = str.substring(second+1, third);
  int time_first = timestr.indexOf(",");
  int time_second = timestr.indexOf(",",time_first+1);
  
  query_bus_info[0].bus_personal_num = timestr.substring(0,time_first).toInt();
  query_bus_info[1].bus_personal_num = timestr.substring(time_first+1, time_second).toInt();
  if(type==1){
    if(query_bus_info[0].bus_personal_num == selected_bus_info.bus_personal_num){
      n=0;
    }else{
      n=1;
    }
  }
  
  timestr = str.substring(first+1, second);
  time_first = timestr.indexOf(",");
  time_second = timestr.indexOf(",",time_first+1);
  query_bus_info[0].bus_time = timestr.substring(0,time_first).toInt();
  query_bus_info[1].bus_time = timestr.substring(time_first+1, time_second).toInt();
  if(type==1){
    selected_bus_info.bus_time = query_bus_info[n].bus_time;
  }

  return 1;
}


///////////////////////////////
String getStatus(bool status)
{
    if (status)
        return ok_flag;
 
    return "KO";
}
 
String getStatus(ESP8266CommandStatus status)
{
    switch (status) {
    case ESP8266_COMMAND_INVALID:
        return "INVALID";
        break;
 
    case ESP8266_COMMAND_TIMEOUT:
        return "TIMEOUT";
        break;
 
    case ESP8266_COMMAND_OK:
        return ok_flag;
        break;
 
    case ESP8266_COMMAND_NO_CHANGE:
        return "NO CHANGE";
        break;
 
    case ESP8266_COMMAND_ERROR:
        return "ERROR";
        break;
 
    case ESP8266_COMMAND_NO_LINK:
        return "NO LINK";
        break;
 
    case ESP8266_COMMAND_TOO_LONG:
        return "TOO LONG";
        break;
 
    case ESP8266_COMMAND_FAIL:
        return "FAIL";
        break;
 
    default:
        return "UNKNOWN COMMAND STATUS";
        break;
    }
}
