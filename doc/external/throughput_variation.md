Quality Assurance : Throughput Variation
========================================

The Throughout Variation chart shows you information about [Predictability](http://focusedobjective.com/team-metrics-right/) – "how consistently" your team is performing. In particular, this charts shows the consistency of your team throughput over time.

What does it show?
------------------

You can see your predictability for two different kinds of throughput.

![](attachments/87623781/87623695.png)

*   The number of JIRA issues [completed](Lead-Times_87624456.html#LeadTimes-completed) per week.

![](attachments/87623781/87623694.png)

*   The number of GitHub pull requests [completed](Lead-Times_87624456.html#LeadTimes-completed) per week.

What do the numbers mean?
-------------------------

This chart shows a metric known as the [coefficient of variation](https://en.wikipedia.org/wiki/Coefficient_of_variation) for your throughput. For each week, this is determined by looking at throughput values for the previous weeks and calculating the [standard deviation](https://en.wikipedia.org/wiki/Standard_deviation) relative to the average. In other words, if the standard deviation is equal to the average, then variation is 1.0. If the standard deviation is small relative to the average, then variation is less than 1.0. If your throughput is exactly the same every week, then variation is 0.0. (And you are probably hallucinating!)

In general, lower variation means that your team throughput is more consistent and predictable.

Can I compare variation for for different types of work?
--------------------------------------------------------

Yes. When viewing Throughput Variation for JIRA issues, you can use the Work Types menu to select which work types are included in the Throughput Variation values.

What does this tell me about my team performance?
-------------------------------------------------

What is a good value for Throughput Variation?

*   That depends on your team and the kind of work you do. The precise value is not what's important here.
*   What's important is how variation changes over time.

Is variation increasing over time?

*   Does the Lead Times chart show that 90th or 80th percentiles values are increasing? 
    *   Maybe you are taking on work items that are bigger than usual. Consider how you could more consistently break your work down into small pieces.
    *   Maybe you are dealing with poorly\-defined work items that demand extra time to clarify. Consider how you could ensure acceptance criteria are defined before work begins.
*   Does the Lead Times chart show that lead times are mostly unchanged? Maybe your work process is suffering from lulls or idle time. Consider what you could do to maintain a steady flow of new work items.

Is variation decreasing over time?

*   You must be doing something to finish work more consistently. Can you find a way to keep it up all the time? Can you do more to drive variation even lower?

Attachments:
------------

![](images/icons/bullet_blue.gif) [git\_pr.png](attachments/87623781/87623694.png) (image/png)  
![](images/icons/bullet_blue.gif) [jira.png](attachments/87623781/87623695.png) (image/png)  