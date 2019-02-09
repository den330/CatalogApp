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
    app.debug = True
    app.run(host='0.0.0.0', port=5000)

