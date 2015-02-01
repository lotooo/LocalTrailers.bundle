VIDEO_PREFIX = "/video/localtrailers"

NAME = L('Title')

# make sure to replace artwork with what you want
# these filenames reference the example files in
# the Contents/Resources/ folder in the bundle
ART  = 'art-default.jpg'
ICON = 'icon-default_w.png'

####################################################################################################

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


### method to retrieve the Theaters info
def getTheaterName(el):
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

def getTheaterAddress(el):
    address = ""
    for t in el:
        if t.tag <> 'div' and t.attrib['class'] <> 'desc':
            continue
        for n in t:
            if n.tag == 'div' and n.attrib['class'] == 'info':
                address = n.text
            continue
    return address

def getTheaterLink(el):
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
    # Try to find if the movie name is in form 'english version (orginal name)'
    my_pattern = Regex("(.*) \(.*\)")
    match = my_pattern.search(name)
    Log.Debug(name)
    if match:
        Log.Debug("Filtered Name: %s" % match.group(1))
        name = match.group(1)
    return name

def getMovieTrailer(el):
    # If no trailer found, choose La classe américaine
    trailer = "https://www.youtube.com/watch?v=qHqYutWuy1E"
    for a in el.iter('a'):
        if a.text == 'Trailer':
            trailer = a.attrib['href']
            Log.Debug(String.Unquote(trailer[7:]))
            return String.Unquote(trailer[7:])
    return trailer

def getMovieIMDB(el):
    imdb = ""
    for a in el.iter('a'):
        if a.text == 'IMDb':
            imdb = a.attrib['href']
    Log.Debug(String.Unquote(imdb[7:]))
    return String.Unquote(imdb[7:])

def getMovieDetails(title):
    url = "http://www.imdbapi.com/?t=%s" % String.Quote(title)

    try:
        details = JSON.ObjectFromURL(url)
    except:
        Log.Debug("Unable to parse JSON from %s" % url)
        details = {}

    return details

def getMovieShowtimes(el):
    showtimes = el.xpath(".//div[@class='times']/span/text()")
    return ' | '.join(showtimes)

def getTheatersFromHTML(theater_blocks):
    theaters = []
    for theater_block in theater_blocks:
        theater                 = {}
        theater['name']         = getTheaterName(theater_block)
        theater['address']      = getTheaterAddress(theater_block)
        theater['link']         = getTheaterLink(theater_block)
        if theater['name'] != "":
            theaters.append(theater)
    return theaters

def getMoviesFromHTML(movie_blocks):
    movies = []
    for movie_block in movie_blocks:
        movie                 = {}
        movie['name']         = getMovieName(movie_block)
        movie['trailer']      = getMovieTrailer(movie_block)
        movie['imdb']         = getMovieIMDB(movie_block)
        movie['showtimes']    = getMovieShowtimes(movie_block)
        movie['details']      = getMovieDetails(movie['name'])
        movies.append(movie)
    return movies


@route('/video/localtrailers/getnearbytheaters') 
def getNearbyTheaters(location):
    theaters = []   

    Log.Debug("Retrieving theaters list for: %s" % String.Quote(location))
    url = "http://www.google.com/movies?near=%s" % String.Quote(location)

    Log.Debug("URL: %s" % url)

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
        Data.Save('theaters.json', JSON.StringFromObject(sorted(theaters, key=lambda k: k['name'])))

    return theaters

#
# Retrieve the theaters list from the local disk
#
@route('/video/localtrailers/gettheaterslist') 
def getTheatersList():
    try:
        theaters = JSON.ObjectFromString(Data.Load('theaters.json'))
    except:
        theaters = []   
        Log.Debug("Unable to read the theaters list")
    return theaters
#
# Get the movies list for the given theater
#
def getMoviesForTheater(theater):
    movies = []
    
    url = "http://www.google.com%s" % theater['link']

    Log.Debug("URL: %s" % url)

    html = HTML.ElementFromURL(url=url)
    movies_block = html.body.find_class('movie')
    movies = getMoviesFromHTML(movies_block) 

    return movies


#
# Example main menu referenced in the Start() method
# for the 'Video' prefix handler
#

def VideoMainMenu():
    # First, let's update the theaters list for today.
    getNearbyTheaters(Prefs['location'])


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

    for theater in theaters:
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

@route('/video/localtrailers/moviesview', theater=Dict) 
def MoviesView(theater=None):
    oc = ObjectContainer(title1='MoviesView', content=ContainerContent.Movies)

    if theater == None:
        #theaters = getNearbyTheaters(Prefs['location'])
        theaters = getTheatersList()
        m = []
        for theater in theaters:
            m += getMoviesForTheater(theater=theater)
            movies = unique(m)
    else:
        movies = getMoviesForTheater(theater=theater)

    sorted_movies = sorted(movies, key=lambda k: k['name'])

    for movie in [ t for t in sorted_movies if t['name'] <> "" ]:

        if movie['details'].has_key('imdbRating'):
            video_rating = movie['details']['imdbRating']
        else:
            video_rating = 5.0

        if movie['details'].has_key('Director'):
            directors = [movie['details']['Director']]
        else:
            directors = []

        if movie['details'].has_key('Genre'):
            genres = movie['details']['Genre'].split(',')
        else:
            genres = []


        if movie['details'].has_key('Poster'):
            thumb = movie['details']['Poster']
        else:
            # Get the youtube info
            video_info = URLService.MetadataObjectForURL(movie['trailer'])
            if video_info <> None:
                thumb = String.Unquote(video_info.thumb.split('=').pop()).replace("%3A",":")
            else:
                thumb = ""

        if movie['details'].has_key('Plot'):
            description = movie['details']['Plot']
        else:
            description = "No synopsis available"

        if movie['details'].has_key('Released'):
            date = movie['details']['Released']
        else:
            date = "14 Nov 2014"

        if movie['details'].has_key('Year'):
            try:
                # Remove every non numerical characters from the year (Example: '2010-')
                pattern = Regex("\d")
                match = pattern.findall(movie['details']['Year'])
                year = int(''.join(match))
            except:
                ## I currently have a problem with some unicode characters in the json file
                Log.Debug("Non readable year: %s" % movie['details']['Year'])
                year = 1800
        else:
            year = 1900

        title = String.StripDiacritics(movie['name'])
        tagline = movie['showtimes']
        rating_key = String.Quote(movie['name'])
            
        oc.add(
            MovieObject(
              key = Callback(Lookup, title=title, date=date, year=year, summary=description, directors=directors, genres=genres, tagline=tagline, thumb=thumb, trailer=movie['trailer'], rating_key = rating_key),
              title = title,
              originally_available_at = Datetime.ParseDate(date),
              year = year,
              summary = description,
              directors = directors,
              genres = genres,
              art=R('movie.jpg'),
              tagline= tagline,
              thumb=Resource.ContentsOfURLWithFallback(url=thumb),
              items = URLService.MediaObjectsForURL(movie['trailer']),
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
