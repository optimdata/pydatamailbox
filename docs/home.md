# Usage

```python
from pydatamailbox import DataMailbox

client = DataMailbox(
    account="test",
    username="test",
    password="test",
    devid="test",
)

# Retrieve status
client.getstatus()

# Retrieve all ewons
client.getewons()

# Retrieve an ewon by id
client.getewon(ewonid=1)

# Retrieve an ewon by name
client.getewon(name="test")

# Iterate on all the data by chunk
for data in client.iterate_syncdata():
    pass

# get tag dat for a given period
client.getdata(1, 1, '2021-07-15T12:30:20', '2021-07-15T12:30:33')
```
