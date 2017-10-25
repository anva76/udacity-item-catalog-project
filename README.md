# Udacity Item Catalog Project
This is a website application for the Udacity item catalog project.

## Usage notes
The application implements an online product catalog. The product catalog has
categories so that each product can be attributed to a specific category.

If a user logs in via Google Plus, categories and products can be created,
updated or deleted. If necessary, a product picture can be uploaded for each
product. If no picture is provided, a place holder image will be displayed.

Apart from the html pages, the application also implements JSON end points:
```
/catalog.json
/catalog/category.json/<int:id>
/catalog/product.json/<int:id>
```

## Installation notes
In order to run this application successfully, you need to have `VirtualBox` and `Vagrant` installed first.
Please refer to the relevant documentation for your operating system for more details.

Then install a predefined `Ubutu Server` virtual machine by cloning or downloading this 
GitHub [repository](https://github.com/udacity/fullstack-nanodegree-vm). 
Put the files into a chosen working directory.
From your terminal, inside the `vagrant` subdirectory, run the command `vagrant up`.

Download or clone the files from [this project](https://github.com/anva76/udacity-item-catalog-project) 
into a new subfolder inside the `vagrant` directory.

Then log into the virtual machine by running `vagrant ssh` inside the `vagrant` directory.

Finally, run the main file:
```
* cd /vagrant
* cd <your subfolder>
* python3 catalog_app.py
```
In your browser, open the following address:
```
http://localhost:8000
```
