# -*- coding: utf-8 -*-

import requests_mock
import pytest
import os
import sys

BASE_DIRECTORY = os.path.join(os.path.dirname(__file__), "..")  # NOQA
sys.path.insert(0, BASE_DIRECTORY)  # NOQA

from pydatamailbox import DataMailbox, Talk2mArgsError, Talk2mBaseException


class Talk2mMocker(requests_mock.mock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def syncdata(request, context):
            return {
                "success": True,
                "transactionId": 1,
                "ewons": [
                    {
                        **ewon,
                        "lastSynchroDate": "2018-10-23T13:04:51Z",
                        "tags": [
                            {
                                **tag,
                                "history": [
                                    {"date": "2018-10-11T01:07:08Z", "value": 0.0}
                                ],
                            }
                        ],
                    }
                ],
                "moreDataAvailable": "lastTransactionId" not in request._request.body,
            }

        ewon = {"id": 1, "name": "test"}
        tag = {
            "id": 1,
            "name": "test",
            "dataType": "Float",
            "description": "Test",
            "alarmHint": "",
            "value": 0.0,
            "quality": "good",
            "ewonTagId": 1,
        }
        self.post(
            "https://data.talk2m.com/getstatus",
            json={
                "historyCount": 2,
                "ewonsCount": 1,
                "ewons": [
                    {
                        **ewon,
                        "historyCount": 1,
                        "firstHistoryDate": "2018-10-10T23:59:48Z",
                        "lastHistoryDate": "2018-10-23T12:45:44Z",
                    }
                ],
            },
        )
        self.post(
            "https://data.talk2m.com/getewons",
            json={
                "success": True,
                "ewons": [{**ewon, "lastSynchroDate": "2018-10-23T12:59:46Z"}],
            },
        )
        self.post(
            "https://data.talk2m.com/getewon",
            json={
                "success": True,
                "id": 1,
                "name": "HMS_Office_BE",
                "tags": [tag],
                "lastSynchroDate": "2018-10-23T13:04:51Z",
            },
        )
        self.post("https://data.talk2m.com/syncdata", json=syncdata)


def test_talk2m():
    client = DataMailbox(account="test", username="test", password="test", devid="test")
    print(client)
    with Talk2mMocker():
        assert client.getstatus()
        assert client.getewons()
        assert client.getewon(ewonid=1)
        assert client.getewon(name="test")
        assert client.syncdata()
        assert client.syncdata(last_transaction_id=1)
        assert list(client.iterate_syncdata())
        with pytest.raises(Talk2mArgsError):
            client.getewon()

    with requests_mock.mock() as mock:
        mock.post(
            "https://data.talk2m.com/getewons",
            json={"success": False, "message": "error", "code": 1},
        )
        with pytest.raises(Talk2mBaseException):
            client.getewons()

    with requests_mock.mock() as mock:
        mock.post("https://data.talk2m.com/getewons", status_code=502)
        with pytest.raises(Talk2mBaseException):
            client.getewons()

    with requests_mock.mock() as mock:
        mock.post("https://data.talk2m.com/getewons", text="no json")
        with pytest.raises(Talk2mBaseException):
            client.getewons()
