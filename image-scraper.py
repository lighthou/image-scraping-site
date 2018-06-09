from selenium import webdriver 
from selenium.webdriver.common.keys import Keys 
from bs4 import BeautifulSoup
import re
import pandas
import os
import urllib
from flask import Flask, request, render_template
from PIL import Image

app = Flask(__name__)


@app.route('/')
def my_form():
    return render_template('my-form.html')


@app.route('/', methods=['POST'])
def my_form_post():
    text = request.form['text']
    uploaded_file = request.files['file']
    uploaded_file.save(os.path.join("UPLOADS", uploaded_file.filename))
    break_image_to_rgb("UPLOADS/" + uploaded_file.filename)
    processed_text = text.upper()
    scrape_images(text)
    return processed_text


def break_image_to_rgb(image):
    photo = Image.open(image)
    photo = photo.convert('RGB')

    width, height = photo.size
    x_y_image_count = 100
    for y in range (0, x_y_image_count):
        for x in range(0, x_y_image_count):
            rgb_total = 0, 0, 0
            for y1 in range(height/x_y_image_count * y, (height / x_y_image_count) * (y+1)):
                for x1 in range(width/x_y_image_count * x, (width / x_y_image_count) * (x+1)):
                    r, g, b = photo.getpixel((x1, y1))
                    r1, g1, b1 = rgb_total
                    rgb_total = r + r1, g + g1, b + b1
            r, g, b = rgb_total
            x = height/x_y_image_count * width/x_y_image_count
            print(r/x, g/x, b/x)




def scrape_images(keyword):
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
        img_url = img.get('data-src')
        if img_url is not None:
            img_name = keyword + "/" + keyword + "_" + str(count)
            count += 1
            urllib.urlretrieve(img_url, img_name)


if __name__ == "__main__":
    app.run() 
