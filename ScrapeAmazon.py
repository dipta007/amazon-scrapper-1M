import os
from sys import platform as _platform
from selenium import webdriver


def get_path_of_chrome_driver():
    path = os.path.join( os.getcwd() + "webdriver/", "chromedriver")
    if _platform == "linux" or _platform == "linux2":
        # linux
        path += "_linux"
    elif _platform == "darwin":
        # MAC OS X
        path += "_mac"
    elif _platform == "win32" or _platform == "win64":
        # Windows
        path += "_win"
    return path


driver = webdriver.Chrome(get_path_of_chrome_driver())
