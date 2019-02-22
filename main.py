import sys
import csv
import urllib.request
import xml.etree.ElementTree as ET
import lxml
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import os
from os.path import join, dirname
from dotenv import load_dotenv
import logging
from logging import getLogger, StreamHandler, DEBUG, Formatter
from time import sleep


####ログの設定####
logger = logging.getLogger(__name__)
#ファイルに出力
file_handler = logging.FileHandler('geocoding.log', encoding='utf-8')
file_handler.setLevel(DEBUG)
fhandler_format = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(fhandler_format)
#ターミナルに出力
terminal_handler = logging.StreamHandler()
terminal_handler.setLevel(DEBUG)
thandler_format = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
terminal_handler.setFormatter(thandler_format)

logger.setLevel(DEBUG)
logger.addHandler(file_handler)
logger.addHandler(terminal_handler)
logger.propagate = False


def main():
    if len(sys.argv) != 3:
        logger.error('usage: ./main.py <input_csv_file> <output_csv_file>')
        exit()

    #入力されたファイルからイエローページID、住所を取得
    inputdata = list(csv.reader(open(sys.argv[1], 'r', encoding="utf-8_sig")))
    yp_id = []
    address_list = []
    #入力ファイルの一行目に名前がついている場合はfor文のinputdataのあとに[1:]を加える
    for corp in inputdata:
        yp_id.append(corp[0])
        address_list.append(corp[5] + corp[6] + corp[7])

    #geocodingAPIに住所を投げて緯度経度を得る
    lat_lng_info = []
    good_count = 0 #正常に終了の数
    bad_count = 0  #異常ありの数
    index_num = 0 #その合計
    ver_num = 1.2 #geocodingAPIのバージョン。2019/02/21時点で1.2が最新

    for address in address_list:
        req = urllib.request.Request("https://www.geocoding.jp/api/?v=" + str(ver_num) +"&q=" + urllib.parse.quote(address))
        try:
            with urllib.request.urlopen(req) as response:
                XmlData = response.read()
        except urllib.error.HTTPError as err:
            logger.error('{0}  address:{1}'.format(err.code, address))
            bad_count += 1
            index_num += 1
            continue
        except urllib.error.URLError as err:
            logger.error('{0}  address:{1}'.format(err.reason, address))
            bad_count += 1
            index_num += 1
            continue

        #ここからパース。APIは緯度経度を度(DD)と度分秒(DMS)で返すが、度のほうをとってきている。
        #soup.<タグ名>.stringでタグに挟まれた部分を取る。
        soup = BeautifulSoup(XmlData, "xml")
        try:
            lat_lng_info.append([yp_id[index_num], address, soup.lat.string, soup.lng.string])
        except AttributeError:
            logger.error('AttributeError 不正な住所の可能性があります address:{}'.format(address))
            bad_count += 1
            continue
        index_num += 1
        good_count += 1
        logger.info('進捗：正常終了{0}件　異常{1}件'.format(good_count, bad_count))

        #APIの規定で5秒以上休止が必要
        sleep(5)

    #CSVファイルに出力
    #========windows encoding========#
    with open(sys.argv[2], 'w', newline='', encoding="utf-8_sig") as f:
        for lat_lng in lat_lng_info:
            writer = csv.writer(f)
            writer.writerow(lat_lng)

if __name__ == "__main__":
    main()