from flask import Flask, Response, request, render_template, url_for, flash, redirect
from flask_cors import CORS
from datetime import datetime
import os
import requests
import re
import os
import pathlib
import requests
from datetime import datetime
from flask import Flask, session, abort, redirect, request
from google.oauth2.credentials import Credentials
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
import secrets

DATE_PATTERN = r'\d{4}-\d{2}-\d{2}'


def validate_date(release_date):
    pattern = re.compile(DATE_PATTERN)
    return pattern.match(release_date)


# Create the Flask application object.
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'whatever'
app.secret_key = secrets.token_hex(16)
base_url = 'https://szbxfmue7c.execute-api.us-east-2.amazonaws.com/music'
middleware_url = 'http://googleauth-env.eba-6yr79q2j.us-east-2.elasticbeanstalk.com'

client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email",
            "openid"],
    redirect_uri="http://frontend-env.eba-kffmqkp3.us-east-2.elasticbeanstalk.com/authorize"
)


def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # Authorization required
        else:
            return function()

    return wrapper


def validate_email(email):
    if not re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", email):
        return False
    else:
        return


def get_data(url, path):
    try:
        data = requests.get(url + path).json()
    except Exception:
        data = []
    return data


def post_data(url, path, data):
    res = requests.post(url + path, json=data)
    return res


def check_user_exist(email):
    res = get_data(base_url, '/users/all')
    for user in res:
        if user['email'] == email:
            return user['id']
    return None


def get_user_collections_sid(uid):
    user_collection_data = get_data(base_url, '/users/{}/songs'.format(uid))
    return [data['sid'] for data in user_collection_data]


# functions for index and login
@app.route('/')
def index():
    return render_template('./login/index.html')


@app.route("/login")
def google_login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/authorize")
def authorize():
    flow.fetch_token(authorization_response=request.url)

    auth_code = request.args.get('code')
    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience='942606144781-d1nlf55298ld772qd9d4h093qnebplpd.apps.googleusercontent.com'
    )

    # store user info
    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["email"] = id_info.get("email")

    # store credential info
    session["token"] = credentials._id_token
    session["refresh_token"] = credentials._refresh_token
    session["scopes"] = credentials._scopes
    session["client_id"] = credentials._client_id
    session["client_secret"] = credentials._client_secret
    session["quota_project_id"] = credentials._quota_project_id
    session["expiry"] = credentials.expiry.strftime("%Y-%m-%dT%H:%M:%S")

    return redirect("/protected_area")


# functions for songs
@app.route("/main", methods=('GET', 'POST'))
def main():
    if session['google_id'] is None:
        return redirect(url_for('index'))
    data = get_data(base_url, '/songs/all')

    collection_data = get_user_collections_sid(session['uid'])
    for song in data:
        song['liked'] = True if song['sid'] in collection_data else False

    if request.method == 'POST':
        query_type = request.form['query_type']
        query_value = request.form['query_value']
        if query_type == 'sid':
            res = [get_data(base_url, '/songs/query/sid/' + query_value)]
        elif query_type == 'name':
            res = get_data(base_url, '/songs/query/song_name/' + query_value)
        data = {'dict': res, 'query_type': query_type, 'query_value': query_value}
        return render_template('./songs/query_result.html', data=data)
    return render_template('./songs/songs.html', data=data, username=session['name'])


@app.route('/songs/add_to_collections', methods=['POST'])
def add_to_collections():
    if session['google_id'] is None:
        return redirect(url_for('index'))
    uid = session['uid']
    sid = request.form['sid']
    song_name = request.form['song_name']
    post_data(base_url, '/collections/create', {'uid': uid, 'sid': sid, 'song_name': song_name})
    return redirect(url_for('main'))


@app.route('/songs/remove_from_collections', methods=['POST'])
def remove_from_collections():
    if session['google_id'] is None:
        return redirect(url_for('index'))
    uid = session['uid']
    data = get_data(base_url, '/users/{}/collections'.format(uid))
    for collection in data:
        if str(collection['sid']) == request.form['sid']:
            requests.post(base_url + '/collections/delete/colid/{}'.format(collection['colid']))
            break
    return redirect(url_for('main'))


@app.route('/songs/detail/<sid>', methods=('GET', 'POST'))
def view_songs_detail(sid):
    if session['google_id'] is None:
        return redirect(url_for('index'))
    song_data = get_data(base_url, '/songs/query/sid/' + str(sid))

    comments_data = get_data(base_url, '/comments/query/sid/' + str(sid))
    data = {'song_data': song_data, 'comments': comments_data}

    if request.method == 'POST':
        # 在html里点击submit，会通过POST进入这个if statement，发送评论
        # TODO: change uid
        comment_dict = {'content': request.form['comment'], 'username': session['name'], 'uid': session['uid'],
                        'sid': sid, 'date': str(datetime.now())}

        # 保存评论，并显示这首歌的detail
        res = post_data(base_url, '/comments/create', comment_dict)
        return redirect(url_for('view_songs_detail', sid=sid))
    return render_template('./songs/song_detail.html', data=data)


