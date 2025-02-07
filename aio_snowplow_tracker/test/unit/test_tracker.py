"""
    test_tracker.py

    Copyright (c) 2013-2021 Snowplow Analytics Ltd. All rights reserved.

    This program is licensed to you under the Apache License Version 2.0,
    and you may not use this file except in compliance with the Apache License
    Version 2.0. You may obtain a copy of the Apache License Version 2.0 at
    http://www.apache.org/licenses/LICENSE-2.0.

    Unless required by applicable law or agreed to in writing,
    software distributed under the Apache License Version 2.0 is distributed on
    an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
    express or implied. See the Apache License Version 2.0 for the specific
    language governing permissions and limitations there under.

    Authors: Anuj More, Alex Dean, Fred Blundun, Paul Boocock
    Copyright: Copyright (c) 2013-2021 Snowplow Analytics Ltd
    License: Apache License Version 2.0
"""

import re
import json
import unittest
import unittest.mock as mock

from freezegun import freeze_time
from typing import Any, Type

import aio_snowplow_tracker
from aio_snowplow_tracker.contracts import disable_contracts, enable_contracts
from aio_snowplow_tracker.tracker import Tracker
from aio_snowplow_tracker.tracker import VERSION as TRACKER_VERSION
from aio_snowplow_tracker.subject import Subject
from aio_snowplow_tracker.payload import Payload
from aio_snowplow_tracker.self_describing_json import SelfDescribingJson

UNSTRUCT_SCHEMA = "iglu:com.snowplowanalytics.snowplow/unstruct_event/jsonschema/1-0-0"
CONTEXT_SCHEMA = "iglu:com.snowplowanalytics.snowplow/contexts/jsonschema/1-0-1"
LINK_CLICK_SCHEMA = "iglu:com.snowplowanalytics.snowplow/link_click/jsonschema/1-0-1"
ADD_TO_CART_SCHEMA = "iglu:com.snowplowanalytics.snowplow/add_to_cart/jsonschema/1-0-0"
REMOVE_FROM_CART_SCHEMA = "iglu:com.snowplowanalytics.snowplow/remove_from_cart/jsonschema/1-0-0"
FORM_CHANGE_SCHEMA = "iglu:com.snowplowanalytics.snowplow/change_form/jsonschema/1-0-0"
FORM_SUBMIT_SCHEMA = "iglu:com.snowplowanalytics.snowplow/submit_form/jsonschema/1-0-0"
SITE_SEARCH_SCHEMA = "iglu:com.snowplowanalytics.snowplow/site_search/jsonschema/1-0-0"
SCREEN_VIEW_SCHEMA = "iglu:com.snowplowanalytics.snowplow/screen_view/jsonschema/1-0-0"

# helpers
_TEST_UUID = '5628c4c6-3f8a-43f8-a09f-6ff68f68dfb6'
geoSchema = "iglu:com.snowplowanalytics.snowplow/geolocation_context/jsonschema/1-0-0"
geoData = {"latitude": -23.2, "longitude": 43.0}
movSchema = "iglu:com.acme_company/movie_poster/jsonschema/2-1-1"
movData = {"movie": "TestMovie", "year": 2021}


def mocked_uuid() -> str:
    return _TEST_UUID


def mocked_track(pb: Any) -> None:
    pass


def mocked_complete_payload(*args: Any, **kwargs: Any) -> None:
    pass


def mocked_track_trans_item(*args: Any, **kwargs: Any) -> None:
    pass


def mocked_track_unstruct(*args: Any, **kwargs: Any) -> None:
    pass


class ContractsDisabled(object):
    def __enter__(self) -> None:
        disable_contracts()

    def __exit__(self, type: Any, value: Any, traceback: Any) -> None:
        enable_contracts()


try:
    AsyncTestCase = unittest.IsolatedAsyncioTestCase
    async_patch = mock.patch
    async_mock = mock.AsyncMock
except AttributeError:
    # Python 3.7 compatibility
    import asynctest  # noqa
    AsyncTestCase = asynctest.TestCase
    async_patch = asynctest.patch
    async_mock = asynctest.create_autospec


def create_mock_emitter() -> aio_snowplow_tracker.Emitter:
    try:
        return mock.AsyncMock()
    except AttributeError:
        return asynctest.create_autospec(aio_snowplow_tracker.Emitter)(endpoint=None)


