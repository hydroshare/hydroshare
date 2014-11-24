# /api/v1/dataresource/
# auth

# url(r'^new/', views.create_dataset),
# url(r'^(?P<slug>[a-z0-9\-/]+)/schema/', views.schema),
# url(r'^(?P<slug>[a-z0-9\-/]+)/query/(?P<x1>[0-9\-.]+),(?P<y1>[0-9\-.]+),(?P<x2>[0-9\-.]+),(?P<y2>[0-9\-.]+)/',
#    views.query),
# url(r'^(?P<slug>[a-z0-9\-/]+)/query/', views.query),
# url(r'^(?P<slug>[a-z0-9\-/]+)/add_column/', views.add_column),
# url(r'^(?P<slug>[a-z0-9\-/]+)/(?P<ogc_fid>[0-9]+)/', views.CRUDView.as_view()),
# url(r'^(?P<slug>[a-z0-9\-/]+)/(?P<ogc_fid_start>[0-9]+):(?P<ogc_fid_end>[0-9]+)/', views.CRUDView.as_view()),
# url(r'^(?P<slug>[a-z0-9\-/]+)/(?P<ogc_fid_start>[0-9]+),(?P<limit>[0-9]+)/', views.CRUDView.as_view()),
# url(r'^(?P<slug>[a-z0-9\-/]+)/fork/', views.derive_dataset),
# url(r'^(?P<slug>[a-z0-9\-/]+)/fork_geometry/', views.create_dataset_with_parent_geometry),
# url(r'^(?P<slug>[a-z0-9\-/]+)/', views.CRUDView.as_view()),
import json

from unittest import TestCase
import requests

AK = '1c6a41ed6a5bc199d10e9594090b17cb83213dbb' # API_KEY
host = 'http://localhost:8000/'

