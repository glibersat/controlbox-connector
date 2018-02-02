import functools
from asyncio import Future


class RequestResponseMatcher:
    """
    Abstract class that matches a Request with a Response
    """
    def match(self, obj1, obj2):
        raise NotImplementError


class RequestResponseResolver:
    def __init__(self, aRequestResponseMatcher):
        self._request_queue = {}
        self._matcher = aRequestResponseMatcher

    @property
    def unmatched_request_count(self):
        return len(self._request_queue)

    def cleanup_future(self, future, aRequest):
        del self._request_queue[aRequest]

    def queue_request(self, aRequest):
        if aRequest not in self._request_queue:
            future = Future()

            future.add_done_callback(functools.partial(self.cleanup_future, aRequest=aRequest))
            self._request_queue[aRequest] = future

        return self._request_queue[aRequest]

    def match_response(self, aResponse):
        for request, future in self._request_queue.items():
            if self._matcher.match(request, aResponse):
                future.set_result(aResponse)
                return future

        return None
