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

from swift.common.http import HTTP_OK
from swift.common.utils import split_path

from swift3.controllers.base import Controller
from swift3.response import AccessDenied, HTTPOk, NoSuchKey
from swift3.etree import Element, SubElement, tostring
from swift3.subresource import ACL, Owner
from swift3.cfg import CONF


class ObjectController(Controller):
    """
    Handles requests on objects
    """
    def GETorHEAD(self, req):
        resp = req.get_response(self.app)

        if req.method == 'HEAD':
            resp.app_iter = None

        for key in ('content-type', 'content-language', 'expires',
                    'cache-control', 'content-disposition',
                    'content-encoding'):
            if 'response-' + key in req.params:
                resp.headers[key] = req.params['response-' + key]

        return resp

    def HEAD(self, req):
        """
        Handle HEAD Object request
        """
        return self.GETorHEAD(req)

    def GET(self, req):
        """
        Handle GET Object request
        """
        return self.GETorHEAD(req)

    def PUT(self, req):
        """
        Handle PUT Object and PUT Object (Copy) request
        """
        if CONF.s3_acl:
            if 'X-Amz-Copy-Source' in req.headers:
                src_path = req.headers['X-Amz-Copy-Source']
                src_path = src_path if src_path.startswith('/') else \
                    ('/' + src_path)
                src_bucket, src_obj = split_path(src_path, 0, 2, True)
                req.get_response(self.app, 'HEAD', src_bucket, src_obj,
                                 permission='READ')
            b_resp = req.get_response(self.app, 'HEAD', obj='')
            # To avoid overwriting the existing object by unauthorized user,
            # we send HEAD request first before writing the object to make
            # sure that the target object does not exist or the user that sent
            # the PUT request have write permission.
            try:
                req.get_response(self.app, 'HEAD')
            except NoSuchKey:
                pass
            req_acl = ACL.from_headers(req.headers,
                                       b_resp.bucket_acl.owner,
                                       Owner(req.user_id, req.user_id))

            req.object_acl = req_acl

        resp = req.get_response(self.app)

        if 'X-Amz-Copy-Source' in req.headers:
            elem = Element('CopyObjectResult')
            SubElement(elem, 'ETag').text = '"%s"' % resp.etag
            body = tostring(elem, use_s3ns=False)
            return HTTPOk(body=body, headers=resp.headers)

        resp.status = HTTP_OK

        return resp

    def POST(self, req):
        raise AccessDenied()

    def DELETE(self, req):
        """
        Handle DELETE Object request
        """
        return req.get_response(self.app)
