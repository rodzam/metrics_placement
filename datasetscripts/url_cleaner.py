#!/usr/bin/python3
##############################################################
# Script name: URL Reducer
# Version: 2.0
# By: Rodrigo Zamith
# License: MPL 2.0 (see LICENSE file in root folder)
# Additional thanks: 
##############################################################

### Load libraries
import pymysql
from configobj import ConfigObj
import datetime, re

### Set variables
pubshort_list = [["dpo", "/ci_[0-9]+", "/ci_(\d+)/?"], ["sjm", "/ci_[0-9]+", "/ci_(\d+)/?"], ["spp", "/ci_[0-9]+", "/ci_(\d+)/?"]] # Publications followed by regular expression (MySQL) and same regular expression (Python)
link_data_table = "adj_link_data" # Table containing the link data

### Load settings
def load_config():
    settings_file = "../settings.conf"
    config = ConfigObj(settings_file)
    return config

config = load_config()

### Prepare our database
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

conn, cur, mysql_table_name, mysql_log_name = create_mysql_conn(config)
mysql_table_name = link_data_table

### For each publication
for publication in pubshort_list:
    pubshort = publication[0]
    regex = publication[1]
    regex_python = publication[2]
    
    print("Creating connection with %s" % (pubshort))
    
    ### Get list of entries
    try:
        matches = cur.execute("SELECT id, article FROM `%s` WHERE pubshort = '%s' AND article REGEXP '%s';" % (mysql_table_name, pubshort, regex))
        matches = cur.fetchall()
    except:
        print("Failed to get entries with statement: SELECT id, article FROM `%s` WHERE pubshort = '%s' AND article REGEXP '%s';" % (mysql_table_name, pubshort, regex))
    
    print("Found %s matches, proceeding to replace..." % (len(matches)))
    pos = 1
    
    for match in matches:
        print("Working on match %s" % pos)
        pos += 1
        
        # Get column values for each row
        m_id = match[0]
        m_article = match[1]
        #m_pubshort = match[2]
        #m_curr_time = match[3]
        #m_on_page = match[4]
        #m_on_mv = match[5]
        
        # Replace the values where we find matches
        try:
            m_article = re.search(regex_python, m_article).group(1)
        except:
            print("Failed to fix article id %s" % m_id)
            pass
        
        # Update the table
        try:
            cur.execute("UPDATE `%s` SET article = '%s' WHERE id = '%s';" % (mysql_table_name, m_article, m_id))
        except:
            print("Failed to update the table with statement: UPDATE `%s` SET article = '%s' WHERE id = '%s';" % (mysql_table_name, m_article, m_id))
            
    conn.commit()
    print("Matches committed for %s" % (pubshort))