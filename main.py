from flask import Flask, render_template, request, redirect, jsonify, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# from database_setup import Base, Restaurant, MenuItem

app = Flask(__name__)


@app.route("/")
@app.route("/catalogList")
def catalogList():
	html = "<html><body>"
	html += "<a href='/catalogList/addNewItem'>Add Item</a>"
	html += "</body></html>"
	return html

@app.route("/catalogList/addNewItem")
def addNewItem():
	html = "<html><body>"
	html += "<form>"
	html += "Item Name: <br>"
	html += "<input type='text', name='Item Name'><br>"
	html += "Item Category: <br>"
	html += "<input type='text', name='Item Category'><br>"
	html += "Item Info: <br>"
	html += "<input type=text, name='Item Info'><br>"
	html += "<input type='submit' value='Submit'>"
	html+= "</body></html>"
	return html
	
if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)

