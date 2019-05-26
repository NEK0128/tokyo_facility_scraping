# 東京都施設予約クローラー
* python3系 + selenium + phantomjs

```
# python scrape.py <date> <span>`
`ipython scrape.py `date '+%Y%m%d'` 10`
```

* cron
```
PATH=$PATH:/usr/local/bin
LANG=ja_JP.UTF-8

*/5 * * * * /Users/takeda/.anyenv/envs/pyenv/versions/3.4.0/bin/python /Users/takeda/work/tokyo_facility_resavation/scrape.py `/bin/date '+\%Y\%m\%d'` 20 > /Users/takeda/work/tokyo_facility_resavation/log
```
# tokyo_facility_scraping
