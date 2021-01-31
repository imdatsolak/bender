# bender

## Introduction

Bender is a customer interaction engine.

A customer interaction engine provides functionalities for a customer to interact with a company in an automated way. Traditionally, customer interaction was performed between two humans.

Bender in this sense takes the role of a customer-agent (e.g. a call-center agent) and tries to respond correctly to most of the customer's requests or questions.

When Bender encounters a situation where it cannot answer a customer question with a high degree of certainty (hereinafter called "confidence level") it forwards that request to a human to be anwered.

When such a person (e.g. call-center agent) responds to the customer requests, the response is not directly sent to the customer but instead it returns to Bender thus enabling Bender to learn from this process. It then takes the customer's request and the call-center agent's response and trains the machine learning component of Bender on the new request/response-pair.

## Warning

This is a `python 2.7`-code, it has not been converted to Python 3.x at the moment.