class TestTracker(AsyncTestCase):

    def patch_emitter(self, name: str) -> Any:
        # patcher = mock.patch(name)
        # emitter = patcher.start()
        # try:
        #     emitter.side_effect = mock.AsyncMock
        # except AttributeError:
        #     emitter.side_effect = asynctest.create_autospec(aio_snowplow_tracker.Emitter)
        # self.addCleanup(patcher.stop)
        # return emitter
        return asynctest.create_autospec(aio_snowplow_tracker.Emitter)

    def setUp(self) -> None:
        pass

    async def test_initialisation(self) -> None:
        e = create_mock_emitter()

        t = Tracker([e], namespace="cloudfront", encode_base64=False, app_id="AF003")
        self.assertEqual(t.standard_nv_pairs["tna"], "cloudfront")
        self.assertEqual(t.standard_nv_pairs["aid"], "AF003")
        self.assertEqual(t.encode_base64, False)

    async def test_initialisation_default_optional(self) -> None:
        e = create_mock_emitter()

        t = Tracker(e)
        self.assertEqual(t.emitters, [e])
        self.assertTrue(t.standard_nv_pairs["tna"] is None)
        self.assertTrue(t.standard_nv_pairs["aid"] is None)
        self.assertEqual(t.encode_base64, True)

    async def test_initialisation_emitter_list(self) -> None:
        e1 = create_mock_emitter()
        e2 = create_mock_emitter()

        t = Tracker([e1, e2])
        self.assertEqual(t.emitters, [e1, e2])

    async def test_initialisation_error(self) -> None:
        with self.assertRaises(ValueError):
            Tracker([])

    async def test_initialization_with_subject(self) -> None:
        e = create_mock_emitter()

        s = Subject()
        t = Tracker(e, subject=s)
        self.assertIs(t.subject, s)

    async def test_get_uuid(self) -> None:
        eid = Tracker.get_uuid()
        self.assertIsNotNone(re.match(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z', eid))

    @freeze_time("1970-01-01 00:00:01")
    async def test_get_timestamp(self) -> None:
        tstamp = Tracker.get_timestamp()
        self.assertEqual(tstamp, 1000)   # 1970-01-01 00:00:01 in ms

    async def test_get_timestamp_1(self) -> None:
        tstamp = Tracker.get_timestamp(1399021242030)
        self.assertEqual(tstamp, 1399021242030)

    async def test_get_timestamp_2(self) -> None:
        tstamp = Tracker.get_timestamp(1399021242240.0303)
        self.assertEqual(tstamp, 1399021242240)

    @freeze_time("1970-01-01 00:00:01")
    async def test_get_timestamp_3(self) -> None:
        tstamp = Tracker.get_timestamp("1399021242030")   # test wrong arg type
        self.assertEqual(tstamp, 1000)                    # 1970-01-01 00:00:01 in ms

    @async_patch('aio_snowplow_tracker.Tracker.track')
    async def test_alias_of_track_unstruct_event(self, mok_track: Any) -> None:
        e = create_mock_emitter()

        mok_track.side_effect = mocked_track
        t = Tracker(e)
        evJson = SelfDescribingJson("test.schema", {"n": "v"})
        # call the alias
        await t.track_self_describing_event(evJson)
        self.assertEqual(mok_track.call_count, 1)

    async def test_flush(self) -> None:
        e1 = create_mock_emitter()
        e2 = create_mock_emitter()

        t = Tracker([e1, e2])
        await t.flush()
        e1.flush.assert_not_called()
        self.assertEqual(e1.sync_flush.call_count, 1)
        e2.flush.assert_not_called()
        self.assertEqual(e2.sync_flush.call_count, 1)

    async def test_flush_async(self) -> None:
        e1 = create_mock_emitter()
        e2 = create_mock_emitter()

        t = Tracker([e1, e2])
        await t.flush(is_async=True)
        self.assertEqual(e1.flush.call_count, 1)
        e1.sync_flush.assert_not_called()
        self.assertEqual(e2.flush.call_count, 1)
        e2.sync_flush.assert_not_called()

    async def test_set_subject(self) -> None:
        e = create_mock_emitter()

        t = Tracker(e)
        new_subject = Subject()
        self.assertIsNot(t.subject, new_subject)
        t.set_subject(new_subject)
        self.assertIs(t.subject, new_subject)

    async def test_add_emitter(self) -> None:
        e1 = create_mock_emitter()
        e2 = create_mock_emitter()

        t = Tracker(e1)
        t.add_emitter(e2)
        self.assertEqual(t.emitters, [e1, e2])

    ###
    # test track and complete payload methods
    ###

    async def test_track(self) -> None:
        e1 = create_mock_emitter()
        e2 = create_mock_emitter()
        e3 = create_mock_emitter()

        t = Tracker([e1, e2, e3])

        p = Payload({"test": "track"})
        await t.track(p)

        e1.input.assert_called_once_with({"test": "track"})
        e2.input.assert_called_once_with({"test": "track"})
        e3.input.assert_called_once_with({"test": "track"})

    @freeze_time("2021-04-19 00:00:01")  # unix: 1618790401000
    @async_patch('aio_snowplow_tracker.Tracker.track')
    @async_patch('aio_snowplow_tracker.Tracker.get_uuid')
    async def test_complete_payload(self, mok_uuid: Any, mok_track: Any) -> None:
        e = create_mock_emitter()

        mok_uuid.side_effect = mocked_uuid
        mok_track.side_effect = mocked_track

        t = Tracker(e)
        p = Payload()
        await t.complete_payload(p, None, None, None)

        self.assertEqual(mok_track.call_count, 1)
        trackArgsTuple = mok_track.call_args_list[0][0]
        self.assertEqual(len(trackArgsTuple), 1)
        passed_nv_pairs = trackArgsTuple[0].nv_pairs

        expected = {
            "eid": _TEST_UUID,
            "dtm": 1618790401000,
            "tv": TRACKER_VERSION,
            "p": "pc"
        }
        self.assertDictEqual(passed_nv_pairs, expected)

    @freeze_time("2021-04-19 00:00:01")  # unix: 1618790401000
    @async_patch('aio_snowplow_tracker.Tracker.track')
    @async_patch('aio_snowplow_tracker.Tracker.get_uuid')
    async def test_complete_payload_tstamp_int(self, mok_uuid: Any, mok_track: Any) -> None:
        e = create_mock_emitter()

        mok_uuid.side_effect = mocked_uuid
        mok_track.side_effect = mocked_track

        t = Tracker(e)
        p = Payload()
        time_in_millis = 100010001000
        await t.complete_payload(p, None, time_in_millis, None)

        self.assertEqual(mok_track.call_count, 1)
        trackArgsTuple = mok_track.call_args_list[0][0]
        self.assertEqual(len(trackArgsTuple), 1)
        passed_nv_pairs = trackArgsTuple[0].nv_pairs

        expected = {
            "eid": _TEST_UUID,
            "dtm": 1618790401000,
            "ttm": time_in_millis,
            "tv": TRACKER_VERSION,
            "p": "pc"
        }
        self.assertDictEqual(passed_nv_pairs, expected)

    @freeze_time("2021-04-19 00:00:01")  # unix: 1618790401000
    @async_patch('aio_snowplow_tracker.Tracker.track')
    @async_patch('aio_snowplow_tracker.Tracker.get_uuid')
    async def test_complete_payload_tstamp_dtm(self, mok_uuid: Any, mok_track: Any) -> None:
        e = create_mock_emitter()

        mok_uuid.side_effect = mocked_uuid
        mok_track.side_effect = mocked_track

        t = Tracker(e)
        p = Payload()
        time_in_millis = 100010001000
        await t.complete_payload(p, None, time_in_millis, None)

        self.assertEqual(mok_track.call_count, 1)
        trackArgsTuple = mok_track.call_args_list[0][0]
        self.assertEqual(len(trackArgsTuple), 1)
        passed_nv_pairs = trackArgsTuple[0].nv_pairs

        expected = {
            "eid": _TEST_UUID,
            "dtm": 1618790401000,
            "ttm": time_in_millis,
            "tv": TRACKER_VERSION,
            "p": "pc"
        }
        self.assertDictEqual(passed_nv_pairs, expected)

    @freeze_time("2021-04-19 00:00:01")  # unix: 1618790401000
    @async_patch('aio_snowplow_tracker.Tracker.track')
    @async_patch('aio_snowplow_tracker.Tracker.get_uuid')
    async def test_complete_payload_tstamp_ttm(self, mok_uuid: Any, mok_track: Any) -> None:
        e = create_mock_emitter()

        mok_uuid.side_effect = mocked_uuid
        mok_track.side_effect = mocked_track

        t = Tracker(e)
        p = Payload()
        time_in_millis = 100010001000
        await t.complete_payload(p, None, time_in_millis, None)

        self.assertEqual(mok_track.call_count, 1)
        trackArgsTuple = mok_track.call_args_list[0][0]
        self.assertEqual(len(trackArgsTuple), 1)
        passed_nv_pairs = trackArgsTuple[0].nv_pairs

        expected = {
            "eid": _TEST_UUID,
            "dtm": 1618790401000,
            "ttm": time_in_millis,
            "tv": TRACKER_VERSION,
            "p": "pc"
        }
        self.assertDictEqual(passed_nv_pairs, expected)

    @freeze_time("2021-04-19 00:00:01")  # unix: 1618790401000
    @async_patch('aio_snowplow_tracker.Tracker.track')
    @async_patch('aio_snowplow_tracker.Tracker.get_uuid')
    async def test_complete_payload_co(self, mok_uuid: Any, mok_track: Any) -> None:
        e = create_mock_emitter()

        mok_uuid.side_effect = mocked_uuid
        mok_track.side_effect = mocked_track

        t = Tracker(e, encode_base64=False)
        p = Payload()

        geo_ctx = SelfDescribingJson(geoSchema, geoData)
        mov_ctx = SelfDescribingJson(movSchema, movData)
        ctx_array = [geo_ctx, mov_ctx]
        await t.complete_payload(p, ctx_array, None, None)

        self.assertEqual(mok_track.call_count, 1)
        trackArgsTuple = mok_track.call_args_list[0][0]
        self.assertEqual(len(trackArgsTuple), 1)
        passed_nv_pairs = trackArgsTuple[0].nv_pairs

        expected_co = {
            "schema": CONTEXT_SCHEMA,
            "data": [
                {
                    "schema": geoSchema,
                    "data": geoData
                },
                {
                    "schema": movSchema,
                    "data": movData
                }
            ]
        }
        self.assertIn("co", passed_nv_pairs)
        self.assertDictEqual(json.loads(passed_nv_pairs["co"]), expected_co)

    @freeze_time("2021-04-19 00:00:01")  # unix: 1618790401000
    @async_patch('aio_snowplow_tracker.Tracker.track')
    @async_patch('aio_snowplow_tracker.Tracker.get_uuid')
    async def test_complete_payload_cx(self, mok_uuid: Any, mok_track: Any) -> None:
        e = create_mock_emitter()

        mok_uuid.side_effect = mocked_uuid
        mok_track.side_effect = mocked_track

        t = Tracker(e, encode_base64=True)
        p = Payload()

        geo_ctx = SelfDescribingJson(geoSchema, geoData)
        mov_ctx = SelfDescribingJson(movSchema, movData)
        ctx_array = [geo_ctx, mov_ctx]
        await t.complete_payload(p, ctx_array, None, None)

        self.assertEqual(mok_track.call_count, 1)
        trackArgsTuple = mok_track.call_args_list[0][0]
        self.assertEqual(len(trackArgsTuple), 1)
        passed_nv_pairs = trackArgsTuple[0].nv_pairs

        self.assertIn("cx", passed_nv_pairs)

    @freeze_time("2021-04-19 00:00:01")  # unix: 1618790401000
    @async_patch('aio_snowplow_tracker.Tracker.track')
    @async_patch('aio_snowplow_tracker.Tracker.get_uuid')
    async def test_complete_payload_event_subject(self, mok_uuid: Any, mok_track: Any) -> None:
        e = create_mock_emitter()

        mok_uuid.side_effect = mocked_uuid
        mok_track.side_effect = mocked_track

        t = Tracker(e)
        p = Payload()
        evSubject = Subject().set_lang('EN').set_user_id("tester")
        await t.complete_payload(p, None, None, evSubject)

        self.assertEqual(mok_track.call_count, 1)
        trackArgsTuple = mok_track.call_args_list[0][0]
        self.assertEqual(len(trackArgsTuple), 1)
        passed_nv_pairs = trackArgsTuple[0].nv_pairs

        expected = {
            "eid": _TEST_UUID,
            "dtm": 1618790401000,
            "tv": TRACKER_VERSION,
            "p": "pc",
            "lang": "EN",
            "uid": "tester"
        }
        self.assertDictEqual(passed_nv_pairs, expected)

    ###
    # test track_x methods
    ###

    @async_patch('aio_snowplow_tracker.Tracker.complete_payload')
    async def test_track_unstruct_event(self, mok_complete_payload: Any) -> None:
        e = create_mock_emitter()

        mok_complete_payload.side_effect = mocked_complete_payload

        t = Tracker(e, encode_base64=False)
        evJson = SelfDescribingJson("test.sde.schema", {"n": "v"})
        await t.track_unstruct_event(evJson)
        self.assertEqual(mok_complete_payload.call_count, 1)
        completeArgsList = mok_complete_payload.call_args_list[0][0]
        self.assertEqual(len(completeArgsList), 4)

        # payload
        actualPayloadArg = completeArgsList[0]
        actualPairs = actualPayloadArg.nv_pairs
        actualUePr = json.loads(actualPairs["ue_pr"])
        # context
        actualContextArg = completeArgsList[1]
        # tstamp
        actualTstampArg = completeArgsList[2]

        expectedUePr = {
            "data": {
                "data": {"n": "v"},
                "schema": "test.sde.schema"
            },
            "schema": UNSTRUCT_SCHEMA
        }

        self.assertDictEqual(actualUePr, expectedUePr)
        self.assertEqual(actualPairs["e"], "ue")
        self.assertTrue(actualContextArg is None)
        self.assertTrue(actualTstampArg is None)

    @async_patch('aio_snowplow_tracker.Tracker.complete_payload')
    async def test_track_unstruct_event_all_args(self, mok_complete_payload: Any) -> None:
        e = create_mock_emitter()

        mok_complete_payload.side_effect = mocked_complete_payload

        t = Tracker(e, encode_base64=False)
        evJson = SelfDescribingJson("test.schema", {"n": "v"})
        ctx = SelfDescribingJson("test.context.schema", {"user": "tester"})
        evContext = [ctx]
        evTstamp = 1399021242030
        await t.track_unstruct_event(evJson, evContext, evTstamp)
        self.assertEqual(mok_complete_payload.call_count, 1)
        completeArgsList = mok_complete_payload.call_args_list[0][0]
        self.assertEqual(len(completeArgsList), 4)

        # payload
        actualPayloadArg = completeArgsList[0]
        actualPairs = actualPayloadArg.nv_pairs
        actualUePr = json.loads(actualPairs["ue_pr"])
        # context
        actualContextArg = completeArgsList[1]
        # tstamp
        actualTstampArg = completeArgsList[2]

        expectedUePr = {
            "data": {
                "data": {"n": "v"},
                "schema": "test.schema"
            },
            "schema": UNSTRUCT_SCHEMA
        }

        self.assertDictEqual(actualUePr, expectedUePr)
        self.assertEqual(actualPairs["e"], "ue")
        self.assertIs(actualContextArg[0], ctx)
        self.assertEqual(actualTstampArg, evTstamp)

    @async_patch('aio_snowplow_tracker.Tracker.complete_payload')
    async def test_track_unstruct_event_encode(self, mok_complete_payload: Any) -> None:
        e = create_mock_emitter()

        mok_complete_payload.side_effect = mocked_complete_payload

        t = Tracker(e, encode_base64=True)
        evJson = SelfDescribingJson("test.sde.schema", {"n": "v"})
        await t.track_unstruct_event(evJson)
        self.assertEqual(mok_complete_payload.call_count, 1)
        completeArgsList = mok_complete_payload.call_args_list[0][0]
        self.assertEqual(len(completeArgsList), 4)

        actualPayloadArg = completeArgsList[0]
        actualPairs = actualPayloadArg.nv_pairs
        self.assertTrue("ue_px" in actualPairs.keys())

    @async_patch('aio_snowplow_tracker.Tracker.complete_payload')
    async def test_track_struct_event(self, mok_complete_payload: Any) -> None:
        e = create_mock_emitter()

        mok_complete_payload.side_effect = mocked_complete_payload

        t = Tracker(e)
        ctx = SelfDescribingJson("test.context.schema", {"user": "tester"})
        evTstamp = 1399021242030
        await t.track_struct_event("Mixes", "Play", "Test", "TestProp", value=3.14, context=[ctx], tstamp=evTstamp)
        self.assertEqual(mok_complete_payload.call_count, 1)
        completeArgsList = mok_complete_payload.call_args_list[0][0]
        self.assertEqual(len(completeArgsList), 4)

        actualPayloadArg = completeArgsList[0]
        actualContextArg = completeArgsList[1]
        actualTstampArg = completeArgsList[2]
        actualPairs = actualPayloadArg.nv_pairs

        expectedPairs = {
            "e": "se",
            "se_ca": "Mixes",
            "se_ac": "Play",
            "se_la": "Test",
            "se_pr": "TestProp",
            "se_va": 3.14
        }
        self.assertDictEqual(actualPairs, expectedPairs)
        self.assertIs(actualContextArg[0], ctx)
        self.assertEqual(actualTstampArg, evTstamp)

    @async_patch('aio_snowplow_tracker.Tracker.complete_payload')
    async def test_track_page_view(self, mok_complete_payload: Any) -> None:
        e = create_mock_emitter()

        mok_complete_payload.side_effect = mocked_complete_payload

        t = Tracker(e)
        ctx = SelfDescribingJson("test.context.schema", {"user": "tester"})
        evTstamp = 1399021242030
        await t.track_page_view("example.com", "Example", "docs.snowplowanalytics.com", context=[ctx], tstamp=evTstamp)
        self.assertEqual(mok_complete_payload.call_count, 1)
        completeArgsList = mok_complete_payload.call_args_list[0][0]
        self.assertEqual(len(completeArgsList), 4)

        actualPayloadArg = completeArgsList[0]
        actualContextArg = completeArgsList[1]
        actualTstampArg = completeArgsList[2]
        actualPairs = actualPayloadArg.nv_pairs

        expectedPairs = {
            "e": "pv",
            "url": "example.com",
            "page": "Example",
            "refr": "docs.snowplowanalytics.com"
        }
        self.assertDictEqual(actualPairs, expectedPairs)
        self.assertIs(actualContextArg[0], ctx)
        self.assertEqual(actualTstampArg, evTstamp)

    @async_patch('aio_snowplow_tracker.Tracker.complete_payload')
    async def test_track_page_ping(self, mok_complete_payload: Any) -> None:
        e = create_mock_emitter()

        mok_complete_payload.side_effect = mocked_complete_payload

        t = Tracker(e)
        ctx = SelfDescribingJson("test.context.schema", {"user": "tester"})
        evTstamp = 1399021242030
        await t.track_page_ping("example.com", "Example", "docs.snowplowanalytics.com", 0, 1, 2, 3, context=[ctx], tstamp=evTstamp)
        self.assertEqual(mok_complete_payload.call_count, 1)
        completeArgsList = mok_complete_payload.call_args_list[0][0]
        self.assertEqual(len(completeArgsList), 4)

        actualPayloadArg = completeArgsList[0]
        actualContextArg = completeArgsList[1]
        actualTstampArg = completeArgsList[2]
        actualPairs = actualPayloadArg.nv_pairs

        expectedPairs = {
            "e": "pp",
            "url": "example.com",
            "page": "Example",
            "refr": "docs.snowplowanalytics.com",
            "pp_mix": 0,
            "pp_max": 1,
            "pp_miy": 2,
            "pp_may": 3
        }
        self.assertDictEqual(actualPairs, expectedPairs)
        self.assertIs(actualContextArg[0], ctx)
        self.assertEqual(actualTstampArg, evTstamp)

    @async_patch('aio_snowplow_tracker.Tracker.complete_payload')
    async def test_track_ecommerce_transaction_item(self, mok_complete_payload: Any) -> None:
        e = create_mock_emitter()

        mok_complete_payload.side_effect = mocked_complete_payload

        t = Tracker(e)
        ctx = SelfDescribingJson("test.context.schema", {"user": "tester"})
        evTstamp = 1399021242030
        await t.track_ecommerce_transaction_item("1234", "sku1234", 3.14, 1, "itemName", "itemCategory", "itemCurrency", context=[ctx], tstamp=evTstamp)
        self.assertEqual(mok_complete_payload.call_count, 1)
        completeArgsList = mok_complete_payload.call_args_list[0][0]
        self.assertEqual(len(completeArgsList), 4)

        actualPayloadArg = completeArgsList[0]
        actualContextArg = completeArgsList[1]
        actualTstampArg = completeArgsList[2]
        actualPairs = actualPayloadArg.nv_pairs

        expectedPairs = {
            "e": "ti",
            "ti_id": "1234",
            "ti_sk": "sku1234",
            "ti_nm": "itemName",
            "ti_ca": "itemCategory",
            "ti_pr": 3.14,
            "ti_qu": 1,
            "ti_cu": "itemCurrency"
        }
        self.assertDictEqual(actualPairs, expectedPairs)
        self.assertIs(actualContextArg[0], ctx)
        self.assertEqual(actualTstampArg, evTstamp)

    @async_patch('aio_snowplow_tracker.Tracker.complete_payload')
    async def test_track_ecommerce_transaction_no_items(self, mok_complete_payload: Any) -> None:
        e = create_mock_emitter()

        mok_complete_payload.side_effect = mocked_complete_payload

        t = Tracker(e)
        ctx = SelfDescribingJson("test.context.schema", {"user": "tester"})
        evTstamp = 1399021242030
        await t.track_ecommerce_transaction("1234", 10, "transAffiliation", 2.5, 1.5, "transCity", "transState", "transCountry", "transCurrency", context=[ctx], tstamp=evTstamp)
        self.assertEqual(mok_complete_payload.call_count, 1)
        completeArgsList = mok_complete_payload.call_args_list[0][0]
        self.assertEqual(len(completeArgsList), 4)
        actualPayloadArg = completeArgsList[0]
        actualContextArg = completeArgsList[1]
        actualTstampArg = completeArgsList[2]
        actualPairs = actualPayloadArg.nv_pairs

        expectedPairs = {
            "e": "tr",
            "tr_id": "1234",
            "tr_tt": 10,
            "tr_af": "transAffiliation",
            "tr_tx": 2.5,
            "tr_sh": 1.5,
            "tr_ci": "transCity",
            "tr_st": "transState",
            "tr_co": "transCountry",
            "tr_cu": "transCurrency"
        }
        self.assertDictEqual(actualPairs, expectedPairs)
        self.assertIs(actualContextArg[0], ctx)
        self.assertEqual(actualTstampArg, evTstamp)

    @async_patch('aio_snowplow_tracker.Tracker.track_ecommerce_transaction_item')
    @async_patch('aio_snowplow_tracker.Tracker.complete_payload')
    async def test_track_ecommerce_transaction_with_items(self, mok_complete_payload: Any, mok_track_trans_item: Any) -> None:
        e = create_mock_emitter()

        mok_complete_payload.side_effect = mocked_complete_payload
        mok_track_trans_item.side_effect = mocked_track_trans_item

        t = Tracker(e)
        ctx = SelfDescribingJson("test.context.schema", {"user": "tester"})
        evTstamp = 1399021242030
        transItems = [
            {"sku": "sku1234", "quantity": 3, "price": 3.14},
            {"sku": "sku5678", "quantity": 1, "price": 2.72}
        ]
        await t.track_ecommerce_transaction("1234", 10, "transAffiliation", 2.5, 1.5, "transCity", "transState", "transCountry", "transCurrency", items=transItems, context=[ctx], tstamp=evTstamp)

        # Transaction
        callCompleteArgsList = mok_complete_payload.call_args_list
        firstCallArgsList = callCompleteArgsList[0][0]
        self.assertEqual(len(firstCallArgsList), 4)
        actualPayloadArg = firstCallArgsList[0]
        actualContextArg = firstCallArgsList[1]
        actualTstampArg = firstCallArgsList[2]
        actualPairs = actualPayloadArg.nv_pairs

        expectedTransPairs = {
            "e": "tr",
            "tr_id": "1234",
            "tr_tt": 10,
            "tr_af": "transAffiliation",
            "tr_tx": 2.5,
            "tr_sh": 1.5,
            "tr_ci": "transCity",
            "tr_st": "transState",
            "tr_co": "transCountry",
            "tr_cu": "transCurrency"
        }
        self.assertDictEqual(actualPairs, expectedTransPairs)
        self.assertIs(actualContextArg[0], ctx)
        self.assertEqual(actualTstampArg, evTstamp)

        # Items
        calls_to_track_trans_item = mok_track_trans_item.call_count
        self.assertEqual(calls_to_track_trans_item, 2)
        callTrackItemsArgsList = mok_track_trans_item.call_args_list
        # 1st item
        firstItemCallArgs = callTrackItemsArgsList[0][0]
        self.assertEqual((), firstItemCallArgs)
        firstItemCallKwargs = callTrackItemsArgsList[0][1]

        expectedFirstItemPairs = {
            'tstamp': evTstamp,
            'order_id': '1234',
            'currency': 'transCurrency',
            'sku': 'sku1234',
            'quantity': 3,
            "price": 3.14,
            'event_subject': None
        }
        self.assertDictEqual(firstItemCallKwargs, expectedFirstItemPairs)
        # 2nd item
        secItemCallArgs = callTrackItemsArgsList[1][0]
        self.assertEqual((), secItemCallArgs)
        secItemCallKwargs = callTrackItemsArgsList[1][1]

        expectedSecItemPairs = {
            'tstamp': evTstamp,
            'order_id': '1234',
            'currency': 'transCurrency',
            'sku': 'sku5678',
            'quantity': 1,
            "price": 2.72,
            'event_subject': None
        }
        self.assertDictEqual(secItemCallKwargs, expectedSecItemPairs)

    @async_patch('aio_snowplow_tracker.Tracker.track_unstruct_event')
    async def test_track_link_click(self, mok_track_unstruct: Any) -> None:
        e = create_mock_emitter()

        mok_track_unstruct.side_effect = mocked_track_unstruct

        t = Tracker(e)
        ctx = SelfDescribingJson("test.context.schema", {"user": "tester"})
        evTstamp = 1399021242030

        await t.track_link_click("example.com", "elemId", ["elemClass1", "elemClass2"], "_blank", "elemContent", context=[ctx], tstamp=evTstamp)

        expected = {
            "schema": LINK_CLICK_SCHEMA,
            "data": {
                "targetUrl": "example.com",
                "elementId": "elemId",
                "elementClasses": ["elemClass1", "elemClass2"],
                "elementTarget": "_blank",
                "elementContent": "elemContent"
            }
        }

        callArgs = mok_track_unstruct.call_args_list[0][0]
        self.assertEqual(len(callArgs), 4)
        self.assertDictEqual(callArgs[0].to_json(), expected)
        self.assertIs(callArgs[1][0], ctx)
        self.assertEqual(callArgs[2], evTstamp)

    @async_patch('aio_snowplow_tracker.Tracker.track_unstruct_event')
    async def test_track_link_click_optional_none(self, mok_track_unstruct: Any) -> None:
        e = create_mock_emitter()

        mok_track_unstruct.side_effect = mocked_track_unstruct

        t = Tracker(e)

        await t.track_link_click("example.com")

        expected = {
            "schema": LINK_CLICK_SCHEMA,
            "data": {
                "targetUrl": "example.com",
            }
        }

        callArgs = mok_track_unstruct.call_args_list[0][0]
        self.assertEqual(len(callArgs), 4)
        self.assertDictEqual(callArgs[0].to_json(), expected)
        self.assertTrue(callArgs[1] is None)
        self.assertTrue(callArgs[2] is None)

    @async_patch('aio_snowplow_tracker.Tracker.track_unstruct_event')
    async def test_track_add_to_cart(self, mok_track_unstruct: Any) -> None:
        e = create_mock_emitter()

        mok_track_unstruct.side_effect = mocked_track_unstruct

        t = Tracker(e)
        ctx = SelfDescribingJson("test.context.schema", {"user": "tester"})
        evTstamp = 1399021242030

        await t.track_add_to_cart("sku1234", 3, "testName", "testCategory", 3.14, "testCurrency", context=[ctx], tstamp=evTstamp)

        expected = {
            "schema": ADD_TO_CART_SCHEMA,
            "data": {
                "sku": "sku1234",
                "quantity": 3,
                "name": "testName",
                "category": "testCategory",
                "unitPrice": 3.14,
                "currency": "testCurrency"
            }
        }

        callArgs = mok_track_unstruct.call_args_list[0][0]
        self.assertEqual(len(callArgs), 4)
        self.assertDictEqual(callArgs[0].to_json(), expected)
        self.assertIs(callArgs[1][0], ctx)
        self.assertEqual(callArgs[2], evTstamp)

    @async_patch('aio_snowplow_tracker.Tracker.track_unstruct_event')
    async def test_track_add_to_cart_optional_none(self, mok_track_unstruct: Any) -> None:
        e = create_mock_emitter()

        mok_track_unstruct.side_effect = mocked_track_unstruct

        t = Tracker(e)

        await t.track_add_to_cart("sku1234", 1)

        expected = {
            "schema": ADD_TO_CART_SCHEMA,
            "data": {
                "sku": "sku1234",
                "quantity": 1
            }
        }

        callArgs = mok_track_unstruct.call_args_list[0][0]
        self.assertEqual(len(callArgs), 4)
        self.assertDictEqual(callArgs[0].to_json(), expected)
        self.assertTrue(callArgs[1] is None)
        self.assertTrue(callArgs[2] is None)

    @async_patch('aio_snowplow_tracker.Tracker.track_unstruct_event')
    async def test_track_remove_from_cart(self, mok_track_unstruct: Any) -> None:
        e = create_mock_emitter()

        mok_track_unstruct.side_effect = mocked_track_unstruct

        t = Tracker(e)
        ctx = SelfDescribingJson("test.context.schema", {"user": "tester"})
        evTstamp = 1399021242030

        await t.track_remove_from_cart("sku1234", 3, "testName", "testCategory", 3.14, "testCurrency", context=[ctx], tstamp=evTstamp)

        expected = {
            "schema": REMOVE_FROM_CART_SCHEMA,
            "data": {
                "sku": "sku1234",
                "quantity": 3,
                "name": "testName",
                "category": "testCategory",
                "unitPrice": 3.14,
                "currency": "testCurrency"
            }
        }

        callArgs = mok_track_unstruct.call_args_list[0][0]
        self.assertEqual(len(callArgs), 4)
        self.assertDictEqual(callArgs[0].to_json(), expected)
        self.assertIs(callArgs[1][0], ctx)
        self.assertEqual(callArgs[2], evTstamp)

    @async_patch('aio_snowplow_tracker.Tracker.track_unstruct_event')
    async def test_track_remove_from_cart_optional_none(self, mok_track_unstruct: Any) -> None:
        e = create_mock_emitter()

        mok_track_unstruct.side_effect = mocked_track_unstruct

        t = Tracker(e)

        await t.track_remove_from_cart("sku1234", 1)

        expected = {
            "schema": REMOVE_FROM_CART_SCHEMA,
            "data": {
                "sku": "sku1234",
                "quantity": 1
            }
        }

        callArgs = mok_track_unstruct.call_args_list[0][0]
        self.assertEqual(len(callArgs), 4)
        self.assertDictEqual(callArgs[0].to_json(), expected)
        self.assertTrue(callArgs[1] is None)
        self.assertTrue(callArgs[2] is None)

    @async_patch('aio_snowplow_tracker.Tracker.track_unstruct_event')
    async def test_track_form_change(self, mok_track_unstruct: Any) -> None:
        e = create_mock_emitter()

        mok_track_unstruct.side_effect = mocked_track_unstruct

        t = Tracker(e)
        ctx = SelfDescribingJson("test.context.schema", {"user": "tester"})
        evTstamp = 1399021242030

        await t.track_form_change("testFormId", "testElemId", "INPUT", "testValue", "text", ["testClass1", "testClass2"], context=[ctx], tstamp=evTstamp)

        expected = {
            "schema": FORM_CHANGE_SCHEMA,
            "data": {
                "formId": "testFormId",
                "elementId": "testElemId",
                "nodeName": "INPUT",
                "value": "testValue",
                "type": "text",
                "elementClasses": ["testClass1", "testClass2"]
            }
        }

        callArgs = mok_track_unstruct.call_args_list[0][0]
        self.assertEqual(len(callArgs), 4)
        self.assertDictEqual(callArgs[0].to_json(), expected)
        self.assertIs(callArgs[1][0], ctx)
        self.assertEqual(callArgs[2], evTstamp)

    @async_patch('aio_snowplow_tracker.Tracker.track_unstruct_event')
    async def test_track_form_change_optional_none(self, mok_track_unstruct: Any) -> None:
        e = create_mock_emitter()

        mok_track_unstruct.side_effect = mocked_track_unstruct

        t = Tracker(e)
        await t.track_form_change("testFormId", "testElemId", "INPUT", "testValue")

        expected = {
            "schema": FORM_CHANGE_SCHEMA,
            "data": {
                "formId": "testFormId",
                "elementId": "testElemId",
                "nodeName": "INPUT",
                "value": "testValue",
            }
        }

        callArgs = mok_track_unstruct.call_args_list[0][0]
        self.assertEqual(len(callArgs), 4)
        self.assertDictEqual(callArgs[0].to_json(), expected)
        self.assertTrue(callArgs[1] is None)
        self.assertTrue(callArgs[2] is None)

    @async_patch('aio_snowplow_tracker.Tracker.track_unstruct_event')
    async def test_track_form_submit(self, mok_track_unstruct: Any) -> None:
        e = create_mock_emitter()

        mok_track_unstruct.side_effect = mocked_track_unstruct

        t = Tracker(e)
        ctx = SelfDescribingJson("test.context.schema", {"user": "tester"})
        evTstamp = 1399021242030
        elems = [
            {
                "name": "user_email",
                "value": "fake@email.fake",
                "nodeName": "INPUT",
                "type": "email"
            }
        ]

        await t.track_form_submit("testFormId", ["testClass1", "testClass2"], elems, context=[ctx], tstamp=evTstamp)

        expected = {
            "schema": FORM_SUBMIT_SCHEMA,
            "data": {
                "formId": "testFormId",
                "formClasses": ["testClass1", "testClass2"],
                "elements": elems
            }
        }

        callArgs = mok_track_unstruct.call_args_list[0][0]
        self.assertEqual(len(callArgs), 4)
        self.assertDictEqual(callArgs[0].to_json(), expected)
        self.assertIs(callArgs[1][0], ctx)
        self.assertEqual(callArgs[2], evTstamp)

    @async_patch('aio_snowplow_tracker.Tracker.track_unstruct_event')
    async def test_track_form_submit_invalid_element_type(self, mok_track_unstruct: Any) -> None:
        e = create_mock_emitter()

        mok_track_unstruct.side_effect = mocked_track_unstruct

        t = Tracker(e)
        ctx = SelfDescribingJson("test.context.schema", {"user": "tester"})
        evTstamp = 1399021242030
        elems = [
            {
                "name": "user_email",
                "value": "fake@email.fake",
                "nodeName": "INPUT",
                "type": "invalid"
            }
        ]

        with self.assertRaises(ValueError):
            await t.track_form_submit("testFormId", ["testClass1", "testClass2"], elems, context=[ctx], tstamp=evTstamp)

    @async_patch('aio_snowplow_tracker.Tracker.track_unstruct_event')
    async def test_track_form_submit_invalid_element_type_disabled_contracts(self, mok_track_unstruct: Any) -> None:
        e = create_mock_emitter()

        mok_track_unstruct.side_effect = mocked_track_unstruct

        t = Tracker(e)
        ctx = SelfDescribingJson("test.context.schema", {"user": "tester"})
        evTstamp = 1399021242030
        elems = [
            {
                "name": "user_email",
                "value": "fake@email.fake",
                "nodeName": "INPUT",
                "type": "invalid"
            }
        ]

        with ContractsDisabled():
            await t.track_form_submit("testFormId", ["testClass1", "testClass2"], elems, context=[ctx], tstamp=evTstamp)

        expected = {
            "schema": FORM_SUBMIT_SCHEMA,
            "data": {
                "formId": "testFormId",
                "formClasses": ["testClass1", "testClass2"],
                "elements": elems
            }
        }

        callArgs = mok_track_unstruct.call_args_list[0][0]
        self.assertEqual(len(callArgs), 4)
        self.assertDictEqual(callArgs[0].to_json(), expected)
        self.assertIs(callArgs[1][0], ctx)
        self.assertEqual(callArgs[2], evTstamp)

    @async_patch('aio_snowplow_tracker.Tracker.track_unstruct_event')
    async def test_track_form_submit_optional_none(self, mok_track_unstruct: Any) -> None:
        e = create_mock_emitter()

        mok_track_unstruct.side_effect = mocked_track_unstruct

        t = Tracker(e)
        await t.track_form_submit("testFormId")

        expected = {
            "schema": FORM_SUBMIT_SCHEMA,
            "data": {
                "formId": "testFormId"
            }
        }

        callArgs = mok_track_unstruct.call_args_list[0][0]
        self.assertEqual(len(callArgs), 4)
        self.assertDictEqual(callArgs[0].to_json(), expected)
        self.assertTrue(callArgs[1] is None)
        self.assertTrue(callArgs[2] is None)

    @async_patch('aio_snowplow_tracker.Tracker.track_unstruct_event')
    async def test_track_form_submit_empty_elems(self, mok_track_unstruct: Any) -> None:
        e = create_mock_emitter()

        mok_track_unstruct.side_effect = mocked_track_unstruct

        t = Tracker(e)
        await t.track_form_submit("testFormId", elements=[])

        expected = {
            "schema": FORM_SUBMIT_SCHEMA,
            "data": {
                "formId": "testFormId"
            }
        }

        callArgs = mok_track_unstruct.call_args_list[0][0]
        self.assertEqual(len(callArgs), 4)
        self.assertDictEqual(callArgs[0].to_json(), expected)

    @async_patch('aio_snowplow_tracker.Tracker.track_unstruct_event')
    async def test_track_site_search(self, mok_track_unstruct: Any) -> None:
        e = create_mock_emitter()

        mok_track_unstruct.side_effect = mocked_track_unstruct

        t = Tracker(e)
        ctx = SelfDescribingJson("test.context.schema", {"user": "tester"})
        evTstamp = 1399021242030

        await t.track_site_search(["track", "search"], {"new": True}, 100, 10, context=[ctx], tstamp=evTstamp)

        expected = {
            "schema": SITE_SEARCH_SCHEMA,
            "data": {
                "terms": ["track", "search"],
                "filters": {"new": True},
                "totalResults": 100,
                "pageResults": 10
            }
        }

        callArgs = mok_track_unstruct.call_args_list[0][0]
        self.assertEqual(len(callArgs), 4)
        self.assertDictEqual(callArgs[0].to_json(), expected)
        self.assertIs(callArgs[1][0], ctx)
        self.assertEqual(callArgs[2], evTstamp)

    @async_patch('aio_snowplow_tracker.Tracker.track_unstruct_event')
    async def test_track_site_search_optional_none(self, mok_track_unstruct: Any) -> None:
        e = create_mock_emitter()

        mok_track_unstruct.side_effect = mocked_track_unstruct

        t = Tracker(e)
        await t.track_site_search(["track", "search"])

        expected = {
            "schema": SITE_SEARCH_SCHEMA,
            "data": {
                "terms": ["track", "search"]
            }
        }

        callArgs = mok_track_unstruct.call_args_list[0][0]
        self.assertEqual(len(callArgs), 4)
        self.assertDictEqual(callArgs[0].to_json(), expected)
        self.assertTrue(callArgs[1] is None)
        self.assertTrue(callArgs[2] is None)

    @async_patch('aio_snowplow_tracker.Tracker.track_unstruct_event')
    async def test_track_screen_view(self, mok_track_unstruct: Any) -> None:
        e = create_mock_emitter()

        mok_track_unstruct.side_effect = mocked_track_unstruct

        t = Tracker(e)
        ctx = SelfDescribingJson("test.context.schema", {"user": "tester"})
        evTstamp = 1399021242030

        await t.track_screen_view("screenName", "screenId", context=[ctx], tstamp=evTstamp)

        expected = {
            "schema": SCREEN_VIEW_SCHEMA,
            "data": {
                "name": "screenName",
                "id": "screenId"
            }
        }

        callArgs = mok_track_unstruct.call_args_list[0][0]
        self.assertEqual(len(callArgs), 4)
        self.assertDictEqual(callArgs[0].to_json(), expected)
        self.assertIs(callArgs[1][0], ctx)
        self.assertEqual(callArgs[2], evTstamp)
