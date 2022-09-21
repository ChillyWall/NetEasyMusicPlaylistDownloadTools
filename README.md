# NetEasyMusicPlaylistDownloadTools

下载网易云音乐歌单中的全部或部分歌曲。

## 依赖

此脚本基于python和[NeteasyCloudMusicApi](https://neteasecloudmusicapi.vercel.app/#/)。

## 开始使用

### 基础

```python
# 外部调用, 确保导入正确
from NetEasyMusicPlaylistDownloadTools import NetEasyPlaylistDownloader as nd
id = '7238513086'
playlist = nd(id)
playlist.get_playlist()
playlist.download()
```

默认情况下`get_playlist()`函数会自动将所有的信息保存到json文件中, 默认保存方式为`./歌单名称/歌单名称.json`, 如要修改可自行修改类函数.

同时会自动创建歌词lrc文件, 默认方式为`./歌单名称/歌曲名称/歌曲名称.lrc`

最终目录结构如下:

```
./歌单名称/
    -歌单名称.json
    -歌单名称.jpg
    -歌曲名称1/
        -歌曲名称1.mp3
        -歌曲名称1.lrc
        -歌曲名称.jpg
    -歌曲名称2/
        -
        ...

```

## 高级

### 从文件导入

默认获取数据之后会导出数据, 导出的数据可以再导入避免不必要的重复获取.

```python
playlist.get_playlist(from_file = 'your_file.json')
```

### 仅部分歌曲

有时歌单歌曲数量非常多, 可以先获取部分歌曲的信息.

同时下载时也可以只先下载部分歌曲.

```python
# 下载前一百首歌
playlist.get_playlist(slice=(0, 100))
playlist.download(slice=(0, 50))
```

(注意: 下载部分歌曲是下载已获取的所有歌曲中的部分歌曲, 范围应被包括在获取歌曲的范围中.)

### 设置类中的变量

在创建新类时可以传入参数, 或使用'set()'函数可以设置类中的一些默认值.

所有默认值:

* `output_dir`: 输出目录, 默认为歌单名称.
* `load_enc`: 读取数据文件时使用的编码, 默认为utf-8.
* `save_enc`: 保存数据文件时使用的编码, 默认为utf-8.
* `lrc_enc`: lrc歌词文件的编码, 默认为utf-8.
* `headers`: 发出请求时的headers.

```
playlist = nd(id, output_dir = './my_songs/')
playlist.set(info_file = './my_songs.json')
playlist.set(lrc_enc = 'gbk')
```

基于CloudMusic api编写的下载网易云音乐的python脚本。
