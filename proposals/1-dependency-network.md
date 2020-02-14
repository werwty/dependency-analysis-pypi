## Global Dependency Network Analysis

Keywords: Package manager, package repository, Dependency graph

Software packages have become more interdependent on each other; every dependency would have their own set of dependencies, making an application's dependency graph increasingly deep.
To assess the health of a software ecosystem, a researcher might want to do analysis on available packages in the software repository.
But it is not feasible for a researcher with limited resources to analyze the whole of a software repository. 

If we model the entirety of a software repository as an directed acyclic dependency graph (DAG) and we sort it in topological order. The packages near the root of this
tree are the ones that are relied on by most other packages.
An researcher can most effectively allocate their resources by focusing on these packages. 

Stated another way, an attacker would compromise the most system by taking over packages near the root of the DAG, therefore the closer to the root a package is, 
the more resources should be allocated to ensure its soundness.

We will focus our attention only on one package repository, the python package index (PyPI). Every python package in PyPI can be found using PyPI's simple API: `https://pypi.org/simple`.
A package's dependencies can be found with a call to PyPI's json API: `https://pypi.org/pypi/{project}/{version}/json`

We can iterate through all the packages in PyPI and store the dependency relations in a GraphQL database. This enables us to reason about the Python software ecosystem from a Graph Theory point of view. We can easily do a topological sort and get the most commonly dependent libraries. If we also store well selected metadata in this database, we can also reason about things such like: 

- For a set of common libraries, how many descendent packages pin the version vs how many use the latest? 
- What kind of packages are the ones near the root of the tree (wheel? egg? binary?)

 
We will utilize this topological sort to do analysis on the packages near the root. We can analyze by hand the top 10, use a tool to analyze the top 100. 

If we find security faults, we will categorize those faults and notify the maintainers.
If we do not find security flaws, we can become increasingly confident in the health of the python package ecosystem.

The packages near the root of this tree should also be made known to the community; maintainers of open source packages often do not get paid to do so. By making this list of global dependencies public, a maintainer can utilize this to ask for funding from the community. 
Researchers and other developers can also utilize it to concentrate their resources on the most influential packages, ensuring that those will not be compromised.

Open questions:
    - What are some other intersting metrics we should include. 
    - What other conclusions can we draw from this dependency graph?