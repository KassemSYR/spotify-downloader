from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from mutagen.mp4 import MP4, MP4Cover
from core.logger import log

import urllib.request


def compare(music_file, metadata):
    """Check if the input music file title matches the expected title."""
    try:
        if music_file.endswith('.mp3'):
            audiofile = EasyID3(music_file)
            already_tagged = audiofile['title'][0] == metadata['name']
        elif music_file.endswith('.m4a'):
            audiofile = MP4(music_file)
            already_tagged = audiofile[tags['title']] == metadata['name']
    except (KeyError, TypeError):
        already_tagged = False

    return already_tagged


def embed(music_file, meta_tags):
    """ Embed metadata. """
    embed = EmbedMetadata(music_file, meta_tags)
    if music_file.endswith('.m4a'):
        log.info('Applying metadata')
        return embed.as_m4a()
    elif music_file.endswith('.mp3'):
        log.info('Applying metadata')
        return embed.as_mp3()
    else:
        log.warning('Cannot embed metadata into given output extension')
        return False


class EmbedMetadata:
    def __init__(self, music_file, meta_tags):
        self.music_file = music_file
        self.meta_tags = meta_tags

    def as_mp3(self):
        """ Embed metadata to MP3 files. """
        music_file = self.music_file
        meta_tags = self.meta_tags
        # EasyID3 is fun to use ;)
        audiofile = EasyID3(music_file)
        audiofile['artist'] = meta_tags['artists'][0]['name']
        audiofile['albumartist'] = meta_tags['artists'][0]['name']
        audiofile['album'] = meta_tags['album']['name']
        audiofile['title'] = meta_tags['name']
        audiofile['tracknumber'] = [meta_tags['track_number'],
                                    meta_tags['total_tracks']]
        audiofile['discnumber'] = [meta_tags['disc_number'], 0]
        audiofile['date'] = meta_tags['release_date']
        audiofile['originaldate'] = meta_tags['release_date']
        audiofile['media'] = meta_tags['type']
        audiofile['author'] = meta_tags['artists'][0]['name']
        audiofile['lyricist'] = meta_tags['artists'][0]['name']
        audiofile['arranger'] = meta_tags['artists'][0]['name']
        audiofile['performer'] = meta_tags['artists'][0]['name']
        audiofile['website'] = meta_tags['external_urls']['spotify']
        audiofile['length'] = str(meta_tags['duration_ms'] / 1000)
        if meta_tags['publisher']:
            audiofile['encodedby'] = meta_tags['publisher']
        if meta_tags['genre']:
            audiofile['genre'] = meta_tags['genre']
        if meta_tags['copyright']:
            audiofile['copyright'] = meta_tags['copyright']
        if meta_tags['external_ids']['isrc']:
            audiofile['isrc'] = meta_tags['external_ids']['isrc']
        audiofile.save(v2_version=3)
        audiofile = ID3(music_file)
        try:
            albumart = urllib.request.urlopen(meta_tags['album']['images'][0]['url'])
            audiofile["APIC"] = APIC(encoding=3, mime='image/jpeg', type=3,
                                     desc=u'Cover', data=albumart.read())
            albumart.close()
        except IndexError:
            pass
        audiofile.save(v2_version=3)
        return True

    def as_m4a(self):
        """ Embed metadata to M4A files. """
        music_file = self.music_file
        meta_tags = self.meta_tags
        # Apple has specific tags - see mutagen docs -
        # http://mutagen.readthedocs.io/en/latest/api/mp4.html
        tags = {'album': '\xa9alb',
                'artist': '\xa9ART',
                'date': '\xa9day',
                'title': '\xa9nam',
                'originaldate': 'purd',
                'comment': '\xa9cmt',
                'group': '\xa9grp',
                'writer': '\xa9wrt',
                'genre': '\xa9gen',
                'tracknumber': 'trkn',
                'albumartist': 'aART',
                'disknumber': 'disk',
                'cpil': 'cpil',
                'albumart': 'covr',
                'copyright': 'cprt',
                'tempo': 'tmpo'}

        audiofile = MP4(music_file)
        audiofile[tags['artist']] = meta_tags['artists'][0]['name']
        audiofile[tags['albumartist']] = meta_tags['artists'][0]['name']
        audiofile[tags['album']] = meta_tags['album']['name']
        audiofile[tags['title']] = meta_tags['name']
        audiofile[tags['tracknumber']] = [(meta_tags['track_number'],
                                           meta_tags['total_tracks'])]
        audiofile[tags['disknumber']] = [(meta_tags['disc_number'], 0)]
        audiofile[tags['date']] = meta_tags['release_date']
        audiofile[tags['originaldate']] = meta_tags['release_date']
        if meta_tags['genre']:
            audiofile[tags['genre']] = meta_tags['genre']
        if meta_tags['copyright']:
            audiofile[tags['copyright']] = meta_tags['copyright']
        try:
            albumart = urllib.request.urlopen(meta_tags['album']['images'][0]['url'])
            audiofile[tags['albumart']] = [MP4Cover(
                albumart.read(), imageformat=MP4Cover.FORMAT_JPEG)]
            albumart.close()
        except IndexError:
            pass
        audiofile.save()
        return True
