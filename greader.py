import json
import pprint
import urllib.request

class GoogleReader:
    def __init__(self, account, password):
        self.account = account
        self.password = password

    def login(self):
        r = urllib.request.urlopen("https://www.google.com/accounts/ClientLogin?service=reader&Email={0}&Passwd={1}".format(self.account, self.password))
        page = r.read().decode("ascii")
        self.auth = dict(x.split("=") for x in page.split("\n") if x)["Auth"]
        print("Auth:", self.auth)
        r = urllib.request.urlopen(urllib.request.Request("http://www.google.com/reader/api/0/token", headers={"Authorization": "GoogleLogin auth={0}".format(self.auth)}))
        self.token = r.read()
        print("Token:", self.token)

    def reading_list(self):
        retval = None
        continuation = None
        while True:
            r = urllib.request.urlopen(urllib.request.Request("http://www.google.com/reader/api/0/stream/contents/user/-/state/com.google/reading-list?xt=user/-/state/com.google/read{0}".format("&c={0}".format(continuation) if continuation else ""), headers={"Authorization": "GoogleLogin auth={0}".format(self.auth)}))
            data = json.loads(r.read().decode("utf-8"))
            if retval is None:
                retval = data
            else:
                retval['items'].extend(data['items'])
            print(len(data['items']))
            if 'continuation' not in data:
                break
            continuation = data['continuation']
        return retval
