# AWS Budget Setup Guide

Create a budget before provisioning EC2 or any other AWS workload.

## Why Start With a Budget

AWS Budgets helps track account spending and send alerts when actual or forecasted costs cross a threshold. It is an early-warning system for a learning project.

A budget alert does not automatically stop resources by default. Billing data and notifications can also be delayed. Continue checking the AWS console and clean up resources after experiments.

## Recommended Starter Budget

Use a recurring monthly cost budget:

- Budget type: `Cost budget`
- Period: `Monthly`
- Budgeting method: `Fixed`
- Suggested amount: `5 USD` or `10 USD`
- Scope: all AWS services in the account

For a first side project, `5 USD` is a cautious starting point. Choose `10 USD` if you plan to run EC2 experiments for longer periods.

## Console Steps

1. Sign in to the AWS Management Console.
2. Open `Billing and Cost Management`.
3. In the navigation pane, choose `Budgets`.
4. Choose `Create budget`.
5. Choose a monthly cost budget. The console may offer a simplified template or a customized cost budget.
6. Enter a unique budget name such as `document-intelligence-monthly-budget`.
7. Set the recurring monthly amount to `5 USD` or `10 USD`.
8. Add an actual-cost alert threshold, such as `80%`.
9. Add your email address as the notification recipient.
10. Optionally add a second alert at `100%`.
11. Review the settings and create the budget.
12. Check your inbox. If AWS sends a subscription confirmation email for the notification option you selected, confirm it.

AWS Budgets can also alert on forecasted spend. Actual-cost alerts are easier to understand at the beginning. Add a forecasted alert later after you are comfortable with the console.

## Important Limits

- A budget notification is not a hard spending limit.
- Charges may continue to increase before or after an alert arrives.
- Stopping an EC2 instance stops instance usage charges, but attached EBS storage can still incur charges.
- Public IPv4 addresses and Elastic IP addresses can incur charges.
- RDS can incur charges until you stop or delete the database.
- Load Balancers can incur charges until deleted.
- Do not create a NAT Gateway for this project. A NAT Gateway has hourly and data-processing charges.

## Cleanup Habit

At the end of each AWS session:

1. Stop or terminate unused EC2 instances.
2. Delete unused Elastic IP addresses.
3. Delete unused Load Balancers.
4. Stop or delete unused RDS databases.
5. Review the `Billing and Cost Management` console.
6. Record teardown steps whenever a new resource is added.

## Official References

- [Creating a cost budget](https://docs.aws.amazon.com/cost-management/latest/userguide/create-cost-budget.html)
- [Managing your costs with AWS Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html)
- [Pricing for NAT gateways](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-pricing.html)
