'''
Created on Sep 21, 2014

@author: rodrigo
'''

### Load libraries
from selenium import webdriver
from sqlalchemy import *
from configobj import ConfigObj
from datetime import datetime
from time import sleep
import os

### Load configuration
def load_config():
    settings_file = "../settings.conf"
    config = ConfigObj(settings_file)
    return config

### Create a WebDriver instance
def create_browser(mobile=None):
    #ff_profile = webdriver.FirefoxProfile("") # Set directory for profile here
    if mobile is not None:
        ff_profile.set_preference("general.useragent.override", "Mozilla/5.0 (iPhone; CPU iPhone OS 7_0 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11A465 Safari/9537.53")
    #browser = webdriver.Firefox(ff_profile) # Use an existing profile (set var above)
    browser = webdriver.Firefox() # Don't use a specific Firefox profile
    browser.set_page_load_timeout(60)
    if mobile is not None:
        browser.set_window_size(640,1136)
    elif mobile is None:
        browser.maximize_window()
    return browser

### Do some early work common to each script
def load_homepage(browser, pubshort, puburl):
    print("Firing up the browser so we can grab data for %s" % (pubshort))
    try:
        browser.get(puburl)
    except:
        print("Time exceeded")
        pass
    sleep(15)
    return

### Close the browser
def close_browser(browser):
    browser.quit()
    return

### Get current time
def get_curr_time(curr_time, parsefile):
    if parsefile is not None:
        curr_time = datetime.strptime(parsefile.rstrip(".html")[-12:], "%Y%m%d%H%M")
    else:
        try:
            if curr_time is not None:
                curr_time = datetime.strptime(curr_time, "%Y-%m-%d %H:%M")
        except:
            curr_time = None
        if curr_time is None:
            curr_time = datetime.utcnow()
    return curr_time

### Add common arguments
def add_common_arguments(parser):
    parser.add_argument("-c", "--curr_time", dest="curr_time", default=None, help="The current time (Optional, follows format 'YYYY-mm-dd HH:MM')")
    parser.add_argument("-dd", "--download_desktop", dest="download_desktop", default=1, type=int, help="Download desktop page? (Optional)")
    parser.add_argument("-dm", "--download_mobile", dest="download_mobile", default=0, type=int, help="Download mobile page? (Optional)")
    parser.add_argument("-p", "--parse", dest="parse", default=1, type=int, help="Parse page? (Optional)")
    parser.add_argument("-pf", "--parsefile", dest="parsefile", default=None, help="File to parse? (Optional)")
    return parser

### Write out to a file
def write_out_file(directory, filename, data):
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open("%s%s" % (directory, filename), "wt") as out_file:
        out_file.write(data)
    return

### Create a database connection
def create_mysql_engine(config):
    mysql_host = config["MySQL Settings"]["mysql_host"]
    mysql_username = config["MySQL Settings"]["mysql_username"]
    mysql_password = config["MySQL Settings"]["mysql_password"]
    mysql_database = config["MySQL Settings"]["mysql_database"]
    mysql_table_name = config["MySQL Settings"]["mysql_table"]
    mysql_log_name = config["MySQL Settings"]["mysql_log"]

    engine = create_engine('mysql+pymysql://' + mysql_username + ':' + mysql_password + '@' + mysql_host + '/' + mysql_database +'?charset=utf8&use_unicode=0') # connect to server
    connection = engine.connect()
    metadata = MetaData(engine)
    return(engine, connection, metadata, mysql_table_name, mysql_log_name)

def store_mysql_entry(mysql_table_name, metadata, pubshort, curr_time, story_1_link, story_2_link, story_3_link, story_4_link, story_5_link, mr_1_link, mr_2_link, mr_3_link, mr_4_link, mr_5_link):
    mysql_table = Table(mysql_table_name, metadata, autoload=True)
    insert_object = mysql_table.insert()
    insert_object.execute(
                         {'pubshort': pubshort,
                          'curr_time': curr_time,
                          'story_1_link': story_1_link,
                          'story_2_link': story_2_link,
                          'story_3_link': story_3_link,
                          'story_4_link': story_4_link,
                          'story_5_link': story_5_link,
                          'mr_1_link': mr_1_link,
                          'mr_2_link': mr_2_link,
                          'mr_3_link': mr_3_link,
                          'mr_4_link': mr_4_link,
                          'mr_5_link': mr_5_link}
                         )
    return

def store_mysql_log(mysql_log_name, metadata, pubshort, curr_time, event, status, message):
    mysql_log = Table(mysql_log_name, metadata, autoload=True)
    insert_object = mysql_log.insert()
    insert_object.execute(
                         {'pubshort': pubshort,
                          'curr_time': curr_time,
                          'event': event,
                          'status': status,
                          'message': message}
                         )
    return

def take_screenshot(browser, screenshots_dir, pubshort, curr_time_str):
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
    browser.save_screenshot("%s%s_%s.png" % (screenshots_dir, pubshort, curr_time_str))