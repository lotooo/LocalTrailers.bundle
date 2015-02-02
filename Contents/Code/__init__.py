VIDEO_PREFIX = "/video/localtrailers"

NAME = L('Title')

# make sure to replace artwork with what you want
# these filenames reference the example files in
# the Contents/Resources/ folder in the bundle
ART  = 'art-default.jpg'
ICON = 'icon-default_w.png'

# Maximum age of the cache in seconds
UPDATE_INFO=3600

####################################################################################################
import json

def Start():

    ## make this plugin show up in the 'Video' section
    ## in Plex. The L() function pulls the string out of the strings
    ## file in the Contents/Strings/ folder in the bundle
    ## see also:
    ##  http://dev.plexapp.com/docs/mod_Plugin.html
    ##  http://dev.plexapp.com/docs/Bundle.html#the-strings-directory
    Plugin.AddPrefixHandler(VIDEO_PREFIX, VideoMainMenu, NAME, ICON, ART)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    ## set some defaults so that you don't have to
    ## pass these parameters to these object types
    ## every single time
    ## see also:
    ##  http://dev.plexapp.com/docs/Objects.html
    MediaContainer.title1 = NAME
    MediaContainer.viewGroup = "List"
    MediaContainer.art = R(ART)
    DirectoryItem.thumb = R(ICON)
    VideoItem.thumb = R(ICON)
    
    HTTP.CacheTime = CACHE_1HOUR

# see:
#  http://dev.plexapp.com/docs/Functions.html#ValidatePrefs
def ValidatePrefs():
    Log.Debug("Validating preferences")
    location = Prefs['location']
    theaters = getNearbyTheaters(location)
    if(len(theaters)) != 0:
        HTTP.ClearCache()
        Log.Debug("Location saved to : %s" % location)
        return MessageContainer(
            "Success",
            "Location provided: %s\n%d theaters found." % (location, len(theaters)) 
        )
    else:
        Log.Debug("Failed to save location to : %s" % location)
        return MessageContainer(
            "Error",
            "No theaters found. Please provide another location."
        )

######################################################################################
#
# Theater Object definition
#
######################################################################################
class Theater:
    def __init__(self, html_block):
        self.name       = ""
        self.link       = ""
        self.address    = ""
        self.id         = ""

        for t in html_block:
            if t.tag <> 'div' and t.attrib['class'] <> 'desc':
                continue
            for n in t:
                if n.tag == 'h2':
                    for link in n:
                        self.name = String.StripDiacritics(link.text)
                        self.link = link.attrib['href']
                if n.tag == 'div' and n.attrib['class'] == 'info':
                    self.address = String.StripDiacritics(n.text)
                continue
        if self.name == "":
            Log.Debug("This theater is closed.")

        # Retrieve the theater id
        pattern = Regex("tid=(\w+)")
        match = pattern.findall(self.link)
        if match:
            self.id = match.pop()

######################################################################################

######################################################################################
#
# Movie Object definition
#
######################################################################################
class Movie:
    def __init__(self, html_block):
        self.name           = ""
        # If no trailer found, choose "La classe américaine"
        self.trailer        = "https://www.youtube.com/watch?v=qHqYutWuy1E" 
        self.imdb           = ""
        self.showtimes      = ""
        self.details        = {}
        self.video_rating   = 5.0
        self.directors      = []
        self.genres         = []
        self.thumb          = ""
        self.description    = "No synopsis available"
        self.date           = "14 Nov 2014"
        self.year           = 1800

        for a in html_block.iter('a'):
            if a.text <> 'Trailer' and a.text <> 'IMDb':
                self.name = a.text
            if a.text == 'Trailer':
                trailer = a.attrib['href']
                self.trailer = String.Unquote(trailer[7:])
            if a.text == 'IMDb':
                imdb = a.attrib['href']
                self.imdb = String.Unquote(imdb[7:])

        # Try to find if the movie name is in form 'english version (orginal name)'
        my_pattern = Regex("(.*) \(.*\)")
        match = my_pattern.search(self.name)
        if match:
            Log.Debug("Filtered Name: %s" % match.group(1))
            self.name = match.group(1)

        # Get showtimes 
        showtimes = html_block.xpath(".//div[@class='times']/span/text()")
        self.showtimes = ' | '.join(showtimes)

        # Get movie details from imdb
        url = "http://www.imdbapi.com/?t=%s" % String.Quote(self.name)

        try:
            self.details = JSON.ObjectFromURL(url)
        except:
            Log.Debug("Unable to parse JSON from %s" % url)

        if self.details.has_key('imdbRating'):
            self.video_rating = self.details['imdbRating']

        if self.details.has_key('Director'):
            self.directors = [self.details['Director']]

        if self.details.has_key('Genre'):
            self.genres = self.details['Genre'].split(',')


        if self.details.has_key('Poster'):
            self.thumb = self.details['Poster']
        else:
            # Get the youtube info
            video_info = URLService.MetadataObjectForURL(self.trailer)
            if video_info:
                thumb = String.Unquote(video_info.thumb.split('=').pop()).replace("%3A",":")

        if self.details.has_key('Plot'):
            self.description = self.details['Plot']

        if self.details.has_key('Released'):
            self.date = self.details['Released']

        if self.details.has_key('Year'):
            try:
                # Remove every non numerical characters from the year (Example: '2010-')
                pattern = Regex("\d")
                match = pattern.findall(self.details['Year'])
                self.year = int(''.join(match))
            except:
                ## I currently have a problem with some unicode characters in the json file
                Log.Debug("Non readable year: %s" % self.details['Year'])

