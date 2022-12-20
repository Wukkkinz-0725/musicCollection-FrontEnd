from flask import Flask, Response, request, render_template, url_for, flash, redirect
from flask_cors import CORS
from datetime import datetime
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
middleware_url = 'http://googleauth-env.eba-6yr79q2j.us-east-2.elasticbeanstalk.com'

def get_data(url, path):
    try:
        data = requests.get(url + path).json()
    except Exception:
        data = []
    return data


def post_data(url, path, data):
    res = requests.post(url + path, json=data)
    return res

# functions for index and login
@app.route('/')
def index():
    return render_template('./login/index.html')

@app.route("/login")
def google_login():
    print("login")
    data = get_data(middleware_url, '/login')
    return data

# functions for songs
@app.route("/main", methods=('GET', 'POST'))
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

@app.route('/songs/detail/<sid>', methods=('GET', 'POST'))
def view_songs_detail(sid):
    song_data = get_data(base_url, '/songs/query/sid/' + str(sid))

    comments_data = get_data(base_url, '/comments/query/sid/' + str(sid))
    data = {'song_data': song_data, 'comments': comments_data}

    if request.method == 'POST':
        # 在html里点击submit，会通过POST进入这个if statement，发送评论
        # TODO: change uid
        comment_dict = {'content': request.form['comment'], 'uid': 1, 'sid': sid, 'date': str(datetime.now())}

        # 保存评论，并显示这首歌的detail
        res = post_data(base_url, '/comments/create', comment_dict)
        return redirect(url_for('view_songs_detail', sid=sid))
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
    res = post_data(base_url, '/songs/delete/' + str(sid), '')
    # TODO: verify success
    return redirect(url_for('main'))


@app.route('/comments/delete/<cid>')
def delete_comment(cid):
    # TODO: delete this function and corresponding button
    sid = get_data(base_url, '/comments/query/cid/' + str(cid))['sid']
    res = post_data(base_url, '/comments/delete/cid/' + str(cid), '')
    # TODO: verify success
    return redirect(url_for('view_songs_detail', sid=sid))


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