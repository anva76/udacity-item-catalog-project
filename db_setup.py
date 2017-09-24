#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the database structure of the product catalog
"""
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import datetime
import sys

Base = declarative_base()


def cur_time():
    return datetime.datetime.now()


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    last_updated = Column(DateTime, default=cur_time, onupdate=cur_time)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "Category(%r, %r)" % (self.id, self.name)

    @property
    def serialize(self):
        return {"id": self.id, "name": self.name}


class Product(Base):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(250))
    last_updated = Column(DateTime, default=cur_time, onupdate=cur_time)
    picture_file = Column(String(50))

    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)

    def __init__(self, name, description, category_id, picture_file=""):
        self.name = name
        self.description = description
        self.category_id = category_id
        self.picture_file = picture_file

    def __repr__(self):
        return ("Product({0}, {1}, {2}, {3})".format(
                self.id, self.name, self.description, self.category,
                self.picture_file))

    @property
    def serialize(self):
        return {"id": self.id, "name": self.name,
                "description": self.description,
                "picture": self.picture_file,
                "category": self.category.name}

engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)
