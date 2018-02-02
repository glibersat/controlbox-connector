import asyncio
from unittest import TestCase
import pytest

import time

from controlbox.resolver import (
    RequestResponseMatcher,
    RequestResponseResolver
)

class TwoTimesMatcher(RequestResponseMatcher):
    def match(self, obj1, obj2):
        return ((obj1 * 2) == obj2)


class TestResolver:
    @pytest.mark.asyncio
    async def test_match_ok(self):
        resolver = RequestResponseResolver(TwoTimesMatcher())

        future = resolver.queue_request(4)

        async def do_resolve():
            return resolver.match_response(8)

        asyncio.ensure_future(do_resolve())
        res = await asyncio.wait_for(future, timeout=3)

        assert future.result() == 8

        assert resolver.unmatched_request_count == 0

    @pytest.mark.asyncio
    async def test_future_timeout(self):
        resolver = RequestResponseResolver(TwoTimesMatcher())

        future = resolver.queue_request(4)

        async def do_resolve():
            return resolver.match_response(9)

        asyncio.ensure_future(do_resolve())

        with pytest.raises(asyncio.TimeoutError):
            res = await asyncio.wait_for(future, timeout=1)

        await asyncio.sleep(0.1)

        assert resolver.unmatched_request_count == 0

    @pytest.mark.asyncio
    async def test_add_many_requests(self):
        resolver = RequestResponseResolver(TwoTimesMatcher())

        future = resolver.queue_request(4)
        future = resolver.queue_request(2)
        future = resolver.queue_request(9)
        future = resolver.queue_request(1)
        future = resolver.queue_request(98)

        assert resolver.unmatched_request_count == 5

    @pytest.mark.asyncio
    async def test_add_same_requests(self):
        resolver = RequestResponseResolver(TwoTimesMatcher())

        future = resolver.queue_request(4)
        future = resolver.queue_request(4)

        assert resolver.unmatched_request_count == 1

    @pytest.mark.asyncio
    async def test_add_same_requests_and_resolve(self):
        resolver = RequestResponseResolver(TwoTimesMatcher())

        future = resolver.queue_request(4)
        future = resolver.queue_request(4)

        async def do_resolve():
            return resolver.match_response(8)

        asyncio.ensure_future(do_resolve())
        res = await asyncio.wait_for(future, timeout=3)

        assert future.result() == 8

        assert resolver.unmatched_request_count == 0
