# Config

In this directory we have the example configurations from the development server.
Because we cannot easily tell what the system will be like when deploying these steps will need to be manual. The things such as groups, users and paths may need to be modified on different deployments.

There are 2 ways we could automate this:

* Dockerize the whole project
* Use some amazon services to create an image of a server where everything is set up and deploy with code deploy to specific EC2 instances

Both of which are out of scope for the project.
