#!/usr/bin/python3
##############################################################
# Script name: Duplicate item remover
# Version: 2.0
# By: Rodrigo Zamith
# License: MPL 2.0 (see LICENSE file in root folder)
# Additional thanks: 
##############################################################

### Load libraries
import pymysql
from configobj import ConfigObj

### Set variables
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
    
    ### Grab list of unique articles
    all_arts = cur.execute("SELECT DISTINCT(article) FROM `%s` WHERE pubshort='%s' ORDER BY curr_time_utc;" % (mysql_table_name, publication))
    all_arts = cur.fetchall()
    all_arts = [x[0] for x in all_arts]
    all_arts_len = len(all_arts)
    
    i = 1
    ### For each unique article
    for article in all_arts:
        print("Working on article %s of %s (%s)" % (i, all_arts_len, publication))
        i += 1
        
        # Check how many items there are at any given time
        arts_res = cur.execute("SELECT article, pubshort, curr_time_utc, COUNT(id) FROM `%s` WHERE pubshort='%s' AND article='%s' GROUP BY article, pubshort, curr_time_utc;" % (mysql_table_name, publication, article)) # Get all the articles in the current snapshot
        arts_res = cur.fetchall()
        
        insert_statements=[]
        for result in arts_res:
            article = result[0]
            pubshort = result[1]
            curr_time_utc = result[2]
            count_id = result[3]
            if int(count_id) > 1:
                time_res = cur.execute("SELECT id, article, pubshort, curr_time, curr_time_utc, is_pro, pro_rank, is_pop, pop_rank, on_page FROM `%s` WHERE pubshort='%s' AND article='%s' AND curr_time_utc='%s';" % (mysql_table_name, publication, article, curr_time_utc)) # Get all the articles in the current snapshot
                time_res = cur.fetchall()
                time_article = time_res[0][1]
                time_pubshort = time_res[0][2]
                time_curr_time = time_res[0][3]
                time_curr_time_utc = time_res[0][4]
                time_is_pro = sorted([x[5] for x in time_res], reverse=True)[0]
                time_pro_rank = sorted([x[6] for x in time_res if x[6] is not None], reverse=True)
                if not time_pro_rank:
                    time_pro_rank = None
                else:
                    time_pro_rank = time_pro_rank[0]               
                time_is_pop = sorted([x[7] for x in time_res], reverse=True)[0]
                time_pop_rank = sorted([x[8] for x in time_res if x[8] is not None], reverse=True)
                if not time_pop_rank:
                    time_pop_rank = None
                else:
                    time_pop_rank = time_pop_rank[0]
                time_on_page =  sorted([x[9] for x in time_res if x[9] is not None], reverse=True)
                if not time_on_page:
                    time_on_page = None
                else:
                    time_on_page = time_on_page[0]
                insert_statements.append([time_article, time_pubshort, time_curr_time, time_curr_time_utc, time_is_pro, time_pro_rank, time_is_pop, time_pop_rank, time_on_page])
                cur.execute("DELETE FROM `%s` WHERE pubshort='%s' AND article='%s' AND curr_time_utc='%s';" % (mysql_table_name, publication, article, curr_time_utc))
                print("DUPLICATE FOUND AND FIXED: %s for %s at %s" % (article, pubshort, curr_time_utc))
        
        stmt = "INSERT INTO `adj_link_data` (article, pubshort, curr_time, curr_time_utc, is_pro, pro_rank, is_pop, pop_rank, on_page) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cur.executemany(stmt, insert_statements)
        conn.commit()