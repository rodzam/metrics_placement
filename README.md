Metrics Placement Project
====================
Author: Rodrigo Zamith
Version: 2.0

Description
-----
This repository contains the source code for a set of scripts used in my analyses of the impact of metrics on the content appearing on the homepages of several different news organizations. These scripts will likely be most useful as a foundation for other research projects; they may not work out of the box since they were designed with a particular project in mind, with human intervention occurring at different stages. If you have any questions, please e-mail me.

The scripts are broken down into three sets:

* Site scripts: A set of scripts used to freeze liquid homepages into static sets of snapshots that contain the browser-processed HTML code and a screenshot of the page
* Parse scripts: A set of scripts to extract information from the list of most-viewed items and from the five most prominent spots of the homepage (as determined by a modified F-shape reading pattern)
* Dataset scripts: A small set of helper scripts used to clean and reshape the data

Dependencies
-----
These scripts depend on Python, MySQL, and Firefox. Additionally, the Selenium framework and the BeautifulSoup and PyMSQL libraries are used.

License
-----
All scripts in this repository are licensed under the Mozilla Public License Version 2.0 (see LICENSE file in the root folder). TL;DR: Feel free to use modify it and distribute it as part of either commercial or non-commercial software, provided you disclose both the source code and any modifications you make to it.