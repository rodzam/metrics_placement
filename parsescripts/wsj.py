#!/usr/bin/python3
##############################################################
# Script name: Wall Street Journal (Page Parser)
# Version: 2.0
# By: Rodrigo Zamith
# License: MPL 2.0 (see LICENSE file in root folder)
# Additional thanks: 
##############################################################

########### Set variables
### Set publication-specific variables # CUSTOM
pubshort = "wsj" # Short name for the publication
pubmv_external = None # Do we need to get the list of most viewed items from another page? (None = No, anything else = Yes)
pattern = "(.+\.com)?/(.+)/(.+)-(\d+)|(.+\.com)?/(\d+)/(\d+)/(\d+)" # Pattern for defining what is and what is not a news item
pub_tz = "US/Eastern" # Timezone the publication is in

process_desktop = 1 # Do we want to process the desktop pages? (None = No, anything else = Yes)
move_on_success = None # Do we want to move files on success? (None = No, anything else = Yes)
success_dir = "success/" # Directory for storing successful files (as subdirectory of data directory)

########### Load libraries
import parserfunctions
import re
from bs4 import BeautifulSoup

### Grab the information from our configuration file
config = parserfunctions.load_config()
homepages_dir = parserfunctions.homepages_dir(pubshort)
link_pattern = re.compile(pattern)

### Establish our MySQL Connection (for logging, etc.)
conn, cur, mysql_table_name, mysql_log_name = parserfunctions.create_mysql_conn(config)

### Create directory for success, if appropriate
parserfunctions.create_success_dir(pubshort, homepages_dir, move_on_success)

