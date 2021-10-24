import os
import time
import random
import pandas as pd
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent



####################################################################################################
#                                             Settins                                              #
####################################################################################################
pd.options.display.expand_frame_repr = False
pd.options.display.max_columns = None



####################################################################################################
#                                            Attribute                                             #
####################################################################################################
DIR_BASE = os.path.dirname(os.path.abspath(__file__))
DIR_RAW_DATA = fr'{DIR_BASE}/raw_data/'

URL = 'https://fhy.wra.gov.tw/reservoirpage_2011/statistics.aspx'



####################################################################################################
#                                             Function                                             #
####################################################################################################
def find_option(id: str, url: str=URL) -> list:
    list_options = []
    r = requests.get(url=url)
    soup = BeautifulSoup(r.text, 'lxml')
    options = soup.select(f'#{id} option')
    for opt in options:
        list_options.append(opt.text)
        
    return list_options


def find_value(id: str, url: str=URL) -> str:
    r = requests.get(url=url)
    soup = BeautifulSoup(r.text, 'lxml')
    
    return soup.select_one(f'#{id}')['value']



####################################################################################################
#                                               Main                                               #
####################################################################################################
### requests
ua = UserAgent()
list_years = find_option(id='ctl00_cphMain_ucDate_cboYear')[35:-1]
list_months = find_option(id='ctl00_cphMain_ucDate_cboMonth')
list_days = find_option(id='ctl00_cphMain_ucDate_cboDay')
list_hours = find_option(id='ctl00_cphMain_ucDate_cboHour')

# 循覽每個整點時間
for year in list_years:
    for month in list_months:
        for day in list_days:
            for hour in list_hours:
                print(f'year: {year}, month: {month}, day: {day}, hour: {hour}')

                # 檢查檔案是否已經出過，若有出過就跳過
                if os.path.exists(f'{DIR_RAW_DATA}/防汛重點水庫_{year}_{month}_{day}_{hour}.csv'):
                    print('File Exist. Jump!')
                    continue

                user_agent = ua.random
                time.sleep(random.randint(1, 2))
                
                # 若爬蟲成功則繼續，若爬蟲失敗則重爬
                again = True
                times = 0
                while (again) and (times < 5):
                    try:
                        data = {
                            'ctl00$cphMain$cboSearch': '防汛重點水庫',
                            'ctl00$cphMain$ucDate$cboYear': year,
                            'ctl00$cphMain$ucDate$cboMonth': month,
                            'ctl00$cphMain$ucDate$cboDay': day,
                            'ctl00$cphMain$ucDate$cboHour': hour,
                            'ctl00$cphMain$ucDate$cboMinute': 0,
                            '__VIEWSTATE': find_value(id='__VIEWSTATE'),
                            '__EVENTVALIDATION': find_value(id='__EVENTVALIDATION'),
                            '__VIEWSTATEGENERATOR': find_value(id='__VIEWSTATEGENERATOR'),
                            '__EVENTTARGET': 'ctl00$cphMain$btnQuery'
                            }

                        r = requests.post(url=URL, headers={'user-agent': user_agent}, data=data)

                        ### BeautifulSoup
                        soup = BeautifulSoup(r.text, 'lxml')

                        # # Get Option
                        # options = [op.text for op in list(soup.select('option')) if 'selected' in str(op)]
                        # print(options)
                        # print(r.headers)

                        ### Data arrange
                        table = soup.select_one('table')
                        df = pd.read_html(table.prettify())[0]
                        # 整理欄位名稱
                        columns = [col[2] for col in df.columns]
                        df.columns = columns
                        for col in df.columns:
                            if 'Unnamed'in col:
                                del df[col]
                            # else:
                            #     df = df.rename(columns={col: col.replace(' ', '')})
                        df.columns = [
                            '水庫名稱', '水情時間', '本日集水區累積降雨量(mm)', '進流量(cms)', '水位(公尺)', '滿水位(公尺)',
                            '有效蓄水量(萬立方公尺)', '蓄水百分比(%)', '取水流量(cms)', '發電放水口', '排砂道/PRO', '排洪隧道',
                            '溢洪道', '其他', '小計', '目前狀態', '預定時間', '預定放流量(cms)'
                        ]
                        # 去掉附註列
                        df = df.drop(df.loc[df['水庫名稱'] == '附註'].index, axis=0)
                        df = df.fillna('--')

                        ### Output csv
                        df.to_csv(f'{DIR_RAW_DATA}/防汛重點水庫_{year}_{month}_{day}_{hour}.csv', index=False, encoding='utf-8-sig')
                        again = False

                    except:
                        again = True
                        times += 1
                        user_agent = ua.random
                        time.sleep(random.randint(1, 2))
