from urllib.parse import urlencode
import requests
from lxml import etree
import re
import pymysql

TABLE = 'douban_movie_top_250'
HOST = 'localhost'
USER = 'root'
PASSWORD = 'abc123456'
PORT = 3306
DATABASE = 'spiders'


def movie_url():
    base_url = 'https://movie.douban.com/top250?'
    movies_url = []
    for start_num in range(0, 226, 25):
        params = {
            'start': start_num,
            'filter': '',
        }
        url = base_url + urlencode(params)
        movies_url.append(url)
    return movies_url


def get_message(url):
    headers = {
        'User-Agent': 'Mozilla/5.0(Macintosh; Intel Mac Os X 10_11_4) AppleWebKit/537.36 (KHML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'}
    response = requests.get(url, headers=headers).text
    html = etree.HTML(response)
    sectors = html.xpath('//*[@id="content"]//li')
    for movie_content in sectors:
        firt_starring = re.findall(
            r'主演: (.*?)\/',
            movie_content.xpath('normalize-space(.//div[@class="bd"]/p/text())'))
        second_starring = re.findall(
            r'主演: (.*?)\.\.\.',
            movie_content.xpath('normalize-space(.//div[@class="bd"]/p/text())'))
        if firt_starring:
            starring = firt_starring[0]
        elif second_starring:
            starring = second_starring[0]
        else:
            starring = '未列出'
        first_director = re.findall(
            '导演: (.*?)\xa0',
            movie_content.xpath('normalize-space(.//div[@class="bd"]/p/text())'))
        second_director = re.findall(
            r'导演: (.*?)\/',
            movie_content.xpath('normalize-space(.//div[@class="bd"]/p/text())'))
        if first_director:
            director = first_director
        elif second_director:
            director = second_director
        else:
            director = '未列出'
        data = {
            'Title': movie_content.xpath('normalize-space(.//div[@class="hd"]//span[@class="title"]/text())'),
            'Director': director,
            'Starring': starring,
            'Star': movie_content.xpath('.//div[@class="bd"]/div[@class="star"]/span[@class="rating_num"]/text()')[0]
        }
        save_to_mysql(data)


def save_to_mysql(data):
    db = pymysql.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        port=PORT,
        db=DATABASE)
    data_keys = ', '.join(data.keys())
    data_values = ', '.join(['%s'] * len(data))
    cursor = db.cursor()
    sql = 'INSERT INTO {table}({keys}) VALUES ({values}) ON DUPLICATE KEY UPDATE'.format(
        table=TABLE, keys=data_keys, values=data_values)
    update = ','.join([" {key} = %s".format(key=key) for key in data])
    sql += update
    cursor.execute(sql, tuple(data.values()) * 2)
    db.commit()
    print(f'{data} update success !')


if __name__ == '__main__':
    movie_url_list = movie_url()
    for movie_url in movie_url_list:
        get_message(movie_url)
