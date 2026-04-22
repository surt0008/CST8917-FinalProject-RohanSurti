# CST8917 Final Project -Expense Approval Workflow

**Name:** Rohan Surti  
**Student Number:** 041164260

**Course Code:** CST8917 -Serverless Applications  
**Project Title:** Expense Approval Workflow using Azure Durable Functions and Logic Apps  


---

#  Introduction

In this project, I implemented an expense approval workflow using two different serverless approaches in Microsoft Azure. The main goal was to understand how different cloud services can solve the same business problem and compare them based on real implementation experience.

The workflow follows these business rules:
- Expenses less than $100 are automatically approved  
- Expenses greater than or equal to $100 require manager approval  
- If the manager does not respond within a certain time, the request is escalated  
- Invalid or incomplete requests are rejected  

Two versions were created:
- Version A using Azure Durable Functions  
- Version B using Azure Logic Apps with Service Bus  

---

# Version A -Durable Functions

## Overview

Version A uses Azure Durable Functions to implement the workflow in a programmatic way. The core of this version is the orchestrator function, which controls the entire flow from start to end.

The process starts with an HTTP trigger, which receives the expense request. The orchestrator function then calls different activity functions to validate the request, check the amount, and decide whether approval is needed. A durable timer is used to simulate waiting for a manager response.

## Key Design Decisions

- Used a single orchestrator function to control the workflow logic  
- Created separate activity functions for validation and decision-making  
- Implemented durable timers to simulate delays and escalation  
- Used HTTP endpoints to trigger and monitor the workflow  

## Challenges Faced

One of the biggest challenges was understanding how Durable Functions manage state and asynchronous execution. Initially, it was confusing to see how the orchestrator pauses and resumes execution.

Another issue was setting up Azurite for local testing, which caused errors related to ports and permissions. Also, debugging Durable Functions required careful reading of logs because errors were not always straightforward.

---

#  Version B- Logic Apps + Service Bus

## Overview

Version B uses Azure Logic Apps combined with Service Bus to implement the same workflow in a more visual way. Instead of writing code, the workflow is designed using a drag-and-drop interface.

The process starts when a message is sent to a Service Bus queue. The Logic App is triggered automatically, and it processes the message using conditions and actions. The result is then sent to a Service Bus topic with filtered subscriptions for approved, rejected, and escalated outcomes.

## Key Design Decisions

- Used Service Bus queue as the entry point for requests  
- Used Logic App conditions to implement workflow logic  
- Used Service Bus topic with subscriptions for routing outcomes  
- Used HTTP function for validation  
- Used delay action to simulate manager response  

## Manager Approval Approach

Since Logic Apps do not easily support human interaction patterns like Durable Functions, I simulated manager decisions using conditions:
- If amount < 300 → approved  
- If amount ≥ 300 → rejected  
- If amount = 175 → escalated  

## Challenges Faced

The main challenge was handling JSON parsing and Base64 encoding from Service Bus messages. Many errors occurred because the message content was not in the expected format.

Another difficulty was managing nested conditions in Logic Apps. As the workflow became more complex, the visual layout became harder to read and maintain.

---

# Comparison Analysis 

This project compares Azure Durable Functions and Azure Logic Apps across six key dimensions: complexity, control, scalability, maintainability, cost, and development experience.

First, in terms of complexity, Durable Functions are more complex to implement because they require writing code and understanding asynchronous programming concepts. The orchestrator pattern, while powerful, can be difficult for beginners to understand. In contrast, Logic Apps are easier to start with because they provide a visual interface where workflows can be built using predefined actions. However, as the workflow becomes more complex, Logic Apps can also become difficult to manage due to multiple nested conditions and branches.

Second, regarding control and flexibility, Durable Functions provide much greater control. Developers can implement custom logic, handle retries, and manage long-running workflows more effectively. In this project, the escalation logic using durable timers was straightforward in Durable Functions. In Logic Apps, the same behavior had to be simulated using delay actions and additional conditions, which was less flexible.

Third, scalability is an important factor. Both Durable Functions and Logic Apps are serverless services and scale automatically based on demand. However, Durable Functions are better suited for compute-heavy workflows, while Logic Apps are more focused on integration between services. For example, Logic Apps easily integrates with Service Bus, email services, and APIs without requiring additional code.

Fourth, in terms of maintainability, Logic Apps have an advantage because the visual representation makes it easier to understand the workflow at a glance. This is useful for teams where not all members are developers. On the other hand, Durable Functions require reading code to understand the workflow, which can be more difficult for non-technical users.

Fifth, cost is another important consideration. Logic Apps are charged based on the number of actions executed, which can become expensive for workflows with many steps. Durable Functions are generally more cost-efficient because they are billed based on execution time and resource usage. In this project, the Logic App used multiple actions, which could increase cost in a real-world scenario.

Finally, development experience differs significantly between the two approaches. Durable Functions felt more powerful and structured, especially for implementing complex workflows. However, it required more time to learn and debug. Logic Apps provided a faster way to build the workflow, but debugging issues like JSON parsing and message formatting took time due to less control over internal processing.

Overall, both approaches successfully implemented the same workflow, but the experience of building and managing them was quite different. Durable Functions are better for complex, logic-heavy workflows, while Logic Apps are better for quick integration-based solutions.

---

#  Recommendation

Based on my experience in this project, I would recommend choosing between Durable Functions and Logic Apps depending on the complexity and requirements of the workflow.

Durable Functions are the better choice for complex workflows that require detailed control, custom logic, and long-running processes. They allow developers to design workflows in a structured way using code, which makes them more flexible and powerful. In this project, implementing escalation and timer-based logic was much easier using Durable Functions compared to Logic Apps.

On the other hand, Logic Apps are more suitable for simpler workflows or integration-focused scenarios. They provide a visual interface that makes it easy to connect different services without writing much code. For teams that prefer low-code solutions or need faster development, Logic Apps can be a better option.

In real-world applications, a hybrid approach can also be used. Logic Apps can handle integration and orchestration between services, while Durable Functions can handle complex processing tasks.

In conclusion, if the workflow is simple and integration-heavy, Logic Apps should be used. If the workflow is complex and requires more control, Durable Functions are the better choice.

---

#  References

- https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview  
- https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-overview  
- https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-messaging-overview  

---

#  AI Disclosure

AI tools (ChatGPT) were used to assist with:
- Understanding Azure concepts  
- Debugging implementation issues  
- Structuring documentation  

All content was reviewed and modified to reflect my own understanding.
