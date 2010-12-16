import ast
import os
import pprint
import shutil
import tempfile

import greader

with open("rss2mobi.config") as f:
    Config = ast.literal_eval(f.read())

reader = greader.GoogleReader(Config['account'], Config['password'])
reader.login()
feed = reader.reading_list()

if os.access("tmp", os.F_OK):
    shutil.rmtree("tmp")
dir = "tmp" #tempfile.mkdtemp(dir=".")
os.mkdir(dir)
try:
    for e in feed['items']:
        #pprint.pprint(e)
        f = open(os.path.join(dir, e['id'].replace("/", "_"))+".html", "w", encoding="utf-8")
        print("""<?xml version="1.0" encoding="UTF-8"?>""", file=f)
        print("""<html xmlns="http://www.w3.org/1999/xhtml>""", file=f)
        print("<body>", file=f)
        print("<h1>{0}</h1>".format(e['origin']['title']), file=f)
        print("""<h2><a href="{0}">{1}</a></h2>""".format(e['alternate'][0]['href'], e['title']), file=f)
        which = "content" if "content" in e else "summary"
        print(e[which]['content'], file=f)
        print("</body>", file=f)
        print("</html>", file=f)
        f.close()
    f = open(os.path.join(dir, "reader.opf"), "w")
    print("""<?xml version="1.0" encoding="UTF-8"?>
    <package unique-identifier="uid" xmlns:dc="Dublin Core">
        <metadata>
            <dc-metadata>
                <dc:Identifier id="uid">reader</dc:Identifier>
                <dc:Title>Reader<dc:Title>
                <dc:Language>EN</dc:Language>
            </dc-metadata>
        </metadata>
        <manifest>""", file=f)
    for e in feed['items']:
        print("""<item id="{0}" href="{0}.html" media-type="text/html" />""".format(e['id'].replace("/", "_")), file=f)
    print("""</manifest>
        <spine>""", file=f)
    for e in feed['items']:
        print("""<itemref idref="{0}" />""".format(e['id'].replace("/", "_")), file=f)
    print("""</spine>
    </package>""", file=f)
    f.close()
    os.system("/home/greg/build/kindlegen/kindlegen {0}".format(os.path.join(dir, "reader.opf")))
finally:
    pass #shutil.rmtree(dir)
