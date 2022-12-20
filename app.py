from flask import Flask, Response, request, render_template, url_for, flash, redirect
from flask_cors import CORS
from datetime import datetime
import os
import json
import requests

# Create the Flask application object.
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'whatever'
base_url = 'https://szbxfmue7c.execute-api.us-east-2.amazonaws.com/music'

def get_data(url, path):
    data = requests.get(url + path).json()
    return data

# functions for songs
@app.route("/", methods=('GET', 'POST'))
def main():
    data = get_data(base_url, '/songs/all')
    # if request.method == 'POST':
        # 在html里点击submit，会通过POST进入这个if statement
        # query_type = request.form['query_type']
        # query_value = request.form['query_value']
        # if query_type == 'sid':
        #     # TODO: 报错，如果sid错误，sid非integer，考虑把这部分放进api function，目前不考虑错误输入
        #     # TODO: 其实这里只需要verify sid，因为打开song detail界面时只用了sid
        #     data = json.loads(get_song_by_id(int(query_value)).data)
        #     return redirect(url_for('view_songs_detail', sid=int(query_value)))
        # elif query_type == 'name':
        #     data = json.loads(get_songs_by_name(query_value).data)[0]
        #     return redirect(url_for('view_songs_detail', sid=data['sid']))
    return render_template('./songs/songs.html', data=data)

@app.route('/songs/detail/<sid>')
def view_songs_detail(sid):
    data = {"sid": 1, "song_name": "happy new year", "artist": "wjz", "release_date": "2020-01-01"}
    return render_template('./songs/song_detail.html', data=data)

@app.route('/songs/new_songs', methods=('GET', 'POST'))
def create_songs_webpage():
    # if request.method == 'POST':
    #     # 在html里点击submit，会通过POST进入这个if statement
    #     songs_name = request.form['song_name']
    #     artist = request.form['artist']
    #     release_date = request.form['release_date']
        
    #     if not songs_name:
    #         # TODO: flash not working properly
    #         flash('Song name is required!')
    #     elif not release_date:
    #         flash('Release date is required!')
    #     elif not artist:
    #         flash('Artist is required!')
    #     else:
    #         # 保存歌曲，并显示这首歌的detail
    #         res = SongsDB.create_song({'song_name': songs_name, 'artist': artist, 'release_date': release_date})
    #         return redirect(url_for('view_songs_detail', sid=res))
    # # 点击create song button后直接渲染html
    return render_template('./songs/create_song.html')

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 9001))
    app.run(host="localhost", port=port)