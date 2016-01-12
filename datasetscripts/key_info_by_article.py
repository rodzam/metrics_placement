#!/usr/bin/python3
##############################################################
# Script name: Creating summary information per article
# Version: 2.0
# By: Rodrigo Zamith
# License: MPL 2.0 (see LICENSE file in root folder)
# Additional thanks: 
##############################################################

### Load libraries
import pymysql
from configobj import ConfigObj

### Set script-specific variables
resurface_max = 7200 # Integer representing minutes for the maximum lifespan of an item before we check if it just resurfaced briefly (e.g., 7200 = 5 days)
link_data_table = "adj_link_data" # Table name for original link data

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

### Additional functions
def prevent_resurface(lifespan, last_appearance, resurface_max, article_row):
    if lifespan >= resurface_max:
        resurface_tp = 1
        try:
            while resurface_tp <= 12: # Go back a maximum of 12 times (3 hours)
                res_last_appearance = article_row[-resurface_tp][0]
                res_lifespan = res_last_appearance - first_appearance
                res_lifespan = (int(res_lifespan.days*24*60*60) + int(res_lifespan.seconds))/60
                if res_lifespan <= resurface_max:
                    last_appearance = res_last_appearance
                    lifespan = res_lifespan
                    break
                else:
                    resurface_tp += 1
        except:
            pass
    return(lifespan, last_appearance)

### Grab list of unique publications
mysql_table_name = link_data_table
unique_pubs = cur.execute("SELECT DISTINCT(pubshort) FROM `%s`;" % (mysql_table_name))
unique_pubs = cur.fetchall()
unique_pubs = [x[0] for x in unique_pubs]
unique_pubs_len = len(unique_pubs)

