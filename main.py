from flask import Flask, render_template, request, redirect, jsonify, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CategoryItem
# from database_setup import Base, Restaurant, MenuItem

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']

app = Flask(__name__)

engine = create_engine('sqlite:///categoryApp.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()


@app.route('/gconnect', methods=['POST'])
def gconnect():
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	code = request.data
	try:
		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])
	if result.get('error') is not None:
		response = make_response(json.dumps(result.get('error')), 500)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Verify that the access token is used for the intended user.
	gplus_id = credentials.id_token['sub']
	if result['user_id'] != gplus_id:
		response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Verify that the access token is valid for this app.
	if result['issued_to'] != CLIENT_ID:
		response = make_response(
		json.dumps("Token's client ID does not match app's."), 401)
		print "Token's client ID does not match app's."
		response.headers['Content-Type'] = 'application/json'
		return response

	stored_access_token = login_session.get('access_token')
	stored_gplus_id = login_session.get('gplus_id')
	if stored_access_token is not None and gplus_id == stored_gplus_id:
		response = make_response(json.dumps('Current user is already connected.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Store the access token in the session for later use.
	login_session['access_token'] = credentials.access_token
	login_session['gplus_id'] = gplus_id

	# Get user info
	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	answer = requests.get(userinfo_url, params=params)

	data = answer.json()

	login_session['username'] = data['name']
	login_session['picture'] = data['picture']
	login_session['email'] = data['email']

	output = ''
	output += '<h1>Welcome, '
	output += login_session['username']
	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
	flash("you are now logged in as %s" % login_session['username'])
	print "done!"
	return output




@app.route('/login')
def showLogin():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
	login_session['state'] = state
	return render_template('login.html', STATE=state)


@app.route("/")
@app.route("/catalogList")
def catalogList():
	cates = session.query(Category).all()
	return render_template('cataList.html', cates=cates)

@app.route("/catalogList/<int:category_id>")
def enterCate(category_id):
	cateItems = session.query(CategoryItem).filter_by(category_id=category_id).all()
	return render_template("cataItems.html", items=cateItems, category_id=category_id)

@app.route("/catalogList/<int:category_id>/<int:item_id>")
def enterItem(category_id, item_id):
	item = session.query(CategoryItem).filter_by(id=item_id)[0]
	category = session.query(Category).filter_by(id=category_id)[0]
	return render_template("itemDetails.html", item=item, category=category)

@app.route("/catalogList/addNewItem", methods=['GET', 'POST'])
def addNewItem():
	if request.method == 'GET':
		return render_template("addNewItem.html")
	else:
		categoryName = request.form['Item Category']
		categoryInStoreList = session.query(Category).filter_by(name=categoryName).all()
		if len(categoryInStoreList) == 0:
			newCate = Category(name=categoryName)
			session.add(newCate)
			session.commit()
			newItem = CategoryItem(name=request.form['Item Name'], 
			info=request.form['Item Info'], category_id= newCate.id)
		else:
			newItem = CategoryItem(name=request.form['Item Name'], 
			info=request.form['Item Info'], category_id= categoryInStoreList[0].id)
		session.add(newItem)
		session.commit()
		return redirect(url_for('catalogList'))

@app.route("/catalogList/deleteItem/<int:item_id>")
def deleteItem(item_id):
	item = session.query(CategoryItem).filter_by(id=item_id)[0]
	category_id = item.category_id
	session.delete(item)
	itemListForThisCate = session.query(CategoryItem).filter_by(category_id=category_id).all()
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
	item = session.query(CategoryItem).filter_by(id=item_id)[0]
	if request.method == "GET":
		category = session.query(Category).filter_by(id=item.category_id)[0]
		return render_template("editItem.html", item=item, category=category)
	else:
		item.name = request.form["Item Name"]
		item.info = request.form["Item Info"]
		categoryName = request.form["Item Category"]
		categoryInStoreList = session.query(Category).filter_by(name=categoryName).all()
		if len(categoryInStoreList) == 0:
			newCate = Category(name=categoryName)
			session.add(newCate)
			session.commit()
			item.category_id = newCate.id
		else:
			item.category_id = categoryInStoreList[0].id
		session.add(item)
		session.commit()
		return redirect(url_for('enterCate', category_id=item.category_id))



	
if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host='0.0.0.0', port=5000)


