import ast
import cgi
import hashlib
import html.parser
import os
import pprint
import shutil
import sys
import tempfile
import time
import urllib

import greader

g_Images = set()

def nameify(s):
    return s.replace("/", "_").replace(":", "_")

def fetch_retry(url):
    tries = 0
    while True:
        try:
            return urllib.request.urlopen(url)
        except urllib.error.URLError as x:
            tries += 1
            if tries < 3:
                print("  retry: {}".format(x))
            else:
                raise

def lget(attrs, name):
    try:
        i = [x[0] for x in attrs].index(name)
        return attrs[i][1]
    except ValueError:
        return None

class ImageRewriter(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.output = ""
        self.images = []
    def handle_starttag(self, tag, attrs):
        if tag == "img":
            if lget(attrs, "height") != "1" or lget(attrs, "width") != "1":
                i = [x[0] for x in attrs].index("src")
                src = attrs[i][1]
                id = hashlib.sha1(src.encode("utf-8")).hexdigest()

                print("fetching {}".format(src))
                try:
                    r = fetch_retry(src)
                    ct = r.getheader("Content-Type")
                    if ';' in ct:
                        # handle bizarre Content-Type: image/png; charset=UTF-8
                        ct = ct[:ct.index(';')]
                    ext = {
                        "image/gif":  ".gif",
                        "image/jpeg": ".jpg",
                        "image/png":  ".png",
                    }.get(ct)
                    if ext is not None:
                        with open(os.path.join(dir, id + ext), "wb") as f:
                            f.write(r.read())
                        attrs[i] = (attrs[i][0], id + ext)
                        g_Images.add((id, id + ext, ct))
                    else:
                        print("  {}".format(ct))
                    self.output += "<{0}{1} />".format(tag, "".join((' {0}="{1}"'.format(x[0], cgi.escape(x[1], True)) if x[1] else " {0}".format(x[0])) for x in attrs))
                except Exception as x:
                    print("oh well:", x)
                    self.output += self.get_starttag_text()
                    return
        else:
            self.output += self.get_starttag_text()
    def handle_endtag(self, tag):
        self.output += "</{}>".format(tag)
    def handle_data(self, data):
        self.output += data
    def handle_charref(self, name):
        self.output += "&#{};".format(name)
    def handle_entityref(self, name):
        self.output += "&{};".format(name)

KeepUnread = False
Label = None

i = 1
while i < len(sys.argv):
    a = sys.argv[i]
    if a in ("--keep-unread", "-k"):
        KeepUnread = True
    elif a in ("--label", "-l"):
        i += 1
        Label = sys.argv[i]
    else:
        print("Unknown command line option: {}".format(a))
        sys.exit(1)
    i += 1

with open("rss2mobi.config") as f:
    Config = ast.literal_eval(f.read())

today = "{0.tm_year:04}-{0.tm_mon:02}-{0.tm_mday:02}".format(time.localtime(time.time()))

reader = greader.GoogleReader(Config['account'], Config['password'])
reader.login()
feed = reader.reading_list(label=Label)

feed['items'].reverse()
feed['items'] = [x for x in feed['items'] if 'alternate' in x]

if os.access("tmp", os.F_OK):
    shutil.rmtree("tmp")
dir = "tmp" #tempfile.mkdtemp(dir=".")
os.mkdir(dir)
try:
    with open(os.path.join(dir, "reading_list.out"), "w", encoding="utf-8") as f:
        pprint.pprint(feed, stream=f)
    for e in feed['items']:
        #pprint.pprint(e)
        fname = nameify(e['id']) + ".html"
        e['fname'] = fname
        f = open(os.path.join(dir, fname), "w", encoding="utf-8")
        print("""<?xml version="1.0" encoding="UTF-8"?>""", file=f)
        print("""<html xmlns="http://www.w3.org/1999/xhtml">""", file=f)
        print("<body>", file=f)
        print("<h1>{0}</h1>".format(e['origin']['title']), file=f)
        print("""<h2><a href="{0}">{1}</a></h2>""".format(e['alternate'][0]['href'], e['title']), file=f)
        which = "content" if "content" in e else "summary"
        if which in e:
            content = e[which]['content']
        else:
            content = ""
        rw = ImageRewriter()
        rw.feed(content)
        print(rw.output, file=f)
        print("</body>", file=f)
        print("</html>", file=f)
        f.close()

    with open(os.path.join(dir, "contents.html"), "w", encoding="utf-8") as f:
        print("""<?xml version="1.0" encoding="UTF-8"?>""", file=f)
        print("""<html xmlns="http://www.w3.org/1999/xhtml>""", file=f)
        print("<body>", file=f)
        print("<h1>Google Reader {}</h1>".format(today), file=f)
        print("<h2>{0}</h2>".format(len(feed['items'])), file=f)
        for e in feed['items']:
            print("""<p><a href="{0}">{2} ({1})</a></p>""".format(e['fname'], e['origin']['title'], e['title']), file=f)
        print("</body>", file=f)
        print("</html>", file=f)

    with open(os.path.join(dir, "toc.ncx"), "w", encoding="utf-8") as f:
        print("""<?xml version="1.0" encoding="UTF-8"?>""", file=f)
        print("""<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="en-US">""", file=f)
        print("""<docTitle><text>Google Reader {}</text></docTitle>""".format(today), file=f)
        print("<navMap>", file=f)
        print("""<navPoint class="toc" id="toc" playOrder="1">""", file=f)
        print("""  <navLabel><text>Table of Contents</text></navLabel>""", file=f)
        print("""  <content src="contents.html" />""", file=f)
        print("""</navPoint>""", file=f)
        order = 2
        for e in feed['items']:
            print("""<navPoint class="chapter" id="{0}" playOrder="{1}">""".format(e['fname'], order), file=f)
            print("""  <navLabel><text>{}</text></navLabel>""".format(e['title']), file=f)
            print("""  <content src="{}" />""".format(e['fname']), file=f)
            print("""</navPoint>""", file=f)
            order += 1
        print("</navMap>", file=f)
        print("</ncx>", file=f)

    opfn = "reader-{0}.opf".format(today)
    f = open(os.path.join(dir, opfn), "w")
    print("""<?xml version="1.0" encoding="UTF-8"?>
    <package unique-identifier="uid" xmlns:dc="Dublin Core">
        <metadata>
            <dc-metadata>
                <dc:Identifier id="uid">reader-{0}</dc:Identifier>
                <dc:Title>Reader {0} ({1})</dc:Title>
                <dc:Language>EN</dc:Language>
                <dc:Date>{0}</dc:Date>
            </dc-metadata>
        </metadata>
        <manifest>""".format(today, len(feed['items'])), file=f)
    print("""<item id="contents" href="contents.html" media-type="text/html" />""", file=f)
    for e in feed['items']:
        print("""<item id="{0}" href="{0}.html" media-type="text/html" />""".format(nameify(e['id'])), file=f)
    for i in g_Images:
        print("""<item id="{0}" href="{1}" media-type="{2}" />""".format(*i), file=f)
    print("""<item id="toc" media-type="application/x-dtbncx+xml" href="toc.ncx" />""", file=f)
    print("""</manifest>
        <spine toc="toc">""", file=f)
    print("""<itemref idref="contents" />""", file=f)
    for e in feed['items']:
        print("""<itemref idref="{0}" />""".format(nameify(e['id'])), file=f)
    print("""</spine>
    </package>""", file=f)
    f.close()
    os.system("{0} {1}".format(Config['kindlegen'], os.path.join(dir, opfn)))
    assert os.access(os.path.join(dir, "reader-{0}.mobi".format(today)), os.F_OK)
    if not KeepUnread:
        for e in feed['items']:
            reader.mark_read(e['origin']['streamId'], e['id'])
finally:
    pass #shutil.rmtree(dir)
