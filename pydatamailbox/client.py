# -*- coding: utf-8 -*-

import json
import requests

from pydatamailbox.exceptions import (
    DataMailboxArgsError,
    DataMailboxConnectionError,
    DataMailboxResponseError,
    DataMailboxStatusError,
)

__all__ = ("DataMailbox", "M2Web")


class EwonClient(object):
    def __init__(self, base_url, account, data=None, timeout=None):
        self.account = account
        self.timeout = timeout
        self.data = data
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/x-www-form-urlencoded"}
        )

    def __str__(self):
        return self.account

    def _build_url(self, url):
        return self.base_url + url

    def _request(self, url, data, check_success=True):
        try:
            response = self.session.post(url=url, data=data, timeout=self.timeout)
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


class DataMailbox(EwonClient):
    """
    Talk2M `DataMailbox api client <https://developer.ewon.biz/content/dmweb-api>`_.
    This client only supports: getstatus, getewons, getewon, syncdata, getdata

    The authentication is done by providing either `username` and `password` or `token`.
    """

    def __init__(self, account, devid, timeout=None, **kwargs):
        data = {"t2mdevid": devid}
        if "token" in kwargs:
            data["t2mtoken"] = kwargs["token"]
        else:
            data["t2maccount"] = account
            data["t2musername"] = kwargs["username"]
            data["t2mpassword"] = kwargs["password"]
        super().__init__("https://data.talk2m.com/", account, data, timeout)

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

    def syncdata(
        self, last_transaction_id=None, create_transaction=True, ewon_ids=None
    ):
        """
        Retrieves all data of a Talk2M account incrementally.
        You must be cautious when using the combination of `last_transaction_id`, `create_transaction` and `ewon_ids`.
        last_transaction_dd is first used to determine what set of data — newer than this transaction id and from all
        the Ewon gateways — must be returned from the DataMailbox, then ewon_dds filters this set of data to send data
        only from the desired Ewon gateways.
        If a first request is called with `last_transaction_id`, `create_transaction` and `ewon_ids`, the following request
        — implying a new `last_transaction_id` — does not contain values history from the previous `last_transaction_id`
        of the Ewon gateways that were not in the `ewon_ids` from previous request.

        :param int last_transaction_id: The id of the last set of data sent by the DataMailbox. By referencing the `last_transaction_id`, the DataMailbox will send a set of data more recent than the data linked to this transaction ID.
        :param bool create_transaction: The indication to the server that a new transaction ID should be created for this request.
        :param list ewon_ids: A list of Ewon gateway IDs. If ewonIds is used, DataMailbox sends values history of the targeted Ewon gateways. If not used, DataMailbox sends the values history of all Ewon gateways.
        """
        data = {**self.data, "createTransaction": create_transaction}
        if last_transaction_id:
            data["lastTransactionId"] = last_transaction_id
        if ewon_ids:
            data["ewonIds"] = ",".join([str(ewon_id) for ewon_id in ewon_ids])
        return self._request(url=self._build_url("syncdata"), data=data)

    def getdata(self, ewon_id, tag_id, from_ts, to_ts, limit=None):
        """
        ``getdata`` is used as a “one-shot” request to retrieve filtered data based on specific
        criteria. It is not destined to grab historical data with the same timestamp or enormous
        data involving the use of the moreData filter.

        :param int ewon_id: The ID of the single Ewon gateway for which data from DataMailbox is requested.
        :param int tag_id: ID of the single tag for which data from DataMailbox is requested.
        :param str from_ts: Timestamp after which data should be returned. No data older than this time stamp will be sent in ISO format.
        :param str to_ts: Timestamp before which data should be returned. No data newer than this time stamp will be sent in ISO format
        :param int limit: The maximum amount of historical data returned. The historical data is the historical tag values but also the historical alarms. If you set the limit to 4, the response will consist in 4 historical tag values and 4 historical alarms (if available) for each tag of each Ewon gateway allowed bu the Talk2M token. If the size of the historical data saved in the DataMailbox exceeds this limit, only the oldest historical data will be returned and the result contains a moreDataAvailable value indicating that more data is available on the server. If limit is not used or is too high, the DataMailbox uses a limit pre-defined in the system (server-side).
        """
        data = {
            **self.data,
            "ewonId": ewon_id,
            "tagId": tag_id,
            "from": from_ts,
            "to": to_ts,
        }
        if limit:
            data["limit"] = limit
        return self._request(url=self._build_url("getdata"), data=data)

    def iterate_syncdata(self, last_transaction_id=None, ewon_ids=None):
        """
        Returns an iterator on syncdata.


        The syncdata API returns partial data and indicates if there are more data to load with `moreDataAvailable`.
        This helper will act as an iterator and yield an api response until there are no more data.

        :param last_transaction_id: The ID of the last set of data sent by the DataMailbox. By referencing the “lastTransactionId”, the DataMailbox will send a set of data more recent than the data linked to this transaction ID.
        :param list ewon_ids: A list of Ewon gateway IDs. If ewonIds is used, DataMailbox sends values history of the targeted Ewon gateways. If not used, DataMailbox sends the values history of all Ewon gateways.
        """
        while True:
            ret = self.syncdata(last_transaction_id, ewon_ids=ewon_ids)
            yield ret
            if not ret.get("moreDataAvailable"):
                break
            last_transaction_id = ret["transactionId"]


class M2Web(EwonClient):
    """
    Talk2M `M2Web api client <https://developer.ewon.biz/content/m2web-api-0>`_.

    This client only supports: getaccountinfo, getewons, getewon
    """

    def __init__(self, account, username, password, devid, timeout=None):
        data = {
            "t2maccount": account,
            "t2musername": username,
            "t2mpassword": password,
            "t2mdeveloperid": devid,
        }
        super().__init__("https://m2web.talk2m.com/t2mapi/", account, data, timeout)

    def getaccountinfo(self):
        """
        Retrieves the basic account information (reference, name, company).

        It also retrieves the set of pools visible by user : pairs name/id as well as the name of each custom attribute.
        There are always 3 custom attributes listed. Some or all of them may be empty.
        The “accountType” attribute will either be “Free” (for non paying account) or “Pro” (for paying account).
        """
        return self._request(
            url=self._build_url("getaccountinfo"), data=self.data, check_success=True
        )

    def getewons(self, pool=None):
        """
        Returns the set of Ewons visible by user along with their properties: displayable names, link names, status, description, the 3 custom attributes, preferred m2web server hostname (currently always m2web.talk2m.com).
        :param int pool: `pool` is the optional numerical id of the pool from which the Ewons should be retrieved. Pool id's are retrieved using a `getaccountinfo` call. If `pool` is not specified, all visible Ewons are listed in the response.
        """
        data = {**self.data}
        if pool is not None:
            data["pool"] = pool
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
