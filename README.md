# Kafka-REST-Confluent

Provides a RESTful interface to a Kafka cluster by [Confluent](https://www.confluent.io/).

Full API overwiew can be found [here](https://docs.confluent.io/current/kafka-rest/docs/api.html#overview).

## Usage

```
juju deploy kafka
juju deploy kafka-rest-confluent 
juju add-relation kafka-rest-confluent kafka
```

## Authors

This software was created in the [IBCN research group](https://www.ibcn.intec.ugent.be/) of [Ghent University](https://www.ugent.be/en) in Belgium. This software is used in [Tengu](https://tengu.io), a project that aims to make experimenting with data frameworks and tools as easy as possible.

 - Sander Borny <sander.borny@ugent.be>