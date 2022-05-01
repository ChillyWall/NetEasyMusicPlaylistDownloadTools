import time
import requests
import os
import json
import re


class NetEasyPlaylistDownloader():
    # api接口链接
    url = 'http://localhost:3000'
    playlist_detail = url + '/playlist/detail?id='
    song_detail = url + '/song/detail?ids='
    song_url = url + '/song/url?id='
    lyric = url + '/lyric?id={0}+&lv=1&tv=-1'

    # 用来发出请求的headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0'
    }
    # 出错的歌曲的列表
    errors = []

    # 用于导出数据时json文件
    info_file = ''
    info_specified = False

    # 输出目录
    output_dir = ''
    out_specified = False
    # 歌词lrc文件、保存、读取数据文件的编码
    lrc_enc = 'utf-8'
    json_enc = 'utf-8'
    load_enc = 'utf-8'


    def __init__(self, playlist_id: str, **kwargs):
        """
        Args:
            playlist_id (str): 网易云音乐歌单id
            **kwargs : 需要修改的参数
        """
        self.playlist_id = playlist_id
        self.set(**kwargs)

    def set(self, **kwargs):
        "修改类中的变量"

        for key, value in kwargs.items():
            setattr(self, key, value)
            if key == 'output_dir':
                self.out_specified = True

    def get_playlist(self, slice: tuple = (None, None),from_file: str = None, to_file: bool = True, info_file: str = None, load_enc: str = None, save_enc: str = None, write_lrc: bool = True, lrc_encoding: str = None):
        """获取歌单信息, 包括歌单的id, 名字, 描述, 封面图片链接, 以及歌曲的信息, 包括名字, id, 歌手, 歌词lrc文本, 封面图片链接. 并将对象设置为类中的变量, 可外部调取.

        Args:
            slice (tuple, optional): 歌单下载范围, 长度为2, 前一个是开始, 后一个是结束, 设为None则从头开始或一直到末尾, 默认为全部.
            from_file (str, optional): 从之前导出的数据文件中获取数据, 而不是再请求一遍, None则不导入.
            to_file (bool, optional): 是否导出数据. Defaults to True.
            info_file (str, optional): 导出数据文件的文件名, None则使用类中定义的名称.
            load_enc (str, optional): 读取数据文件时使用的编码. None则使用类中定义的默认值.
            save_enc (str, optional): 保存数据文件时使用的编码. None则使用类中定义的默认值.
            write_lrc (bool, optional): 是否创建lrc歌词文件. Defaults to True.
            lrc_encoding (str, optional):lrc歌词文件的编码, 一些mp3, mp4播放器不支持utf-8编码, 须设为gbk编码. 默认为None即使用类中定义的值.
        """
        if from_file:
            # 导入数据
            playlist = self.load_info(from_file, load_enc)
            if not self.out_specified:
                self.output_dir = playlist['name'] + '/'
            if not os.path.exists(self.output_dir):
                os.mkdir(self.output_dir)
        else:
            # 通过api获取数据
            playlist = self.get_playlist_detail()
            ids_all = playlist['song_ids']
            ids = ids_all[slice[0]:slice[1]]
            songs = self.get_songs(ids)
            playlist['songs'] = songs
            if not self.out_specified:
                self.output_dir = playlist['name'] + '/'
            if not os.path.exists(self.output_dir):
                os.mkdir(self.output_dir)
        self.playlist = playlist
        if not self.info_specified:
            self.info_file = self.output_dir + playlist['name'] + '.json'
        # 保存数据
        if to_file and not from_file:
            self.save_info(info_file, save_enc)
        # 创建歌词lrc
        if write_lrc:
            self.write_lyrics(playlist['songs'], lrc_encoding)

    def get_songs(self, ids: list):
        """获取歌曲对象, 包括信息(包括名称, 歌手, 封面图片链接), id, 歌词lrc文本内容和经过处理的下载文件时使用的文件名.

        Args:
            ids (list): 歌曲id列表, 其中的id应为str格式. 函数`get_playlist_detail()['song_ids']`或者`self.playlist['song_ids']`的输出

        Returns:
            dict: 歌曲信息
        """
        songs = []
        for id in ids:
            try:
                info = self.get_song_info(id)
                lrc = self.get_lrc(id)
                file_name = self.get_file_name(info)
            except:
                print("There's something wrong with the song(id={0})".format(id))
                error = {
                    'name': id,
                    'type': 'song_info'
                }
                self.errors.append(error)
                continue
            
            song = {
                'info': info,
                'id': id,
                'lrc': lrc,
                'file_name': file_name,
            }

            songs.append(song)
            print('Finish get the information of the song {0}'.format(info['title']))
            time.sleep(1)

        return songs

    def get_playlist_detail(self):
        """获取歌单基本信息, 包括歌单名称, id, 描述, 和其中所有歌曲的id.

        Returns:
            dict: 歌单信息
        """
        p_u = self.playlist_detail + self.playlist_id
        response = requests.get(p_u, headers=self.headers).json()
        playlist_name = response['playlist']['name']
        description = response['playlist']['description']
        cover_image = response['playlist']['coverImgUrl']
        trackIds = response['playlist']['trackIds']

        song_ids = []
        for ti in trackIds:
            id = str(ti['id'])
            song_ids.append(id)

        playlist = {
            'name': playlist_name,
            'id': self.playlist_id,
            'description': description,
            'cover_image': cover_image,
            'song_ids': song_ids,
        }
        return playlist

    def get_song_info(self, id: str):
        """获取歌曲基本信息, 包括名称, 歌手, 封面图片链接

        Args:
            id (str): 歌曲id

        Returns:
            dict: 歌曲基本信息
        """
        song_detail = self.song_detail
        song_detail_url = song_detail + id

        response = requests.get(song_detail_url, headers=self.headers).json()
        name = response['songs'][0]['name']
        ar = response['songs'][0]['ar']
        cover_image = response['songs'][0]['al']['picUrl']
        # 将所有歌手变成一个字符串
        authors = ''
        for author in ar:
            authors += author['name']
            if author != ar[-1]:
                authors += ', '

        song_info = {
            'title': name,
            'authors': authors,
            'cover': cover_image
        }

        return song_info

    def get_lrc(self, id: str):
        """获取歌词lrc文本内容

        Args:
            id (str): 歌曲id

        Returns:
            str: _description_
        """
        response = requests.get(self.lyric.format(
            id), headers=self.headers).json()
        lrc = response['lrc']['lyric']
        return lrc

    def get_media_url(self, id: str):
        """获取歌曲文件下载链接, 因过一段时间后会失效, 所以每一次下载要重新获取一次.

        Args:
            id (str): 歌曲id

        Returns:
            str: 下载链接
        """
        response = requests.get(self.song_url + id, headers=self.headers).json()
        url = response['data'][0]['url']

        return url

    def get_file_name(self, song_info: dict):
        """获取下载时文件名, 默认为歌曲名+歌手名, 并去除其中的禁用字符

        Args:
            song_info (dict): 歌曲基本信息, 为函数`get_song_info()`或`self.playlist['songs'][0]['info']`

        Returns:
            _type_: _description_
        """
        name = song_info['title']
        authors = song_info['authors']

        file_name = name + ' - ' + authors

        file_name = self.check_name(file_name)

        return file_name

    def save_info(self, file: str = None, encoding: str = None):
        """保存`self.playlist`对象到json文件

        Args:
            file (str, optional): 数据文件文件名. 为None则默认为`./歌单名称/歌单名称.json`.
            encoding (str, optional): 编码. 为None则使用类中定义得值.
        """
        info = self.playlist

        if encoding:
            enc = encoding
        else:
            enc = self.json_enc

        if not file:
            file = self.playlist['name']
            file = self.check_name(file)
            file = self.output_dir + file + '.json'
        data = json.dumps(info, indent=4, ensure_ascii=False)

        with open(file, 'w', encoding=enc) as f:
            f.write(data)

    def load_info(self, file: str = None, encoding: str = None):
        """从数据文件中导入数据, 所导入的应为之前导出的数据文件

        Args:
            file (str, optional): 导入的文件名. 为None则使用`./歌单名称/歌单名称.json`.
            encoding (str, optional): 编码. 为None则使用类中的值.

        Returns:
            _type_: _description_
        """
        if encoding:
            enc = encoding
        else:
            enc = self.load_enc
        
        if not file:
            file = self.playlist['name'] + '.json'

        with open(file, 'r', encoding=enc) as f:
            contents = f.read()

        data = json.loads(contents)
        return data

    def write_lyrics(self, songs: list, encoding: str = None):
        """创建lrc文件并写入数据

        Args:
            songs (list): 歌曲对象列表, 应为`get_songs()`的输出或`self.playlist['songs']`的值
            encoding (str, optional): lrc文件的编码. 为None则使用类中定义的值.
        """
        if not encoding:
            encoding = self.lrc_enc

        for song in songs:
            output_dir = self.output_dir + song['file_name'] + '/'
            if not os.path.exists(output_dir):
                os.mkdir(output_dir)

            lrc = song['lrc']

            with open(output_dir + song['file_name'] + '.lrc', 'w', encoding=encoding, errors='ignore') as f:
                f.write(lrc)

    def download_file(self, url: str, out: str):
        """利用requests下载文件

        Args:
            url (str): 链接
            out (str): 输出文件名
        """
        headers = self.headers
        r = requests.get(url, headers=headers).content

        with open(out, 'bw') as f:
            f.write(r)

    def download_images(self, songs: list, output_dir: str = None):
        """下载歌单及歌曲封面

        Args:
            songs (list): 歌曲对象列表, 应为`get_songs()`的输出或`self.playlist['songs']`的值
            output_dir (str, optional): 输出目录. 为None则默认使用`./歌单名称/`.
        """
        if not output_dir:
            output_dir = self.output_dir

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        # 下载歌单封面
        pl = self.playlist
        pl_cov_url = pl['cover_image']
        suf = os.path.splitext(pl_cov_url)[-1]
        pl_cov_out = '{0}{1}{2}'.format(output_dir, pl['name'], suf)
        try:
            self.download_file(pl_cov_url, pl_cov_out)
        except:
            print("Failed to download the cover picture of playlist")
            error = {
                'name': 'playlist_cover_pic',
                'type': 'pl_cover_pic_dl'
            }
            self.errors.append(error)

        # 下载歌曲封面
        for song in songs:
            cover_url = song['info']['cover']
            suf = os.path.splitext(cover_url)[-1]
            cover_out = '{2}{0}/{0}{1}'.format(song['file_name'], suf, output_dir)
            try:
                print('Downloading the cover picture of the song ' + song['info']['title'])
                self.download_file(cover_url, cover_out)
            except:
                print("Failed to download the cover picture of the song whose id is {0}".format(song['id']))
                error = {
                    'name': id,
                    'type': 'song_cover_pic_dl'
                }
                self.errors.append(error)

            time.sleep(1)

    def download_songs(self, songs: list, output_dir: str = None):
        """下载歌曲mp3文件

        Args:
            songs (list): 歌曲对象列表, 应为`get_songs()`的输出或`self.playlist['songs']`的值
            output_dir (str, optional): 输出目录. 为None则默认使用`./歌单名称/`.
        """
        if not output_dir:
            output_dir = self.output_dir

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        for song in songs:
            # 获取下载连接
            media_url = self.get_media_url(song['id'])
            # 检查url是否有效
            if not isinstance(media_url, str):
                print("There is no the url of the song named '{0}'".format(
                    song['info']['title']))
                # 加入错误信息
                error = {
                    'name': id,
                    'type': 'song_url_missed'
                }
                print(repr(e))
                self.errors.append(error)
                continue

            # 下载文件名
            pre = output_dir + song['file_name'] + '/'
            if not os.path.exists(pre):
                os.mkdir(pre)
            out = pre + song['file_name'] + '.mp3'

            try:
                print('Downloading the song ' + song['info']['title'])
                self.download_file(media_url, out)
            except Exception as e:
                print("Failed to download the song whose id is ".format(song['id']))
                error = {
                    'name': id,
                    'type': 'song_dl'
                }
                print(repr(e))
                self.errors.append(error)
            time.sleep(1)

    def download(self, slice: tuple = (None, None), output_dir: str = None, if_img: bool = True):
        """下载所有歌曲文件及响应图片

        Args:
            slice (tuple, optional): 长度为2, 是将要下载歌曲切片, 前一个结束, 后一个为开始. 默认全部下载.
            output_dir (str, optional): 输出目录. 为None则使用默认值.
            if_img (bool, optional): 是否下载歌单及歌曲封面. Defaults to True.
        """
        playlist = self.playlist
        total_songs = playlist['songs']
        songs = total_songs[slice[0]:slice[1]]

        self.download_songs(songs, output_dir)
        if if_img:
            self.download_images(songs, output_dir)

    def check_name(self, file_name: str):
        """ 去掉文件名敏感字符

        Args:
            file_name (str): 原名称

        Returns:
            str: 处理后名称
        """
        pattern = re.compile('[\\/:*?"<>|\r\n]+')
        new_name = re.sub(pattern, ' ', file_name)
        return new_name

    def output_errors(self):
        "将所有出错歌曲列表写入到文件`./errors.json`中"
        errors = self.errors
        data = json.dumps(errors, ensure_ascii=False, indent=4)
        with open('errors.json', 'w', encoding='utf-8') as f:
            f.write(data)
