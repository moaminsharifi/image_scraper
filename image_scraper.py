"""
Search Engines Image Scraper

Licensed under the MIT License (see LICENSE for details)
Written by Amin Sharifi bigmpc@github.com
------------------------------------------------------------
Check Readme.md file 
"""
from selenium import webdriver
import time
import requests
import shutil
import os
import numpy as np
import cv2

############################################################
#  Config Class
############################################################
class Scraper_Config:

    def __init__(self,
                 SEARCH_QUERY = '',
                 NUMBER_OF_PICTURES = 5,
                 IMAGE_RATIO = (16, 9),
                 IMAGE_SIZE = (200 , 100),
                 CHECK_RATIO_AND_RESIZE = False,
                 EPSILON_RATIO_ERROR = 0.5 ,
                 MAKE_GRAY = False,
                 SEARCH_ENGINE_TYPE='duckduckgo',
                 MINIMUM_ELEMENT_ERROR = 0.2,
                 SLEEP_TIME = 0,
                 SCROLL_PAUSE_TIME = 2):
        """ Create Deffualt Config
        Args:
            SEARCH_QUERY (str, optional): What is for search in browser. Defaults to ''.
            NUMBER_OF_PICTURES (int, optional): how much image you need. Defaults to 5.
            IMAGE_RATIO (tuple, optional): Image Ratio. Defaults to (16, 9).
            IMAGE_SIZE (tuple, optional): Image Size. Defaults to (200 , 100).
            CHECK_RATIO_AND_RESIZE (bool, optional): Change downlowed image. Defaults to False.
            EPSILON_RATIO_ERROR (float, optional): how much error between your and input image ratio . Defaults to 0.5.
            MAKE_GRAY (bool, optional): Make Gray image or no. Defaults to False.
            SEARCH_ENGINE_TYPE (str, optional): Search. Defaults to 'duckduckgo'.
            SLEEP_TIME (int, optional): check how much need to sleep between any action. Defaults to 0.
            SCROLL_PAUSE_TIME (int, optional): Pause between any scroll. Defaults to 0.5.
        """
        
        self.SEARCH_ENGINE_LIST = ['google', 'duckduckgo']

        """Check inputs
        """        
        assert (SEARCH_ENGINE_TYPE in self.SEARCH_ENGINE_LIST,
                f"enter valid search engine, {SEARCH_ENGINE_TYPE}")

        assert (NUMBER_OF_PICTURES  > 1, f"enter valid number for images")
        if CHECK_RATIO_AND_RESIZE:
            assert (IMAGE_RATIO[0] >= 1 and IMAGE_RATIO[1] >= 1 , "image ratio is invalid")
            assert (IMAGE_SIZE[0] >= 5 and IMAGE_SIZE[1] >= 5 , "image size is invalid")
            assert (EPSILON_RATIO_ERROR >= 0.1 , "at least must be greater than 0.1")
        
        assert (type(SLEEP_TIME) == int and SLEEP_TIME>= 0,
                "SLEEP_TIME must be int")
        assert (type(MAKE_GRAY) == bool, 'MAKE_GRAY must be boolean')
        
        assert (SCROLL_PAUSE_TIME >= 1 , ' scroll time at least must be 2 s')

        # Search Engine Setup
        self.SEARCH_ENGIN_TYPE = SEARCH_ENGINE_TYPE
        self.SEARCH_QUERY = SEARCH_QUERY
        self.GOOGLE_URL = f'https://www.google.com/search?q={SEARCH_QUERY}&source=lnms&tbm=isch&sa=X&ved=2ahUKEwie44_AnqLpAhUhBWMBHUFGD90Q_AUoAXoECBUQAw&biw=1920&bih=947'
        self.DUCKDUCKGO_URL = f'https://duckduckgo.com/?q={SEARCH_QUERY}&v207-1&iax=images&ia=images'
        self.SEARCH_ENGINE_DICT = {
            'google': self.GOOGLE_URL, 'duckduckgo': self.DUCKDUCKGO_URL}
        self.SLEEP_TIME = SLEEP_TIME
        self.SCROLL_PAUSE_TIME = SCROLL_PAUSE_TIME
        # Image Path and Count Setup
        self.NUMBER_OF_PICTURES =  max(5, NUMBER_OF_PICTURES)
        self.PATH_OF_THIS_FILE = os.path.abspath(os.getcwd())
        self.IMAGE_BASE_DIR = f'{self.PATH_OF_THIS_FILE}/images/{SEARCH_QUERY.replace(" ", "-")}'
        self.GOOGLE_CHROM_DRIVER_PATH = '/usr/bin/chromedriver'

        # Image Resize and Ratio Setup
        self.CHECK_RATIO_AND_RESIZE = CHECK_RATIO_AND_RESIZE
        self.IMAGE_SIZE = IMAGE_SIZE
        self.IMAGE_RATIO = IMAGE_RATIO
        self.IMAGE_RATIO_PERSENT = IMAGE_RATIO[0] / IMAGE_RATIO[1]
        self.EPSILON_RATIO_ERROR = EPSILON_RATIO_ERROR
        self.MAKE_GRAY = MAKE_GRAY
        self.MINIMUM_ELEMENT_ERROR = MINIMUM_ELEMENT_ERROR
        self.MINIMUM_EMELMET = NUMBER_OF_PICTURES + NUMBER_OF_PICTURES * MINIMUM_ELEMENT_ERROR
        # Image Elemnt
        self.HTML_EMELMT_CLASS_NAME = 'tile--img__media'
       
    def set_SEARCH_QUERY(self):
        self.SEARCH_QUERY  = input('Enter Query to search:  ')
        self.GOOGLE_URL = f'https://www.google.com/search?q={self.SEARCH_QUERY}&source=lnms&tbm=isch&sa=X&ved=2ahUKEwie44_AnqLpAhUhBWMBHUFGD90Q_AUoAXoECBUQAw&biw=1920&bih=947'
        self.DUCKDUCKGO_URL = f'https://duckduckgo.com/?q={self.SEARCH_QUERY}&v207-1&iax=images&ia=images'
    

    def get_url(self):
       return self.SEARCH_ENGINE_DICT[self.SEARCH_ENGIN_TYPE]


