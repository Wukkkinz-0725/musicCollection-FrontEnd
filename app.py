from flask import Flask, Response, request, render_template, url_for, flash, redirect
from flask_cors import CORS
import os
import requests
import re

DATE_PATTERN = r'\d{4}-\d{2}-\d{2}'

def validate_date(release_date):
    pattern = re.compile(DATE_PATTERN)
    return pattern.match(release_date)

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
        query_type = request.form['query_type']
        query_value = request.form['query_value']
        if query_type == 'sid':
            res = [get_data(base_url, '/songs/query/sid/' + query_value)]
        elif query_type == 'name':
            res = get_data(base_url, '/songs/query/song_name/' + query_value)
        data = {'dict': res, 'query_type': query_type, 'query_value': query_value}
        return render_template('./songs/query_result.html', data=data)
    return render_template('./songs/songs.html', data=data)

@app.route("/show_song_data", methods=('GET', 'POST'))
def show_partial_songs(data):
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
            flash('Song name is invalid.')
        elif not release_date or not validate_date(release_date):
            flash('Release date is invalid.')
        elif not artist:
            flash('Artist is invalid.')
        else:
            # 保存歌曲，并显示这首歌的detail
            res = post_data(base_url, '/songs/create', {'song_name': songs_name, 'artist': artist, 'release_date': release_date})
            # res = SongsDB.create_song({'song_name': songs_name, 'artist': artist, 'release_date': release_date})
            return redirect(url_for('view_songs_detail', sid=res.json()['sid']))
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
    data = get_data(base_url, '/songs/query/sid/' + str(sid))
    if request.method == 'POST':
        # 在html里点击submit，会通过POST进入这个if statement
        dic = {}
        if len(request.form['song_name']) > 0:
            dic['song_name'] = request.form['song_name']
        if len(request.form['artist']) > 0:
            dic['artist'] = request.form['artist']
        if len(request.form['release_date']) > 0:
            if validate_date(request.form['release_date']):
                dic['release_date'] = request.form['release_date']
            else:
                flash('Release date is invalid.')
                return redirect(url_for('edit_song_detail', sid=sid))
        if len(dic) > 0:
            res = post_data(base_url, '/songs/update/' + str(sid), dic)
            return redirect(url_for('view_songs_detail', sid=sid))
    return render_template('./songs/edit_song_detail.html', data=data)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 9001))
    app.run(host="localhost", port=port)