for publication in unique_pubs:
    ### Grab list of unique articles
    unique_arts = cur.execute("SELECT DISTINCT(article) FROM `%s` WHERE pubshort='%s';" % (mysql_table_name, publication))
    unique_arts = cur.fetchall()
    unique_arts = [x[0] for x in unique_arts]
    unique_arts_len = len(unique_arts)
    
    insert_statements = []
    i = 1
    for article in unique_arts:
        ### Check when the article first appeared, and how long it stuck around
        article_row = cur.execute("SELECT curr_time FROM `%s` WHERE pubshort='%s' AND article='%s' ORDER BY curr_time;" % (mysql_table_name, publication, article))
        article_row = cur.fetchall()
        all_appearances = [x[0] for x in article_row]
        first_appearance = all_appearances[0]
        last_appearance = all_appearances[-1]
        lifespan = last_appearance - first_appearance
        lifespan = (int(lifespan.days*24*60*60) + int(lifespan.seconds))/60
        lifespan, last_appearance = prevent_resurface(lifespan, last_appearance, resurface_max, article_row)
        all_appearances = [x for x in all_appearances if x <= last_appearance]
        
        ### Check how long article was on page
        on_page_row = cur.execute("SELECT curr_time FROM `%s` WHERE pubshort='%s' AND article='%s' AND on_page='1' ORDER BY curr_time;" % (mysql_table_name, publication, article))
        on_page_row = cur.fetchall()
        if on_page_row:
            on_page = 1
            on_page_all_appearances = [x[0] for x in on_page_row]
            on_page_first_appearance = on_page_all_appearances[0]
            on_page_last_appearance = on_page_all_appearances[-1]
            on_page_lifespan = on_page_last_appearance - on_page_first_appearance
            on_page_lifespan = (int(on_page_lifespan.days*24*60*60) + int(on_page_lifespan.seconds))/60
            on_page_lifespan, on_page_last_appearance = prevent_resurface(on_page_lifespan, on_page_last_appearance, resurface_max, on_page_row)
            on_page_all_appearances = [x for x in on_page_all_appearances if x <= on_page_last_appearance]
        else:
            on_page = 0
            on_page_all_appearances = None
            on_page_first_appearance = None
            on_page_last_appearance = None
            on_page_lifespan = None
        
        ### Check if the article was ever in a prominent location
        is_pro_row = cur.execute("SELECT curr_time, pro_rank FROM `%s` WHERE pubshort='%s' AND article='%s' AND is_pro='1' ORDER BY curr_time;" % (mysql_table_name, publication, article))
        is_pro_row = cur.fetchall()
        if is_pro_row:
            is_pro = 1
            pro_all_appearances = [x[0] for x in is_pro_row]
            pro_first_appearance = pro_all_appearances[0]
            pro_last_appearance = pro_all_appearances[-1]
            pro_lifespan = pro_last_appearance - pro_first_appearance
            pro_lifespan = (int(pro_lifespan.days*24*60*60) + int(pro_lifespan.seconds))/60
            pro_lifespan, pro_last_appearance = prevent_resurface(pro_lifespan, pro_last_appearance, resurface_max, is_pro_row)
            pro_all_appearances = [x for x in pro_all_appearances if x <= pro_last_appearance]
            pro_first_pos = is_pro_row[0][1]
            pro_highest_pos = [x[1] for x in is_pro_row]
            pro_lowest_pos = pro_highest_pos
            pro_highest_pos.sort()
            pro_highest_pos = pro_highest_pos[0]
            pro_lowest_pos.sort(reverse=True)
            pro_lowest_pos = pro_lowest_pos[0]
            time_first_to_pro = pro_first_appearance - first_appearance
            time_first_to_pro = (int(time_first_to_pro.days*24*60*60) + int(time_first_to_pro.seconds))/60
            if on_page_first_appearance is not None:
                time_on_page_to_pro = pro_first_appearance - on_page_first_appearance
                time_on_page_to_pro = (int(time_on_page_to_pro.days*24*60*60) + int(time_on_page_to_pro.seconds))/60
            else:
                time_on_page_to_pro = None
        else:
            is_pro = 0
            pro_all_appearances = None
            pro_first_appearance = None
            pro_last_appearance = None
            pro_lifespan = None
            pro_first_pos = None
            pro_highest_pos = None
            pro_lowest_pos = None
            time_first_to_pro = None
            time_on_page_to_pro = None
        
        ### Check if the article was ever in a most-viewed list
        is_pop_row = cur.execute("SELECT curr_time, pop_rank FROM `%s` WHERE pubshort='%s' AND article='%s' AND is_pop='1' ORDER BY curr_time;" % (mysql_table_name, publication, article))
        is_pop_row = cur.fetchall()
        if is_pop_row:
            is_pop = 1
            pop_all_appearances = [x[0] for x in is_pop_row]
            pop_first_appearance = pop_all_appearances[0]
            pop_last_appearance = pop_all_appearances[-1]
            pop_lifespan = pop_last_appearance - pop_first_appearance
            pop_lifespan = (int(pop_lifespan.days*24*60*60) + int(pop_lifespan.seconds))/60
            pop_lifespan, pop_last_appearance = prevent_resurface(pop_lifespan, pop_last_appearance, resurface_max, is_pop_row)
            pop_all_appearances = [x for x in pop_all_appearances if x <= pop_last_appearance]
            pop_first_pos = is_pop_row[0][1]
            pop_highest_pos = [x[1] for x in is_pop_row]
            pop_lowest_pos = pop_highest_pos
            pop_highest_pos.sort()
            pop_highest_pos = pop_highest_pos[0]
            pop_lowest_pos.sort(reverse=True)
            pop_lowest_pos = pop_lowest_pos[0]
            time_first_to_pop = pop_first_appearance - first_appearance
            time_first_to_pop = (int(time_first_to_pop.days*24*60*60) + int(time_first_to_pop.seconds))/60
            if on_page_first_appearance is not None:
                time_on_page_to_pop = pop_first_appearance - on_page_first_appearance
                time_on_page_to_pop = (int(time_on_page_to_pop.days*24*60*60) + int(time_on_page_to_pop.seconds))/60
            else:
                time_on_page_to_pop = None
            
            if is_pro == 1:
                time_pro_to_pop = pop_first_appearance - pro_first_appearance
                time_pro_to_pop = (int(time_pro_to_pop.days*24*60*60) + int(time_pro_to_pop.seconds))/60
            else:
                time_pro_to_pop = None
        else:
            is_pop = 0
            pop_all_appearances = None
            pop_first_appearance = None
            pop_last_appearance = None
            pop_lifespan = None
            pop_first_pos = None
            pop_highest_pos = None
            pop_lowest_pos = None
            time_first_to_pop = None
            time_on_page_to_pop = None
            time_pro_to_pop = None
        
        ### Check if the articles ever overlapped between the most-viewed list, the most prominent area, and anywhere on the page
        if pro_all_appearances is not None and pop_all_appearances is not None:
            pro_pop_overlap_times = len(set.intersection(set(pro_all_appearances), set(pop_all_appearances)))
            if (pro_last_appearance >= pop_first_appearance and pro_last_appearance <= pop_last_appearance) or (pro_first_appearance >= pop_first_appearance and pro_first_appearance <= pop_last_appearance) or (pro_first_appearance <= pop_first_appearance and pro_last_appearance >= pop_last_appearance) or (pro_first_appearance >= pop_first_appearance and pro_last_appearance <= pop_last_appearance):
                pro_pop_overlap = 1
            else:
                pro_pop_overlap = 0
        else:
            pro_pop_overlap_times = 0 # Times refers to the amount of times they appear on both lists (not necessary for below to be true)
            pro_pop_overlap = 0 # General overlap refers to whether the first time it appeared on the pop list came before the last time it was on an area of prominence
        if on_page_all_appearances is not None and pop_all_appearances is not None:
            on_page_pop_overlap_times = len(set.intersection(set(on_page_all_appearances), set(pop_all_appearances)))
            if (on_page_last_appearance >= pop_first_appearance and on_page_last_appearance <= pop_last_appearance) or (on_page_first_appearance >= pop_first_appearance and on_page_first_appearance <= pop_last_appearance) or (on_page_first_appearance <= pop_first_appearance and on_page_last_appearance >= pop_last_appearance) or (on_page_first_appearance >= pop_first_appearance and on_page_last_appearance <= pop_last_appearance):
                on_page_pop_overlap = 1
            else:
                on_page_pop_overlap = 0
        else:
            on_page_pop_overlap_times = 0
            on_page_pop_overlap = 0
        if pop_first_appearance is not None and pro_last_appearance is not None:
            pro_possible_effect_time = pro_last_appearance - pop_first_appearance
            pro_possible_effect_time = (int(pro_possible_effect_time.days*24*60*60) + int(pro_possible_effect_time.seconds))/60
        else:
            pro_possible_effect_time = None
                    
        insert_statements.append([article, publication, first_appearance, last_appearance, lifespan, on_page, on_page_first_appearance, on_page_last_appearance, on_page_lifespan, is_pro, pro_first_appearance, pro_last_appearance, pro_lifespan, pro_first_pos, pro_highest_pos, pro_lowest_pos, time_first_to_pro, time_on_page_to_pro, is_pop, pop_first_appearance, pop_last_appearance, pop_lifespan, pop_first_pos, pop_highest_pos, pop_lowest_pos, time_first_to_pop, time_on_page_to_pop, time_pro_to_pop, pro_pop_overlap, pro_pop_overlap_times, on_page_pop_overlap, on_page_pop_overlap_times, pro_possible_effect_time])
        print("Finished processing article %s of %s (publication: %s)" % (i, unique_arts_len, publication))
        i += 1
    
    ### Insert the items
    stmt = "INSERT INTO key_info_by_article (article, pubshort, first_appearance, last_appearance, lifespan, on_page, on_page_first_appearance, on_page_last_appearance, on_page_lifespan, is_pro, pro_first_appearance, pro_last_appearance, pro_lifespan, pro_first_pos, pro_highest_pos, pro_lowest_pos, time_first_to_pro, time_on_page_to_pro, is_pop, pop_first_appearance, pop_last_appearance, pop_lifespan, pop_first_pos, pop_highest_pos, pop_lowest_pos, time_first_to_pop, time_on_page_to_pop, time_pro_to_pop, pro_pop_overlap, pro_pop_overlap_times, on_page_pop_overlap, on_page_pop_overlap_times, pro_possible_effect_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
    cur.executemany(stmt, insert_statements)
    conn.commit()