############################################################
#  Image_Scraper Class
############################################################
class Image_Scraper:
  
    def __init__(self , custom_config = False):
        """init Image Scraper class
        Args:
            custom_config (bool, optional): check it use custom config or must be create one. Defaults to False.
        """       
        
        # create 
        
        if False == custom_config:
            self.config = Scraper_Config()
            self.config.set_SEARCH_QUERY()
        else:
            self.config = custom_config
        attrs = vars(self.config)

        print("############# CONFIGS       ##########")
        print(' '.join("%s: %s \n" % item for item in attrs.items()))
        print("############# ############# ##########")
        

        self.preper_dir()
        self.browser = webdriver.Chrome()
        self.verbose = True
        self.counter = 1

    def preper_dir(self):
        if not os.path.exists(self.config.IMAGE_BASE_DIR):
            os.mkdir(self.config.IMAGE_BASE_DIR)
            print(f" path {self.config.IMAGE_BASE_DIR} created")


    def resize_recolor_reratio(self, image , image_name = ''):
        """Resize and check rotarion

        Args:
            image (image , numpy ndarray): image
            image_name (str, optional): image name. Defaults to ''.

        Returns:
            numpy nd array: output image
        """        
        
        h, w, c = image.shape
        # check image is valid for save or no
        if w / h - self.config.EPSILON_RATIO_ERROR < self.config.IMAGE_RATIO_PERSENT:
            # 
            self.log_it(f"image {image_name} is ok for resize")
            # make resize image
            image = cv2.resize(
                image, self.config.IMAGE_SIZE, interpolation=cv2.INTER_AREA)
            # make grayscale image
            if self.config.MAKE_GRAY:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
        else:
            image = False

        return image

    def save_image(self , image , image_name = ''):
        """save image into file

        Args:
            image (nd numpy array): image array
            image_name (str, optional): file nanme. Defaults to ''.
        """        
        image_path = f'{self.config.IMAGE_BASE_DIR}/{image_name}.jpg'
        cv2.imwrite(image_path, image)
        


    def download_image(self , image_url):
        """download image from url

        Args:
            image_url (str): image url

        Returns:
            nd numpy: image as numpy array
        """        
        self.log_it(f"now downloading {image_url} url ")
        # download image 
        responce = requests.get(image_url, stream=True).raw
        # convert image as 1d array
        image = np.asarray(bytearray(responce.read()), dtype="uint8")
        # convert 1d array as 3d array or image
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        return image

    def log_it(self , input_string):
        """log and print 

        Args:
            input_string (str): string for print
        """        
        if self.verbose:
            print(input_string)

        
    def scrap(self , verbose = True):
        """Main functionality

        Args:
            verbose (bool, optional): If True print process. Defaults to True.

        
        """        
        # reset
        assert (type(verbose) == bool , "verbose must be boolean")
        start_time = time.time()
        self.verbose = verbose
        # open url in browser
        self.browser.get(self.config.get_url())
        self.log_it(f" url {self.config.get_url()}")
        last_height = self.browser.execute_script("return document.body.scrollHeight")
         

        # Check how much Element 
        
        #while True:
        #    pass
        
        last_height = self.browser.execute_script("return document.body.scrollHeight")
        
        while True:
            element_lenght  = len(self.browser.find_elements_by_class_name(self.config.HTML_EMELMT_CLASS_NAME))
            if element_lenght > self.config.MINIMUM_EMELMET :
                self.log_it(f"found {element_lenght} element in page and that's must be enough for Your dataset")
                break

            
            time.sleep(self.config.SCROLL_PAUSE_TIME)
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Calculate new scroll height and compare with last scroll height
            new_height = self.browser.execute_script("return document.body.scrollHeight")
           

            if new_height == last_height:
                if element_lenght < self.config.MINIMUM_EMELMET:
                    maximum_element = element_lenght if self.config.NUMBER_OF_PICTURES <= element_lenght else self.config.NUMBER_OF_PICTURES
                    self.log_it(f"""I achive at to end of page and there is {element_lenght} element
                this is {self.config.MINIMUM_EMELMET - element_lenght} lower than {self.config.MINIMUM_EMELMET} 
                I hope find good images :)""")
                break
            last_height = new_height
            
            
            


        for element in self.browser.find_elements_by_class_name(self.config.HTML_EMELMT_CLASS_NAME):
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            image_name = str(self.counter)
            # image url
            image_url = element.find_element_by_xpath(
                './/img').get_attribute("src")
            # if SLEEP_TIME greater than 0 then need to sleep some time :)
            if self.config.SLEEP_TIME > 0:
                time.sleep(self.config.SLEEP_TIME)
            
            try:
                # download image
                image = self.download_image(image_url)


                if self.config.CHECK_RATIO_AND_RESIZE:
                    image = self.resize_recolor_reratio(image, image_name)
                    # check return image as numpy
                    if type(image).__module__ == np.__name__:
                        self.save_image(image, image_name)
                else:
                    self.save_image(image, image_name)
                self.counter += 1

            except Exception:
                self.log_it(f" erorr for image {image_name} ")
            
            # for each 50 scroll page
            # https://stackoverflow.com/questions/20986631/how-can-i-scroll-a-web-page-using-selenium-webdriver-in-python
           
            
            if self.counter > self.config.NUMBER_OF_PICTURES:
                print(
                    f" process ended and download about {self.config.NUMBER_OF_PICTURES} image")
                break
        # close browser
        self.browser.close()
        print("--- %d seconds ---" % (time.time() - start_time))

            
############################################################
#  CLI
############################################################
if __name__ == "__main__":
    #
    import argparse
    parser = argparse.ArgumentParser(
        description='Download Image From Google or DuckDuckGo Search Engin')


    parser.add_argument('--qeury', required=True,
                        metavar="People",
                        help='Qeury for search in Search Engine')
    parser.add_argument('--amount', required=True,
                        default=5,
                        metavar="<amount>",
                        help='Amount of how much download data , default:5')
    args = parser.parse_args()
    # simple usage
    conf = Scraper_Config(args.qeury, int(args.amount))
    image_scraper = Image_Scraper(conf)
    image_scraper.scrap()

    
