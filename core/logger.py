from logstash.handler_tcp import TCPLogstashHandler
import logging


handler = TCPLogstashHandler(host='85.143.173.70', port=5960)
logger = logging.getLogger('oauth_bru')
logger.addHandler(handler)