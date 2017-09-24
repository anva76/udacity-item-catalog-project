from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Category, Product

engine = create_engine('sqlite:///catalog.db')

Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)

session = DBSession()

cat_names = ["Photo","Video","Clothes","Kitchen"]

for name in cat_names:
	category = Category(name = name)
	session.add(category)
	session.commit()

photo_products = [ 	["PocketCam","Pocket photo camera"],
					["HDCam","HD  DSLR camera"],
					["WaterCam","Waterproof camera"] ]


category = session.query(Category).filter(Category.name == "Photo").one()
print ("*********************")
print (category)
print ("*********************")
for product in photo_products:
	product = Product(name = product[0],description = product[1], category = category)
	session.add(product)
	session.commit()	
	print (product)
	
