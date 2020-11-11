from selenium import webdriver
import numpy as np
from sklearn.preprocessing import normalize
from flask import Flask, render_template, request

model_fname = "/Users/vctr/PycharmProjects/untitled/lyric-movie-book.vecs"
app = Flask(__name__)


def search_doc_id(track_id):
   with open("Row-TrackID.txt", 'r', encoding='utf-8') as F:
      for line in F:
         if not line:
            continue
         row = line.split()

         if row[1] == str(track_id):
            num = int(row[0])
            return num


def get_track_id(track_title):
   # usd Firefox as a webdriver
   driver = webdriver.Firefox(executable_path='/Users/vctr/PycharmProjects/untitled/geckodriver')

   path = "https://vibe.naver.com/"

   # open webdriver
   driver.implicitly_wait(10)
   driver.get(path)

   # delete pop up
   driver.implicitly_wait(10)
   driver.find_element_by_xpath('//*[@id="app"]/div[2]/div/div/a').click()

   # click search button
   driver.find_element_by_xpath('//*[@id="app"]/div/header/a[1]').click()
   find = driver.find_element_by_xpath('/html/body/div[1]/div/header/div[1]/span/input')

   # delete data in search section
   find.clear()

   # input track title
   driver.implicitly_wait(10)
   find.send_keys(track_title)

   # push the enter button
   driver.implicitly_wait(10)
   find.send_keys('\n')

   # click the song category
   driver.implicitly_wait(10)
   driver.find_element_by_xpath('//*[@id="app"]/div/header/div[1]/div/ul/li[1]/a').click()

   # click the most high located song
   driver.implicitly_wait(10)
   driver.find_element_by_xpath('//*[@id="content"]/div[2]/h3/a').click()

   # get url from that song
   driver.implicitly_wait(10)
   url = driver.find_element_by_xpath(
      '//*[@id="content"]/div/div[4]/div[1]/div/table/tbody/tr[1]/td[3]/div[1]/span/a').get_attribute("href")

   # get title from that song
   driver.implicitly_wait(10)
   title = driver.find_element_by_xpath(
      '//*[@id="content"]/div/div[4]/div[1]/div/table/tbody/tr[1]/td[3]/div[1]/span/a').text.strip()
   title = ''.join(title)

   # remove url and get track id
   track_id = url.replace('https://vibe.naver.com/track/', '')

   # close webdriver
   driver.implicitly_wait(10)
   driver.close()

   return track_id, title


def load_movie(model_fname):
   movie_titles, movie_vectors, movie_urls, movie_imgs = [], [], [], []
   with open(model_fname, 'r', encoding='utf-8') as M:
      for num in range(len(M)):
         if 5958 <= num < 20622:
            m_title, m_vec, m_url, m_img = M[num].strip().split("\u241E")
            m_vector = [float(el) for el in m_vec.split()]
            movie_titles.append(m_title)
            movie_vectors.append(m_vector)
            movie_urls.append(m_url)
            movie_imgs.append(m_img)

   return movie_titles, normalize(movie_vectors, axis=1, norm='l2'), movie_urls, movie_imgs


def load_model(model_fname):
   titles, vectors = [], []
   with open(model_fname, 'r', encoding='utf-8') as L:
      for num in range(len(L)):
         if 20622 <= num:
            title, str_vec = L[num].strip().split("\u241E")
            vector = [float(el) for el in str_vec.split()]
            titles.append('https://vibe.naver.com/track/' + title)
            vectors.append(vector)

   return titles, normalize(vectors, axis=1, norm='l2')


def load_book(model_fname):
   book_titles, book_vectors, book_urls, book_imgs = [], [], [], []
   with open(model_fname, 'r', encoding='utf-8') as B:
      for num in range(len(B)):
         if 0 <= num < 5958:
            b_title, b_vec, b_url, b_img = B[num].strip().split("\u241E")
            b_vector = [float(el) for el in b_vec.split()]
            book_titles.append(b_title)
            book_vectors.append(b_vector)
            book_urls.append(b_url)
            book_imgs.append(b_img)

   return book_titles, normalize(book_vectors, axis=1, norm='l2'), book_urls, book_imgs


def most_similar(title, top_n):
   track_id, track_name = get_track_id(title)
   doc_id = search_doc_id(track_id)  # 트랙id에 대한 doc_id 구함
   query_doc_vec = L_vectors[doc_id]  # doc_id에 대한 임베딩 벡터 = query_doc_vec
   query_vec_norm = np.linalg.norm(query_doc_vec)  # query_doc_vec 정규화

   if query_vec_norm:
      query_unit_vec = query_doc_vec / query_vec_norm
   else:
      query_unit_vec = query_doc_vec

   m_scores = np.dot(M_vectors, query_unit_vec)  # 노래 트랙의 벡터와 전체 벡터를 내적하여 score구함. 여기서 영화 데이터랑
   b_scores = np.dot(B_vectors, query_unit_vec)
   l_scores = np.dot(L_vectors, query_unit_vec)

   l_result = sorted(zip(L_titles, l_scores), key=lambda x: x[1], reverse=True)[1:top_n + 1]  # 자기자신 제외
   m_result = sorted(zip(M_titles, M_url, M_img, m_scores), key=lambda x: x[3], reverse=True)[:top_n]
   b_result = sorted(zip(B_titles, B_url, B_img, b_scores), key=lambda x: x[3], reverse=True)[:top_n]

   return track_name, l_result, m_result, b_result


L_titles, L_vectors = load_model(model_fname)
M_titles, M_vectors, M_url, M_img = load_movie(model_fname)
B_titles, B_vectors, B_url, B_img = load_book(model_fname)

@app.route('/')
def search():
   return render_template('search.html')


@app.route('/result', methods=['POST', 'GET'])
def result():
   if request.method == 'POST':

      value = request.form.getlist('name')
      print("get value!")
      title, lyric, movie, book = most_similar(value[0], 5)

      print(value[0])
      return render_template("result.html", title=title, lyric=lyric, movie=movie, book=book)


if __name__ == '__main__':
    app.run()
