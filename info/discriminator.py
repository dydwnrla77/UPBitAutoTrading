import requests
import datetime


def is_holiday(logger):
    code_url = 'http://open.krx.co.kr/contents/OPN/99/OPN99000001.jspx'
    code_params = {
        'search_bas_yy': '2021',
        'gridTp': 'KRX',
        'pagePath': '/contents/MKD/01/0110/01100305/MKD01100305.jsp',
        'code': 'vsK/ukjD04bVNJ59wnhq3lDNH0TzZyMqMZXGUFTAefEfHDe6dyTHjGQro+Rh2hW5vJodBa4twaVMGERCg41Mhh65mwP/R/A0UOAsY12A0G/c1JirJs0JF8Uux3TTnQ1zWTDLAh01V7j5F5PRNVcUSLBsYRJHOltdMbAwOXrNXGnPRL3Gy6dY5CHr/AfBCANp'
    }

    response = None

    try:
        code_response = requests.post(url=code_url, data=code_params)
        code_result = eval(code_response.content.decode())
        response = code_result['block1']
    except Exception as e:
        logger.debug(f'error:{e}')

    holiday_list = list(map(lambda x: x['calnd_dd_dy'], response))

    today = datetime.datetime.today()
    today_str = today.strftime('%Y-%m-%d')

    if today_str in holiday_list or today.weekday() == 5 or today.weekday() == 6:
        return True

    return False

