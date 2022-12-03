import time
import requests
import os
import json
import re


class Base():
    _headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0'
    }
    _host = 'http://localhost:3000'
    name = str()
    cover_img = str()
    id = str()
    dir = str()

    def __init__(self):
        pass

    def set_dir(self, dir):
        self.dir = dir
        os.makedirs(dir, exist_ok=True)

    def check_name(self, file_name: str):
        pattern = re.compile('[\\/:*?"<>|\r\n]+')
        new_name = re.sub(pattern, ' ', file_name)
        return new_name

    def download(self, url: str, out: str):
        content = requests.get(url, headers=self._headers).content

        with open(out, 'bw') as f:
            f.write(content)


class Playlist(Base):
    error = []
    def __init__(self, id, dir='.'):
        self.id = id
        self.set_detail()
        self.set_dir(os.path.join(dir, self.name))
        self.set_file_name()

    def set_detail(self):
        p_u = self._host + f'/playlist/detail?id={self.id}'
        pl = requests.get(p_u, headers = self._headers).json()['playlist']
        self.name = pl['name']
        self.description = pl['description']
        self.cover_img = pl['coverImgUrl']
        self.trackIds = pl['trackIds']

        self._song_ids = [str(ti['id']) for ti in self.trackIds]

    def create_songs(self):
        songs = []
        for id in self._song_ids:
            try:
                song = Song(id, self.dir)
                song.run()
                time.sleep(1)
                songs.append(song)
            except:
                self.error.append(id)

        self.songs = songs

    def set_file_name(self):
        self.file_name = f'{self.name}.json'

    def download_cover(self):
        print('Downloading the playlist cover.')
        suf = os.path.splitext(self.cover_img)[-1]
        path = os.path.join(self.dir, self.name + suf)
        self.download(self.cover_img, path)

    def get_info(self):
        info = {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'cover': self.cover_img,
            'songs': [song.get_info() for song in self.songs]
        }
        return info

    def save(self, encoding='utf-8'):
        print('Saving the data.')
        data = self.get_info()
        text = json.dumps(data, ensure_ascii=False, indent=4)
        path = os.path.join(self.dir, self.file_name)

        with open(path, 'w', encoding=encoding) as f:
            f.write(text)

    def run(self, encoding='utf-8'):
        print('Downloading the songs:')
        self.create_songs(encoding)
        self.save(encoding)
        print('The ids of the songs with error: ')
        for id in self.error:
            print(id)


class Song(Base):
    def __init__(self, id, dir='.'):
        self.id = id
        self.set_info()
        self.set_dir(os.path.join(dir, self.name))
        self.set_lrc()
        self.set_media_url()
        self.set_file_name()

    def set_info(self):
        url = self._host + f'/song/detail?ids={self.id}'
        data = requests.get(url, headers=self._headers).json()['songs'][0]
        self.name = data['name']
        self.cover_img = data['al']['picUrl']
        ar = data['ar']
        authors = ''
        for author in ar[:-1]:
            authors = authors + author['name'] + ', '
        self.authors = authors + ar[-1]['name']

    def set_lrc(self):
        url = self._host + f'/lyric?id={self.id}+&lv=1&tv=-1'
        self.lrc = requests.get(url, headers=self._headers).json()['lrc']['lyric']

    def set_media_url(self):
        url = self._host + f'/song/url?id={self.id}'
        self.media_url = requests.get(url, headers=self._headers).json()['data'][0]['url']

    def set_file_name(self):
        file_name = f'{self.name} - {self.authors}.mp3'
        self.file_name = self.check_name(file_name)

    def download_media(self):
        print(f'Downloading {self.name}')
        path = os.path.join(self.dir, self.file_name)
        self.download(self.media_url, path)

    def write_lrc(self, encoding='utf-8'):
        print('Writing the lrc file.')
        path = os.path.join(self.dir, f'{self.name}.lrc')
        with open(path, 'w', encoding=encoding) as f:
            f.write(self.lrc)

    def download_cover(self):
        print('Downloading the cover.')
        suf = os.path.splitext(self.cover_img)[-1]
        path = os.path.join(self.dir, self.name + suf)
        self.download(self.cover_img, path)

    def get_info(self):
        info = {
            'name': self.name,
            'id': self.id,
            'author': self.authors,
            'lrc': self.lrc,
            'media': self.media_url,
            'cover': self.cover_img,
        }
        return info

    def run(self, encoding='utf-8'):
        self.download_media()
        self.download_cover()
        self.write_lrc(encoding)
        print('Finished.\n\n')


def run(id, mode, dir, enc):
    if mode:
        song = Song(id, dir)
        song.run(enc)
    else:
        pl = Playlist(id, dir)
        pl.run(enc)


if __name__ == '__main__':
    mode = True
    while True:
        print('输入q退出\n输入c跳过循环\n输入p切换为歌单模式\n输入s切换为单曲模式（默认状态）\n\n')

        if mode:
            id = input('歌曲id：')
        else:
            id = input('歌单id：')

        if id == 'q':
            break
        elif id == 'p':
            mode = False
            continue
        elif id == 's':
            mode = True
            continue
        elif id == 'c':
            continue

        dir = input('输出目录（默认为./）: ')
        if dir == 'q':
            break
        elif dir == 'c':
            continue
        elif dir == 'p':
            mode = False
            continue
        elif dir == 's':
            mode = True
            continue
        elif not dir:
            dir = '.'

        enc = input('文件编码（默认为utf-8）：')
        if enc == 'q':
            break
        elif enc == 'c':
            continue
        elif enc == 'p':
            mode = False
            continue
        elif enc == 's':
            mode = True
            continue
        elif not enc:
            enc = 'utf-8'

        run(id, mode, dir, enc)
