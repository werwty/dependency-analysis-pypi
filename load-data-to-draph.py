#!/usr/bin/env python
# coding: utf-8

# In[166]:


import json
import logging
import os

import click
import pydgraph
from pprint import pprint


# In[167]:


logger = logging.getLogger("Dependency Graph Generation")
client_stub = pydgraph.DgraphClientStub('localhost:9080')
client = pydgraph.DgraphClient(client_stub)


# In[168]:


# Drop All - discard all data and start from a clean slate.
def drop_all(client):
    return client.alter(pydgraph.Operation(drop_all=True))

# Set schema.
def set_schema(client):
    schema = """
    name: string @index(exact) .
    depends: [uid] @reverse .
    version: string .
    src: string .
    pkg_rel_date: string .
    number_dependents: int .
    type Package {
        name
        depends
        version
    }
    """
    return client.alter(pydgraph.Operation(schema=schema))

#drop_all(client)
#set_schema(client)


# In[169]:


def query_package(client, package_name, package_version):
    """Check if package(name,version) is already in dgraph"""
    query = """query all($name: string, $version: string) {
        all(func: eq(name, $name)) @filter(eq($version, version)) {
            uid
            name
            version
            depends {
                name
                version
                version_specifier
            }
            number_dependents
        }
    }"""

    variables = {'$name': package_name, '$version': package_version}
    res = client.txn(read_only=True).query(query, variables=variables)
    packages = json.loads(res.json)

    # Print results.
    if packages.get("all"):
        return packages.get("all")[0]
    return []

def insert_package(package_json):
    txn = client.txn()

    package_uid = {}
    pkg_dependencies = {}
    for package_name, package in package_json.get("dep_info", {}).items():
        version = package.get("ver")
        
        # Check if this package already exists in the graph db.
        # if it does increment its number of dependents by 1
        # otherwise insert it into the graph db.
        existing_package = query_package(client, package_name, version)
        if existing_package:
            existing_package['number_dependents'] = existing_package['number_dependents']+1
            txn.mutate(set_obj=existing_package)   
            package_uid[(package_name, version)] = existing_package['uid']
            continue
            
        pkg_to_insert = {
            'uid': '_:{}'.format(package_name),
            'dgraph.type': 'Package',
            'name': package_name,
            'version': version,
            'pkg_rel_date': package['pkg_rel_date'][0],
            'src': package['src'][0],
            'number_dependents': 0

        }
        
        insert_data = txn.mutate(set_obj=pkg_to_insert)   
        package_uid[(package_name, version)] = insert_data.uids[package_name]
        
        pkg_dependencies[insert_data.uids[package_name]] = package.get('dep')

    # it is important that we commit the dependencies after we insert the nodes
    # otherwise we can't link them via uuid
    for package_uuid, dependencies in pkg_dependencies.items():
        for dependency in dependencies:
            dependency_to_insert = {
                "uid": package_uuid,
                "depends": {
                    "uid": package_uid[(dependency['dep_name'], dependency['dep_ver'])],
                    'name': dependency['dep_name'],
                    'version': dependency['dep_ver'],
                    'version_specifier': dependency['dep_constraint']
                }
            }
            
            response = txn.mutate(set_obj=dependency_to_insert)   
    txn.commit()

        


# In[170]:


@click.command()
@click.option('--datadir', help='Directory of the dependency JSON files.')
def generate_dep_graph(datadir):
    set_schema(client)
    entries = os.listdir(datadir)
    for entry in entries:
        with open(os.path.join(datadir, entry)) as file:
            json_data = json.load(file)
            logger.info("Inserting data for {}".format(json_data.get("root_pkg")))
            try:
                insert_package(json_data)
            except Exception as e:
                logger.info("Failed to parse data for {} with exception {}".format(json_data.get("root_pkg"), e))

if __name__ == '__main__':
    generate_dep_graph()


# In[163]:



        


# In[164]:





# In[ ]:




