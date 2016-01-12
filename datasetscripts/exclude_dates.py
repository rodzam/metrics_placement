#!/usr/bin/python3
##############################################################
# Script name: Date Exclusion Script
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
all_pubs_exclude = ["2014-10-17", "2014-11-03", "2014-11-04", "2014-11-05", "2014-12-21"]
pub_exclude = {"cpd": ["2014-11-11", "2014-11-12"], "hch": ["2014-10-22"], "jse": ["2014-11-05"], "mhe": ["2014-11-04", "2014-11-05"], "mst": ["2014-11-16", "2014-11-28", "2014-11-29"], "nsl": ["2014-11-05", "2014-11-10"], "nyd": ["2014-12-04", "2014-12-05"], "ore": ["2014-11-29"], "sjm": ["2014-10-23"], "slt": ["2014-10-22", "2014-10-23", "2014-10-24"], "spp": ["2014-10-23"], "tst": ["2014-11-03"], "vjr": ["2014-11-25", "2014-11-26", "2014-12-10"]}
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

### Grab list of unique publications
unique_pubs = cur.execute("SELECT DISTINCT(pubshort) FROM `%s`;" % (mysql_table_name))
unique_pubs = cur.fetchall()
unique_pubs = [x[0] for x in unique_pubs]
unique_pubs_len = len(unique_pubs)

### For each publication
for publication in unique_pubs:
    if publication in pub_exclude:
        exclude_dates = all_pubs_exclude + pub_exclude[publication]
    else:
        exclude_dates = all_pubs_exclude
    
    for exclude_date in exclude_dates:
        exclude_date = datetime.datetime.strptime(exclude_date, '%Y-%m-%d')
        exclude_date_nextday = exclude_date + datetime.timedelta(days=1)
        
        print("Erasing items on date %s for %s" % (exclude_date, publication))
        
        ### Get list of entries
        try:
            matches = cur.execute("SELECT id FROM `%s` WHERE pubshort = '%s' AND curr_time >= '%s' AND curr_time < '%s';" % (mysql_table_name, publication, exclude_date, exclude_date_nextday))
            matches = cur.fetchall()
        except:
            print("Failed to get entries with statement: SELECT id FROM `%s` WHERE pubshort = '%s' AND curr_time >= '%s' AND curr_time < '%s';" % (mysql_table_name, publication, exclude_date, exclude_date_nextday))
        
        matches_len = len(matches)
        print("Found %s matches, proceeding to delete..." % (matches_len))
        pos = 1
        
        for match in matches:
            print("Working on match %s of %s (%s on %s)" % (pos, matches_len, publication, exclude_date))
            pos += 1
            
            # Get column values for each row
            m_id = match[0]
            
            # Update the table
            try:
                cur.execute("DELETE FROM `%s` WHERE `id` = '%s';" % (mysql_table_name, m_id))
            except:
                print("Failed to update the table with statement: DELETE FROM `%s` WHERE `id` = '%s';" % (mysql_table_name, m_id))
                
    conn.commit()
    print("Matches committed for %s" % (publication))