from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
 
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage
 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

import pandas as pd
line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

class THSRScraper:
    def __init__(self, start_location, end_location, date, time):
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 10)
        self.start_location = start_location
        self.end_location = end_location
        self.date = date
        self.time = time

    def depart(self):
        url = "https://www.thsrc.com.tw"
        self.driver.get(url)
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[5]/div/div[3]/button[2]'))).click()
        start = self.driver.find_element(By.ID, 'select_location01')
        dropdown = Select(start)
        dropdown.select_by_visible_text(self.start_location)#導入起點
        destination = self.driver.find_element(By.ID, 'select_location02')
        dropdown2 = Select(destination)
        dropdown2.select_by_visible_text(self.end_location)#導入終點
        date_element = self.driver.find_element(By.ID, 'Departdate01')
        self.driver.execute_script("arguments[0].value = arguments[1]", date_element, self.date)
        time_element = self.driver.find_element(By.ID, "outWardTime")
        self.driver.execute_script("arguments[0].value = arguments[1]", time_element, self.time)
        query_button = self.driver.find_element(By.XPATH, '//*[@id="start-search"]')
        query_button.click()
        self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'font-16r.darkgray')))
        time_depart = self.driver.find_elements(By.CLASS_NAME, 'font-16r.darkgray')
        
        time_list = []
        b=1#控制time_depart的變數
        s_time = []
        e_time = []
        for i in time_depart:
            if b%2 == 1:
                s_time.append(str(i.text))
                b+=1
            else:
                e_time.append(str(i.text))
                b+=1
        print("start",s_time)
        print("end",e_time)
        time_data = {
            "start_time":s_time,
            "end_time":e_time,
        }
        df = pd.DataFrame(time_data)
        df.reset_index(drop=True, inplace=True)
        df.index.name = '' 
        df.columns = ["出發時間","抵達時間"]   
        print(df)
        self.driver.quit()
        return df


@csrf_exempt
def callback(request):
 
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
 
        try:
            events = parser.parse(body, signature)  # 傳入的事件
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()
        # # 使用 THSRScraper class
        # thsr = THSRScraper("桃園", "苗栗", "2023.04.01", "17:00")
        # thsr.depart()
        for event in events:#Python迴圈進行讀取()，如果其中有訊息事件()，則回覆使用者所傳入的文字()。
            if isinstance(event, MessageEvent):  # 如果有訊息事件
                demand = event.message.text.split('\n')
                thsr = THSRScraper(demand[0], demand[1], demand[2], demand[3])
                line_bot_api.reply_message(  # 回復傳入的訊息文字
                    event.reply_token,
                    TextSendMessage(text=f" {thsr.depart()}")
                )
        return HttpResponse()
    else:
        return HttpResponseBadRequest()