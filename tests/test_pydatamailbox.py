# -*- coding: utf-8 -*-

import requests_mock
import pytest
import os
import sys

BASE_DIRECTORY = os.path.join(os.path.dirname(__file__), "..")  # NOQA
sys.path.insert(0, BASE_DIRECTORY)  # NOQA

from pydatamailbox import (
    DataMailbox,
    DataMailboxArgsError,
    DataMailboxBaseException,
    M2Web,
)


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

        def getdata(request, context):
            return {
                "ewons": [
                    {
                        **ewon,
                        "tags": [
                            {
                                **tag,
                                "history": [
                                    {"date": "2021-07-15T12:30:22Z", "value": 1},
                                    {"date": "2021-07-15T12:30:28Z", "value": 0},
                                    {"date": "2021-07-15T12:30:29Z", "value": 1},
                                ],
                            }
                        ],
                        "lastSynchroDate": "2021-07-16T14:59:40Z",
                        "timeZone": "Europe/Paris",
                    }
                ],
                "success": True,
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
        self.post("https://data.talk2m.com/getdata", json=getdata)
        self.post(
            "https://m2web.talk2m.com/t2mapi/getaccountinfo",
            json={
                "accountReference": "0",
                "accountName": "test",
                "company": "Test",
                "customAttributes": [
                    "Custom Field 1",
                    "Custom Field 2",
                    "Custom Field 3",
                ],
                "pools": [{"id": 1, "name": "Device pool"}],
                "accountType": "Free",
                "success": True,
            },
        )
        self.post(
            "https://m2web.talk2m.com/t2mapi/getewons",
            json={
                "success": True,
                "ewons": [
                    {
                        "id": 1,
                        "name": "test",
                        "encodedName": "test",
                        "status": "online",
                        "description": "",
                        "customAttributes": ["", "", ""],
                        "m2webServer": "eu1.m2web.talk2m.com",
                        "lanDevices": [],
                        "ewonServices": [],
                    }
                ],
            },
        )
        self.post(
            "https://m2web.talk2m.com/t2mapi/getewon",
            json={
                "ewon": {
                    "id": 1,
                    "name": "test",
                    "encodedName": "test",
                    "status": "online",
                    "description": "",
                    "customAttributes": ["", "", ""],
                    "m2webServer": "eu1.m2web.talk2m.com",
                    "lanDevices": [],
                    "ewonServices": [],
                },
                "success": True,
            },
        )


def test_datamailbox():
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
        assert client.getdata(1, 1, "2021-07-15T12:30:20", "2021-07-15T12:30:33")
        with pytest.raises(DataMailboxArgsError):
            client.getewon()

    with requests_mock.mock() as mock:
        mock.post(
            "https://data.talk2m.com/getewons",
            json={"success": False, "message": "error", "code": 1},
        )
        with pytest.raises(DataMailboxBaseException):
            client.getewons()

    with requests_mock.mock() as mock:
        mock.post("https://data.talk2m.com/getewons", status_code=502)
        with pytest.raises(DataMailboxBaseException):
            client.getewons()

    with requests_mock.mock() as mock:
        mock.post("https://data.talk2m.com/getewons", text="no json")
        with pytest.raises(DataMailboxBaseException):
            client.getewons()


def test_m2web():
    client = M2Web(account="test", username="test", password="test", devid="test")
    print(client)
    with Talk2mMocker():
        assert client.getaccountinfo()
        assert client.getewons()
        assert client.getewon(ewonid=1)
        assert client.getewon(name="test")
        with pytest.raises(DataMailboxArgsError):
            client.getewon()

    with requests_mock.mock() as mock:
        mock.post(
            "https://m2web.talk2m.com/t2mapi/getaccountinfo",
            json={"success": False, "message": "error", "code": 1},
        )
        with pytest.raises(DataMailboxBaseException):
            client.getaccountinfo()

    with requests_mock.mock() as mock:
        mock.post("https://m2web.talk2m.com/t2mapi/getewons", status_code=502)
        with pytest.raises(DataMailboxBaseException):
            client.getewons()

    with requests_mock.mock() as mock:
        mock.post("https://m2web.talk2m.com/t2mapi/getewons", text="no json")
        with pytest.raises(DataMailboxBaseException):
            client.getewons()
