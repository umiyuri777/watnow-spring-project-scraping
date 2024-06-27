import requests
from bs4 import BeautifulSoup
import urllib
import json
from pydantic import BaseModel
from typing import Tuple
from typing import Union

class Coordinate(BaseModel):
    coordinate: Union[Tuple[float, float], Tuple[None, None]]     # tuple[float, float] = [lng, lat]

LNG_ROW = 1
LAT_ROW = 0

def get_location(izakaya_address : str)-> Coordinate:
    coordinate_api_url = "https://msearch.gsi.go.jp/address-search/AddressSearch?q="
    s_quote = urllib.parse.quote(izakaya_address)
    api_response = requests.get(coordinate_api_url + s_quote)
    if api_response.text:
        try:
            tmp_coordinate = api_response.json()[0]["geometry"]["coordinates"] # type: Tuple[float, float] # [lat, lng] 緯度経度逆になってる
            coordinate = Coordinate(
                coordinate=(
                    tmp_coordinate[LNG_ROW],
                    tmp_coordinate[LAT_ROW]
                )
            )

        except json.decoder.JSONDecodeError:
            print("Invalid JSON received:", response.text)
            coordinate = Coordinate(
                coordinate=(None, None)
            )

    else:
        print("No response received")
        coordinate = Coordinate(
            coordinate=(None, None)
        )

    return coordinate

id = 1

# ファイルを開く
f = open('example.csv', 'w', encoding='utf-8')
f.write('id,name,lat,lng,category,prompt,photo_url,address,izakaya_url\n')

# ページ数を取得
ibaraki_izakaya_url = f"https://www.hotpepper.jp/SA23/Y356/G001_G012/net1/bgn1/"
# ページにアクセス
response = requests.get(ibaraki_izakaya_url)
response.encoding = response.apparent_encoding

# BeautifulSoupでHTMLを解析
soup = BeautifulSoup(response.text, 'html.parser')
izakaya_page_elements = soup.find(class_='pageLinkLinearBasic cf').find_all('a')

if izakaya_page_elements[-1].text.strip() == "次へ":
    page_limit = int(izakaya_page_elements[-2].text.strip()) + 1
else:
    page_limit = int(izakaya_page_elements[-1].text.strip()) + 1

print(f"page_limit : {page_limit}")


for page_num in range(1, page_limit):

    # ホットペッパーグルメの茨木エリアの居酒屋、バーのURL
    ibaraki_izakaya_url = f"https://www.hotpepper.jp/SA23/Y356/G001_G012/net1/bgn{page_num}/"

    # ページにアクセス
    try:
        response = requests.get(ibaraki_izakaya_url)
        response.encoding = response.apparent_encoding
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        break

    # BeautifulSoupでHTMLを解析
    soup = BeautifulSoup(response.text, 'html.parser')

    # 居酒屋情報を取得
    izakaya_elements = soup.select('.shopDetailCoreInner.cf')
    for row_num, izakaya_info in enumerate(izakaya_elements):

        izakaya_detail_text = izakaya_info.find(class_='shopDetailText')

        # 店名を取得
        izakaya_name = izakaya_detail_text.find('a').text.replace("　", " ")
        izakaya_detail_page_url = izakaya_detail_text.find('a').get('href')

        # エリアを取得
        izakaya_area = izakaya_detail_text.find(class_ = "parentGenreName")

        if izakaya_area == None:
            izakaya_area = "None"
        else:
            izakaya_area = izakaya_area.text.replace(" ", "").replace("\n", "").replace("\r", "")

        # レビューを取得
        izakaya_review_content = requests.get(f"https://www.hotpepper.jp{izakaya_detail_page_url}report/")
        izakaya_review_content.encoding = izakaya_review_content.apparent_encoding
        izakaya_review_content_soup = BeautifulSoup(izakaya_review_content.text, 'html.parser')

        izakaya_review_text = izakaya_review_content_soup.find(class_="text")

        if izakaya_review_text == None:
            izakaya_review_text = "None"
        else:
            izakaya_review_text = izakaya_review_text.text.replace(",", " ").replace("\n", " ").replace("\r", " ")

        # 居酒屋の住所を取得
        izakaya_address_url = f"https://www.hotpepper.jp{izakaya_detail_page_url}"
        response = requests.get(izakaya_address_url)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        izakaya_address = soup.find(class_= "shopInfoDetail").find('address').text.strip().replace("〒", "").replace(" ", "").replace("\n", "").replace("\r", "")

        # 営業時間を取得
        izakaya_opening_hours = soup.find(class_= "shophour").text.strip().replace(" ", "").replace("\n", "").replace("\r", "")

        # 居酒屋の緯度経度を取得
        izakaya_coordinate = get_location(izakaya_address)

        image_url = izakaya_info.find('img').get('src')
        izakaya_tag = izakaya_info.find("p", class_='storeNamePrefix fcGray')
        if izakaya_tag == None:
            izakaya_tag = "None"
        else:
            izakaya_tag = izakaya_tag.text.replace("　", " ").replace("/", " ").replace(" ", " ").replace(",", " ")

        f.write(str(id))
        f.write(',')
        f.write(izakaya_name)
        f.write(',')
        f.write(str(izakaya_coordinate.coordinate[0]))
        f.write(',')
        f.write(str(izakaya_coordinate.coordinate[1]))
        f.write(',')
        f.write(izakaya_tag)
        f.write(',')
        f.write(izakaya_review_text)
        f.write(',')
        f.write(image_url)
        f.write(',')
        f.write(izakaya_address)
        f.write(',')
        f.write(izakaya_address_url)
        f.write('\n')
        id += 1
    
    print(f"page{page_num} success!")

# ファイルを閉じる
f.close()


print("file created successfully!")
