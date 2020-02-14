## Meta Reproducibility Analysis of Network Security Papers and Tools

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
