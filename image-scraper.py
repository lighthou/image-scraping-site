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
import math

app = Flask(__name__)


@app.route('/')
def my_form():
    return render_template('my-form.html')


@app.route('/', methods=['POST'])
def my_form_post():
    text = request.form['text']
    uploaded_file = request.files['file']
    uploaded_file.save(os.path.join("UPLOADS", uploaded_file.filename))
    col_dic, width, height, width_par, height_par = break_image_to_rgb("UPLOADS/" + uploaded_file.filename)

    IMAGE_SIZE_MULTIPLIER = 10
    
    width = width * IMAGE_SIZE_MULTIPLIER
    height = height * IMAGE_SIZE_MULTIPLIER
    width_par = width_par * IMAGE_SIZE_MULTIPLIER
    height_par = height_par * IMAGE_SIZE_MULTIPLIER

    result = Image.new("RGB", (width, height))
##    
##    pix1 = result.load()
##    for (key, value) in col_dic.items():
##        for x_y in value:
##            for x in range(width_par * x_y[0], width_par * (x_y[0] + 1)):
##                for y in range (height_par * x_y[1], height_par * (x_y[1] + 1)):
##                    if (x < width and y < height): 
##                        pix1[x,y] = key
##                
##    result.save("result.png", "PNG")
    

    processed_text = text.upper()
    image_dic = scrape_images(text, width_par, height_par, col_dic)
    for (key, value) in image_dic.items():
        image = Image.open(key)
        for x_y in value:
            adjusted = (x_y[0] * width_par, x_y[1] * height_par)
            result.paste(im=image, box=adjusted)

    result.save("result.png", "PNG")
    
    return processed_text

def break_image_to_rgb(image):
    photo = Image.open(image)
    photo = photo.convert('RGB')
    color_dictionary = {}
    width, height = photo.size
    x_y_image_count = 100
    width_partition = math.ceil(width/x_y_image_count)
    height_paritition = math.ceil(height/x_y_image_count)
    divider = width_partition * height_paritition
    for y in range(x_y_image_count):
        for x in range(x_y_image_count):
            tr, tg, tb = 0, 0, 0
            for y1 in range(height_paritition * y, height_paritition * (y+1)):
                for x1 in range(width_partition * x, width_partition * (x+1)):
                    if x1 < width and y1 < height:
                        r, g, b = photo.getpixel((x1, y1))
                        tr, tg, tb = tr + r, tg + g, tb + b

            r, g, b = min(255, int(tr/divider)), min(int(tg/divider), 255), min(255, int(tb/divider))
            check_r_g_b(r, g, b, x, y, color_dictionary)
            
    return  color_dictionary, width, height, width_partition, height_paritition

def scrape_images(keyword, width, height, color_dictionary):
    image_dictionary = {}
    
    url = "http://google.com.au/search?q=" + keyword
    driver = webdriver.Chrome()
    driver.implicitly_wait(30)
    driver.get(url)
    images_button = driver.find_element_by_xpath("//*[text()='Images']")
    images_button.click()

    soup = BeautifulSoup(driver.page_source, "html.parser")
    alt = "Image result for " + keyword


    #
    count = 0
    #
    
    if not os.path.exists(keyword):
        os.makedirs(keyword)

    for img in soup.find_all('img', alt=alt):
        img_url = img.get('data-src')
        if img_url is not None:
            img_name = keyword + "/temp.png"
            urlretrieve(img_url, img_name)
            r,g,b = rgb_of_whole_img(img_name)


            #Check here
            rgb_name = is_valid_rgb_for_image(r,g,b, color_dictionary, image_dictionary, keyword)
            if rgb_name == "":
                os.remove(img_name)
            else:
                #
                count +=1
                #

                os.rename(img_name, rgb_name)
                img = Image.open(rgb_name)
                img.thumbnail((width, height), Image.ANTIALIAS)
                img.save(rgb_name)

                if (count == 40):
                    return image_dictionary
                
    return image_dictionary