@app.route('/songs/new_songs', methods=('GET', 'POST'))
def create_songs_webpage():
    if session['google_id'] is None:
        return redirect(url_for('index'))
    if request.method == 'POST':
        # 在html里点击submit，会通过POST进入这个if statement
        songs_name = request.form['song_name']
        artist = request.form['artist']
        release_date = request.form['release_date']

        if not songs_name:
            flash('Song name is invalid.')
        elif not release_date or not validate_date(release_date):
            flash('Release date is invalid.')
        elif not artist:
            flash('Artist is invalid.')
        else:
            res = post_data(base_url, '/songs/create',
                            {'song_name': songs_name, 'artist': artist, 'release_date': release_date})
            # res = SongsDB.create_song({'song_name': songs_name, 'artist': artist, 'release_date': release_date})
            return redirect(url_for('view_songs_detail', sid=res.json()['sid']))
    return render_template('./songs/create_song.html')


@app.route('/songs/delete/<sid>')
def delete_song(sid):
    if session['google_id'] is None:
        return redirect(url_for('index'))
    res = post_data(base_url, '/songs/delete/' + str(sid), '')
    return redirect(url_for('main'))


@app.route('/comments/delete/<cid>')
def delete_comment(cid):
    if session['google_id'] is None:
        return redirect(url_for('index'))
    sid = get_data(base_url, '/comments/query/cid/' + str(cid))['sid']
    res = post_data(base_url, '/comments/delete/cid/' + str(cid), '')
    return redirect(url_for('view_songs_detail', sid=sid))


@app.route('/songs/edit/<sid>', methods=('GET', 'POST'))
def edit_song_detail(sid):
    if session['google_id'] is None:
        return redirect(url_for('index'))
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


@app.route("/logout_google")
def logout():
    if session['google_id'] is None:
        return redirect(url_for('index'))
    session.clear()
    return redirect("/")


@app.route("/protected_area")
def protected_area():
    if session['google_id'] is None:
        return redirect(url_for('index'))
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    credentials = Credentials.from_authorized_user_info({
        "token": session["token"],
        "refresh_token": session["refresh_token"],
        "scopes": session["scopes"],
        "client_id": session["client_id"],
        "client_secret": session["client_secret"],
        "quota_project_id": session["quota_project_id"],
        "expiry": session["expiry"]
    })
    return redirect(url_for('create_user'))


@app.route("/create_user", methods=('GET', 'POST'))
def create_user():
    if session['google_id'] is None:
        return redirect(url_for('index'))
    dic = {}
    dic['username'] = session['name']
    dic['email'] = session['email']
    dic['password'] = session['google_id']
    dic['age'] = 0
    dic['description'] = "This is " + session['name'] + "'s description."
    uid = check_user_exist(session['email'])
    if not uid:
        res = post_data(base_url, '/users/create', dic)
        session['uid'] = res.json()['uid']
    else:
        session['uid'] = uid  # TODO: get uid from res
    return redirect(url_for('main'))

# code for user profile
@app.route("/profile", methods=('GET', 'POST'))
def user_detail():
    if session['google_id'] is None:
        return redirect(url_for('index'))

    def get_song_data(sid):
        song_data = get_data(base_url, '/songs/query/sid/' + str(sid))
        return song_data

    # get user data
    uid = session['uid']
    user_data = get_data(base_url, '/users/query/' + str(uid))
    user_data['uid'] = uid
    user_collections = get_user_collections_sid(uid)
    collection_data = [get_song_data(sid) for sid in user_collections]

    if request.method == 'POST':
        # check username
        dic = {}
        if len(request.form['username']) > 0:
            dic['username'] = request.form['username']
            session['name'] = request.form['username']

        if len(request.form['age']) > 0:
            dic['age'] = request.form['age']

        if len(request.form['description']) > 0:
            dic['description'] = request.form['description']

        if len(dic) > 0:
            res = post_data(base_url, '/users/update/' + str(uid), dic)
            return redirect(url_for('user_detail'))
        else:
            flash('Please enter something.')
        post_data(base_url, '/users/update/' + str(uid), user_data)
        return redirect(url_for('user_detail'))

    return render_template('./users/user_detail.html', username=session['name'], user_data=user_data,
                           collection_data=collection_data)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    app.run(host="0.0.0.0", port=port)
