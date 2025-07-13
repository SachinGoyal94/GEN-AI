from pytube import YouTube

yt = YouTube("https://www.youtube.com/watch?v=dQw4w9WgXcQ")  # known to work
print(yt.title)