########### Parse Desktop Pages
if process_desktop is not None:
    ### Get list of files to parse
    file_list, file_list_len = parserfunctions.get_file_list(pubshort, homepages_dir)
    i = 1
    
    ### For each desktop homepage
    for homepage in file_list:
        print("Opening file %s (%s of %s for %s)" % (homepage, i, file_list_len, pubshort))
        i += 1
        
        ### Reset key variables
        curr_time, curr_time_utc, document_data, document_soup, document_soup_on_page, insert_statements, is_pop, is_pro, layout, link, message, mostviewed_linklist, on_page, on_page_link_list, on_page_link_list_tmp, pop_rank, pop_top_5_links, pro_rank, pro_top_5_links, prominence_linklist, seriousness = [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]
        prominence_leftbar_linklist, prominence_rightbar_linklist, prominence_supplemental_linklist = [None, None, None] # Publication-specific
        
        try:
            ### Get data from file
            curr_time, curr_time_utc = parserfunctions.get_curr_time(homepage, pub_tz)
            document_data = parserfunctions.open_data_file(homepage)
        except:
            message = "Failed to open document"
            seriousness = 1
            parserfunctions.error_log_entry(cur, conn, mysql_log_name, curr_time, pubshort, homepage, seriousness, message)
            #continue

        ### Create a souped object
        try:
            document_soup = parserfunctions.soupify(document_data)
        except:
            message = "Failed to soupify document"
            seriousness = 1
            parserfunctions.error_log_entry(cur, conn, mysql_log_name, curr_time, pubshort, homepage, seriousness, message)
            #continue
        
        ### Check layout
        layout = None
        try:
            if document_soup.find("div", class_="headlineSummary whatsNews wide colOverflowTruncated clear-left").find("div", class_="wide whatsNews-4-2").find("div", class_="col4wide") is not None:
                layout = 2
        except:
            pass
        if layout is None:
            try:
                if document_soup.find("div", class_="headlineSummary whatsNews wide colOverflowTruncated clear-left") is not None:
                    layout = 1
            except:
                pass
        if layout is None:
            message = "Failed to detect the layout"
            seriousness = 2
            parserfunctions.error_log_entry(cur, conn, mysql_log_name, curr_time, pubshort, homepage, seriousness, message)
            #continue
        
        ##### Get Most Viewed
        try:
            mostviewed_1to5 = [link.find("a", href=re.compile(pattern)) for link in document_soup.find("div", class_="headlineSummary trendingNow").find_all("li")]
            mostviewed_linklist = []
            for link in mostviewed_1to5:
                try:
                    link = link.get("href")
                    mostviewed_linklist = parserfunctions.linklist_actions(link, mostviewed_linklist)                        
                except:
                    pass
        except:
            message = "Failed at getting MV link list"
            seriousness = 2
            parserfunctions.error_log_entry(cur, conn, mysql_log_name, curr_time, pubshort, homepage, seriousness, message)
            #continue
        
        try:
            pop_top_5_links = parserfunctions.get_top_5_list_links(mostviewed_linklist)
        except:
            pop_top_5_links = []
            message = "Failed to get a POP link"
            seriousness = 2
            parserfunctions.error_log_entry(cur, conn, mysql_log_name, curr_time, pubshort, homepage, seriousness, message)
            #continue

        ##### Get Most Prominent Items            
        ### LAYOUT #1
        if layout == 1:
            try: # Get left bar stories
                prominence_leftbar = [link.find("a", href=re.compile(pattern)) for link in document_soup.find("div", class_="headlineSummary whatsNews wide colOverflowTruncated clear-left").find("div", class_="col2wide").find_all("h2")]
                prominence_leftbar_linklist = []
                for link in prominence_leftbar:
                    try:
                        link = link.get("href")
                        prominence_leftbar_linklist = parserfunctions.linklist_actions(link, prominence_leftbar_linklist)
                    except:
                        pass
            except:
                message = "Failed to get linklist for prominence leftbar (layout 1)"
                seriousness = 3
                parserfunctions.error_log_entry(cur, conn, mysql_log_name, curr_time, pubshort, homepage, seriousness, message)
                #continue
            
            try: # Get right bar stories
                prominence_rightbar = [link.find("a", href=re.compile(pattern)) for link in document_soup.find("div", class_="headlineSummary whatsNews wide colOverflowTruncated clear-left").find("div", class_="col4wide").find_all("h2")]
                prominence_rightbar_linklist = []
                for link in prominence_rightbar:
                    try:
                        link = link.get("href")
                        prominence_rightbar_linklist = parserfunctions.linklist_actions(link, prominence_rightbar_linklist)
                    except:
                        pass
            except:
                message = "Failed to get linklist for prominence rightbar (layout 1)"
                seriousness = 3
                parserfunctions.error_log_entry(cur, conn, mysql_log_name, curr_time, pubshort, homepage, seriousness, message)
                #continue
            
            try: # Get remaining main headlines ("What's News")
                prominence_supplemental = [link.find("a", href=re.compile(pattern)) for link in document_soup.find("h3", text=re.compile("(.+)What’s News(.+)")).parent.find_all("h2")]
                prominence_supplemental_linklist = []
                for link in prominence_supplemental:
                    try:
                        link = link.get("href")
                        prominence_supplemental_linklist = parserfunctions.linklist_actions(link, prominence_supplemental_linklist)
                    except:
                        pass
            except:
                message = "Failed to get linklist for prominence supplemental (layout 1)"
                seriousness = 3
                parserfunctions.error_log_entry(cur, conn, mysql_log_name, curr_time, pubshort, homepage, seriousness, message)
                #continue
            
            try: # Now, order the prominence linklist. We favor the top-left because it has the biggest headline, then the right because it has a featured image, then the remainder of the left bar, then the remainder of the right bar, followed by any supplemental stories
                prominence_linklist_tmp = [prominence_leftbar_linklist[0]] + [prominence_rightbar_linklist[0]] + prominence_leftbar_linklist + prominence_rightbar_linklist + prominence_supplemental_linklist # Because we check for duplicates, we can follow this
                prominence_linklist = []
                for link in prominence_linklist_tmp:
                    if link in prominence_linklist:
                        pass
                    else:
                        prominence_linklist.append(link)
            except:
                message = "Failed to produce an ordered prominence linklist (layout 1)"
                seriousness = 2
                parserfunctions.error_log_entry(cur, conn, mysql_log_name, curr_time, pubshort, homepage, seriousness, message)
                #continue
        
        ### LAYOUT #2
        if layout == 2:
            try: # Get left bar stories
                prominence_leftbar = [link.find("a", href=re.compile(pattern)) for link in document_soup.find("div", class_="wide whatsNews-4-2").find("div", class_="col4wide").find_all("h2")]
                prominence_leftbar_linklist = []
                for link in prominence_leftbar:
                    try:
                        link = link.get("href")
                        prominence_leftbar_linklist = parserfunctions.linklist_actions(link, prominence_leftbar_linklist)
                    except:
                        pass
            except:
                message = "Failed to get linklist for prominence left bar (layout 2)"
                seriousness = 3
                parserfunctions.error_log_entry(cur, conn, mysql_log_name, curr_time, pubshort, homepage, seriousness, message)
                #continue

            
            try: # Get right bar stories
                prominence_rightbar = [link.find("a", href=re.compile(pattern)) for link in document_soup.find("div", class_="wide whatsNews-4-2").find("div", class_="col2wide").find_all("h2")]
                prominence_rightbar_linklist = []
                for link in prominence_rightbar:
                    try:
                        link = link.get("href")
                        prominence_rightbar_linklist = parserfunctions.linklist_actions(link, prominence_rightbar_linklist)
                    except:
                        pass
            except:
                message = "Failed to get linklist for prominence rightbar (layout 2)"
                seriousness = 3
                parserfunctions.error_log_entry(cur, conn, mysql_log_name, curr_time, pubshort, homepage, seriousness, message)
                #continue

            
            try: # Get remaining main headlines ("What's News")
                prominence_supplemental = [link.find("a", href=re.compile(pattern)) for link in document_soup.find("h3", text=re.compile("(.+)What’s News(.+)")).parent.find_all("h2")]
                prominence_supplemental_linklist = []
                for link in prominence_supplemental:
                    try:
                        link = link.get("href")
                        prominence_supplemental_linklist = parserfunctions.linklist_actions(link, prominence_supplemental_linklist)
                    except:
                        pass
            except:
                message = "Failed to get linklist for prominence supplemental (layout 2)"
                seriousness = 3
                parserfunctions.error_log_entry(cur, conn, mysql_log_name, curr_time, pubshort, homepage, seriousness, message)
                #continue

            
            try: # Now, order the prominence linklist. We favor the top-left because it has the biggest headline, then the right because it has a featured image, then the remainder of the left bar, then the remainder of the right bar, followed by any supplemental stories
                prominence_linklist_tmp = [prominence_leftbar_linklist[0]] + [prominence_rightbar_linklist[0]] + prominence_leftbar_linklist + prominence_rightbar_linklist + prominence_supplemental_linklist # Because we check for duplicates, we can follow this
                prominence_linklist = []
                for link in prominence_linklist_tmp:
                    if link in prominence_linklist:
                        pass
                    else:
                        prominence_linklist.append(link)
            except:
                message = "Failed to produce an ordered prominence linklist (layout 2)"
                seriousness = 2
                parserfunctions.error_log_entry(cur, conn, mysql_log_name, curr_time, pubshort, homepage, seriousness, message)
                #continue

        ### For all layouts
        try:
            pro_top_5_links = parserfunctions.get_top_5_list_links(prominence_linklist)
        except:
            pro_top_5_links = []
            message = "Failed to get a PRO link"
            seriousness = 2
            parserfunctions.error_log_entry(cur, conn, mysql_log_name, curr_time, pubshort, homepage, seriousness, message)
            #continue
        
        ###### Get list of links on the page
        try:
            document_soup_on_page = parserfunctions.soupify(document_data)
        except:
            message = "Failed to resoupify the document"
            seriousness = 1
            parserfunctions.error_log_entry(cur, conn, mysql_log_name, curr_time, pubshort, homepage, seriousness, message)
        
        try:
            document_soup_on_page.find("div", class_="headlineSummary trendingNow").decompose()
        except:
            message = "Failed to decompose the area for most viewed items"
            seriousness = 2
            parserfunctions.error_log_entry(cur, conn, mysql_log_name, curr_time, pubshort, homepage, seriousness, message)
        
        try:
            on_page_link_list_tmp = document_soup_on_page.find_all('a', {'href': link_pattern})
        except:
            message = "Failed at attempt to extract all links on page"
            seriousness = 2
            parserfunctions.error_log_entry(cur, conn, mysql_log_name, curr_time, pubshort, homepage, seriousness, message)
        
        try:
            on_page_link_list = []
            for link in on_page_link_list_tmp:
                link = link.get('href')
                on_page_link_list = parserfunctions.linklist_actions(link, on_page_link_list)
        except:
            message = "Failed to clean up links for list of all links on page"
            seriousness = 2
            parserfunctions.error_log_entry(cur, conn, mysql_log_name, curr_time, pubshort, homepage, seriousness, message)
            #continue
        
        insert_statements = []
        ###### Prepare insert statement for each link
        try:
            for article in set(on_page_link_list + pop_top_5_links + pro_top_5_links):
                article, is_pro, pro_rank, is_pop, pop_rank, on_page = parserfunctions.assess_article(article, on_page_link_list, pop_top_5_links, pro_top_5_links)
                insert_statements.append([article, pubshort, curr_time, curr_time_utc, is_pro, pro_rank, is_pop, pop_rank, on_page])
        except:
            message = "Failed to prepare list of insert statements"
            seriousness = 1
            parserfunctions.error_log_entry(cur, conn, mysql_log_name, curr_time, pubshort, homepage, seriousness, message)
        
        try:
            parserfunctions.data_point_multi_entry(insert_statements, cur, conn, mysql_table_name)
        except:
            message = "Failed to insert the statements into the database"
            seriousness = 1
            parserfunctions.error_log_entry(cur, conn, mysql_log_name, curr_time, pubshort, homepage, seriousness, message)
        
        ### Move files if necessary
        if move_on_success is not None:
            parserfunctions.move_file(homepage, success_dir)
    
### Perform closing actions
print("Finished parsing")