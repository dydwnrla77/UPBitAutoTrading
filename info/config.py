import configparser
import datetime
import os
import sys
import re


def config_setting(logger):
    abs_loc = os.path.dirname(os.path.abspath(__file__))
    file_loc = os.path.join(abs_loc, 'setting.ini')

    parser = configparser.ConfigParser()
    parser.read(file_loc, encoding='utf-8')

    buying_count = None
    stop_profit = None
    stop_loss = None
    finish_time = None
    condition_name = None
    slack_token = None
    slack_channel = None
    slack_mode = None

    try:
        buying_count = parser.get('TRADING', 'BUYING_COUNT')
        stop_profit = parser.get('TRADING', 'STOP_PROFIT')
        stop_loss = parser.get('TRADING', 'STOP_LOSS')
        finish_time = parser.get('TRADING', 'FINISH_TIME')
        condition_name = parser.get('TRADING', 'CONDITION_NAME')
        slack_token = parser.get('TRADING', 'SLACK_TOKEN')
        slack_channel = parser.get('TRADING', 'SLACK_CHANNEL')
        slack_mode = parser.get('TRADING', 'SLACK_MODE')
    except Exception as e:
        logger.debug(f'parsing error:{e}\nsetting.ini를 다시 확인하세요.')
        sys.exit()

    #validation
    config_validation(logger, buying_count, stop_profit, stop_loss, finish_time, condition_name, slack_token, slack_channel, slack_mode)

    buying_count = int(buying_count)
    stop_profit = float(stop_profit)
    stop_loss = float(stop_loss)

    today = datetime.datetime.today()
    hour, minute = finish_time.split(':')
    finish_time = datetime.datetime(today.year, today.month, today.day, hour=int(hour), minute=int(minute))
    market_start_time = datetime.datetime(today.year, today.month, today.day, hour=9, minute=0)
    market_end_time = datetime.datetime(today.year, today.month, today.day, hour=15, minute=15)

    if finish_time < market_start_time or finish_time > market_end_time:
        finish_time = datetime.datetime(today.year, today.month, today.day, hour=15, minute=15)

    return buying_count, stop_profit, stop_loss, finish_time, condition_name, slack_token, slack_channel, slack_mode


def config_validation(logger, buying_count, stop_profit, stop_loss, finish_time, condition_name, slack_token, slack_channel, slack_mode):
    buying_count = int(buying_count)
    stop_profit = int(stop_profit)
    stop_loss = int(stop_loss)

    if buying_count <= 0 or buying_count > 5:
        logger.info('갯수를 5개 이하로 지정해주세요.')
        sys.exit()

    elif (stop_profit <= 0 or stop_profit > 30) or (stop_loss <= 0 or stop_loss > 30):
        logger.info('익절율, 손절율은 양수로 설정해주세요. (1 ~ 30)')
        sys.exit()

    elif finish_time != '':
        reg = re.compile(r'\d{2}:\d{2}')
        result = reg.match(finish_time)

        if result is None:
            logger.info('종료시간을 00:00 타입으로 작성해주세요.')
            sys.exit()

    elif condition_name == '':
        logger.info('키움증권에 등록한 조건검색 명을 입력해주세요.')
        sys.exit()

    elif slack_token == '' or slack_channel == '':
        logger.info('slack token, slack channel을 입력해주세요.')
        sys.exit()

    elif slack_mode not in ['on', 'off']:
        logger.info('slack mode는 on 또는 off만 가능합니다.')
        sys.exit()

