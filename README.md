plugins.video.localtrailers
===================

This is a plex channel to watch trailers of movies available on your local theaters from your plex media center

Manual Installation: with git
=============================
* Open a Terminal
* Execute the following commands:

```bash
  # mkdir github
  # cd github
  # git clone https://github.com/lotooo/LocalTrailers.bundle.git
  # cd
  # rm -fr $PLEX_FOLDER/Plug-ins/LocalTrailers.bundle
  # ln -s ~/github/LocalTrailers.bundle/ $PLEX_FOLDER/Plug-ins/LocalTrailers.bundle
```

* Close the Terminal program

To update the plugin:
* Open a Terminal
* Execute the following commands:

```bash
  # cd github/LocalTrailers.bundle
  # git pull
```

* Close the Terminal program

Manual installation : without git
================================
* Download zip file from here: https://github.com/lotooo/LocalTrailers.bundle/archive/master.zip
* Unzip the file
* Move the unzipped folder to your home directory into a folder called github and rename the unzipped folder to LocalTrailers.bundle (removing the -master suffix)
* Open a Terminal
* Execute the following commands

```bash
  # rm -fr $PLEX_FOLDER/Plug-ins/LocalTrailers.bundle
  # ln -s ~/github/LocalTrailers.bundle/ $PLEX_FOLDER/Plug-ins/LocalTrailers.bundle
```

To update the plugin.
Redownload the zip file and replace the .bundle file found here: github/LocalTrailers.bundle
