#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module contains the main Flask web application and
some auxiliary functions
"""
import json
import os
import random
import string

from flask import Flask, render_template, request, redirect, url_for, flash
from flask import session as login_session
from flask import jsonify
from werkzeug.utils import secure_filename

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Category, Product

from google_auth import make_json_response, generate_state_token
from google_auth import get_credentials, check_credentials
from google_auth import get_user_name_and_email, revoke_access

# Create a Flask application instance
app = Flask(__name__)
app.secret_key = 'ABCDEFDGDFGFDHB90'

# Configure the upload folder
UPLOAD_FOLDER = app.root_path+'/static/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Obtain the client id from "client_secrets.json"
CLIENT_SEC_FILE = 'client_secrets.json'
CLIENT_ID = json.loads(open(CLIENT_SEC_FILE, 'r').read())['web']['client_id']

# Connect to the database
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# ============================================================================
# Some helper functions
# Generate a unique file name for image upload
def unique_file_name(file_name):
    ext = file_name.rsplit('.', 1)[1]
    name = ''.join(random.choice(string.ascii_lowercase + string.digits)
                   for x in range(12))

    return name+"."+ext


# Upload a picture file with a unique name
def upload_unique(picfile):
    filename = secure_filename(picfile.filename)
    filename = unique_file_name(filename)
    picfile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return filename


# Delete an uploaded file
def delete_uploaded_file(file_name):
    full_name = UPLOAD_FOLDER+'/'+file_name
    if os.path.isfile(full_name):
        os.remove(full_name)


# Check if the picture file name is valid
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


# Clear auth data from the current login session
def clear_login_session():
    del login_session['access_token']
    del login_session['gplus_id']
    del login_session['username']
    return


# Check if a user is logged in
def user_logged_in():
    return ("username" in login_session)


# Check the current user and provide the user name
def check_current_user():
    if user_logged_in():
        return login_session["username"]
    else:
        return None


# Check if a category is empty
def category_not_empty(id):
    first_found = session.query(Product).filter(Product.category_id == id) \
        .first()
    return (first_found is not None)


# Validate a new category
def validate_category(form, current_id=None):
    # Check if the name is empty
    name = form['name'].strip()
    if name == "":
        return "Category name is empty"

    # Check if a category with the same name already exists
    if current_id is not None:
        cat = session.query(Category).filter(Category.name == name) \
                        .filter(Category.id != current_id).first()
    else:
        cat = session.query(Category) \
                        .filter(Category.name == name).first()

    if cat is not None:
        return "Category with the name '{0}' already exists".format(name)

    return "OK"


# Validate a new product
def validate_product(form):
    name = form['name'].strip()
    if name == "":
        return "Product name is empty"

    category = form['category']
    if category == "":
        return "Please select a category"

    return "OK"


# Log information to console for debug purposes
def log_to_console(messages):
    print ("\n**********************************")
    for message in messages:
        print (message)
    print ("**********************************")
    return


# ===========================================================================
# Google authentication functions
# Get access via Google plus account
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Check the state token
    if request.args.get('state') != login_session['state']:
        return make_json_response('Invalid state parameter.', 401)

    # Get authorization code
    code = request.data

    # Get Google credentials
    credentials = get_credentials(code, CLIENT_SEC_FILE)
    if credentials is None:
        return make_json_response('Failed to upgrade the authorization code.',
                                  401)

    # Check if the credentials are valid and ok
    res = check_credentials(credentials, CLIENT_ID)
    if len(res) > 0:
        return make_json_response(res.message, res.code)

    # Check if the authenticated user is already connected
    gplus_id = credentials.id_token['sub']
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        return make_json_response('Current user is already connected.', 200)

    # Store the access token in the session for later use.
    name, email = get_user_name_and_email(credentials)
    # Check if the actual user name is present
    # If not, use the email address instead
    if len(name.strip()) == 0 or name is None:
        login_session['username'] = email
    else:
        login_session['username'] = name

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    flash("You are now logged in as %s" % login_session['username'], "success")

    msgs = [("Authorized successfully."),
            ("Access token: {0}".format(login_session['access_token'])),
            ("User name: {0}".format(login_session['username']))]
    log_to_console(msgs)

    return make_json_response('Success', 200)


# Revoke Google plus access
@app.route('/logout')
def logout():
    access_token = login_session.get('access_token')
    if access_token is None:
        print ("Current user is not connected")

        flash("You are not logged in", "warning")
        return redirect(url_for('show_home_page'))

    msgs = [("Disconnecting..."),
            ("Access token: {0}".format(login_session['access_token'])),
            ("User name: {0}".format(login_session['username']))]
    log_to_console(msgs)

    if not revoke_access(access_token):
        print ("Failed to revoke token for given user")

    clear_login_session()
    flash("Logged out", "success")

    return redirect(url_for('show_home_page'))


# ============================================================================
# Flask routing
# Login page
@app.route('/login')
def login():

    if user_logged_in():
        flash("Already logged in", "success")
        return redirect(url_for('show_home_page'))

    state = generate_state_token()
    login_session['state'] = state
    return render_template('login.html', STATE=state, login_page=True)


# Show the main page
@app.route("/")
@app.route("/catalog/")
def show_home_page():
    categories = session.query(Category).all()
    products = session.query(Product).order_by(desc(Product.last_updated)). \
        limit(10)

    return render_template('home_page.html', categories=categories,
                           products=products)


# Show a specific category
@app.route("/catalog/category/<int:id>/")
def show_category(id):
    category = session.query(Category).filter(Category.id == id).first()
    # Show Eror 404 if a category is not found
    if not category:
        return render_template('error404.html', title="Category"), 404

    products = session.query(Product).filter(Product.category_id == id). \
        order_by(desc(Product.last_updated)).all()

    return render_template('category.html', category=category,
                           products=products)


# Create a new category
@app.route("/catalog/category/new/", methods=['GET', 'POST'])
def new_category():

    if not user_logged_in():
        flash("Login required for this operation", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Validate the form data
        res = validate_category(request.form)
        if res != "OK":
            flash(res, "warning")
            return redirect(url_for('new_category'))

        # Save the new category
        category_db = Category(name=request.form['name'].strip())
        session.add(category_db)
        session.commit()
        flash("Category successfully created", "success")
        return redirect(url_for('show_home_page'))
    else:
        return render_template('new_category.html')


# Edit a specific category
@app.route("/catalog/category/<int:id>/edit/", methods=['GET', 'POST'])
def edit_category(id):

    if not user_logged_in():
        flash("Login required for this operation", "warning")
        return redirect(url_for('login'))

    category = session.query(Category).filter(Category.id == id).first()
    # Show Eror 404 if a category is not found
    if not category:
        return render_template('error404.html', title="Category"), 404

    if request.method == 'POST':
        # Validate the form data
        res = validate_category(request.form, id)
        if res != "OK":
            flash(res, "warning")
            return redirect(url_for('edit_category', id=id))

        # Save the updated category
        category.name = request.form['name'].strip()
        session.add(category)
        session.commit()
        flash("Category updated", "success")
        return redirect(url_for('show_home_page'))
    else:

        return render_template('edit_category.html', category=category)


# Delete a specific category
@app.route("/catalog/category/<int:id>/delete/", methods=['GET', 'POST'])
def delete_category(id):

    if not user_logged_in():
        flash("Login required for this operation", "warning")
        return redirect(url_for('login'))

    category = session.query(Category).filter(Category.id == id).first()
    # Show Eror 404 if a category is not found
    if not category:
        return render_template('error404.html', title="Category"), 404

    if request.method == 'POST':
        if category_not_empty(category.id):
            flash("Category not empty", "danger")
            return redirect(url_for('show_home_page'))

        session.delete(category)
        session.commit()
        flash("Category deleted", "success")
        return redirect(url_for('show_home_page'))
    else:
        return render_template('delete_category.html', category=category)

    return 0


# Show a specific product
@app.route("/catalog/product/<int:id>/")
def show_product(id):
    product = session.query(Product).filter(Product.id == id).first()
    # Show Eror 404 if a product is not found
    if not product:
        return render_template('error404.html', title="Product"), 404

    return render_template('product.html', product=product)


# Create a new product within a specific category
@app.route("/catalog/category/<int:cat_id>/product/new/",
           methods=['GET', 'POST'])
def new_product(cat_id):

    if not user_logged_in():
        flash("Login required for this operation", "warning")
        return redirect(url_for('login'))

    category = session.query(Category).filter(Category.id == cat_id).first()
    # Show Eror 404 if a category is not found
    if not category:
        return render_template('error404.html', title="Category"), 404

    if request.method == 'POST':
        # Validate the form data
        res = validate_product(request.form)
        if res != "OK":
            flash(res, "warning")
            return redirect(url_for('new_product', cat_id=cat_id))

        # Upload the product picture
        filename = ""
        picfile = request.files.get('picfile')
        if picfile and allowed_file(picfile.filename):
            filename = upload_unique(picfile)

        # Save the new product
        product = Product(name=request.form['name'],
                          description=request.form['description'],
                          picture_file=filename,
                          category_id=cat_id)

        session.add(product)
        session.commit()
        flash("Product successfully created", "success")
        return redirect(url_for('show_category', id=cat_id))
    else:

        categories = session.query(Category).all()
        # Redirect urls for submission and cancellaton
        params = dict(submit_url=url_for('new_product', cat_id=category.id),
                      cancel_url=url_for('show_category', id=category.id))

        return render_template('new_product.html', category=category,
                               categories=categories, params=params)


# Create a new product
@app.route("/catalog/product/new/", methods=['GET', 'POST'])
def new_product_alt():

    if not user_logged_in():
        flash("Login required for this operation", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Validate the form data
        res = validate_product(request.form)
        if res != "OK":
            flash(res, "warning")
            return redirect(url_for('new_product_alt'))

        # Upload the product picture
        filename = ""
        picfile = request.files.get('picfile')
        if picfile and allowed_file(picfile.filename):
            filename = upload_unique(picfile)

        # Save the new product
        product = Product(name=request.form['name'],
                          description=request.form['description'],
                          category_id=int(request.form['category']),
                          picture_file=filename)

        session.add(product)
        session.commit()
        flash("Product successfully created", "success")
        return redirect(url_for('show_category', id=product.category_id))

    else:

        categories = session.query(Category).all()
        # Redirect urls for submission and cancellation
        params = dict(submit_url=url_for('new_product_alt'),
                      cancel_url=url_for('show_home_page'))

        return render_template('new_product.html', categories=categories,
                               params=params)


# Edit a specific product
@app.route("/catalog/product/<int:id>/edit/", methods=['GET', 'POST'])
def edit_product(id):

    if not user_logged_in():
        flash("Login required for this operation", "warning")
        return redirect(url_for('login'))

    product = session.query(Product).filter_by(id=id).first()
    # Show Eror 404 if a product is not found
    if not product:
        return render_template('error404.html', title="Product"), 404

    if request.method == 'POST':
        # Validate the form data
        res = validate_product(request.form)
        if res != "OK":
            flash(res, "warning")
            return redirect(url_for('edit_product', id=id))

        old_pic_file = product.picture_file
        # Upload the product picture
        uploaded = False
        picfile = request.files.get('picfile')
        if picfile and allowed_file(picfile.filename):
            product.picture_file = upload_unique(picfile)
            uploaded = True

        # Save the updated product
        product.name = request.form['name']
        product.description = request.form['description']
        product.category_id = int(request.form['category'])
        session.add(product)
        session.commit()

        # delete the old picture file
        if uploaded:
            delete_uploaded_file(old_pic_file)
        flash("Product updated", "success")
        return redirect(url_for('show_product', id=product.id))
    else:

        categories = session.query(Category).all()
        return render_template('edit_product.html', product=product,
                               categories=categories)


# Delete a specific product
@app.route("/catalog/product/<int:id>/delete/", methods=['GET', 'POST'])
def delete_product(id):

    if not user_logged_in():
        flash("Login required for this operation", "warning")
        return redirect(url_for('login'))

    product = session.query(Product).filter(Product.id == id).first()
    # Show Eror 404 if a product is not found
    if not product:
        return render_template('error404.html', title="Product"), 404

    if request.method == 'POST':
        category_id = product.category_id
        pic_file = product.picture_file
        # delete the selected product
        session.delete(product)
        session.commit()
        # delete the related picture file
        delete_uploaded_file(pic_file)

        flash("Product deleted", "success")
        return redirect(url_for('show_category', id=category_id))
    else:
        return render_template('delete_product.html', product=product)


# Error 404 handler
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error404.html', title="Page"), 404


# =======================================================================
# JSON
# Provide the whole catalog
@app.route("/catalog.json/")
def get_catalog_json():
    result = []
    categories = session.query(Category).all()
    for category in categories:
        products = session.query(Product).filter_by(category_id=category.id)
        product_list = [p.serialize for p in products]

        result.append(dict(id=category.id, name=category.name,
                      products=product_list))

    return jsonify(Categories=result)


# Get a specific category
@app.route("/catalog/category.json/<int:id>/")
def get_category_json(id):
    result = []
    category = session.query(Category).filter_by(id=id).first()
    if not category:
        return make_json_response("Category not found", 404)

    products = session.query(Product).filter_by(category_id=category.id)
    product_list = [p.serialize for p in products]

    result.append(dict(id=category.id, name=category.name,
                  products=product_list))

    return jsonify(Category=result)


# Get a specific product
@app.route("/catalog/product.json/<int:id>/")
def get_product_json(id):
    product = session.query(Product).filter_by(id=id).first()
    if not product:
        return make_json_response("Product not found", 404)

    result = [product.serialize, ]
    return jsonify(Product=result)


# =======================================================================
# Run the application
if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
