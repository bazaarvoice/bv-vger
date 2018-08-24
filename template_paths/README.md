# bv-vger-config


## General

There is a paths.txt file in the root that contains the file paths of all the files in both 'blanks' and 'private'. This is used by the moving scripts (vger-config-setup-private and vger-config-setup-public) and should be updated if a file is ever moved or a new private file and template file has been added. 

There is 2 scripts: vger-config-setup-private.sh and vger-config-setup-public.sh. For these scripts to run properly, the bv-vger-config repo needs to be in the same local root directory as the bv-vger repo (for me, they both existed in a folder called 'GitHub'). 

The private script moves all the private files (from the private folder) into the local instance of vger that someone has. 

The public script moves all the template/public files (from the blanks folder) into the local instance of vger that someone has.


## Deployment

Ideally, the private script should be ran anytime something is about to be deployed into S3, followed by the public script once the deployment is done. 


## Local Development

For local development, the private files are required in the local vger repo to spin up a local instance with './ui-local.sh' or './report-ui-local.sh'. Therefore the private script should be run before local development, but **the public script NEEDS to be run manually after local development finishes** or else the private files will remain in the github branch when the code is merged into the public repo. 


## Solution

The deploy script will run both the public and private scripts in between deployment. The local development scripts will run the private script automatically, but will require you to manually run the public script after local development is done. 
