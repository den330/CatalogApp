import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
	__tablename__ = 'user'
	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=False)
	picture = Column(String(250), nullable=True)
	email = Column(String(250), nullable=False)

	@property
	def serialize(self):
		return {
			'name': self.name,
			'picture': self.picture,
			'email': self.email,
			'id': self.id
		}

class Category(Base):
	__tablename__ = 'category'
	id = Column(Integer, primary_key=True)
	name = Column(String(20), nullable=False)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)

	@property
	def serialize(self):
		return{
			'name': self.name,
			'id': self.id,
			'user_id': self.user_id
		}
		
class CategoryItem(Base):
	__tablename__ = 'categoryItem'
	id = Column(Integer, primary_key=True)
	name = Column(String(80), nullable=False)
	info = Column(String(200), nullable=True)
	category_id = Column(Integer, ForeignKey('category.id'))
	category = relationship(Category)



	@property
	def serialize(self):
		return{
			'name': self.name,
			'info': self.info,
			'id': self.id,
		}


	


engine = create_engine('sqlite:///categoryAppWithUsers.db')
Base.metadata.create_all(engine)
	
