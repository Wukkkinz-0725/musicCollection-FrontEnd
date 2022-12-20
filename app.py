from flask import Flask, Response, request, render_template, url_for, flash, redirect
from flask_cors import CORS
import os
import requests

# Create the Flask application object.
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'whatever'
base_url = 'https://szbxfmue7c.execute-api.us-east-2.amazonaws.com/music'


def get_data(url, path):
    data = requests.get(url + path).json()
    return data


def post_data(url, path, data):
    res = requests.post(url + path, json=data)
    return res


# functions for songs
@app.route("/", methods=('GET', 'POST'))
def main():
    data = get_data(base_url, '/songs/all')
    if request.method == 'POST':
        # 在html里点击submit，会通过POST进入这个if statement
        query_type = request.form['query_type']
        query_value = request.form['query_value']
        if query_type == 'sid':
            # TODO: 报错，如果sid错误，sid非integer，目前未考虑错误输入
            # TODO: 其实这里只需要verify sid，因为打开song detail界面时只用了sid
            return redirect(url_for('view_songs_detail', sid=int(query_value)))
        elif query_type == 'name':
            data = get_data(base_url, '/songs/query/song_name/' + query_value)
            # TODO: 目前默认result只有一首歌，如果需要处理query结果为多首歌需要增加html
            return redirect(url_for('view_songs_detail', sid=data[0]['sid']))
    return render_template('./songs/songs.html', data=data)

@app.route('/songs/detail/<sid>')
def view_songs_detail(sid):
    data = get_data(base_url, '/songs/query/sid/' + str(sid))
    return render_template('./songs/song_detail.html', data=data)

@app.route('/songs/new_songs', methods=('GET', 'POST'))
def create_songs_webpage():
    if request.method == 'POST':
        # 在html里点击submit，会通过POST进入这个if statement
        songs_name = request.form['song_name']
        artist = request.form['artist']
        release_date = request.form['release_date']
        
        if not songs_name:
            # TODO: flash not working properly
            flash('Song name is required!')
        elif not release_date:
            flash('Release date is required!')
        elif not artist:
            flash('Artist is required!')
        else:
            # 保存歌曲，并显示这首歌的detail
            res = post_data(base_url, '/songs/create', {'song_name': songs_name, 'artist': artist, 'release_date': release_date})
            # res = SongsDB.create_song({'song_name': songs_name, 'artist': artist, 'release_date': release_date})
            print(res.json())
            return redirect(url_for('view_songs_detail', sid=res.json()))
    # 点击create song button后直接渲染html
    return render_template('./songs/create_song.html')


@app.route('/songs/delete/<sid>')
def delete_song(sid):
    # TODO: delete this function and corresponding button
    # delete_song_by_sid(sid)
    res = post_data(base_url, '/songs/delete' + str(sid), '')
    # TODO: verify success
    return redirect(url_for('main'))


@app.route('/songs/edit/<sid>', methods=('GET', 'POST'))
def edit_song_detail(sid):
    # data = SongsDB.get_song_by_sid(sid)
    #
    # if request.method == 'POST':
    #     # 在html里点击submit，会通过POST进入这个if statement
    #     songs_name = request.form['song_name']
    #     artist = request.form['artist']
    #     release_date = request.form['release_date']
    #
    #     if not songs_name:
    #         flash('Song name is required!')
    #     elif not artist:
    #         flash('Artist is required!')
    #     elif not release_date:
    #         flash('Release Date is required!')
    #     else:
    #         # 保存歌曲，并显示这首歌的detail
    #         SongsDB.update_song_by_sid(sid, {'song_name': songs_name, 'artist': artist, 'release_date': release_date})
    #         return redirect(url_for('view_songs_detail', sid=sid))
    # 点击edit song button后直接渲染html
    return render_template('edit_song_detail.html', data=data)



if __name__ == "__main__":
    port = int(os.environ.get('PORT', 9001))
    app.run(host="localhost", port=port)