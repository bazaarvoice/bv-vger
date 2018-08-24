# Quarterly Reports
Vger is an internal Web app developed by QA team giving engineering teams insight into their agile performance. It scrapes 
data from Github and JIRA to answer questions such as:
* How has performance changed over time?
* How has performance changed between releases?
* Does performance vary for different work type? For different work states?

## Getting started
NOTE: node_modules is excluded from S3 uploads in order to compress upload size. However it is needed to run 'npm run build' to get dependencies and root components to be able to develop the app

## Basic Understanding
Once you have a project selected through VGer's project selection screens, you are taken to a short-term quartile view of the teams project represented by Throughput, Backlog Growth, Throughput Variation, and Lead Times. However, due to the nature of VGer, it presents the data in weekly snippits that can be used to draw trendlines of the data. Quarterly Reports allows you to see some of these graphs and more in a quarterly view to leverage larger data sets that are still a part of VGer (hence why the app is accessed through VGer and relies on VGers database). Currently, you are able to see Quarterly Throughtput and Quarterly Lead Times. 

## Quarterly Throughput
* Each dataset shows you the throughput that took place from the previous quarters end up until the listed data in the tooltip
* The percentiles are actually known as likeliness, which display the "likelihood" of X% of data falling under the trendline. They are calculated through R7 quartile calculations to line up with Excel's percentile function. For example, 80% likeliness in Quarterly Reports represents a number where 80% of the dataset is less than or equal to that number. In Excel, if you use 'Percentile([dataarray], 20%)', you will achieve the same result.

## Quarerly Lead Times
* The same quarter end dates that can be seen in Quarterly Throughput are used as dividors in Quarterly Lead Times
* The data is comprised of every ticket that was open AND closed in the set data range defined by 'since' the earliest quarters start date and 'until' the latest quarters end date
* The date of each point is the date that it was closed
* Hovering over each point displays more information about the point (name, number of working days, and date closed)
* Clicking on a point re-directs you to the JIRA ticket view of that point

## Developer Notes
* Development is done to the folders under /source/webpage/reports
* It is a react app that is overlayed with an angular div since it is routed using angular's router in VGer
* The build folder is the one that is used by QA and PROD
* Everytime you deploy the folder, it re-routes it (using re-router.sh) so that its file paths are satisfactory with the file structure of VGer's S3 bucket, and the de-routes it (using de-router.sh) for local development.
* When developing specifically for quarterly reports, use report-ui-local.sh since it is a react specific script that lets you edit the non-minified files and dynamically view your changes on a page refresh. 
* When developing for VGer but still wanting access to quarterly reports, you can use ui-local.sh (keep in mind that this uses the minified files in the /reports/build directory so your changes to quarterly reports will not take effect unless you cd into the reports folder and run npm run build)
* Quarterly Reports uses VGer's database and web_api folder
* There is a rerouter and derouter script located in this folder. Since this application is a stand-alone application built in react, there was a need to 'reroute' the file paths for the Vger angular app to properly utilize the react app and vise versa. There is also a derouter that keeps the react app as a stand-alone app so that if you ever need to do local development (./report-ui-local.sh), you don't need to remove all the router instances that reroute puts in place. These files will not need to be modified unless you are required to modify some of the base files that they need to reroute and deroute (for a file list, see either scripts 'sed' commands to see which files are being changed).



