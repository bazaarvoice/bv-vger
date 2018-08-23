Quality Assurance : Throughput
==============================

The Throughout chart shows you information about [Productivity](http://focusedobjective.com/team-metrics-right/) – "how much" work your team is completing.

What does it show?
------------------

You can see how your team is completing two different kinds of work items.

![](attachments/87623690/87623546.png)

*   The number of JIRA issues completed per week.
*   An issue is "[completed](Lead-Times_87624456.html#LeadTimes-completed)" if its status history shows that you actually worked on it...
*   ... and its status has moved past the end of the [lead time interval](Lead-Times_87624456.html#LeadTimes-leadTimeInterval).

![](attachments/87623690/87623547.png)

*   The number of GitHub pull requests completed per week.
*   A PR is "[completed](Lead-Times_87624456.html#LeadTimes-completed)" if it is closed and merged.

What do the lines mean?
-----------------------

The Throughput chart normally shows weekly throughput values measured for each week in the time range defined by the From and To dates. Or, if you want to see only the overall trend between the From date and the To date, click on ![](attachments/87623690/87625342.png).

**Actual**

The actual number of work items completed during the week preceding the given date.

**Likeliness 50%**

An optimistic view of throughput: For 50% of previous weeks, throughput was greater than or equal to this value.

**Likeliness 80%**

A conservative view of throughput: For 80% of previous weeks, throughput was greater than or equal to this value.

**Likeliness 90%**

A super\-conservative view of throughput: For 90% of previous weeks, throughput was greater than or equal to this value.

Can I compare throughput for different types of work?
-----------------------------------------------------

Yes. When viewing Throughput for JIRA issues, you can use the Work Types menu to select which work types are included in the Throughput values.

Can I export throughput value?
------------------------------

Yes. Click on ![](attachments/87623690/89181844.png) to download actual throughput value in CSV format.

What does this tell me about my team performance?
-------------------------------------------------

Are the Likeliness values trending lower over time?

*   Does the Lead Times chart show that lead times are increasing? Maybe your work items are becoming too complex. Consider breaking large work items into smaller pieces.
*   Does the Backlog Growth chart show that "failure" work types (e.g. Bug, etc) are increasing? Maybe you are spending too much dealing with failures. Consider how better or earlier reviews or testing could reduce this "failure demand".
*   Does the Lead Times chart show that lead times are mostly unchanged? Maybe the number of people working on these items has changed. Consider if this is now the "new normal" for throughput.

Are the Actual and Likeliness values increasing over time?

*   You must be doing something to make the team more productive! Find out what it is, and do more of it!

Attachments:
------------

![](images/icons/bullet_blue.gif) [jira.png](attachments/87623690/87623546.png) (image/png)  
![](images/icons/bullet_blue.gif) [git\_pr.png](attachments/87623690/87623547.png) (image/png)  
![](images/icons/bullet_blue.gif) [Trend.png](attachments/87623690/87625342.png) (image/png)  
![](images/icons/bullet_blue.gif) [Screen Shot 2018\-04\-25 at 3.57.18 PM.png](attachments/87623690/89181844.png) (image/png)  