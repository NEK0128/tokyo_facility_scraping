from selenium import webdriver
from selenium.webdriver.support.ui import Select
import sys
import datetime
from collections import defaultdict
import json

class EmptySearch():
    def __init__(self, save_file):
        # ブラウザ起動
        self.driver = webdriver.PhantomJS()
        self.save_file = save_file
        self.weekday = ['（月）', '（火）', '（水）', '（木）', '（金）', '（土）', '（日）']


    def empty_search_by_dates(self, start, span):
        """
        利用日時から検索
        date（YYYYMMDD）からspan日分の空き状況をスクレープ
        """
        # クロール開始時刻を記述
        # 最後にデータまとめて書き込むのでも良いかも
        with open(self.save_file, "w") as f:
            f.write(datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S') + '\n'
                    + "https://yoyaku.sports.metro.tokyo.jp/user/view/user/homeIndex.html\n")

        # startからspan日分の空き状況をスクレープ
        date = datetime.datetime.strptime(start, "%Y%m%d")
        scraper.empty_search_by_date(date)
        for i in range(int(span)):
            date = date + datetime.timedelta(days=1)
            print(date)
            scraper.empty_search_by_date(date)


    def empty_search_by_date(self, search_date):
        """利用日時から検索を行うので、オムニとハードで2回検索しないといけない
        """
        self.empty_search_by_date_surface(search_date, 'omni')
        self.empty_search_by_date_surface(search_date, 'hard')


    def empty_search_by_date_surface(self, search_date, surface):
        """
        施設予約ページに飛んで利用日時から検索をクリックして、日時とサーフェス指定して検索
        """
        surface_idx = 2 if surface == "hard" else 3
        self.driver.get("https://yoyaku.sports.metro.tokyo.jp/user/view/user/homeIndex.html")
        self.driver.find_element_by_id("dateSearch").click()

        # 日時設定
        self.__set_date(search_date.year, search_date.month, search_date.day)

        self.driver.find_elements_by_id("purposeRadio")[surface_idx].click()
        self.driver.find_element_by_id("srchBtn").click()
        #print(self.driver.current_url, self.driver.title)

        # パース
        self.parse_empty_info_page(search_date)


    def parse_empty_info_page(self, search_date):
        """
        予約状況ページをパース
        結果が複数ページに渡る場合は遷移する
        """
        table = self.driver.find_elements_by_class_name("tablebg2")
        date = table[0].find_element_by_tag_name("b").text \
               + self.weekday[search_date.weekday()]

        # 結果に出てる施設の数で場合分け
        if len(table) == 1:
            print(date, "no result")
        elif 1 < len(table) <= 6:
            self.__parse_empty_info(date, table[1:])
        elif len(table) == 8:
            while(len(table[1].find_elements_by_id("goNextPager")) >= 1):
                #このページの飽き状況把握
                self.__parse_empty_info(date, table[2:-1])

                #次のページへ
                table[1].find_element_by_id("goNextPager").click()
                table = self.driver.find_elements_by_class_name("tablebg2")
        else:
            print("exception")



    def __parse_empty_info(self, date, facilities):
        """
        各施設毎の空き状況をパース
        """
        for facility in facilities:
            facility_name = facility.find_element_by_id("bnamem").text
            surface = facility.find_element_by_id("ppsname").text
            times = facility.find_elements_by_class_name("time-table1")
            empty_court_counts = facility.find_elements_by_id("emptyFieldCnt")

            # ファイルに書き出し
            for (time, empty_court_count) in zip(times, empty_court_counts):
                self.__save_empty_info(date, facility_name, surface, time.text, empty_court_count.text)
                print(date, facility_name, surface, time.text, empty_court_count.text)


    def __set_date(self, y, m, d):
        year = Select(self.driver.find_element_by_id("year"))
        year.select_by_value(str(y))
        month = Select(self.driver.find_element_by_id("month"))
        month.select_by_value(str(m))
        day = Select(self.driver.find_element_by_id("day"))
        day.select_by_value(str(d))
        s_hour = Select(self.driver.find_element_by_id("sHour"))

        # TODO: 0時0分から23時30分にしてしまうと、全ての時間で空いている施設しかとれない
        #       そこで、全ての時間で検索できるような何かを考えるべき
        #       種目から検索したほうが良い？
        s_hour.select_by_value("17")
        s_minute = Select(self.driver.find_element_by_id("sMinute"))
        s_minute.select_by_value("0")
        e_hour = Select(self.driver.find_element_by_id("eHour"))
        e_hour.select_by_value("18")
        e_minute = Select(self.driver.find_element_by_id("eMinute"))
        e_minute.select_by_value("0")


    def __del__(self):
        self.driver.quit()


    def __save_empty_info(self, date, facility_name, surface, time,
                          empty_court_count):
        with open(self.save_file, "a") as f:
            f.write(date + '\t' + facility_name + '\t' + surface + '\t' +
                    time + '\t' + empty_court_count + '\n')


if __name__ == "__main__":
    output = "/Users/takeda/work/tokyo_facility_resavation/empty_info.tsv"
    scraper = EmptySearch(output)
    scraper.empty_search_by_dates(sys.argv[1], sys.argv[2])

