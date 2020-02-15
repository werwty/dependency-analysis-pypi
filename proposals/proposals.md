# 774 Proposals
Bihan Zhang & John Li

## 1. Global Dependency Network Analysis

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

- What are some other interesting metrics we should include. 
- What other conclusions can we draw from this dependency graph?


## 2. Meta Reproducibility Analysis of Network Security Papers and Tools

Keywords: reproducibility, networking tools


The reliability of research, and therefore reproducibility, is the backbone of cumulative knowledge.
Open data, clear methodology, and software tooling each play their part in making research reproducible.

We will focus on the software side of reproducibility. Many [citation needed] research papers in the network security domain
publish the source code they developed to gather their results. Unfortunately these are oftentimes not well documented, incomplete,
don't have their dependencies listed, have dependencies that we cannot locate, or need additional work done to compile. 
This makes utilizing their code difficult or even impossible.

We would like to do a meta analysis of this problem and develop automation around this problem.

We would get the source code of a good set of tools created in recent papers. With these we would focus on a specific language (C/++ or Python).
We will automate the process of attempting to compile/install and run these tools by classifying each tool by the build system used, and determining the right command to build the tool. Of the ones that our automation fails to run, we will need to figure out if the root cause is our automation (and iteratively improve it), or if something is faulty with the analyzed code. This process will have to be manual.

We expect that a good portion of the chosen software would take effort to install and run. Of these we can classify each tool as needs a little work to install (installing an unlisted dependency), needs a lot of work to install, and not installable. During this process we can compile a list of guidelines for future researchers to follow as they publish their code.

Note: Yes, this is a meta study and not at the surface a security research project. But if we choose to focus only on the network security domain, I think a well written study of this topic could be accepted at a network security venue. 


## 3. A Reproducibility Study

Reproducibility is the backbone of science! We found 2 previously published papers with questionable results that would benefit from a reproducibility study. 

### Faulds: A Non-Parametric Iterative Classifier for Internet-Wide OS Fingerprinting

For all the reasons discussed in class Faulds is a good candidate for a reproducibility study. 
Given their assumed 50% packet loss rate just isn't reasonable, we can measure how Faulds and Hershel+ does in a reasonable setting.

We would:

1. Reproduce the Faulds study with the parameters used in their paper
2. See if Faulds is still useful given reasonable parameters.
3. Do the same for Hershel+ and use that to compare against the Faulds results. 


### An empirical study of Namecoin and lessons for decentralized namespace design

https://www.cs.princeton.edu/~arvindn/publications/namespaces.pdf

The researchers found that there were only 28 domains registered with namecoin and used. 

The Namecoin developers claim that this study only produced such results because of faulty methodology design.

We can analyze and update the methodology and see if the results are comparable to what the Princeton researchers found in 2015. 


## 4. Measurement of Post-Quantum Cryptography Protocol Usage in the Wild

Nowadays new crypto protocols have to claim post quantum security to be taken seriously, but what is the actual adoption of post-quantum secure protocols?
 What is causing the big gap between quantum based crypto protocols, their implementations and their usage? 
 
It would be interesting to do a measurement on the current adoption of post-quantum cryptographic protocols, this can be the first in a longitudinal studies so we can observe the adoption of post-quantum protocols.

We can find the crypto libraries that have post-quantum support and then scan github for how common those features are used. 

We'll either find: 1. there is close to zero adoption (most likely) or 2. There is some small adoption. 

We can reason about and who are the early adopter of post-quantum protocols and reason about the users of such applications/libraries.
If #1 is found, how much of this is because of how the crypto libraries are written? Are these protocols just not ready for mainstream usage? Are they just confusing/hard to use? How are they documented differently from traditional crypto protocols? Is it just a matter of the general public needing more education? Or is the runtime of these significantly worse and therefore not worth the tradeoff?


