# -*- coding: utf-8 -*-

# Copyright 2012 Fanficdownloader team, 2018 FanFicFare team
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
import logging
logger = logging.getLogger(__name__)
import re
from ..htmlcleanup import stripHTML
from .. import exceptions as exceptions

# py2 vs py3 transition
from ..six import text_type as unicode
from ..six.moves.urllib.error import HTTPError

from .base_adapter import BaseSiteAdapter,  makeDate

def getClass():
    return SilmarillionWritersGuildOrgAdapter

# Class name has to be unique.  Our convention is camel case the
# sitename with Adapter at the end.  www is skipped.
class SilmarillionWritersGuildOrgAdapter(BaseSiteAdapter):

    def __init__(self, config, url):
        BaseSiteAdapter.__init__(self, config, url)

        self.username = "NoneGiven" # if left empty, site doesn't return any message at all.
        self.password = ""
        self.is_adult=False

        # get storyId from url--url validation guarantees query is only sid=1234
        self.story.setMetadata('storyId',self.parsedUrl.query.split('=',)[1])

        # normalized story URL.
        self._setURL('http://' + self.getSiteDomain() + '/archive/home/viewstory.php?sid='+self.story.getMetadata('storyId'))

        # Each adapter needs to have a unique site abbreviation.
        self.story.setMetadata('siteabbrev','swg')

        # The date format will vary from site to site.
        # http://docs.python.org/library/datetime.html#strftime-strptime-behavior
        self.dateformat = "%B %d, %Y"

    @staticmethod # must be @staticmethod, don't remove it.
    def getSiteDomain():
        # The site domain.  Does have www here, if it uses it.
        return 'www.silmarillionwritersguild.org'

    @classmethod
    def getSiteExampleURLs(cls):
        return "https://"+cls.getSiteDomain()+"/archive/home/viewstory.php?sid=123"

    def getSiteURLPattern(self):
        return r"https?://"+re.escape(self.getSiteDomain()+"/archive/home/viewstory.php?sid=")+r"\d+$"

    ## Getting the chapter list and the meta data, plus 'is adult' checking.
    def extractChapterUrlsAndMetadata(self):

        # index=1 makes sure we see the story chapter index.  Some
        # sites skip that for one-chapter stories.
        url = self.url
        logger.debug("URL: "+url)

        try:
            data = self._fetchUrl(url)
        except HTTPError as e:
            if e.code == 404:
                raise exceptions.StoryDoesNotExist(self.url)
            else:
                raise e

        # use BeautifulSoup HTML parser to make everything easier to find.
        soup = self.make_soup(data)
        # print data

        # Now go hunting for all the meta data and the chapter list.

        ## Title and author
        a = soup.find('h6')

        titlelinks = a.find_all('a')
        aut= titlelinks[1]
        
        self.story.setMetadata('authorId',aut['href'].split('=')[1])
        self.story.setMetadata('authorUrl','https://'+self.host+'/archive/home/'+aut['href'])
        self.story.setMetadata('author',aut.string)
        asoup = self.make_soup(self._fetchUrl(self.story.getMetadata('authorUrl')))

        self.story.setMetadata('title',a.find('strong').find('a').get_text())
        
        try:
            # Find Series name from series URL.
            a = soup.find('a', href=re.compile(r"viewseries.php\?seriesid=\d+"))
            series_name = a.string
            series_url = 'https://'+self.host+'/archive/home/'+a['href']

            # use BeautifulSoup HTML parser to make everything easier to find.
            seriessoup = self_make_soup(self._fetchUrl(series_url))
            storyas = seriessoup.findAll('a', href=re.compile(r'^viewstory.php\?sid=\d+$'))
            i=1
            for a in storyas:
                if a['href'] == ('viewstory.php?sid='+self.story.getMetadata('storyId')):
                    self.setSeries(series_name, i)
                    self.story.setMetadata('seriesUrl',series_url)
                    break
                i+=1

        except:
            # I find it hard to care if the series parsing fails
            pass

        # Find the chapters by regexing urls
        chapters=soup.findAll('a', href=re.compile(r'viewstory.php\?sid='+self.story.getMetadata('storyId')+"&chapter=\d+$"))
        
        #logger.debug(chapters)
        
        if len(chapters)==1:
            self.add_chapter(self.story.getMetadata('title'),'https://'+self.host+'/archive/home/'+chapters[0]['href'])
        else:
            for chapter in chapters:
                logger.debug("Added Chapter: "+chapter.string)
                self.add_chapter(chapter,'https://'+self.host+'/archive/home/'+chapter['href'])
                
        

	# find the details section for the work
	
        workDetails = soup.find('div', {'id' : 'general'}).find('div', {'id' : 'general'})
        
        # Find the summary 
        summary = workDetails.find_all('p')[3]
        summary.name='div' # change td to div.  Makes Calibre
                           # sanitize_html() happier when description
                           # is empty.
        self.setDescription(url,summary)
        
        # no convenient way to extract metadata so bodge it by finding relevant identifier string and using next element as the data source

        #get characters
        charList = workDetails.findAll('a', href=re.compile(r'browse.php?type=characters'+"&charid=\d+$"))
        charText = [char.string for char in charList]
        self.chararacters = ', '.join(charText)
        for char in charText:
            self.story.addToList('characters',char.string)
            
        #get warnings
        warnList = workDetails.findAll('a', href=re.compile(r'browse.php?type=characters'+"&charid=\d+$"))
        warnText = [warn.string for warn in warnList]
        self.warnings = ', '.join(charText)
        for warn in charText:
            self.story.addToList('warnings',char.string)
            
        #get genres
        genresList = workDetails.findAll('a', href=re.compile(r'browse.php?type=class&type_id=1'+"&classid=\d+$"))
        genrestext = [genre.string for genre in genresList]
        self.genre = ', '.join(genrestext)
        for genre in genrestext:
            self.story.addToList('genre',genre.string)            
        
        #get rating
        rating = workDetails.find('strong',text='Rated:').next_sibling.string
        
        #get completion status and correct for consistency with other adapters
        if (workDetails.find('strong',text='Completed:').next_sibling.string).lower() == "yes":
            status="Completed"
        else:
            status="In-Progress"
        
        #get wordcount
        wordCount = workDetails.find('strong',text='Word count:').next_sibling.string
        
        #get published date, this works for some reason yet doesn't without the spaces in it
        datePublished = workDetails.find('strong',text=' Published: ').next_sibling.string
        
        #get updated date
        dateUpdated = workDetails.find('strong',text='Updated:').next_sibling.string
        
        # try setting metadata values on story, warn if it fails
        try:
            self.story.setMetadata('rating', rating)
            self.story.setMetadata('status', status)
            self.story.setMetadata('numWords', wordCount)
            self.story.setMetadata('datePublished', makeDate(datePublished, self.dateformat))
            self.story.setMetadata('dateUpdated', makeDate(dateUpdated, self.dateformat))
        except Exception as e:
            logger.warn("rating, status and/or datePublished parsing failed(%s) -- This can be caused by bad HTML in story description."%e)

    # grab the text for an individual chapter.
    def getChapterText(self, url):

        logger.debug('Getting chapter text from: %s' % url)

        if self.getConfig('is_adult'):
            params = {'confirmAge':'1'}
            data = self._postUrl(url,params)
        else:
            data = self._fetchUrl(url)

        soup = self.make_soup(data)

        if "Please indicate that you are an adult by selecting the appropriate choice below" in data:
            raise exceptions.FailedToDownload("Chapter requires you be an adult.  Set is_adult in personal.ini (chapter url:%s)" % url)

        # No convenient way to get story without the rest of the page, so get whole page and strip unneeded sections
        
        contentParent = soup.find('div', {'id' : 'maincontent'}).find('div', {'id' : 'general'})
        
        #remove redundant formating tags
        for tag in contentParent("hr"):
            tag.decompose()
        
        contentParent.find('p').decompose() # remove page header        
        contentParent.find_all('div',id='general')[2].decompose() #remove page footer
        contentParent.find_all('div',id='general')[0].decompose() #remove chapter select etc.
        
        contentParent.name='div'
        
        #error on failure
        if None == contentParent:
            raise exceptions.FailedToDownload("Error downloading Chapter: %s!  Missing required element!" % url)

        return self.utf8FromSoup(url,contentParent)
