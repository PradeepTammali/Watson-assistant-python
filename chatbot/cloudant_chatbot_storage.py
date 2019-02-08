import time

from cloudant.query import Query


class CloudanChatBot(object):

    def __init__(self, client, db_name):
        """
        Creates a new instance of CloudantChatBot.
        Parameters
        ----------
        client - The instance of cloudant client to connect to
        db_name - The name of the database to use
        """
        self.client = client
        self.db_name = db_name

    def init(self):
        """
        Creates and initializes the database.
        """
        try:
            self.client.connect()
            print('Getting database...')
            if self.db_name not in self.client.all_dbs():
                print('Creating database {}...'.format(self.db_name))
                self.client.create_database(self.db_name)
            else:
                print('Database {} exists.'.format(self.db_name))
                pass
            # see if the by_popularity design doc exists, if not then create it
            db = self.client[self.db_name]
            query = Query(db, selector={ '_id': '_design/by_popularity' })
            result = query()['docs']
            if result is None or len(result) <= 0:
                design_doc = {
                    '_id': '_design/by_popularity',
                    'views': {
                        'ingredients': {
                            'map': 'function (doc) {\n  if (doc.type && doc.type==\'userIngredientRequest\') {\n    emit(doc.ingredient_name, 1);\n  }\n}',
                            'reduce': '_sum'
                        },
                        'cuisines': {
                            'map': 'function (doc) {\n  if (doc.type && doc.type==\'userCuisineRequest\') {\n    emit(doc.cuisine_name, 1);\n  }\n}',
                            'reduce': '_sum'
                        },
                        'recipes': {
                            'map': 'function (doc) {\n  if (doc.type && doc.type==\'userRecipeRequest\') {\n    emit(doc.recipe_title, 1);\n  }\n}',
                            'reduce': '_sum'
                        }
                    },
                    'language': 'javascript'
                }
                db.create_document(design_doc)
            # see if the by_day_of_week design doc exists, if not then create it
            query = Query(db, selector={ '_id': '_design/by_day_of_week' })
            result = query()['docs']
            if result is None or len(result) <= 0:
                design_doc = {
                    '_id': '_design/by_day_of_week',
                    'views': {
                        'ingredients': {
                            'map': 'function (doc) {\n  if (doc.type && doc.type==\'userIngredientRequest\') {\n    var weekdays = [\'Sunday\',\'Monday\',\'Tuesday\',\'Wednesday\',\'Thursday\',\'Friday\',\'Saturday\'];\n    emit(weekdays[new Date(doc.date).getDay()], 1);\n  }\n}',
                            'reduce': '_sum'
                        },
                        'cuisines': {
                            'map': 'function (doc) {\n  if (doc.type && doc.type==\'userCuisineRequest\') {\n    var weekdays = [\'Sunday\',\'Monday\',\'Tuesday\',\'Wednesday\',\'Thursday\',\'Friday\',\'Saturday\'];\n    emit(weekdays[new Date(doc.date).getDay()], 1);\n  }\n}',
                            'reduce': '_sum'
                        },
                        'recipes': {
                            'map': 'function (doc) {\n  if (doc.type && doc.type==\'userRecipeRequest\') {\n    var weekdays = [\'Sunday\',\'Monday\',\'Tuesday\',\'Wednesday\',\'Thursday\',\'Friday\',\'Saturday\'];\n    emit(weekdays[new Date(doc.date).getDay()], 1);\n  }\n}',
                            'reduce': '_sum'
                        }
                    },
                    'language': 'javascript'
                }
                db.create_document(design_doc)
        finally:
            self.client.disconnect()

    # User

    def add_user(self, user_id):
        """
        Adds a new user to Cloudant if a user with the specified ID does not already exist.
        Parameters
        ----------
        user_id - The ID of the user (typically the ID returned from Slack)
        """
        user_doc = {
            'type': 'user',
            'name': user_id
        }
        return self.add_doc_if_not_exists(user_doc, 'name')

    
    # Cloudant Helper Methods

    def find_doc(self, doc_type, property_name, property_value):
        """
        Finds a doc based on the specified doc_type, property_name, and property_value.
        Parameters
        ----------
        doc_type - The type value of the document stored in Cloudant
        property_name - The property name to search for
        property_value - The value that should match for the specified property name
        """
        try:
            self.client.connect()
            db = self.client[self.db_name]
            selector = {
                '_id': {'$gt': 0},
                'type': doc_type,
                property_name: property_value
            }
            query = Query(db, selector=selector)
            for doc in query()['docs']:
                return doc
            return None
        finally:
            self.client.disconnect()
            
    def add_doc_if_not_exists(self, doc, unique_property_name):
        """
        Adds a new doc to Cloudant if a doc with the same value for unique_property_name does not exist.
        Parameters
        ----------
        doc - The document to add
        unique_property_name - The name of the property used to search for an existing document (the value will be extracted from the doc provided)
        """
        doc_type = doc['type']
        property_value = doc[unique_property_name]
        existing_doc = self.find_doc(doc_type, unique_property_name, property_value)
        if existing_doc is not None:
            print('Returning {} doc where {}={}'.format(doc_type, unique_property_name, property_value))
            return existing_doc
        else:
            print('Creating {} doc where {}={}'.format(doc_type, unique_property_name, property_value))
            try:
                self.client.connect()
                db = self.client[self.db_name]
                return db.create_document(doc)
            finally:
                self.client.disconnect()

