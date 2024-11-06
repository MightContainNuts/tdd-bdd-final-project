# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory
from unittest.mock import patch

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)


    def test_read_a_product(self):
        """It should Read a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Fetch it back
        found_product = Product.find(product.id)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)

    def test_update_a_product(self):
        """It should Update a Product"""
        # Create product instance
        product = ProductFactory()
        product.create()
        self.assertIsNotNone(product.id)

        # Modify product description and save it
        original_description = product.description
        product.description = "testing"
        original_id = product.id

        product.update()
        self.assertEqual(product.id, original_id)  # Ensure ID hasn't changed
        self.assertEqual(product.description, "testing")  # Ensure description updated

        # Fetch updated product and verify changes
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(products[0].description, "testing")

    def test_update_a_product_without_id(self):
            """It should raise DataValidationError if product has no id"""
            # Create product instance
            product = ProductFactory()
            product.id = None  # Set product ID to None (invalid)
            
            # Ensure DataValidationError is raised when calling update with None ID
            with self.assertRaises(DataValidationError) as context:
                product.update()
            
            # Check that the exception message is as expected
            self.assertEqual(str(context.exception), "Update called with empty ID field")

    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        # delete the product and make sure it isn't in the database
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should List all Products in the database"""
        products = Product.all()
        self.assertEqual(products, [])
        # Create 5 Products
        for _ in range(5):
            product = ProductFactory()
            product.create()
        # See if we get back 5 products
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_by_name(self):
        """It should Find a Product by Name"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        name = products[0].name
        count = len([product for product in products if product.name == name])
        found = Product.find_by_name(name)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.name, name)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        available = products[0].available
        count = len([product for product in products if product.available == available])
        found = Product.find_by_availability(available)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.available, available)

    def test_find_by_category(self):
        """It should Find Products by Category"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        category = products[0].category
        count = len([product for product in products if product.category == category])
        found = Product.find_by_category(category)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.category, category)

    def test_deserialize_invalid_available(self):
        """Test that DataValidationError is raised if 'available' is not a boolean"""
        
        invalid_data = {
            "name": "Test Product",
            "description": "A product for testing",
            "price": "19.99",  # Assuming price is a string but will be converted to Decimal
            "available": "yes"  # This should raise an error because it's not a boolean
        }

        product = Product()

        with self.assertRaises(DataValidationError) as context:
            product.deserialize(invalid_data)
        
        self.assertEqual(
            str(context.exception),
            "Invalid type for boolean [available]: <class 'str'>"
        )

    def test_deserialize_missing_field(self):
        """Test that DataValidationError is raised if a required field is missing"""
        
        missing_field_data = {
            "name": "Test Product",
            "description": "A product for testing",
            "price": "19.99",
            # Missing 'available' field
        }

        product = Product()

        with self.assertRaises(DataValidationError) as context:
            product.deserialize(missing_field_data)
        
        self.assertEqual(
            str(context.exception),
            "Invalid product: missing available"
        )

    def test_deserialize_invalid_category(self):
        """Test that DataValidationError is raised if 'category' does not match a valid enum value"""
        
        invalid_category_data = {
            "name": "Test Product",
            "description": "A product for testing",
            "price": "19.99",
            "available": True,
            "category": "non_existent_category"  # Invalid category
        }

        product = Product()

        with self.assertRaises(DataValidationError) as context:
            product.deserialize(invalid_category_data)
        
        self.assertEqual(
            str(context.exception),
            "Invalid attribute: non_existent_category"
        )

    def test_deserialize_invalid_price(self):
        """Test that DataValidationError is raised if price is not a valid Decimal"""
    
        invalid_price_data = {
            "name": "Test Product",
            "description": "A product for testing",
            "price": "not_a_number",  # Invalid price
            "available": True,
            "category": "ValidCategory"  # Assume this is a valid category
        }

        product = Product()

        with self.assertRaises(DataValidationError) as context:
            product.deserialize(invalid_price_data)
        
        self.assertEqual(
            str(context.exception),
            "Invalid price: not_a_number"
        )

    def test_deserialize_type_error(self):
        """Test that DataValidationError is raised if there's a TypeError during deserialization"""
        
        # Invalid data that will trigger a TypeError
        invalid_data = {
            "name": "Test Product",
            "description": "A product for testing",
            "price": "19.99",  # Valid price
            "available": True,  # Valid available
            # Missing or malformed category data that could trigger a TypeError
            "category": None  # This could raise a TypeError when attempting to use getattr
        }

        product = Product()

        with self.assertRaises(DataValidationError) as context:
            product.deserialize(invalid_data)
        
        # Adjust the expected exception message to match the one raised by getattr error
        self.assertEqual(
            str(context.exception),
            "Invalid product: body of request contained bad or no data getattr(): attribute name must be string"
        )

    @patch('service.models.logger')  # Adjust the logger path as needed
    def test_find_by_price_logging(self, mock_logger):
        """Test that logger.info is called correctly when calling find_by_price"""
        
        # Test data
        price = Decimal('19.99')

        # Mock the return value of query.filter (you can adjust based on your actual ORM)
        mock_query = unittest.mock.MagicMock()
        Product.query.filter = mock_query

        # Call the method we're testing
        Product.find_by_price(price)

        # Check that logger.info was called with the correct message
        mock_logger.info.assert_called_with("Processing price query for %s ...", price)

    @patch('service.models.logger')
    def test_find_by_price_logging_with_string_price(self, mock_logger):
        """Test that logger.info is called correctly when price is passed as a string"""

        # Test data as a string
        price = '19.99'

        # Mock the return value of query.filter (you can adjust based on your actual ORM)
        mock_query = unittest.mock.MagicMock()
        Product.query.filter = mock_query

        # Call the method we're testing
        Product.find_by_price(price)

        # Check that logger.info was called with the correct message (logging the string, not Decimal)
        mock_logger.info.assert_called_with("Processing price query for %s ...", price)