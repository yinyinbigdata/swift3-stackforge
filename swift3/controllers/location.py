# Copyright (c) 2010-2014 OpenStack Foundation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from swift3.controllers.base import Controller, bucket_operation
from swift3.etree import Element, tostring
from swift3.response import HTTPOk
from swift3.cfg import CONF


class LocationController(Controller):
    """
    Handles GET Bucket location, which is logged as a LOCATION operation in the
    S3 server log.
    """
    @bucket_operation
    def GET(self, req):
        """
        Handles GET Bucket location.
        """
        req.get_response(self.app, method='HEAD')

        elem = Element('LocationConstraint')
        if CONF.location != 'US':
            elem.text = CONF.location
        body = tostring(elem)

        return HTTPOk(body=body, content_type='application/xml')
