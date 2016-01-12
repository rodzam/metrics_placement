#!/usr/bin/python3
##############################################################
# Script name: Fort Worth Star-Telegram (Site Scraper)
# Version: 2.0
# By: Rodrigo Zamith
# License: MPL 2.0 (see LICENSE file in root folder)
# Additional thanks: 
##############################################################

########### Set variables
### Set publication-specific variables # CUSTOM
pubshort = "fws"
puburl = "http://www.star-telegram.com/"
puburl_mobile = "http://www.star-telegram.com/"
puburl_mv = None
puburl_mv_extraactions = None

### Set data storage variables
root_folder = "../"
homepages_dir = root_folder + "html_src/" + pubshort + "/"
screenshots_dir = root_folder + "screenshots/" + pubshort + "/"

########### Load libraries
from selenium import webdriver
from datetime import datetime
from pyvirtualdisplay import Display
import scraperfunctions
import argparse, sys

########### Let's check for command-line arguments
parser = argparse.ArgumentParser()
parser = scraperfunctions.add_common_arguments(parser)
### Add additional arguments here.
args = parser.parse_args()
curr_time = args.curr_time
download_desktop = args.download_desktop
download_mobile = args.download_mobile
parse = args.parse
parsefile = args.parsefile

### Grab the information from our configuration file
config = scraperfunctions.load_config()

### Get the current time if we don't already have one (and transform into a date object)
curr_time = scraperfunctions.get_curr_time(curr_time, parsefile)

### Establish our MySQL Connection (for logging, etc.)
engine, connection, metadata, mysql_table_name, mysql_log_name = scraperfunctions.create_mysql_engine(config)

########### Download actions
if download_desktop == 1:
    try:
        ### Initiate our virtual display
        print("Initiating virtual display")
        display = Display(visible=0, size=(1920, 1080))
        display.start()
    
        ### Let's start our browser
        browser = scraperfunctions.create_browser()
        
        ### Let's load the page work
        scraperfunctions.load_homepage(browser, pubshort, puburl)
        
        ### See if the MV list requires extra actions
        if puburl_mv_extraactions != None:
            ### Actions for acquiring MV List
            pass
        
        ### Let's first store the source code
        html_code = browser.page_source
        write_out_file = scraperfunctions.write_out_file("%s" % (homepages_dir), "%s_%s.html" % (pubshort, curr_time.strftime("%Y%m%d%H%M")), html_code)
        
        ### See if the MV list is in a separate URL
        if puburl_mv != None:
            ### Actions for acquiring MV List
            pass
        
        ### Save a screenshot
        scraperfunctions.take_screenshot(browser, screenshots_dir, pubshort, curr_time.strftime("%Y%m%d%H%M"))
        print("Screenshot taken")
        
        ### Close the browser
        scraperfunctions.close_browser(browser)
        
        ### Close our virtual display
        display.stop()
        print("Display closed")
        
        ### Perform closing actions
        print("Successfully downloaded the page!")
        #scraperfunctions.store_mysql_log(mysql_log_name, metadata, pubshort, curr_time, "1", "1", "") # Log success
    except:
        scraperfunctions.store_mysql_log(mysql_log_name, metadata, pubshort, curr_time, "1", "0", "") # Log failure
        
if download_mobile == 1:
    # Grab Mobile Page
    try:
        ### Initiate our virtual display
        print("Initiating virtual display")
        display = Display(visible=0, size=(1920, 1080))
        display.start()
    
        ### Let's start our browser
        browser = scraperfunctions.create_browser(mobile=1)
        
        ### Let's load the page work
        scraperfunctions.load_homepage(browser, pubshort, puburl_mobile)
        
        ### Let's first store the source code
        html_code = browser.page_source
        write_out_file = scraperfunctions.write_out_file("%s" % (homepages_dir), "%s_%s_%s.html" % (pubshort, "mobile", curr_time.strftime("%Y%m%d%H%M")), html_code)
        
        ### Save a screenshot
        scraperfunctions.take_screenshot(browser, screenshots_dir, "%s_%s" % (pubshort, "mobile"), curr_time.strftime("%Y%m%d%H%M"))
        print("Screenshot taken")
        
        ### Close the browser
        scraperfunctions.close_browser(browser)
        
        ### Close our virtual display
        display.stop()
        print("Display closed")
        
        ### Perform closing actions
        print("Successfully downloaded the page!")
        #scraperfunctions.store_mysql_log(mysql_log_name, metadata, pubshort, curr_time, "2", "1", "") # Log success
    except:
        scraperfunctions.store_mysql_log(mysql_log_name, metadata, pubshort, curr_time, "2", "0", "") # Log failure