######################################################################################

def getTheatersFromHTML(theater_blocks):
    theaters = []
    for theater_block in theater_blocks:
        theater = Theater(theater_block)
        if theater.name != "":
            theaters.append(theater)
    return theaters

def getMoviesFromHTML(movie_blocks):
    movies = []
    for movie_block in movie_blocks:
        movie   = Movie(movie_block)
        if movie.name != "":
            movies.append(movie)
    return movies


@route('/video/localtrailers/getnearbytheaters') 
def getNearbyTheaters(location):
    theaters = []   

    Log.Debug("Retrieving theaters list for: %s" % String.Quote(location))
    url = "http://www.google.com/movies?near=%s" % String.Quote(location)

    html = HTML.ElementFromURL(url=url)
    theater_blocks = html.body.find_class('theater')

    page = 20
    while len(getTheatersFromHTML(theater_blocks)) != 0:
        theaters += getTheatersFromHTML(theater_blocks)
        url = "http://www.google.com/movies?near=%s&start=%d" % (String.Quote(location), page)
        html = HTML.ElementFromURL(url=url)
        theater_blocks = html.body.find_class('theater')
        page += 10

    # if the list is not empty, save it to disk to be re-used
    # but save a sorted list of theaters by name
    if len(theaters) != 0:
        Dict['theaters'] = {}
        for theater in sorted(theaters, key=lambda k: k.name):
            Dict['theaters'][theater.id] = theater 

    return theaters

#
# Retrieve the theaters list from the local disk
#
@route('/video/localtrailers/gettheaterslist') 
def getTheatersList():
    try:
        theaters = Dict['theaters']
    except:
        theaters = []   
        Log.Debug("Unable to read the theaters list")
    return theaters

#
# Get the movies list for the given theater
#
def getMoviesForTheater(theater_id):
    movies = []

    # Let's initiate our caching object
    if theater_id in Dict:
        try:
            last_parsed = Dict[theater_id]['lastParsed']
        except Exception as e:
            Log.Debug(e)
            last_parsed = Datetime.ParseDate('22 Oct 2014')
        now = Datetime.Now()
        age=now-last_parsed
        Log.Debug("Last parsing: %ds ago" % age.seconds)
        if age.seconds > UPDATE_INFO:
            to_be_parsed = True
        else:
            to_be_parsed = False
    else:
        Log.Debug("This theater has not been parsed yet.")
        Dict[theater_id] = {
            'lastParsed'    : Datetime.Now(),
            'movies'        : {}
        }
        Log.Debug(Dict[theater_id]['lastParsed'])
        to_be_parsed = True

    if to_be_parsed: 
        Log.Debug("Theater %s must be parsed" % theater_id)

        url = "http://www.google.com%s" % Dict['theaters'][theater_id].link

        Log.Debug("URL: %s" % url)

        html = HTML.ElementFromURL(url=url)
        movies_block = html.body.find_class('movie')
        movies = getMoviesFromHTML(movies_block) 

        # Update the dict
        Dict[theater_id]['movies']      = movies
        Dict[theater_id]['lastParsed']  = Datetime.Now()
    else:
        Log.Debug("Theater %s don't have to be parsed" % theater_id)
        movies = Dict[theater_id]['movies']

    return sorted(movies, key=lambda k: k.name)


