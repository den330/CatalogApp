from flask import Flask, render_template, request, \
    redirect, jsonify, url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CategoryItem, User
# from database_setup import Base, Restaurant, MenuItem

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())[
    'web']['client_id']

app = Flask(__name__)

engine = create_engine('sqlite:///categoryAppWithUsers.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type='\
        'fb_exchange_token&client_id='\
        '%s&client_secret=%s&fb_exchange_token=%s' % (
            app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
		Due to the formatting for the result from the server token exchange we have to
		split the token first on commas and select the first index which gives us the key : value
		for the server access token then we split it on colons to pull out the actual token value
		and replace the remaining quotes with nothing so that it can be used directly in the graph
		api calls
	'''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?a' \
        'ccess_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?'\
        'access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius:' \
        ' 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (
        facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]

    del login_session['facebook_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['user_id']
    del login_session['provider']
    return redirect('/catalogList')


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route("/")
@app.route("/catalogList")
def catalogList():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    if 'username' not in login_session:
        return redirect('/login')
    cates = session.query(Category).all()
    if len(cates) != 0:
        cates = session.query(Category).filter_by(
            user_id=login_session['user_id']).all()
    return render_template('cataList.html', cates=cates)


@app.route("/catalogList/<int:category_id>")
def enterCate(category_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    if 'username' not in login_session:
        return redirect('/login')
    cateItems = session.query(CategoryItem).filter_by(
        category_id=category_id).all()
    return render_template("cataItems.html",
                           items=cateItems, category_id=category_id)


@app.route("/catalogList/<int:category_id>/<int:item_id>")
def enterItem(category_id, item_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(CategoryItem).filter_by(id=item_id)[0]
    category = session.query(Category).filter_by(id=category_id)[0]
    return render_template("itemDetails.html", item=item, category=category)


@app.route("/catalogList/addNewItem", methods=['GET', 'POST'])
def addNewItem():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'GET':
        return render_template("addNewItem.html")
    else:
        categoryName = request.form['Item Category']
        # categoryInStoreList = session.query(Category).filter_by(name=categoryName).all()
        categoryInStoreList = session.query(Category).filter_by(
            name=categoryName, user_id=login_session['user_id']).all()
        if len(categoryInStoreList) == 0:
            newCate = Category(name=categoryName,
                               user_id=login_session['user_id'])
            session.add(newCate)
            session.commit()
            newItem = CategoryItem(name=request.form['Item Name'],
                                   info=request.form['Item Info'],
                                   category_id=newCate.id)
        else:
            newItem = CategoryItem(name=request.form['Item Name'],
                                   info=request.form['Item Info'],
                                   category_id=categoryInStoreList[0].id)
        session.add(newItem)
        session.commit()
        return redirect(url_for('catalogList'))


@app.route("/catalogList/deleteItem/<int:item_id>")
def deleteItem(item_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(CategoryItem).filter_by(id=item_id)[0]
    category_id = item.category_id
    session.delete(item)
    itemListForThisCate = session.query(
        CategoryItem).filter_by(category_id=category_id).all()
    if len(itemListForThisCate) == 0:
        thisCate = session.query(Category).filter_by(id=category_id)[0]
        session.delete(thisCate)
        session.commit()
        return redirect(url_for('catalogList'))
    else:
        session.commit()
        return redirect(url_for('enterCate', category_id=category_id))


@app.route("/catalogList/editItem/<int:item_id>", methods=['GET', 'POST'])
def editItem(item_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(CategoryItem).filter_by(id=item_id)[0]
    if request.method == "GET":
        category = session.query(Category).filter_by(id=item.category_id)[0]
        return render_template("editItem.html", item=item, category=category)
    else:
        item.name = request.form["Item Name"]
        item.info = request.form["Item Info"]
        categoryName = request.form["Item Category"]
        categoryInStoreList = session.query(
            Category).filter_by(name=categoryName).all()
        if len(categoryInStoreList) == 0:
            newCate = Category(name=categoryName,
                               user_id=login_session['user_id'])
            session.add(newCate)
            session.commit()
            item.category_id = newCate.id
        else:
            item.category_id = categoryInStoreList[0].id
        session.add(item)
        session.commit()
        return redirect(url_for('enterCate', category_id=item.category_id))


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    threaded = False
    app.run(host='0.0.0.0', port=5000)
