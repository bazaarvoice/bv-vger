Quality Assurance : Lead Times
==============================

The Lead Times chart shows you information about [Responsiveness](http://focusedobjective.com/team-metrics-right/) – how quickly work is finished once it begins.

What does it show?
------------------

You can see how your team is responding to two different kinds of work items.

![](attachments/87624456/87624441.png)

*   JIRA issues

![](attachments/87624456/87624440.png)

*   GitHub pull requests

What does "lead time" mean?
---------------------------

In Vger, "lead time" means the amount of time between the moment you commit to work on something and the moment you declare it completed – no more work is needed from your team.

**Something you need to know:** Vger measures lead time only for work items that you actually work on. If you abandon a work item without actually doing any work on it, Vger does not consider that work item to be "completed". Work items that are not "completed" are not included in Vger statistics. The exact definition of "completed" is different for JIRA issues and GitHub pull requests – see details below.

How is PR lead time defined?
----------------------------

For pull requests, the definition of lead time is simple.

![](attachments/87624456/87624440.png)

*   PR lead time is the time interval between...
    *   ... the time the PR is created...
    *   ... and the time the PR is merged.
*   A PR that is closed without merging is not "completed" and is not included in Vger statistics

How is JIRA issue lead time defined?
------------------------------------

For JIRA issues, the definition of lead time is your responsibility – it depends on how you organize your workflow in JIRA.

In general, an issue moves from one "work state" to the next, as shown on your board. By default, the work states defined for your team project correspond to the columns on your board. But for Vger, you may want to organize work states differently. To change work state definitions, click on ![](attachments/87624456/87624450.png) in the Lead Times chart.

Lead time begins when an issue enters a work state that signifies your commitment to work on it. This commitment usually occurs some time after the issue has been created (when status becomes "Open") but before someone actually begins the work (when status becomes something like "In Progress"). Similarly, lead time ends when an issue enters a work state that indicates no more work is needed. For example, you might define lead time to begin with a work state named "Ready" (or something like that) and to end with a work state named "Deployed" (or something like that). The work states that lie between the start and end states represent the "lead time interval" for your team project.

To define the proper lead time interval for your team project, click on ![](attachments/87624456/87624450.png) in the Lead Times chart to select the start and end work states.

![](attachments/87624456/87624441.png)

*   Issue lead time is the time interval between...
    *   ... the time an issue first enters a work state within the lead time interval and...
    *   ... the time an issue finally enters a work state that comes after the lead time interval.
*   But an issue is not "completed" and is not included in Vger statistics if:
    *   it never enters a work state within the lead time interval, or
    *   it has a final Resolution that indicates no work was actually done (e.g. Won't Do, Abandoned, Duplicate, etc.)

What do the lines mean?
-----------------------

**50%**

An optimistic view of lead times: 50% of the work items completed during previous weeks had a lead time that was less than or equal to this value.

**80%**

A conservative view of lead times: 80% of the work items completed during previous weeks had a lead time that was less than or equal to this value.

**90%**

A super\-conservative view of lead times: 90% of the work items completed during previous weeks had a lead time that was less than or equal to this value.

Can I compare lead times for different types of work?
-----------------------------------------------------

Yes. When viewing Throughput for JIRA issues, you can use the Work Types menu to select which work types are included in the Lead Times values.

What does this tell me about my team performance?
-------------------------------------------------

Are lead times trending higher over time?

*   Maybe your work items are becoming too complex. Consider breaking large work items into smaller pieces.
*   Maybe you are spending too much time in code reviews. (For JIRA issues, look at the Detailed view.) Consider different ways to sort out design issues before coding begins.
*   Maybe you are spending too much time finding and fixing defects. (For JIRA issues, look at the Detailed view.) Consider different ways to prevent defects earlier and faster.

Are lead times trending lower over time?

*   You must be doing something to make the team more responsive! Find out what it is, and do more of it!

Attachments:
------------

![](images/icons/bullet_blue.gif) [git\_pr.png](attachments/87624456/87624440.png) (image/png)  
![](images/icons/bullet_blue.gif) [jira.png](attachments/87624456/87624441.png) (image/png)  
![](images/icons/bullet_blue.gif) [Pencil.png](attachments/87624456/87624450.png) (image/png)  
![](images/icons/bullet_blue.gif) [image2018\-3\-6 18:23:6.png](attachments/87624456/87624454.png) (image/png)  
![](images/icons/bullet_blue.gif) [image2018\-3\-6 18:23:14.png](attachments/87624456/87624455.png) (image/png)  