#
# Example main menu referenced in the Start() method
# for the 'Video' prefix handler
#

def VideoMainMenu():
    # First, let's update the theaters list for today.
    getNearbyTheaters(Prefs['location'])
    # Then, erase the movies info. these need to be updated
    Dict['movies'] = {}


    oc = ObjectContainer(title1='Watch your local trailers !')
    oc.add(
        DirectoryObject(
            key=Callback(TheatersView),
            title=L(String.StripDiacritics('By Theaters')),
            summary="List of available theaters around your location",
            art=R('theater.jpg'),
            thumb=R('theater_w.png'),
        )
    )
    oc.add(
        DirectoryObject(
            key=Callback(MoviesView),
            title=L(String.StripDiacritics('By Movies')),
            summary="List of available movies around your location",
            art=R('movie.jpg'),
            thumb=R('movie_w.png'),
        )
    )
    oc.add(
        PrefsObject(
            title = L('Preferences'),
            tagline = L('Modify your location'),
            summary = L('Modify your location.\nMust be compatible with http://www.google.com/movies')
        )
    )
    return oc

#
# Build the theaters list view
#
@route('/video/localtrailers/theatersview') 
def TheatersView():
    # Retrieve the theaters
    theaters = getTheatersList()

    # Build our container
    oc = ObjectContainer(title1='TheatersView')

    for t in sorted(theaters.items(),key = lambda x :x[1].name, reverse = True):
        id, theater = t
        oc.add(
            DirectoryObject(
                key=Callback(MoviesView, theater_id=id),
                title=theater.name,
                summary=theater.address,
                art=R('theater.jpg'),
                thumb=R('theater_w.png'),
            )
        )
    return oc

def unique(lst):
    return [] if lst==[] else [lst[0]] + unique(filter(lambda x: x!= lst[0], lst[1:]))

@route('/video/localtrailers/moviesview') 
def MoviesView(theater_id=None):
    if theater_id:
        oc_title=Dict['theaters'][theater_id].name
    else:
        oc_title="By Movies"

    oc = ObjectContainer(title1=oc_title, content=ContainerContent.Movies)

    if theater_id == None:
        theaters = getTheatersList()
        movies = []
        for id in theaters:
            for m in getMoviesForTheater(theater_id=id):
                if m not in movies:
                    movies.append(m)
    else:
        movies = getMoviesForTheater(theater_id=theater_id)

    for movie in movies:

        title = String.StripDiacritics(movie.name)
        tagline = movie.showtimes
        rating_key = String.Quote(movie.name)
            
        oc.add(
            MovieObject(
              key = Callback(Lookup, 
                        title=title, 
                        date=movie.date, 
                        year=movie.year, 
                        summary=movie.description, 
                        directors=movie.directors, 
                        genres=movie.genres, 
                        tagline=tagline, 
                        thumb=movie.thumb, 
                        trailer=movie.trailer, 
                        rating_key = rating_key
              ),
              title = title,
              originally_available_at = Datetime.ParseDate(movie.date),
              year = movie.year,
              summary = movie.description,
              directors = movie.directors,
              genres = movie.genres,
              art=R('movie.jpg'),
              tagline= tagline,
              thumb=Resource.ContentsOfURLWithFallback(url=movie.thumb),
              items = URLService.MediaObjectsForURL(movie.trailer),
              rating_key = rating_key

            )
        )
    return oc


@route('/video/localtrailers/lookup', directors=list, genres=list, year=int) 
def Lookup(title, date, year, summary, directors, genres, tagline, thumb, trailer, rating_key,includeRelatedCount=None,includeRelated=None,includeExtras=None):
    oc = ObjectContainer(title1='Lookup', content=ContainerContent.Movies)
    oc.add(
        MovieObject(
          key = Callback(Lookup, title=title, date=date, year=year, summary=summary, directors=directors, genres=genres, tagline=tagline, thumb=thumb, trailer=trailer, rating_key=rating_key),
          title = title,
          originally_available_at = Datetime.ParseDate(date),
          year = year,
          summary = summary,
          directors = directors,
          genres = genres,
          art=R('movie.jpg'),
          tagline=tagline,
          thumb=thumb,
          items = URLService.MediaObjectsForURL(trailer),
          rating_key = rating_key

        )
    )
    return oc
