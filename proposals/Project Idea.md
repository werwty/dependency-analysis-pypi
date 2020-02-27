# Project Idea

## 1. Global Dependency Network Analysis

### Problem

- When comes to security audit of a package repo, how to focus finite analysis resources?

### Solution

- Give those influential package higher priority when making a analysis plan

### Method

- 1, Build the Global Dependency Network Graph (GDNG)

	- Howto?

		- 1. fetch a zip from PyPi
		- 2. unzip the .zip package
		- 3. mocking the function "setup(extra_requirements={})" and run setup.py
		- 4. store the result and drop the .zip package

- 2. Analysis the dependency network graph

	- 1. Ranking the package by their influence 

		- 1. Do manual security audit on the top 10 most influential package
		- 2. Do automated static analysis on the remaining top n most influential package

			- Potential tools?

				- OSAWP dependency-check

					- https://pypi.org/project/dependency-check/
					- https://owasp.org/www-project-dependency-check/

## 2. Meta analysis - Measurement on Reproducibility of Publication's code

### Measurement target

- How many recent paper's result are reducible

### Method

- Check whether the code compile for recent Network Security papers

	- 1. Need a classifier for checking the build system used by project and figuring out the right command to build the project
	- 2. Manual analysis the project that cannot pass the build

## 3. AMI monitor tool

### Problem

- Company cold deploy AMI with known issue or software that later found vulnerable 

### Solution

- Create a tool for automated AMI vulnerability analyzing 

### Method

- Mount AMI image on AWS machine and perform automated check on it

	- Potential tool

		- Claire

### *Has novelty Concerns

