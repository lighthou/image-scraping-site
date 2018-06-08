from selenium import webdriver 
from selenium.webdriver.common.keys import Keys 
from bs4 import BeautifulSoup
import re
import pandas
import os
import urllib
from flask import Flask, request, render_template

app = Flask(__name__)


@app.route('/')
def my_form():
    return render_template('my-form.html')


@app.route('/', methods=['POST'])
def my_form_post():
    text = request.form['text']
    processed_text = text.upper()
    get_to_images(text)
    return processed_text


def get_to_images(keyword):
    url = "http://google.com.au/search?q=" + keyword
    driver = webdriver.Chrome()
    driver.implicitly_wait(30)
    driver.get(url)
    images_button = driver.find_element_by_xpath("//*[text()='Images']")
    images_button.click()

    soup = BeautifulSoup(driver.page_source, "html.parser")
    alt = "Image result for " + keyword

    count = 0

    if not os.path.exists(keyword):
        os.makedirs(keyword)

    for img in soup.find_all('img', alt=alt):
        imgUrl = img.get('data-src')
        if imgUrl is not None:
            imgName = keyword + "/" + keyword + "_" + str(count)
            count += 1
            urllib.urlretrieve(imgUrl, imgName)


if __name__ == "__main__":
    app.run() 
