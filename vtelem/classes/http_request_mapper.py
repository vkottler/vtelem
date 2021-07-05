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
from typing import Dict, Callable, List, Tuple
from typing import Optional as Opt
import urllib

RequestHandle = Callable[[BaseHTTPRequestHandler, dict], Tuple[bool, str]]
LOG = logging.getLogger(__name__)


class HttpRequestMapper:
    """
    A class that facilitates composability in implmementing request handlers.
    """

    def __init__(self) -> None:
        """Construct a new request mapper."""

        req: dict = defaultdict(lambda: defaultdict(lambda: None))
        self.requests: Dict[str, Dict[str, Opt[RequestHandle]]] = req
        data: dict = defaultdict(lambda: defaultdict(lambda: None))
        self.handle_data: Dict[str, Dict[str, Opt[dict]]] = data

        def index_handler(
            _: BaseHTTPRequestHandler, __: dict
        ) -> Tuple[bool, str]:
            """
            A default handler that can be used to discover the implemented
            request handles.
            """

            handles: dict = {}
            for method, handlers in self.requests.items():
                handles[method] = []
                for path in handlers.keys():
                    handle_inst = self.handle_data[method][path]
                    handle_data = {"path": path}
                    if handle_inst is not None:
                        handle_data["description"] = handle_inst["Description"]
                    handles[method].append(handle_data)
            return True, json.dumps(handles, indent=4)

        self.add_handler("GET", "", index_handler, "request index")

    def get_handle(
        self, request_type: str, path: str
    ) -> Tuple[Opt[RequestHandle], Opt[dict]]:
        """Retrieve a handle by request type and path."""

        return (
            self.requests[request_type][path],
            self.handle_data[request_type][path],
        )

    def add_handler(
        self,
        request_type: str,
        path: str,
        handle: RequestHandle,
        description: str,
        data: dict = None,
        response_type: str = "application/json",
        charset: str = "utf-8",
    ) -> None:
        """
        A default handler for displaying the list of registered handles.
        """

        path = "/" + path.lower()
        self.requests[request_type][path] = handle
        handle_data = {}
        handle_data["Description"] = description
        handle_data["Content-Type"] = "{}; charset={}".format(
            response_type, charset
        )
        if data is not None:
            handle_data.update(data)
        self.handle_data[request_type][path] = handle_data


# pylint: disable=attribute-defined-outside-init
class MapperAwareRequestHandler(BaseHTTPRequestHandler):
    """A request handler that integrates with the request mapper."""

    def log_message(self, fmt, *args):  # pylint: disable=arguments-differ
        """Overrides the default logging method."""

        fmt = "%s - - [%s] " + fmt
        new_args = [self.address_string(), self.log_date_time_string()]
        new_args += list(args)
        args = tuple(new_args)

        if "code" in fmt:
            LOG.error(fmt, *args)
        else:
            LOG.info(fmt, *args)

    def _no_mapper_response(self) -> None:
        """Handle responding when no server mapper is detected."""

        self.send_error(
            HTTPStatus.NOT_IMPLEMENTED, "no request-mapper configured"
        )
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
        """Handle an arbitrary request."""

        if _data is None:
            _data = {}
        data: dict = defaultdict(lambda: None)
        data.update(_data)

        # parse the request uri
        parsed = urllib.parse.urlparse(self.path)  # type: ignore
        self.path = parsed.path
        if parsed.query:
            data.update(urllib.parse.parse_qs(parsed.query))  # type: ignore

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
        """Respond to a HEAD request."""
        return self._handle()

    def do_GET(self) -> None:  # pylint: disable=invalid-name
        """Respond to a GET request."""
        return self._handle()

    def do_POST(self) -> None:  # pylint: disable=invalid-name
        """Respond to a POST request."""
        return self._handle(get_post_request_data(self))


def parse_content_type(value: str) -> Opt[dict]:
    """Parse a 'Content-Type' header field. (RFC 2045 5.1)"""

    params = [x.strip() for x in value.split(";")]
    if len(params) >= 1 and "/" in params[0]:
        types = [x.strip() for x in params[0].split("/")]
        if len(types) == 2 and types[0] and types[1]:
            return {
                "type": types[0],
                "subtype": types[1],
                "params": params[1:],
            }

    return None


