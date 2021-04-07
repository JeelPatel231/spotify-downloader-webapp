from django.http import HttpResponse
from django.shortcuts import render, redirect
import os,youtube_dl, eyed3, urllib, shutil, spotipy, subprocess
from spotipy.oauth2 import SpotifyClientCredentials
from youtube_search import YoutubeSearch as ys

downloadlist=[]

def envvars(request):
    client_id=request.GET.get('client_id')
    client_secret=request.GET.get('client_secret')
    os.environ['SPOTIPY_CLIENT_ID'] = client_id
    os.environ['SPOTIPY_CLIENT_SECRET'] = client_secret
    return redirect('/')

def root(request):
    if 'SPOTIPY_CLIENT_ID' in os.environ and 'SPOTIPY_CLIENT_SECRET' in os.environ:
        global spotify
        spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
        return redirect('/homepage')
    else:
        return redirect('/setvars')

def setvars(request):
    return render(request, 'setvars.html')

def homepage(request):
    return render(request, 'index.html')

def downloadandmetadata(token, albumname, albumart, track_number, albumartist, songname, artist, ytdldownload):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': "templates/YTDL/" + token + "/" + songname + " - " + artist + ".%(ext)s",
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download(ytdldownload)
    audiofile = eyed3.core.load("templates/YTDL/" + token + "/" + songname + " - " + artist + ".mp3")
    audiofile.tag.artist = artist
    audiofile.tag.album = albumname
    audiofile.tag.album_artist = albumartist
    audiofile.tag.title = songname
    audiofile.tag.track_num = track_number
    audiofile.tag.images.set(3, urllib.request.urlopen(albumart).read(), 'image/jpeg')
    audiofile.tag.save()

def track(request):
    if request.method == 'GET':
        urls=request.GET.get('urls')
        downloadlist=urls.split('\r\n')
        print(downloadlist)
        token=request.GET.get('csrfmiddlewaretoken')
        for track_id in downloadlist:
            if 'track' in track_id:
                print('used track function')
                results = spotify.track(track_id)
                albumart = results['album']['images'][0]['url']
                songname = results['name']
                artist = results['artists'][0]['name']
                albumartist = results['album']['artists'][0]['name']
                track_number = results['track_number']
                albumname = results['album']['name']
                artistandsong = songname + ' by ' + artist + ' lyrics'
                print(artistandsong)
                results = ys(artistandsong, max_results=1).to_dict()
                youtubeurl = 'youtube.com' + results[0]['url_suffix']
                ytdldownload=[]
                ytdldownload.append(youtubeurl)
                downloadandmetadata(token, albumname, albumart, track_number, albumartist, songname, artist, ytdldownload)
                # checktype(token, albumname, albumart, track_number, albumartist, songname, artist, ytdldownload)

            elif 'playlist' in track_id:
                print('used playlist function')
                results = spotify.playlist(track_id)
                songsindict = results['tracks']
                songname = songsindict['items']
                for i in songname:
                    albumart = i['track']['album']['images'][0]['url']
                    songname = i['track']['name']
                    artist = i['track']['artists'][0]['name']
                    albumartist = i['track']['album']['artists'][0]['name']
                    track_number = i['track']['track_number']
                    albumname = i['track']['album']['name']
                    artistandsong = songname + ' by ' + artist + ' lyrics'
                    print(artistandsong)
                    results = ys(artistandsong, max_results=1).to_dict()
                    youtubeurl = 'youtube.com' + results[0]['url_suffix']
                    ytdldownload=[]
                    ytdldownload.append(youtubeurl)
                    downloadandmetadata(token, albumname, albumart, track_number, albumartist, songname, artist, ytdldownload)
    
        subprocess.run(['zip','-r','templates/YTDL/'+token+'/spotify_downloads.zip','templates/YTDL/'+token])

        #serve below, if you are running locally, you can comment all of this, 
        # and uncomment the last line, since you dont need to download the file again,
        # you will find your files in YTDL folder with a random foldername
        with open('templates/YTDL/'+token+'/spotify_downloads.zip', 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/zip")
            response['Content-Disposition'] = 'inline; filename=' + 'spotify_downloads.zip'
            return response
        
        #uncomment this line below if you have commented out the above lines
        # return HttpResponse('<h1>Should see your files in YTDL Folder</h1>')