def is_valid_rgb_for_image(r,g,b, color_dictionary, image_dictionary, keyword):
    
    if((r,g,b) in color_dictionary):
        img_name = keyword + "/" + str(r) + "," + str(g) + "," + str(b) + ".png"
        image_dictionary[img_name] = color_dictionary[(r,g,b)]
        color_dictionary.pop((r,g,b), None)
        return img_name
    
    for i in range(10):
        for j in range(10):
            for z in range(10):
                if ((r - i,g - j,b + z) in color_dictionary):
                    img_name = keyword + "/" + str(r - i) + "," + str(g - j) + "," + str(b + z) + ".png"
                    image_dictionary[img_name] = color_dictionary[(r - i,g - j,b + z)]
                    color_dictionary.pop((r - i,g - j,b + z), None)
                    return img_name
                elif ((r - i,g - j,b - z) in color_dictionary):
                    img_name = keyword + "/" + str(r - i) + "," + str(g - j) + "," + str(b - z) + ".png"
                    image_dictionary[img_name] = color_dictionary[(r - i,g - j,b - z)]
                    color_dictionary.pop((r - i,g - j,b - z), None)
                    return img_name
                elif ((r - i,g + j,b + z) in color_dictionary):
                    img_name = keyword + "/" + str(r - i) + "," + str(g + j) + "," + str(b + z) + ".png"
                    image_dictionary[img_name] = color_dictionary[(r - i,g + j,b + z)]
                    color_dictionary.pop((r - i,g + j,b + z), None)
                    return img_name
                elif ((r - i,g + j,b - z) in color_dictionary):
                    img_name = keyword + "/" + str(r - i) + "," + str(g + j) + "," + str(b - z) + ".png"
                    image_dictionary[img_name] = color_dictionary[(r - i,g + j,b - z)]
                    color_dictionary.pop((r - i,g + j,b - z), None)
                    return img_name
                elif ((r + i,g - j,b + z) in color_dictionary):
                    img_name = keyword + "/" + str(r + i) + "," + str(g - j) + "," + str(b + z) + ".png"
                    image_dictionary[img_name] = color_dictionary[(r + i,g - j,b + z)]
                    color_dictionary.pop((r + i,g - j,b + z), None)
                    return img_name
                elif ((r + i,g - j,b - z) in color_dictionary):
                    img_name = keyword + "/" + str(r + i) + "," + str(g - j) + "," + str(b - z) + ".png"
                    image_dictionary[img_name] = color_dictionary[(r + i,g - j,b - z)]
                    color_dictionary.pop((r + i,g - j,b - z), None)
                    return img_name
                elif ((r + i,g + j,b + z) in color_dictionary):
                    img_name = keyword + "/" + str(r + i) + "," + str(g + j) + "," + str(b + z) + ".png"
                    image_dictionary[img_name] = color_dictionary[(r + i,g + j,b + z)]
                    color_dictionary.pop((r + i,g + j,b + z), None)
                    return img_name
                elif ((r + i,g + j,b - z) in color_dictionary):
                    img_name = keyword + "/" + str(r + i) + "," + str(g + j) + "," + str(b - z) + ".png"
                    image_dictionary[img_name] = color_dictionary[(r + i,g + j,b - z)]
                    color_dictionary.pop((r + i,g + j,b - z), None)
                    return img_name
    return ""
    

def check_r_g_b(r,g,b,x,y, color_dictionary):
    if((r,g,b) in color_dictionary):
        color_dictionary[(r,g,b)] += [(x,y)]
        return
    
    for i in range(10):
        for j in range(10):
            for z in range(10):
                if ((r - i,g - j,b + z) in color_dictionary):
                    color_dictionary[(r - i,g - j,b + z)] += [(x,y)]
                    return
                elif ((r - i,g - j,b - z) in color_dictionary):
                    color_dictionary[(r - i,g - j,b - z)] += [(x,y)]
                    return
                elif ((r - i,g + j,b + z) in color_dictionary):
                    color_dictionary[(r - i,g + j,b + z)] += [(x,y)]
                    return
                elif ((r - i,g + j,b - z) in color_dictionary):
                    color_dictionary[(r - i,g + j,b - z)] += [(x,y)]
                    return
                elif ((r + i,g - j,b + z) in color_dictionary):
                    color_dictionary[(r + i,g - j,b + z)] += [(x,y)]
                    return
                elif ((r + i,g - j,b - z) in color_dictionary):
                    color_dictionary[(r + i,g - j,b - z)] += [(x,y)]
                    return
                elif ((r + i,g + j,b + z) in color_dictionary):
                    color_dictionary[(r + i,g + j,b + z)] += [(x,y)]
                    return
                elif ((r + i,g + j,b - z) in color_dictionary):
                    color_dictionary[(r + i,g + j,b - z)] += [(x,y)]
                    return
    
    color_dictionary[(r,g,b)] = [(x,y)]
    
def rgb_of_whole_img(image):
    photo = Image.open(image)
    photo = photo.convert('RGB')
    width, height = photo.size
    divider = width * height

    tr, tg, tb = 0, 0, 0
    for y in range(0, height):
        for x in range(0, width):
            r, g, b = photo.getpixel((x, y))
            tr, tg, tb = tr + r, tg + g, tb + b
    return min(255, int(tr/divider)), min(int(tg/divider), 255), min(255, int(tb/divider))

if __name__ == "__main__":
    app.run()






































                                                                     