def get_multipart_boundary(content_type: dict) -> Opt[str]:
    """
    Attempt to parse the 'boundary=gc0p4Jq0M2Yt08j34c0p' portion of of a
    'Content-Type' header field. This is generall required for further
    processing of 'multipart' MIME data.
    """

    if (
        "params" in content_type
        and isinstance(content_type["params"], list)
        and len(content_type["params"]) == 1
    ):
        boundary_raw = content_type["params"][0].split("=")
        if len(boundary_raw) == 2 and boundary_raw[0] == "boundary":
            return boundary_raw[1]

    return None


def parse_request_lines(lines: List[str]) -> dict:
    """
    Parse lines from an (RFC 822) message into headers and body lines.
    """

    part_data: dict = {"headers": {}, "body": []}
    headers = []
    for idx, line in enumerate(lines):
        if line == "" and idx != 0 and idx + 1 != len(lines):
            headers = lines[:idx]
            part_data["body"] = lines[idx + 1 :]
            break

    header_parsers = {"content-disposition": parse_content_disposition}

    # parse headers (RFC 822 3.2)
    for header in headers:
        name_body = header.split(":")
        if len(name_body) == 2:
            name = name_body[0].strip().lower()
            body = name_body[1].strip()
            part_data["headers"][name] = body

            # parse headers further if they have a parser
            if name in header_parsers:
                part_data["headers"][name] = header_parsers[name](body)

    return part_data


def dequote(data: str) -> str:
    """
    Attempt to remove single or double quote characters from the outside of a
    String.
    """

    if len(data) > 1 and data[0] == data[-1] and data.startswith(("'", '"')):
        data = data[1:-1]
    return data


def parse_multipart_data(
    boundary: str, data: str
) -> List[Dict[str, List[str]]]:
    """
    Given a boundary and valid request data, attempt to parse it into 'parts'
    where a 'part' is provided as a list of the lines it contained.
    """

    delim = "--" + boundary
    chunks = data.split(delim)

    # remove leading empty element
    if chunks and not chunks[0]:
        chunks = chunks[1:]

    parts = []
    if chunks:
        # (RFC 2616 2.2)
        parts = [x.split("\r\n") for x in chunks]
        for idx, part in enumerate(parts):
            # strip the 'terminating CRLF' (RFC 2047 5.1.1)
            if part and not part[0]:
                parts[idx] = part[1:]

    # (RFC 2046 5.1)
    return [parse_request_lines(part) for part in parts]


def parse_content_disposition(data: str) -> dict:
    """
    Attempt to parse a 'Content-Disposition' header field into an expected
    result. (RFC 2183)
    """

    result = {}
    items = [x.strip() for x in data.split(";")]
    if items:
        result["type"] = items[0]
        for param in items[1:]:
            param_split = param.split("=")
            if len(param_split) == 2:
                key = param_split[0].strip().lower()
                result[key] = dequote(param_split[1].strip())

    return result


def get_post_request_data(request: BaseHTTPRequestHandler) -> dict:
    """Obtain a dictionary of POST request data from a given request."""

    result = {}
    assert request.command == "POST"

    def form_parser(
        request: BaseHTTPRequestHandler, content_type: dict
    ) -> dict:
        """Parse form data from a POST request. (RFC 7578)"""

        boundary = get_multipart_boundary(content_type)
        real_parts = []
        if boundary is not None:
            data = request.rfile.read(length).decode("utf-8")
            parsed = parse_multipart_data(boundary, data)

            # this is now essentially 'lines of an http request', so we should
            # figure out the best way to parse it...
            for part in parsed:
                if "content-disposition" in part["headers"]:
                    real_parts.append(part)

        return {"parts": real_parts}

    def url_encoded_parser(request: BaseHTTPRequestHandler, _: dict) -> dict:
        """Parse url-encoded POST request data."""
        field_data = request.rfile.read(length).decode("utf-8")
        return urllib.parse.parse_qs(field_data)  # type: ignore

    parsers: dict = {
        "multipart": {"form-data": form_parser},
        "application": {"x-www-form-urlencoded": url_encoded_parser},
    }

    # if the request has content, attempt to find a parser for it
    keys = ["Content-Length", "Content-Type"]
    if all(key in request.headers for key in keys):
        content_type = parse_content_type(request.headers["Content-Type"])
        length = int(request.headers["Content-Length"])
        if content_type is not None and content_type["type"] in parsers:
            subparsers = parsers[content_type["type"]]
            if content_type["subtype"] in subparsers:
                result = subparsers[content_type["subtype"]](
                    request, content_type
                )

    return result
