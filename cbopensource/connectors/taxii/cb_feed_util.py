#
#The MIT License (MIT)
#
# Copyright (c) 2015 Bit9 + Carbon Black
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import os
import simplejson as json
import traceback
from datetime import datetime, timedelta
from util import TZ_UTC
from cbfeeds import CbFeed
from cbfeeds import CbFeedInfo

class FeedHelper(object):
    def __init__(self, output_dir, feed_name, minutes_to_advance, start_date_str, export_mode):
        self.output_dir = output_dir
        self.feed_name = feed_name
        self.export_mode = export_mode
        self.minutes_to_advance = minutes_to_advance
        self.path = os.path.join(output_dir, feed_name)
        self.details_path = self.path + ".details"
        self.feed_details = {"latest": start_date_str}
        if not self.export_mode and os.path.exists(self.details_path):
            try:
                feed_details_file = file(self.details_path, "rb")
                self.feed_details = json.loads(feed_details_file.read())
            except:
                traceback.print_exc()
        self.start_date = datetime.strptime(self.feed_details.get('latest'), "%Y-%m-%d %H:%M:%S").replace(tzinfo=TZ_UTC)
        self.end_date = self.start_date + timedelta(minutes=self.minutes_to_advance)
        self.done = False
        self.now = datetime.utcnow().replace(tzinfo=TZ_UTC)
        if self.end_date > self.now:
            self.end_date = self.now

    def advance(self):
        """
        returns true if keep going, false if we already hit the end time and cannot advance
        """
        if self.done:
            return False

        self.start_date = self.end_date
        self.end_date += timedelta(minutes=self.minutes_to_advance)
        if self.end_date > self.now:
            self.end_date = self.now
            self.done = True

        return True

    def load_existing_feed_data(self):
        reports = []
        if os.path.exists(self.path):
            data = file(self.path, 'rb').read()
            data = json.loads(data)
            reports = data.get('reports', [])
        return reports

    def write_feed(self, data):
        f = file(self.path, 'wb')
        f.write(data)
        f.close()
        return True # TODO -- when to return False?

    def save_details(self):
        self.feed_details['latest'] = self.end_date.strftime("%Y-%m-%d %H:%M:%S")

        feed_details_file = file(self.details_path, "wb")
        feed_details_file.write(json.dumps(self.feed_details))
        feed_details_file.close()

def remove_duplicate_reports(reports):
    out_reports = []
    reportids = set()
    for report in reports:
        if report['id'] in reportids:
            continue
        reportids.add(report['id'])
        out_reports.append(report)
    return out_reports

def build_feed_data(feed_name, feed_description, site, icon_link, reports):
    """
    :return:feed as bytes to be written out
    """
    feedinfo = {'name': feed_name,
                'display_name': feed_description,
                'provider_url': 'http://' + site,
                'summary': "TAXII Feed %s" % feed_description,
                'tech_data': "There are no requirements to share any data to receive this feed.",
                'icon': icon_link
                }

    feedinfo = CbFeedInfo(**feedinfo)

    reports = remove_duplicate_reports(reports)

    feed = CbFeed(feedinfo, reports)
    return feed.dump()
