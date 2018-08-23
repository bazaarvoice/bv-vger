# Vger
Vger is an internal Web app developed by QA team giving engineering teams insight into their agile performance. It scrapes 
data from Github and JIRA to answer questions such as:
* How has performance changed over time?
* How has performance changed between releases?
* Does performance vary for different work type? For different work states?

## What does "Vger" mean?

Read your [Star Trek history](http://memory-alpha.wikia.com/wiki/V%27ger). Then decide for yourself.

## Notes for those outside of bazaarvoice

Welcome to a bazaarvoice public repo! More importantly, welcome to Vger. This is the only out of the box, fully functioning, OPEN-SOURCED, productivity management tool that has been built from the ground up by a company the size of bazaarvoice or greater.

There is a few things that need to be done after downloading the repo in order to configure the vger project to work for your company. It does take a bit of time to do, but trust me when I say this, you will be loving the benefits of Vger much more than the small amount of setup required.

Because Vger uses AWS to work (see the [Hitchhiker's Guide to Vger](doc/developer-guide.md) in order to find pictures of our architecture), there is some constants files that need to be updated with the AWS credentials of your company. In fact, all the files that are currently 'templates' in bv-vger in template_paths/paths.txt. There is also the scripts that we use for moving the templates files and private files during deployment. More information about this can be read in the README.md located inside template_paths/.

Lastly, the deploy scripts we have in the deploy/ folder are modified to include function calls for the 2 scripts in the template_paths/ folder. If you or your company is not planning to keep template files alongside your actual private files, please remove these 2 lines of code from your deploy scripts:
*source ../../bv-vger-config/vger-config-setup-private.sh*
*source ../../bv-vger-config/vger-config-setup-public.sh*

Also don't forget to read 'Getting Started' for more information regarding what Vger is, what it does, and how to use it!

## Getting started
* Want to know how to use Vger? Read the [The Complete Guide](doc/external/vger_the_complete_guide.md).
* Are you a Vger developer? Read the [Hitchhiker's Guide to Vger](doc/developer-guide.md).

## Understanding the file structure
Please read the [Vger Directory Structure](doc/directory-structure.md) for an overview of how Vger source files are organized. 

## Vger UI
Vger is currently being hosted statically on s3 and can be accessed through this [link]()
<!-- S3 bucket link -->

## Some Small Things to Keep in Mind
* If you are deploying ui code (./deploy-ui.sh) and quarterly reports code (./build-deploy-reports.sh), you have to deploy ui before quarterly reports since there is routing scripts that run in quarterly reports to properly configure the 2 apps to work from the same S3 bucket. More information about quarterly reports can be found in README.md in the source/webpage/reports/ folder.

* Sometimes when deploying lambdas (./deployLambda.sh), the console will give you an error for duplicate 'env' variable in the .yml file. To fix this, go to the .yml file and remove the duplicate 'env' and run the deploy script once again.

