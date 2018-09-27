
from flask import Flask, request, render_template
from PIL import Image
import os
import math
from urllib.request import urlretrieve
from bs4 import BeautifulSoup
from multiprocessing import Pool, Manager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

app = Flask(__name__)

color_dictionary = {}
mgr_color_dictionary = Manager().dict()
image_dictionary = Manager().dict()

RESIZED_HEIGHT_PARTITION = 0
RESIZED_WIDTH_PARTITION = 0
TOTAL_IMAGES_NEEDED = 0


@app.route('/')
def my_form():
    return render_template('my-form.html')


@app.route('/', methods=['POST'])
def my_form_post():
    global RESIZED_HEIGHT_PARTITION
    global RESIZED_WIDTH_PARTITION

    image_keyword = request.form['text']
    uploaded_file = request.files['file']
    uploaded_file.save(os.path.join("UPLOADS", uploaded_file.filename))
    print("Breaking down uploaded image...")
    photo_width, photo_height, pixels_per_width_image, pixels_per_height_image = break_image_to_rgb("UPLOADS/" + uploaded_file.filename)
    mgr_color_dictionary.update(color_dictionary)
    print("Done breaking down image.")

    IMAGE_SIZE_MULTIPLIER = 10
    constructed_photo_width = photo_width * IMAGE_SIZE_MULTIPLIER
    constructed_photo_height = photo_height * IMAGE_SIZE_MULTIPLIER
    RESIZED_WIDTH_PARTITION = pixels_per_width_image * IMAGE_SIZE_MULTIPLIER
    RESIZED_HEIGHT_PARTITION = pixels_per_height_image * IMAGE_SIZE_MULTIPLIER

    searches = ["", " pictures", " photos", " images", " pics", " photographs"]
    searches_with_key_words = []

    for word in searches:
        searches_with_key_words.append(image_keyword + word)

    with Pool(6) as p:
        p.map(scrape_images_by_keyword, searches_with_key_words)

    result = Image.new("RGB", (constructed_photo_width, constructed_photo_height))
    for (key, value) in image_dictionary.items():
        image = Image.open(key)
        for x_y in value:
            adjusted = (x_y[0] * RESIZED_WIDTH_PARTITION, x_y[1] * RESIZED_HEIGHT_PARTITION)
            result.paste(im=image, box=adjusted)

    result.save("result.png", "PNG")




    processed_text = image_keyword.upper()
    return processed_text


# want to break the image into rgb

def scrape_images_by_keyword(keyword):

    url = "http://google.com.au/search?q=" + keyword
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')  # Last I checked this was necessary.
    driver = webdriver.Chrome(executable_path='/usr/bin/chromedriver', chrome_options=options)
    driver.implicitly_wait(30)
    driver.get(url)

    images_button = driver.find_element_by_xpath("//*[text()='Images']")
    images_button.click()

    scroll(driver)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    alt = "Image result for " + keyword

    if not os.path.exists(keyword):
        os.makedirs(keyword)

    for img in soup.find_all('img', alt=alt):
        img_url = img.get('src')
        if img_url is None:
            img_url = img.get('data-src')

        if img_url is not None:
            img_name = keyword + "/temp.png"
            urlretrieve(img_url, img_name)
            temp_r, temp_g, temp_b = get_average_rgb(img_name)

            r, g, b = get_closest_rgb(int(temp_r), int(temp_g), int(temp_b), mgr_color_dictionary)
            if r is None:
                os.remove(img_name)
            else:
                rgb_name = keyword + "/" + str(r) + "," + str(g) + "," + str(b) + ".png"
                image_dictionary[rgb_name] = color_dictionary[(r, g, b)]
                mgr_color_dictionary.pop((r, g, b), None)

                percent=(len(color_dictionary.keys())-len(mgr_color_dictionary.keys()))/len(color_dictionary.keys())*100
                print(str(int(percent)) + "% of images sourced.")
                img = Image.open(img_name)
                img_resized = img.resize((RESIZED_WIDTH_PARTITION, RESIZED_HEIGHT_PARTITION))
                os.remove(img_name)
                img_resized.save(rgb_name)





def scroll(driver):
    SCROLL_PAUSE_TIME = 0.5

    last_height = driver.execute_script("return document.body.scrollHeight")
    saw_more = False

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            if saw_more:
                break

            see_more_results = driver.find_element_by_xpath("//input[@value='Show more results']");
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            if see_more_results.is_displayed():
                see_more_results.click()
            else:
                break

        last_height = new_height


def break_image_to_rgb(image):
    photo = Image.open(image)
    photo = photo.convert('RGB')
    photo_width, photo_height = photo.size

    width_image_count = 100
    height_image_count = 100

    pixels_per_width_image = int(math.ceil(photo_width / width_image_count))
    pixels_per_height_image = int(math.ceil(photo_height / height_image_count))

    pixels_in_section = pixels_per_width_image * pixels_per_height_image

    for width_image in range(width_image_count):
        for height_image in range(height_image_count):
            # for each image that we need to pull an RGB value for.
            
            temp_r, temp_g, temp_b = 0, 0, 0 # init base rgb values

            # for each pixel in the section specified
            for x in range(pixels_per_width_image * width_image, pixels_per_width_image * (width_image + 1)):
                for y in range(pixels_per_height_image * height_image, pixels_per_height_image * (height_image + 1)):
                    if x < photo_width and y < photo_height:
                        r, g, b = photo.getpixel((x, y))
                        temp_r, temp_g, temp_b = temp_r + r, temp_g + g, temp_b + b
                        
            r, g, b = int(temp_r / pixels_in_section), int(temp_g / pixels_in_section), int(temp_b / pixels_in_section)

            closest_rgb = get_closest_rgb(r, g, b, color_dictionary)
            if closest_rgb[0] is None:
                color_dictionary[(r, g, b)] = [(width_image, height_image)]
            else:
                color_dictionary[closest_rgb] += [(width_image, height_image)]

    return photo_width, photo_height, pixels_per_width_image, pixels_per_height_image


def get_closest_rgb(r, g, b, color_dic):
    if (r, g, b) in color_dic:
        return r, g, b

    for i in range(1, 10):
        for j in range(1, 10):
            for z in range(1, 10):
                if (r - i, g - j, b + z) in color_dic:
                    return r - i, g - j, b + z

                elif (r - i, g - j, b - z) in color_dic:
                    return r - i, g - j, b - z

                elif (r - i, g + j, b + z) in color_dic:
                    return r - i, g + j, b + z

                elif (r - i, g + j, b - z) in color_dic:
                    return r - i, g + j, b - z

                elif (r + i, g - j, b + z) in color_dic:
                    return r + i, g - j, b + z

                elif (r + i, g - j, b - z) in color_dic:
                    return r + i, g - j, b - z

                elif (r + i, g + j, b + z) in color_dic:
                    return r + i, g + j, b + z

                elif (r + i, g + j, b - z) in color_dic:
                    return r + i, g + j, b - z

    return None, None, None


def get_average_rgb(image):
    photo = Image.open(image)
    photo = photo.convert('RGB')
    width, height = photo.size
    divider = width * height

    temp_r, temp_g, temp_b = 0, 0, 0
    for y in range(0, height):
        for x in range(0, width):
            r, g, b = photo.getpixel((x, y))
            temp_r, temp_g, temp_b = temp_r + r, temp_g + g, temp_b + b
    return temp_r/divider, temp_g/divider, temp_b/divider


if __name__ == "__main__":
    app.run()


