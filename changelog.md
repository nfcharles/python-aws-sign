0.4.5
* http module defers logging configuration to application.

0.4.3
* DefaultServiceConstants supports parsing endpoints with ports.

0.4.2
* Updated ServiceConstants scheme parsing and url property

0.4.1
* `constants_cls` parameter in http.get_instance has DefaultServiceConstants
default value
* Added path method to ServiceConstants

0.4.0
* Added apigateway module
* auth module sets 'X-Amz-Security-Token' header if Credentials object has
valid security token

0.3.0
* Modified HTTPClient default logging level to INFO
* Modified http.get_instance signature

0.2.0
* Added `defaults` parameter to HTTP class constructor
* Modified HTTP request method return type to response object instead
of response body

0.1.0
* Initial commit
* AWS signature 4 signing classes
