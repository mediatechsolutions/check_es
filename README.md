Elasticsearch checker for nagios and icinga
===================

----------


Dependencies
-------------
* pip install PySock urllib3 elasticsearch requests

`nginx-response-times.py` requires python 3 and requests

----------


Functionalities
-------------------

* Execute a elasticsearch query and parse result
* Check status cluster health
* Check for nginx request times ranges.


Examples
-------------

* python check_es.py --host 127.0.0.1 --port 9200 --index winlogbeat-* --fields-to-be-returned message,computer_name,source_name --critical 1 --query $QUERY
* python nginx-response-times.py --uri http://localhost:9200 --username WHOEVER --password WHATEVER --index nginx --range 0:0.3  0.3:0.5  0.5:1:10  1:2 2:3:10:15 3: --minutes 5;
