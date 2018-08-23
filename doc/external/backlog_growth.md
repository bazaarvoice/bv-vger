Quality Assurance : Backlog Growth
==================================

The Backlog Growth chart shows you information about [Quality](http://focusedobjective.com/team-metrics-right/) – "how well" your team is delivering value to your customers.

What does it show?
------------------

![](attachments/87625258/87625144.png)

Backlog Growth appears only when viewing your work on JIRA issues.

Backlog Growth shows how well your team is closing the gap between the value needed and the value delivered.

What do the numbers mean?
-------------------------

**Created**

*   The total number of issues created prior to the given week.
*   Or, if Relative Growth is selected, the total number of issues created since the selected From date.

**Completed**

*   The total number of issues [completed](Lead-Times_87624456.html#LeadTimes-completed) prior to the given week.
*   Or, if Relative Growth is selected, the total number of issues [completed](Lead-Times_87624456.html#LeadTimes-completed) since the selected From date.

**Backlog**

*   The gap between the Created and Completed lines.
*   The total number of improvements requested but not yet delivered.

Can I compare backlog growth for different types of work?
---------------------------------------------------------

Yes. You can use the Work Types menu to select which work types are included in the Backlog Growth values.

In particular, when you select one or more "failure" work types (e.g. Bug, Incident, etc.), the Backlog Growth chart shows your "failure backlog", a more urgent quality indicator. This is the gap between the value you intended to deliver and the value that actually was delivered.

What does this tell me about my team performance?
-------------------------------------------------

Is the backlog increasing over time?

*   Does the Throughput chart show that throughput is generally decreasing? Consider changes you could make to improve team productivity.
*   Does the Throughput chart show that throughput remains generally normal? 
    *   Maybe new value requests are being created faster than the team can handle them. Consider how to balance the rate of new requests with the team's throughput.
    *   Maybe you are spending too much time on unplanned work items, such defects and production failures. Consider changes you could make to reduce such unplanned work.

Is the failure backlog increasing over time?

*   Maybe the team is focused too much on pushing out new features. Consider changes you could make to ensure that reported failures are quickly reviewed and resolved.
*   Maybe some unresolved failures are not really important. Consider reviewing and discarding issues that the team really doesn't need to work on.

Is the backlog generally constant over time?

*   This is your normal value gap. But is it OK?
    *   Imagine a horizontal line extending across the chart. The distance between the points where it crosses the Created and Completed lines shows the amount of time it takes to close your normal value gap. This is your "delivery cycle time".
    *   How often does your team meet to evaluate your priorities and "replenish" the list of improvements to make next? This is your "replenishment cycle time".
    *   Is your delivery cycle time roughly equal to your replenishment cycle time? If so, your workflow is in balance. But consider if replenishing more frequently with fewer new requests could reduce your value gap.
    *   Is your delivery cycle time much greater than your replenishment cycle time? If so, new requests may be getting "stale" while they wait to be completed.

Attachments:
------------

![](images/icons/bullet_blue.gif) [git\_pr.png](attachments/87625258/87625143.png) (image/png)  
![](images/icons/bullet_blue.gif) [jira.png](attachments/87625258/87625144.png) (image/png)  