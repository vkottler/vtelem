
"""
vtelem - An interface for simplifying registering implementations for
         individual request types.
"""

# built-in
from collections import defaultdict
from http.server import BaseHTTPRequestHandler
from http import HTTPStatus
import json
import logging
from typing import Dict, Callable, Tuple
from typing import Optional as Opt
import urllib

RequestHandle = Callable[[BaseHTTPRequestHandler, dict], Tuple[bool, str]]
LOG = logging.getLogger(__name__)


class HttpRequestMapper:
    """
    A class that facilitates composability in implmementing request handlers.
    """

    def __init__(self) -> None:
        """ Construct a new request mapper. """

        req: dict = defaultdict(lambda: defaultdict(lambda: None))
        self.requests: Dict[str, Dict[str, Opt[RequestHandle]]] = req
        data: dict = defaultdict(lambda: defaultdict(lambda: None))
        self.handle_data: Dict[str, Dict[str, Opt[dict]]] = data

        def index_handler(_: BaseHTTPRequestHandler,
                          __: dict) -> Tuple[bool, str]:
            """
            A default handler that can be used to discover the implemented
            request handles.
            """

            handles: dict = {}
            for method in self.requests.keys():
                handles[method] = []
                for path in self.requests[method].keys():
                    handle_inst = self.handle_data[method][path]
                    handle_data = {"path": path}
                    if handle_inst is not None:
                        handle_data["description"] = handle_inst["Description"]
                    handles[method].append(handle_data)
            return True, json.dumps(handles, indent=4)

        self.add_handler("GET", "", index_handler, "request index")

    def get_handle(self, request_type: str,
                   path: str) -> Tuple[Opt[RequestHandle], Opt[dict]]:
        """ Retrieve a handle by request type and path. """

        return (self.requests[request_type][path],
                self.handle_data[request_type][path])

    def add_handler(self, request_type: str, path: str,
                    handle: RequestHandle, description: str, data: dict = None,
                    response_type: str = "application/json",
                    charset: str = "utf-8") -> None:
        """
        A default handler for displaying the list of registered handles.
        """

        path = "/" + path.lower()
        self.requests[request_type][path] = handle
        handle_data = {}
        handle_data["Description"] = description
        handle_data["Content-Type"] = "{}; charset={}".format(response_type,
                                                              charset)
        if data is not None:
            handle_data.update(data)
        self.handle_data[request_type][path] = handle_data


# pylint: disable=attribute-defined-outside-init
class MapperAwareRequestHandler(BaseHTTPRequestHandler):
    """ A request handler that integrates with the request mapper. """

    def log_message(self, fmt, *args):  # pylint: disable=arguments-differ
        """ Overrides the default logging method. """

        fmt = "%s - - [%s] " + fmt
        new_args = [self.address_string(), self.log_date_time_string()]
        new_args += list(args)
        args = tuple(new_args)

        if "code" in fmt:
            LOG.error(fmt, *args)
        else:
            LOG.info(fmt, *args)

    def _no_mapper_response(self) -> None:
        """ Handle responding when no server mapper is detected. """

        self.send_error(HTTPStatus.NOT_IMPLEMENTED,
                        "no request-mapper configured")
        self.end_headers()
        self.close_connection = True

    def _no_handle_response(self, command: str) -> None:
        """
        Handle a response where no mapper is found for the requested path.
        """

        msg = "no request-mapper for '{}' path '{}'".format(command, self.path)
        self.send_error(HTTPStatus.NOT_FOUND, msg)
        self.end_headers()
        self.close_connection = True

    def _handle(self, _data: dict = None) -> None:
        """ Handle an arbitrary request. """

        if _data is None:
            _data = {}
        data: dict = defaultdict(lambda: None)
        data.update(_data)

        # parse the request uri
        parsed = urllib.parse.urlparse(self.path)
        self.path = parsed.path
        if parsed.query:
            data.update(urllib.parse.parse_qs(parsed.query))

        if not hasattr(self.server, "mapper"):
            return self._no_mapper_response()
        mapper: HttpRequestMapper
        mapper = self.server.mapper  # type: ignore

        headers_only = self.command == "HEAD"
        command = "GET" if headers_only else self.command

        handle, handle_data = mapper.get_handle(command, self.path)
        if handle is None:
            return self._no_handle_response(command)

        # run handler
        success, content = handle(self, data)
        status = HTTPStatus.OK if success else HTTPStatus.BAD_REQUEST

        if not success:
            self.send_error(status, content)
            self.end_headers()
            self.close_connection = True
            return None

        self.send_response(status)
        if handle_data is not None:
            for key, value in handle_data.items():
                self.send_header(key, value)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        if not headers_only:
            self.wfile.write(content.encode())
        self.log_request(status)
        return None

    def do_HEAD(self) -> None:  # pylint: disable=invalid-name
        """ Respond to a HEAD request. """
        return self._handle()

    def do_GET(self) -> None:  # pylint: disable=invalid-name
        """ Respond to a GET request. """
        return self._handle()

    def do_POST(self) -> None:  # pylint: disable=invalid-name
        """ Respond to a POST request. """
        return self._handle(get_post_request_data(self))


def get_post_request_data(request: BaseHTTPRequestHandler) -> dict:
    """ Obtain a dictionary of POST request data from a given request. """

    result = {}
    assert request.command == "POST"

    def form_parser(_: BaseHTTPRequestHandler) -> dict:
        """ Parse form data from a POST request. (RFC 7578) """
        return {}

    def url_encoded_parser(request: BaseHTTPRequestHandler) -> dict:
        """ Parse url-encoded POST request data. """
        field_data = request.rfile.read(length).decode("utf-8")
        return urllib.parse.parse_qs(field_data)

    parsers = {"multipart/form-data": form_parser,
               "application/x-www-form-urlencoded": url_encoded_parser}

    # if the request has content, attempt to parse it
    keys = ["Content-Length", "Content-Type"]
    if all(key in request.headers for key in keys):
        length = int(request.headers["Content-Length"])
        for mtype, parser in parsers.items():
            if mtype in request.headers["Content-Type"].lower():
                result = parser(request)
                break

    return result
