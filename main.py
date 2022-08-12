from pykiwoom.kiwoom import *
from info.config import *
from info.alarm import *
from info.discriminator import *
import logging
import datetime


if __name__ == '__main__':

    # 초기화
    logger = logging.getLogger(__name__)
    streamHandler = logging.StreamHandler()
    fileHandler = logging.FileHandler(filename='./record.txt',
                                      encoding='utf-8')
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)
    logger.setLevel(logging.DEBUG)

    kiwoom = Kiwoom()
    buying_count, stop_profit, stop_loss, finish_time, condition_name, slack_token, slack_channel, slack_mode = config_setting(logger)
    logger.info(f'[config]\n매수 갯수:{buying_count}\n익절율:{stop_profit}\n손절율:{stop_loss}\n매도 시간:{finish_time}\n조건검색명:{condition_name}')
    stock_account = None

    # 주식 휴장일 검사
    if is_holiday(logger):
        logger.info('휴장일입니다.')
        # sys.exit()

    # 키움 연결 검사
    while True:
        try:
            kiwoom.CommConnect(block=True)
            state = kiwoom.GetConnectState()

            if state == 0:
                print("미연결")
                print("재연결 중...")

            elif state == 1:
                text = '키움API 연결 완료'
                logger.info(text)
                slack_message(slack_channel, text, slack_token, slack_mode)

                account_num = kiwoom.GetLoginInfo("ACCOUNT_CNT")  # 전체 계좌수
                accounts = kiwoom.GetLoginInfo("ACCNO")  # 전체 계좌 리스트
                user_id = kiwoom.GetLoginInfo("USER_ID")  # 사용자 ID
                user_name = kiwoom.GetLoginInfo("USER_NAME")  # 사용자명

                stock_account = accounts[0]

                logger.info(f'account_num:{account_num}|accounts:{accounts[0]}|user_id:{user_id}|user_name:{user_name}')
                break

        except Exception as e:
            logger.debug(f'error:{e}')

    # 예수금 가져와서 종목 금액 비중 설정
    # 예수금이 즉각 반영안돼서 주문가능금액으로 가져옴
    df = kiwoom.block_request("opw00001",
                              계좌번호=stock_account,
                              비밀번호="",
                              비밀번호입력매체구분="00",
                              조회구분=2,
                              output="예수금상세현황",
                              next=0)

    print(type(df))
    print(df)
    deposit = df.loc[0]["100%종목주문가능금액"]
    deposit = int(deposit)
    logger.info(f'100%종목주문가능금액:{deposit}')

    # 저장된 조건으로 종목 선정
    kiwoom.GetConditionLoad()
    conditions = kiwoom.GetConditionNameList()
    print(conditions)

    buying_list = []

    for condition in conditions:
        if condition_name == condition[1]:
            condition_index = condition[0]
            buying_list = kiwoom.SendCondition("0101", condition_name, condition_index, 0)

    print(buying_list)

    # 검색된 종목 없으면 종료
    if len(buying_list) <= 0:
        logger.info('조건에 부합하는 종목이 없습니다.')
        sys.exit()


    # 지정한 매수 갯수만큼 거래량 기준으로 정렬하여 필터링
    buying_deposit = None

    if len(buying_list) > buying_count:
        buying_list = buying_list[0:buying_count]
        buying_deposit = deposit / buying_count

    elif len(buying_list) < buying_count:
        buying_deposit = deposit / len(buying_list)

    else:
        buying_deposit = deposit / buying_count

    print(f'buying deposit:{buying_deposit}')

    # 매수
    for stock_code in buying_list:
        df = None

        while True:
            df = kiwoom.block_request("opt10001",
                                      계좌번호=stock_account,
                                      종목코드=stock_code,
                                      output="주식기본정보",
                                      next=0)

            print(df)

            # 데이터가 안 들어올 경우
            if df.loc[0]['종목코드'] == '':
                continue

            break


        current_price = df.loc[0]['현재가']
        stock_name = df.loc[0]['종목명']
        print(f'종목명:{stock_name}|현재가:{current_price}')

        if '-' in current_price or '+' in current_price:
            current_price = current_price[1:]

        current_price = int(current_price)

        print(f'기호 제거 현재가:{current_price}')

        # 종목 정보에서 현재가의 상한가 기준으로 매수 갯수 세기
        market_price = current_price * 1.3
        buying_amount = buying_deposit // market_price
        buying_amount = int(buying_amount)

        kiwoom.SendOrder("시장가매수", "0101", stock_account, 1, stock_code, buying_amount, 0, "03", "")

        text = f'{stock_name} {buying_amount}주 시장가 매수 완료'
        logger.info(text)
        slack_message(slack_channel, text, slack_token, slack_mode)


    # 요청한 종목 매수 검사
    rest_flag = 0

    while True:
        if rest_flag == len(buying_list):
            print('요청 종목 체결 완료')
            break

        for code in buying_list:
            df = kiwoom.block_request("opt10075",
                                      계좌번호=stock_account,
                                      전체종목구분='0',
                                      매매구분='1',
                                      종목코드=code,
                                      체결구분='1',
                                      output="미체결",
                                      next=0)
            print(df)

            if df.iloc[0][0] == '':
                print('수신대기...')
                continue

            rest_amount = df.iloc[0]['미체결수량']
            rest_amount = int(rest_amount)
            print(rest_amount)

            if rest_amount <= 0:
                rest_flag = rest_flag + 1


            time.sleep(1)


    # 종목별 계좌 모니터링하며 매도
    today = datetime.datetime.today()
    start_time = datetime.datetime(today.year, today.month, today.day, hour=9, minute=0)

    while True:
        # 장 시작 후 매수되므로 시작까지 대기
        if today < start_time:
            print('장 시작 전...')
            time.sleep(1)
            continue

        df = kiwoom.block_request("opw00004",
                                  계좌번호=stock_account,
                                  비밀번호="",
                                  상장폐지조회구분="1",
                                  비밀번호입력매체구분="00",
                                  output="종목별계좌평가현황",
                                  next=0)

        df = df.set_index('종목코드')
        print(df)


        # 데이터가 안들어온 경우
        if df.iloc[0][1] == '':
            logger.info('보유 종목 X')
            break

        elif df.iloc[0][0] == df.iloc[0][1]:
            print('데이터 수신 대기 ...')
            time.sleep(1)
            continue


        # 매수한 모든 종목 손익율 모니터링, code 앞에 'A' 존재
        for code in df.index:
            rate = df.loc[code]['손익율']
            amount = df.loc[code]['보유수량']
            stock_name = df.loc[code]['종목명']
            rate = float(rate)
            amount = int(amount)
            print(f'{code}|{stock_name}|{amount}|{rate}')

            if datetime.datetime.today() >= finish_time or rate >= stop_profit or rate <= stop_loss:
                kiwoom.SendOrder("시장가매도", "0101", stock_account, 2, code[1:], amount, 0, "03", "")

                text = f'{stock_name} {amount}주 시장가 매도 완료'
                logger.info(text)
                slack_message(slack_channel, text, slack_token, slack_mode)


    # 일별 수익률 알림
    df = kiwoom.block_request("opt10074",
                              계좌번호=stock_account,
                              시작일자='20210501',
                              종료일자='20210530',
                              output="일자별실현손익",
                              next=0)

    profit = df.iloc[0]['당일매도손익']

    text = f'당일 손익:{profit}원\n프로그램을 종료합니다.'
    logger.info(text)
    slack_message(slack_channel, text, slack_token, slack_mode)