# @skip
class TestRestAPI(TestCase):
    def assertSuccess(self, response, msg='response status code: {code}\n{response}'):
        msg = msg.format(code=response.status_code, response=response.text)
        self.assertGreaterEqual(response.status_code, 200, msg=msg)
        self.assertLess(response.status_code, 300, msg=msg)

    def test_create_dataset(self):
        blank_dataset = requests.get(
            host + 'ga_resources/new/',
            headers={
                "content-type" : 'application/json'
            },
            params={
                "api_key" : AK,
                "title" : 'test create empty dataset'
            }
        )

        blank_dataset_with_columns = requests.get(host + 'ga_resources/new/', params={
          "api_key": AK,
          "title": 'test create empty dataset',
          'srid': 4326,
          'columns_definitions': json.dumps({
              "i": "real",
              "j": "integer",
              "name": "text"
          })
        })

        self.assertSuccess(blank_dataset_with_columns)
        self.assertSuccess(blank_dataset)
        self.assertIn(
            'path', blank_dataset.json(),
            msg='no path in response: {response}'.format(response=blank_dataset.text))
        self.assertIn(
            'path', blank_dataset_with_columns.json(),
            msg='no path in response: {response}'.format(response=blank_dataset_with_columns.text))


    def test_fork_dataset(self):
        blank_dataset_with_columns = requests.get(host + 'ga_resources/new/',
                                                  headers={
                                                      "content-type": 'application/json'
                                                  }
        , params={
          "api_key": AK,
          "title": 'test create empty dataset',
          'srid': 4326,
          'columns_definitions': json.dumps({
              "i": "real",
              "j": "integer",
              "name": "text"
          })
        })

        self.assertSuccess(blank_dataset_with_columns)
        self.assertIn(
            'path', blank_dataset_with_columns.json(),
            msg='no path in response: {response}'.format(response=blank_dataset_with_columns.text))

        path = blank_dataset_with_columns.json()['path']
        new_dataset = requests.get(host + 'ga_resources/' + path + '/fork/',
                                   headers={
                                       "content-type": 'application/json'
                                   }
            , params={
            "api_key" : AK,
        })
        self.assertSuccess(new_dataset, msg='failed to fork dataset')



    def test_fork_dataset_geometry(self):
        blank_dataset_with_columns = requests.get(host + 'ga_resources/new/',
                                                  headers={
                                                      "content-type": 'application/json'
                                                  }
            , params={
          "api_key": AK,
          "title": 'test create empty dataset',
          'srid': 4326,
          'columns_definitions': json.dumps({
              "i": "real",
              "j": "integer",
              "name": "text"
          })
        })

        self.assertSuccess(blank_dataset_with_columns)
        self.assertIn(
            'path', blank_dataset_with_columns.json(),
            msg='no path in response: {response}'.format(response=blank_dataset_with_columns.text))

        path = blank_dataset_with_columns.json()['path']
        new_dataset = requests.get(host + 'ga_resources/' + path + '/fork_geometry/',
                                   headers={
                                       "content-type": 'application/json'
                                   }
            , params={
            "api_key": AK,
        })
        self.assertSuccess(new_dataset)


    def test_schema(self):
        blank_dataset_with_columns = requests.get(host + 'ga_resources/new/',
                                                  headers={
                                                      "content-type": 'application/json'
                                                  }
            , params={
            "api_key": AK,
            "title": 'test schema dataset',
            'srid': 4326,
            'columns_definitions': json.dumps({
                "i": "real",
                "j": "integer",
                "name": "text"
            })
        })
        self.assertSuccess(blank_dataset_with_columns, msg='failed to create dataset {code}')

        path = blank_dataset_with_columns.json()['path']
        schema = requests.get(host + 'ga_resources/{path}/schema/'.format(path=path))

        self.assertSuccess(schema)
        schema = schema.json()

        self.assertListEqual(
            sorted([c['name'].lower() for c in schema]),
            ['geometry','i','j','name','ogc_fid'],
            msg='schema should have had 5 fields, was\n{schema}'.format(schema=schema))


    def test_add_column(self):
        blank_dataset = requests.get(host + 'ga_resources/new/',
                                     headers={
                                         "content-type": 'application/json'
                                     }
            , params={
            "api_key": AK,
            "title": 'test create empty dataset'
        })
        self.assertSuccess(blank_dataset, msg='failed to create dataset {code}')


        path = blank_dataset.json()['path']
        add_column = requests.get(host + 'ga_resources/' + path + '/add_column/',
                                  headers={
                                      "content-type": 'application/json'
                                  }
            , params={
            "api_key": AK,
            "name" : "p",
            "type" : "text"
        })
        self.assertSuccess(add_column)



    def test_add_row(self):
        blank_dataset_with_columns = requests.get(host + 'ga_resources/new/',
                                                  headers={
                                                      "content-type": 'application/json'
                                                  }
            , params={
            "api_key": AK,
            "title": 'test schema dataset',
            'srid': 4326,
            'columns_definitions': json.dumps({
                "i": "real",
                "j": "integer",
                "name": "text"
            })
        })
        self.assertSuccess(blank_dataset_with_columns, msg='failed to create dataset {code}')

        path = blank_dataset_with_columns.json()['path']
        add_row = requests.post(host + 'ga_resources/' + path + '/',
                                headers={
                                    "content-type": 'application/json'
                                }
            , params={
                "api_key": AK,
                "i": 0.0,
                "j": 2,
                "name": "folly",
                'GEOMETRY': "POINT(1 1)"
            })
        self.assertSuccess(add_row)


    def test_attribute_query(self):
        blank_dataset_with_columns = requests.get(host + 'ga_resources/new/',
                                                  headers={
                                                      "content-type": 'application/json'
                                                  }
            , params={
            "api_key": AK,
            "title": 'test schema dataset',
            'srid': 4326,
            'columns_definitions': json.dumps({
                "i": "real",
                "j": "integer",
                "name": "text"
            })
        })
        self.assertSuccess(blank_dataset_with_columns, msg='failed to create dataset {code}')

        path = blank_dataset_with_columns.json()['path']
        add_row = requests.post(host + 'ga_resources/' + path + '/',
                                headers={
                                    "content-type": 'application/json'
                                }
            , params={
                "api_key": AK,
                "i": 0.0,
                "j": 2,
                "name": "folly",
                'GEOMETRY': "POINT(1 1)"
            })
        self.assertSuccess(add_row)

        query = requests.get(host + 'ga_resources/' + path + '/query/',
                             headers={
                                 "content-type": 'application/json'
                             }
            , params={
            "name__contains" : 'oll'
        })
        self.assertSuccess(query)

        self.assertGreater(len(query.json()), 0, msg='zero results returned')



    def test_spatial_query(self):
        blank_dataset_with_columns = requests.get(host + 'ga_resources/new/',
                                                  headers={
                                                      "content-type": 'application/json'
                                                  }
            , params={
            "api_key": AK,
            "title": 'test schema dataset',
            'srid': 4326,
            'columns_definitions': json.dumps({
                "i": "real",
                "j": "integer",
                "name": "text"
            })
        })
        self.assertSuccess(blank_dataset_with_columns, msg='failed to create dataset {code}')

        path = blank_dataset_with_columns.json()['path']
        add_row = requests.post(host + 'ga_resources/' + path + '/',
                                headers={
                                    "content-type": 'application/json'
                                }
            , params={
                "api_key": AK,
                "i": 0.0,
                "j": 2,
                "name": "folly",
                'GEOMETRY': "POINT(1 1)"
            })
        self.assertSuccess(add_row)

        query = requests.get(host + 'ga_resources/' + path + '/query/0,0,2,2/')
        self.assertSuccess(query)
        self.assertGreater(len(query.json()), 0, msg='zero results returned')

        query = requests.get(host + 'ga_resources/' + path + '/query/',
                             headers={
                                 "content-type": 'application/json'
                             }
            , params={
            "g" : "POLYGON((0 0, 2 0, 2 2, 0 2, 0 0))"
        })
        self.assertSuccess(query)
        self.assertGreater(len(query.json()), 0, msg='zero results returned')

    def test_get_row(self):
        blank_dataset_with_columns = requests.get(host + 'ga_resources/new/',
                                                  headers={
                                                      "content-type": 'application/json'
                                                  }
            , params={
            "api_key": AK,
            "title": 'test schema dataset',
            'srid': 4326,
            'columns_definitions': json.dumps({
                "i": "real",
                "j": "integer",
                "name": "text"
            })
        })
        self.assertSuccess(blank_dataset_with_columns, msg='failed to create dataset {code}')

        path = blank_dataset_with_columns.json()['path']
        add_row = requests.post(host + 'ga_resources/' + path + '/',
                                headers={
                                    "content-type": 'application/json'
                                }
            , params={
                "api_key": AK,
                "i": 0.0,
                "j": 2,
                "name": "folly",
                'GEOMETRY': "POINT(1 1)"
            })
        self.assertSuccess(add_row)

        query = requests.get(host + 'ga_resources/' + path + '/1/')
        self.assertSuccess(query)
        self.assertGreater(len(query.json().keys()), 0, msg='no results returned')

    def test_get_rows(self):
        blank_dataset_with_columns = requests.get(host + 'ga_resources/new/',
                                                  headers={
                                                      "content-type": 'application/json'
                                                  }
            , params={
            "api_key": AK,
            "title": 'test schema dataset',
            'srid': 4326,
            'columns_definitions': json.dumps({
                "i": "real",
                "j": "integer",
                "name": "text"
            })
        })
        self.assertSuccess(blank_dataset_with_columns, msg='failed to create dataset {code}')

        path = blank_dataset_with_columns.json()['path']
        add_row = requests.post(host + 'ga_resources/' + path + '/',
                                headers={
                                    "content-type": 'application/json'
                                }
            , params={
                "api_key": AK,
                "i": 0.0,
                "j": 2,
                "name": "folly",
                'GEOMETRY': "POINT(0 1)"
            })
        self.assertSuccess(add_row)

        add_row = requests.post(host + 'ga_resources/' + path + '/',
                                headers={
                                    "content-type": 'application/json'
                                }
            , params={
                "api_key": AK,
                "i": 0.0,
                "j": 2,
                "name": "folly",
                'GEOMETRY': "POINT(1 1)"
            })
        self.assertSuccess(add_row)

        add_row = requests.post(host + 'ga_resources/' + path + '/',
                                headers={
                                    "content-type": 'application/json'
                                }
            , params={
                "api_key": AK,
                "i": 0.0,
                "j": 2,
                "name": "folly",
                'GEOMETRY': "POINT(2 1)"
            })
        self.assertSuccess(add_row)

        query = requests.get(host + 'ga_resources/' + path + '/1:3/',
                             headers={
                                 "content-type": 'application/json'
                             }
        )
        self.assertSuccess(query)
        self.assertEqual(len(query.json()), 3, msg='no results returned {n}'.format(n=len(query.json())))

        query = requests.get(host + 'ga_resources/' + path + '/1,3/',
                             headers={
                                 "content-type": 'application/json'
                             }
        )
        self.assertSuccess(query)
        self.assertEqual(len(query.json()), 3, msg='no results returned {n}'.format(n=len(query.json())))

        query = requests.get(host + 'ga_resources/' + path + '/0,3/',
                             headers={
                                 "content-type": 'application/json'
                             }
        )
        self.assertSuccess(query)
        self.assertEqual(len(query.json()), 3, msg='no results returned {n}'.format(n=len(query.json())))


    def test_only(self):
        blank_dataset_with_columns = requests.get(host + 'ga_resources/new/',
                                                  headers={
                                                      "content-type": 'application/json'
                                                  }
            , params={
            "api_key": AK,
            "title": 'test schema dataset',
            'srid': 4326,
            'columns_definitions': json.dumps({
                "i": "real",
                "j": "integer",
                "name": "text"
            })
        })
        self.assertSuccess(blank_dataset_with_columns, msg='failed to create dataset {code}')

        path = blank_dataset_with_columns.json()['path']
        add_row = requests.post(host + 'ga_resources/' + path + '/',
                                headers={
                                    "content-type": 'application/json'
                                }
            , params={
                "api_key": AK,
                "i": 0.0,
                "j": 2,
                "name": "folly",
                'GEOMETRY': "POINT(1 1)"
            })
        self.assertSuccess(add_row)

        query = requests.get(host + 'ga_resources/' + path + '/1/')
        self.assertSuccess(query)
        self.assertGreater(len(query.json().keys()), 0, msg='no results returned')


    def test_update_row(self):
        blank_dataset_with_columns = requests.get(host + 'ga_resources/new/',
                                                  headers={
                                                      "content-type": 'application/json'
                                                  }
            , params={
            "api_key": AK,
            "title": 'test schema dataset',
            'srid': 4326,
            'columns_definitions': json.dumps({
                "i": "real",
                "j": "integer",
                "name": "text"
            })
        })
        self.assertSuccess(blank_dataset_with_columns, msg='failed to create dataset {code}')

        path = blank_dataset_with_columns.json()['path']
        add_row = requests.post(host + 'ga_resources/' + path + '/',
                               headers={
                                   "content-type": 'application/json'
                               }
            , params={
                "api_key": AK,
                "i": 0.0,
            "j": 2,
            "name": "folly",
            'GEOMETRY': "POINT(1 1)"
        })
        self.assertSuccess(add_row)

        query = requests.put(host + 'ga_resources/' + path + '/1/',
                             headers={
                                 "content-type": 'application/json'
                             }
            , params={
            "api_key":AK,
            "i" : 1.0
        })
        self.assertSuccess(query)


    def test_delete_row(self):
        blank_dataset_with_columns = requests.get(host + 'ga_resources/new/',
                                                  headers={
                                                      "content-type": 'application/json'
                                                  }
            , params={
            "api_key": AK,
            "title": 'test schema dataset',
            'srid': 4326,
            'columns_definitions': json.dumps({
                "i": "real",
                "j": "integer",
                "name": "text"
            })
        })
        self.assertSuccess(blank_dataset_with_columns, msg='failed to create dataset {code}')

        path = blank_dataset_with_columns.json()['path']
        add_row = requests.post(host + 'ga_resources/' + path + '/',
                                headers={
                                    "content-type": 'application/json'
                                }
            , params={
                "api_key": AK,
                "i": 0.0,
                "j": 2,
                "name": "folly",
                'GEOMETRY': "POINT(1 1)"
            })
        self.assertSuccess(add_row)

        query = requests.delete(host + 'ga_resources/' + path + '/1/',
                                headers={
                                    "content-type": 'application/json'
                                },
                                params={ "api_key": AK, }

        )
        self.assertSuccess(query)