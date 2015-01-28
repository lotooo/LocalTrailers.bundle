VIDEO_PREFIX = "/video/localtrailers"

NAME = L('Title')

# make sure to replace artwork with what you want
# these filenames reference the example files in
# the Contents/Resources/ folder in the bundle
ART  = 'art-default.jpg'
ICON = 'icon-default_w.png'

####################################################################################################
from datetime import date
from urllib import unquote
from urllib import quote

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
    location = Prefs['location']
    ## do some checks and return a
    ## message container
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

### method to retrieve the Theaters info
def getName(el):
    name = ""
    for t in el:
        if t.tag <> 'div' and t.attrib['class'] <> 'desc':
            continue
        for n in t:
            if n.tag == 'h2':
                for link in n:
                    name = link.text
            continue
    if name == "":
        Log.Debug("This theater is closed.")
    return name

def getAddress(el):
    address = ""
    for t in el:
        if t.tag <> 'div' and t.attrib['class'] <> 'desc':
            continue
        for n in t:
            if n.tag == 'div' and n.attrib['class'] == 'info':
                address = n.text
            continue
    return address

def getLink(el):
    link = ""
    for t in el:
        if t.tag <> 'div' and t.attrib['class'] <> 'desc':
            continue
        for n in t:
            if n.tag == 'h2':
                for l in n:
                    link = l.attrib['href']
            continue
    return link

## Methods to retrieve the movie info
def getMovieName(el):
    name = ""
    for a in el.iter('a'):
        if a.text <> 'Trailer' and a.text <> 'IMDb':
            name = a.text
    Log.Debug(name)
    return name

def getMovieTrailer(el):
    trailer = ""
    for a in el.iter('a'):
        if a.text == 'Trailer':
            trailer = a.attrib['href']
    Log.Debug(unquote(trailer[7:]))
    return unquote(trailer[7:])

def getMovieIMDB(el):
    imdb = ""
    for a in el.iter('a'):
        if a.text == 'IMDb':
            imdb = a.attrib['href']
    Log.Debug(unquote(imdb[7:]))
    return unquote(imdb[7:])

def getTheatersFromHTML(theater_blocks):
    theaters = []
    for theater_block in theater_blocks:
        theater                 = {}
        theater['name']         = getName(theater_block)
        theater['address']      = getAddress(theater_block)
        theater['link']         = getLink(theater_block)
        theaters.append(theater)
    return theaters

def getMoviesFromHTML(movie_blocks):
    movies = []
    for movie_block in movie_blocks:
        movie                 = {}
        movie['name']         = getMovieName(movie_block)
        movie['trailer']      = getMovieTrailer(movie_block)
        movie['imdb']         = getMovieIMDB(movie_block)
        movies.append(movie)
    return movies


@route('/video/localtrailers/getnearbytheaters') 
def getNearbyTheaters(location):
    theaters = []   

    Log.Debug("Retrieving theaters list for: %s" % quote(location))
    url = "http://www.google.com/movies?near=%s" % quote(location)

    Log.Debug("URL: %s" % url)

    html = HTML.ElementFromURL(url=url)
    theater_blocks = html.body.find_class('theater')

    page = 20
    while len(getTheatersFromHTML(theater_blocks)) != 0:
        theaters += getTheatersFromHTML(theater_blocks)
        url = "http://www.google.com/movies?near=%s&start=%d" % (quote(location), page)
        html = HTML.ElementFromURL(url=url)
        theater_blocks = html.body.find_class('theater')
        page += 10

    return theaters

def getMoviesForTheater(theater):
    movies = []
    
    url = "http://www.google.com%s" % theater['link']

    Log.Debug("URL: %s" % url)

    html = HTML.ElementFromURL(url=url)
    movies_block = html.body.find_class('movie')
    movies = getMoviesFromHTML(movies_block) 

    return movies


#### the rest of these are user created functions and
#### are not reserved by the plugin framework.
#### see: http://dev.plexapp.com/docs/Functions.html for
#### a list of reserved functions above



#
# Example main menu referenced in the Start() method
# for the 'Video' prefix handler
#

def VideoMainMenu():
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

@route('/video/localtrailers/theatersview') 
def TheatersView():
    oc = ObjectContainer(title1='TheatersView')

    theaters = getNearbyTheaters(Prefs['location'])
    sorted_theaters = sorted(theaters, key=lambda k: k['name'])
    for theater in [ t for t in sorted_theaters if t['name'] <> "" ]:
        oc.add(
        DirectoryObject(
            key=Callback(MoviesView, theater=theater),
            title=L(String.StripDiacritics(theater['name'])),
            summary=L(String.StripDiacritics(theater['address'])),
            art=R('theater.jpg'),
            thumb=R('theater_w.png'),
        )
        )
    return oc

def unique(lst):
    return [] if lst==[] else [lst[0]] + unique(filter(lambda x: x!= lst[0], lst[1:]))

def MoviesView(theater=None):
    oc = ObjectContainer(title1='MoviesView')
    if theater == None:
        theaters = getNearbyTheaters(Prefs['location'])
        m = []
        for theater in theaters:
            m += getMoviesForTheater(theater=theater)
            movies = unique(m)
    else:
        movies = getMoviesForTheater(theater=theater)

    sorted_movies = sorted(movies, key=lambda k: k['name'])

    for movie in [ t for t in sorted_movies if t['name'] <> "" ]:
        video_rating = 5.0;
        video_date = date.today()

        # Get the youtube info
        video_info = URLService.MetadataObjectForURL(movie['trailer'])
        if video_info <> None:
            thumb = unquote(video_info.thumb.split('=').pop()).replace("%3A",":")
            description = video_info.summary.split('=').pop()
        else:
            thumb = ""
            description = ""

        if movie['trailer'] <> '':
            oc.add(
                VideoClipObject(
                  title = String.StripDiacritics(movie['name']),
                  summary = description,
                  art=R('movie.jpg'),
                  thumb=Resource.ContentsOfURLWithFallback(url=thumb),
                  url = movie['trailer']
                )
            )
        else:
            Log.Debug('No trailer found for %s' % movie['name'] )  
    return oc


def CallbackExample():

    ## you might want to try making me return a MediaContainer
    ## containing a list of DirectoryItems to see what happens =)

    return MessageContainer(
        "Not implemented",
        "In real life, you'll make more than one callback,\nand you'll do something useful."
    )

  
