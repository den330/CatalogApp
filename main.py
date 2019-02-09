from flask import Flask, render_template, request, redirect, jsonify, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CategoryItem
# from database_setup import Base, Restaurant, MenuItem

app = Flask(__name__)

engine = create_engine('sqlite:///categoryApp.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()


@app.route("/")
@app.route("/catalogList")
def catalogList():
	cates = session.query(Category).all()
	return render_template('cataList.html', cates=cates)

@app.route("/catalogList/<int:category_id>")
def enterCate(category_id):
	cateItems = session.query(CategoryItem).filter_by(category_id=category_id).all()
	return render_template("cataItems.html", items=cateItems)

@app.route("/catalogList/addNewItem", methods=['GET', 'POST'])
def addNewItem():
	if request.method == 'GET':
		html = "<html><body>"
		html += "<form action='/catalogList/addNewItem' method = 'post'>"
		html += "Item Name: <br>"
		html += "<input type='text', name='Item Name'><br>"
		html += "Item Category: <br>"
		html += "<input type='text', name='Item Category'><br>"
		html += "Item Info: <br>"
		html += "<input type=text, name='Item Info'><br>"
		html += "<input type='submit' value='Submit'>"
		html += "</form>"
		html+= "</body></html>"
		return html
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

	
if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)

