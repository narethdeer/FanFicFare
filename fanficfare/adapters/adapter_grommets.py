#  -*- coding: utf-8 -*-

# Copyright 2018 FanFicFare team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import absolute_import
from .base_adapter import BaseSiteAdapter, makeDate
from ..six.moves.urllib.error import HTTPError
from .. import exceptions as exceptions
import re
import bs4

import logging
logger = logging.getLogger(__name__)

def getClass():
    return GrometsAdapter

class GrometsAdapter(BaseSiteAdapter):

    def __init__(self, config, url):
        BaseSiteAdapter.__init__(self, config, url)
        logger.warn("test")
        # Each adapter needs to have a unique site abbreviation.
        self.story.setMetadata('siteabbrev','grom')

        # Gromet's plaza doesn't have storyIds
        storyId = "#1"
        self.story.setMetadata('storyId', storyId)

        ## set url
        self._setURL(url)

        # The date format will vary from site to site.
        # http://docs.python.org/library/datetime.html#strftime-strptime-behavior
        self.dateformat = "%d.%m.%y"

        logger.warn("__init__end")


    @staticmethod
    def getSiteDomain():
        return 'grometsplaza.net'

    @classmethod
    def getAcceptDomains(cls):
        return ['grometsplaza.net',
                'www.boundstories.net',
                'www.packagedstories.net',
                'www.dollstories.net',
                'www.selfbound.net',
                'www.latexstories.net',
                'www.mummified.net',
                'www.maidbots.net',
                'www.trashcanstories.net',
                'www.devouredstories.net']

    def getSiteURLPattern(self):
        return r"https?://(" \
               r"www.packagedstories.net|" \
               r"www.mummified.net|" \
               r"www.boundstories.net|" \
               r"www.dollstories.net|" \
               r"www.selfbound.net|" \
               r"www.latexstories.net|" \
               r"www.maidbots.net|" \
               r"www.trashcanstories.net|" \
               r"www.devouredstories.net|" \
               r"grometsplaza.net/eroticstories|" \
               r"grometsplaza.net/world/" \
               r"(ponygirl|transformation|machine|tg|buried|giantess))" \
               r"/storie[a-zA-Z0-9_-]+/([a-zA-Z0-9_-]+)"

    def getPageText(self, raw_page, url):
        logger.debug('Getting page text')

        page_soup = self.make_soup(raw_page)

        story = page_soup.find('div', 'storym')

        logger.debug('got len: %i'%len(story))

        full_html = unicode(story)
        #         logger.debug(full_html)
        # Strip some starting and ending tags,
        full_html = re.sub(r'^<div.*?>', r'', full_html)
        full_html = re.sub(r'</div>$', r'', full_html)
        full_html = re.sub(r'<p></p>$', r'', full_html)
        #         logger.debug('getPageText - full_html: %s' % full_html)
        return full_html

    def extractChapterUrlsAndMetadata(self):

        try:
            raw_page = self._fetchUrl(self.url)
            page_soup = self.make_soup(raw_page)

        except HTTPError as e:
            if e.code in [404, 410]:
                raise exceptions.StoryDoesNotExist(self.url)
            else:
                raise e
        logger.debug("Chapter/Story URL: <%s> " % self.url)

        a = page_soup.find("h3", id="author").string
        a = a.replace("by ","")



        self.story.setMetadata('authorId', a)
        self.story.setMetadata('author', a)
        logger.debug('Getting author : %s' % a)

#TAGS
        forum_entry =  page_soup.find('div', {'class': 'story1', 'id':'forum'})
        ps = forum_entry.find_all('p')

        for p in ps:
            entry = p.string
            try:

                if u'Storycodes' in entry:
                    entry=entry.strip().replace('Storycodes:','')
                    tags=entry.split(';')
                    for tag in tags:
                        self.story.addToList('category', tag)
            except TypeError:
                pass





        title = page_soup.find("h1").string
        self.story.setMetadata('title', title)

        is_single_chapter = True
        if is_single_chapter:
            self.add_chapter(title, self.url)

        logger.debug('Getting title : %s' % title)

    def getChapterText(self, url):
        logger.debug('Getting chapter text from: %s' % url)

        raw_page = self._fetchUrl(url)
        page_soup = self.make_soup(raw_page)

        full_html = ""


        chapter_description = ''
        # if self.getConfig("description_in_chapter"):
        #     chapter_description = page_soup.find("meta", {"name": "description"})['content']
        #     logger.debug("\tChapter description: %s" % chapter_description)
        #     chapter_description = '<p><b>Description:</b> %s</p><hr />' % chapter_description
        full_html += self.getPageText(raw_page, url)
        logger.debug('Getting chapter text for len: %i' % len(full_html))

        # TODO Multipart story support
        # pages = page_soup.find('select', {'name': 'page'})
        # page_nums = [page.text for page in pages.findAll('option')] if pages else 0
        # if pages:
        #     for page_no in range(2, len(page_nums) + 1):
        #         page_url = url + "?page=%s" % page_no
        #         logger.debug("page_url= %s" % page_url)
        #         raw_page = self._fetchUrl(page_url)
        #         full_html += self.getPageText(raw_page, url)

        #         logger.debug(full_html)
        # page_soup = self.make_soup(full_html)
        full_html = self.utf8FromSoup(url, self.make_soup(full_html))
        # full_html = chapter_description + full_html
        full_html = unicode(full_html)
        logger.warn("getChapterText_end %i"%len(full_html))
        return full_html
