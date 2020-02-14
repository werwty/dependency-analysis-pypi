## Meta Reproducibility Analysis of Network Security Papers and the Software they Write

The reliability of research, and therefore reproducibility, is the backbone of cumulative knowledge.
Open data, clear methodology, and software tooling each play their part in making research reproducible.

We will focus on the software side of reproducibility. Many [citation needed] research papers in the network security domain
publish the source code they developed to gather their results. Unfortunately these are oftentimes not well documented, 
don't have their dependencies listed, have missing dependencies, or need additional work done to compile. Making reproducibility studies
difficult or even impossible.

We propose to do a meta analysis of this problem and develop automation around this problem.

We would get the source code of a good set of tools created in recent papers. With these we would focus on a specific language (probably C/++, maybe Python).
We would automate the process of attempting to compile/install and run these tools. And we would do this by classifing each tool by the build system used, and figuring out the right command to build the project. Of the ones that this tool fails to run, we will need to figure out if it's something lacking in the tool (and the iterate over the tool), or if something is faulty with the software. This process will have to be manual.

We expect that a good portion of the chosen software would take effort to install and run. Of these we can classify each tool as needs a little work to install (installing an unlisted dependency), and not able to run at all. During this process we can compile a list of guidelines for future researchers to follow as they publish their code.


Note: Yes, this is a meta study and not a security research project. But if we choose to focus only on the network security domain, I think this paper would 
be accepted at a network security venue. 
