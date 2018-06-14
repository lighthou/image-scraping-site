from selenium import webdriver 
from selenium.webdriver.common.keys import Keys 
from bs4 import BeautifulSoup
import re
import pandas
import os
import sys
from urllib.request import urlretrieve
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
    dic, width, height = break_image_to_rgb("UPLOADS/" + uploaded_file.filename)
    width = width * 10
    height = height * 10
    
    images_on_side = 100

    
    im = Image.new("RGB", (width, height))
    pix = im.load()
    for (key, value) in dic.items():
        for x in range(width // images_on_side * key[0], (width // images_on_side) * (key[0] + 1)):
            for y in range (height // images_on_side * key[1], (height // images_on_side) * (key[1] + 1)):
                pix[x,y] = value
                
    im.save("test.png", "PNG")


    
    processed_text = text.upper()
    #scrape_images(text, dic)
    return processed_text


def break_image_to_rgb(image):
    photo = Image.open(image)
    photo = photo.convert('RGB')
    photo_dictionary = {}
    width, height = photo.size
    x_y_image_count = 100
    divider = (width/x_y_image_count) * (height/x_y_image_count)
    for y in range (0, x_y_image_count):
        for x in range(0, x_y_image_count):
            tr, tg, tb = 0, 0, 0
            for y1 in range(round(height/x_y_image_count * y), round(height / x_y_image_count * (y+1))):
                for x1 in range(round(width/x_y_image_count * x), round(width / x_y_image_count * (x+1))):
                    if x1 < width and y1 < height:
                        r, g, b = photo.getpixel((x1, y1))
                        tr, tg, tb = tr + r, tg + g, tb + b
            photo_dictionary[x, y] = min(255, int(tr/divider)), min(int(tg/divider), 255), min(255, int(tb/divider))
    return photo_dictionary, width, height
            

def rgb_of_whole_img(image):
    photo = Image.open(image)
    photo = photo.convert('RGB')
    width, height = photo.size
    divider = width * height

    tr, tg, tb = 0, 0, 0
    for y in range(0, height):
        for x in range(0, width):
            r, g, b = photo.getpixel((x1, y1))
            tr, tg, tb = tr + r, tg + g, tb + b
    return min(255, int(tr/divider)), min(int(tg/divider), 255), min(255, int(tb/divider))
                                                     

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
            img_name = keyword + "/" + keyword + "_" + str(count) +".png"
            count += 1
            urlretrieve(img_url, img_name)
            #r,g,b = rgb_of_whole_img(img_name)
            
    

if __name__ == "__main__":
    app.run()






































                                                                     
