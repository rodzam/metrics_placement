'''
Created on Sep 21, 2014

@author: rodrigo
'''

### Load libraries
import pymysql, pytz, os, glob, re, shutil
from pytz import timezone
from configobj import ConfigObj
from datetime import datetime
from bs4 import BeautifulSoup

### Load configuration
def load_config():
    settings_file = "../settings.conf"
    config = ConfigObj(settings_file)
    return config

def homepages_dir(pubshort):
    homepages_dir = "../html_src/%s/" % (pubshort)
    return homepages_dir

### Get current time
def get_curr_time(parsefile, pub_tz):
    try:
        curr_time = datetime.strptime(parsefile.rstrip(".html")[-12:], "%Y%m%d%H%M")
        curr_time = curr_time.replace(tzinfo=timezone('UTC'))
        curr_time_adj = curr_time.astimezone(timezone(pub_tz))
    except:
        curr_time_adj = None
    return(curr_time_adj, curr_time)

### Write out to a file
def write_out_file(directory, filename, data):
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open("%s%s" % (directory, filename), "wt") as out_file:
        out_file.write(data)
    return

### Create a database connection
def create_mysql_conn(config):
    mysql_host = config["MySQL Settings"]["mysql_host"]
    mysql_username = config["MySQL Settings"]["mysql_username"]
    mysql_password = config["MySQL Settings"]["mysql_password"]
    mysql_database = config["MySQL Settings"]["mysql_database"]
    mysql_table_name = config["MySQL Settings"]["mysql_table"]
    mysql_log_name = config["MySQL Settings"]["mysql_log"]

    conn = pymysql.connect(host=mysql_host, user=mysql_username, passwd=mysql_password, db=mysql_database) # connect to server
    cur = conn.cursor()
    return(conn, cur, mysql_table_name, mysql_log_name)

### Create success directory
def create_success_dir(pubshort, homepages_dir, move_on_success):
    if move_on_success is not None:
        success_dir = "%ssuccess/" % (homepages_dir)
        if not os.path.exists(success_dir):
            os.makedirs(success_dir)
    return

### Get list of files
def get_file_list(pubshort, homepages_dir):
    file_list = glob.glob('%s%s_[0-9]*.html' % (homepages_dir, pubshort))
    file_list.sort()
    file_list_len = len(file_list)
    return(file_list, file_list_len)

### Open documents
def open_data_file(homepage):
    with open(homepage, "rt") as in_file:
        document_data = in_file.read()
    return document_data

### Soupify documents
def soupify(document_data):
    document_data = BeautifulSoup(document_data)
    return document_data

### Clean links
def clean_link(link):
    link = link.split("?")[0].split("#")[0]
    remove_prefix = re.search("^(.+\.com)/", link) 
    if remove_prefix is not None:
        link = "/" + link[:remove_prefix.start()] + link[remove_prefix.end():]
    return link

### Most Viewed Linklist Actions
def linklist_actions(link, linklist):
    link = clean_link(link)
    if link in linklist:
        pass
    else:
        linklist.append(link)
    return linklist

### Create error log entry
def error_log_entry(cur, conn, mysql_log_name, curr_time, pubshort, homepage, seriousness, message):
    mysql_log_name = "error_log_tmp"
    stmt = "INSERT INTO %s (curr_time, pubshort, homepage, seriousness, message) VALUES ('%s', '%s', '%s', '%s', '%s');" % (mysql_log_name, curr_time, pubshort, homepage, seriousness, message)
    cur.execute(stmt)
    conn.commit()
    return

### Get Most-Viewed Links
def get_top_5_list_links(linklist):
    l_1_link = linklist[0]
    l_2_link = linklist[1]
    l_3_link = linklist[2]
    l_4_link = linklist[3]
    l_5_link = linklist[4]
    top_5_links = [l_1_link, l_2_link, l_3_link, l_4_link, l_5_link]
    return(top_5_links)

### Assess if article appears in the right places
def assess_article(article, on_page_link_list, pop_top_5_links, pro_top_5_links):
    try:
        if article in on_page_link_list:
            on_page = 1
        else:
            on_page = 0
    except:
        on_page = None
    
    try:
        if article in pop_top_5_links:
            is_pop = 1
            pop_rank = pop_top_5_links.index(article)+1
        else:
            is_pop = 0
            pop_rank = None
    except:
        is_pop = None
        pop_rank = None
    
    try:
        if article in pro_top_5_links:
            is_pro = 1
            pro_rank = pro_top_5_links.index(article)+1
        else:
            is_pro = 0
            pro_rank = None
    except:
        is_pro = None
        pro_rank = None
        
    return(article, is_pro, pro_rank, is_pop, pop_rank, on_page)

### Store entry
def data_point_multi_entry(insert_statements, cur, conn, mysql_table_name):
    stmt = "INSERT INTO orig_link_data_tmp (article, pubshort, curr_time, curr_time_utc, is_pro, pro_rank, is_pop, pop_rank, on_page) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
    cur.executemany(stmt, insert_statements)
    conn.commit()
    return

### Move files
def move_file(homepage, success_dir):
    try:
        shutil.move(homepage, success_dir)
    except:
        print("Failed to move files to success dir for document %s" % (homepage))
    return