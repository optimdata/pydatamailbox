# -*- coding: utf-8 -*-

import json
import requests

from pydatamailbox.exceptions import (
    DataMailboxArgsError,
    DataMailboxConnectionError,
    DataMailboxResponseError,
    DataMailboxStatusError,
)


class DataMailbox(object):
    """
    Talk2M DataMailbox api client.

    https://developer.ewon.biz/content/dmweb-api
    This client only supports: getstatus, getewons, getewon, syncdata
    """

    def __init__(self, account, username, password, devid):
        self.account = account
        self.username = username
        self.password = password
        self.devid = devid
        self.data = {
            "t2maccount": account,
            "t2musername": username,
            "t2mpassword": password,
            "t2mdevid": devid,
        }
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/x-www-form-urlencoded"}
        )
        self.base_url = "https://data.talk2m.com/"

    def __str__(self):
        return self.account

    def _build_url(self, url):
        return self.base_url + url

    def _request(self, url, data, check_success=True):
        try:
            response = self.session.post(url=url, data=data)
        except requests.exceptions.ConnectionError as e:  # pragma: nocover
            raise DataMailboxConnectionError(str(e))  # pragma: nocover
        if response.status_code != 200:
            raise DataMailboxStatusError(
                "Bad status from talk2m: %s" % response.status_code
            )
        try:
            content = response.json()
        except json.decoder.JSONDecodeError:
            raise DataMailboxResponseError(
                "Cannot deserialize json from %s" % response.content
            )
        if check_success and not content["success"]:
            raise DataMailboxStatusError(
                "Got error code=%(code)s, message=%(message)s" % content
            )
        return response.json()

    def getstatus(self):
        """
        Returns the storage consumption of the account and of each Ewon.

        The result contains the following information:

        - number of history points currently stored in the DataMailbox for this account,
        - number of Ewons which send data to the DataMailbox.

        The result also contains the following information for each Ewon listed:

        - its id,
        - its name,
        - its number of history points currently stored in the DataMailbox,
        - its date of the first history point currently saved in the DataMailbox,
        - its date of the last history point currently saved in the DataMailbox.
        """
        return self._request(
            url=self._build_url("getstatus"), data=self.data, check_success=False
        )

    def getewons(self):
        """
        Returns the list of Ewons sending data to be stored in the DataMailbox. The result contains the following information for each Ewon:

        - its name and id,
        - its number of tags,
        - the date of its last data upload to the Data Mailbox.
        """
        return self._request(url=self._build_url("getewons"), data=self.data)

    def getewon(self, ewonid=None, name=None):
        """
        Returns the configuration of the targeted Ewon as seen by the DataMailbox.

        :param ewonid: ID of the Ewon as returned by the “getewons” API request.
        :param name: Name of the Ewon as returned by the “getewons” API request.
        """
        if not ewonid and not name:
            raise DataMailboxArgsError("id and name cannot be null in the same time")
        data = {**self.data}
        if ewonid:
            data["id"] = ewonid
        else:
            data["name"] = name
        return self._request(url=self._build_url("getewon"), data=data)

    def syncdata(self, last_transaction_id=None):
        """
        Retrieves all data of a Talk2M account incrementally.

        :param last_transaction_id: The ID of the last set of data sent by the DataMailbox. By referencing the “lastTransactionId”, the DataMailbox will send a set of data more recent than the data linked to this transaction ID.
        """
        data = {**self.data, "createTransaction": 1}
        if last_transaction_id:
            data["lastTransactionId"] = last_transaction_id
        return self._request(url=self._build_url("syncdata"), data=data)

    def iterate_syncdata(self, last_transaction_id=None):
        """
        Returns an iterator on syncdata.


        The syncdata API returns partial data and indicates if there are more data to load with `moreDataAvailable`.
        This helper will act as an iterator and yield an api response until there are no more data.

        :param last_transaction_id: The ID of the last set of data sent by the DataMailbox. By referencing the “lastTransactionId”, the DataMailbox will send a set of data more recent than the data linked to this transaction ID.
        """
        while True:
            ret = self.syncdata(last_transaction_id)
            yield ret
            if not ret.get("moreDataAvailable"):
                break
            last_transaction_id = ret["transactionId"]
