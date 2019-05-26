from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.support.ui import Select
import datetime
import json
import sys
import time
import argparse
import os
from spreadsheet_repository import SpreadsheetRepository

class EmptySearch():
    WEEKDAY = ['（月）', '（火）', '（水）', '（木）', '（金）', '（土）', '（日）']

    def __init__(self, credential_path, client_secret_path):
        # ブラウザ起動
        self.driver = webdriver.PhantomJS(service_log_path=os.path.devnull)
        # スプレッドシートAPIクライアント
        self.repository = SpreadsheetRepository(
            credential_path, client_secret_path
        )


    def empty_search_by_dates(self, start, span):
        """
        種目から検索
        date（YYYYMMDD）からspan日分の空き状況をスクレープ
        """
        # spreadsheetに書き込み始める位置
        self.rows = 2

        # 種目から検索のページへ移動
        self.driver.get("https://yoyaku.sports.metro.tokyo.jp/user/view/user/homeIndex.html")
        self.driver.find_element_by_id("purposeSearch").click()

        # オムニとハードをチェックして検索
        checkBtns = self.driver.find_elements_by_id('checked')
        checkBtns[2].click()
        checkBtns[3].click()
        self.driver.find_element_by_id("srchBtn").click()

        # startからspan日分の空き状況をスクレープ
        start_date = datetime.datetime.strptime(start, "%Y%m%d")
        for i in range(span):
            # dateの空き状況を表示するページへ移動（ページで使われているJSを利用）
            date = start_date + datetime.timedelta(days=i)
            self.driver.execute_script('selectCalendarDate({0}, {1}, {2});'
                                       .format(date.year, date.month, date.day))
            # JS実行と結果が返ってくるのを待つ
            time.sleep(3)

            # 結果をパースしてスプレッドシートに書き込み
            try:
                self.__update_sheet(self.parse_empty_info_page(date))
            except Exception as e:
                print(e)
                pass


    def parse_empty_info_page(self, search_date):
        """
        予約状況ページをパース
        結果が複数ページに渡る場合は遷移する
        """
        results = []
        table = self.driver.find_elements_by_class_name("tablebg2")
        date = table[0].find_element_by_tag_name("b").text \
               + EmptySearch.WEEKDAY[search_date.weekday()]
        print(date)
        # 結果に出てる施設の数で場合分け
        table_length = len(table)
        if table_length == 1:
            print(date, "no result")
        elif 1 < table_length <= 6:
            # 1ページしかない場合
            results.extend(self.__parse_empty_info(date, table[1:]))
        elif table_length == 8:
            # 複数ページある場合
            while(True):
                #このページの空き状況把握
                results.extend(self.__parse_empty_info(date, table[2:-1]))

                # 最後のページまでいったら終了
                if len(table[1].find_elements_by_id("goNextPager")) < 1:
                    break

                # 次のページへ
                table[1].find_element_by_id("goNextPager").click()
                table = self.driver.find_elements_by_class_name("tablebg2")
        else:
            print("予約状況ページパース失敗")

        return results


    def __parse_empty_info(self, date, facilities):
        """
        各施設毎の空き状況をパース
        """
        results = []
        for facility in facilities:
            facility_name = facility.find_element_by_id("bnamem").text
            surface = facility.find_element_by_id("ppsname").text
            times = facility.find_elements_by_class_name("time-table1")
            empty_court_counts = facility.find_elements_by_id("emptyFieldCnt")

            # 時間ごとに結果を格納したリストを作成
            result = [
                [datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                 date, facility_name, surface, time.text, empty_court_count.text]
                for time, empty_court_count in zip(times, empty_court_counts)
                if empty_court_count.text != '0'
            ]
            results.extend(result)

        return results


    def __update_sheet(self, data):
        """スプレッドシートを更新する。
        """
        # 更新がわかりやすいように空白行追加する
        data.extend([[''] * 6 for x in range(10)])
        self.repository.update(
            "1okZajm209ROu2a55xpvGApor5ErzxIlBdT4bBir1HvQ",
            "empty_info!A{}".format(self.rows),
            {"values": data}
        )
        self.rows += len(data) - 10


    def __del__(self):
        self.driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('start_date')
    parser.add_argument('fetch_days', type=int)
    parser.add_argument('credential_path')
    parser.add_argument('client_secret_path', nargs='?', default=None)
    args = parser.parse_args()

    # 20161103から30日間の空き状況を検索
    # python scrape_comp.py 20161103 30 ~/.credentials/sheets.googleapis.json client_secret.json
    scraper = EmptySearch(args.credential_path, args.client_secret_path)
    scraper.empty_search_by_dates(args.start_date, args.fetch_days)
