# recruitment

> a lib for sourcing actionpacked entities capable of getting the job done

[![tests](https://github.com/withtwoemms/recruitment/workflows/tests/badge.svg)](https://github.com/withtwoemms/recruitment/actions?query=workflow%3Atests) [![codecov](https://codecov.io/gh/withtwoemms/recruitment/branch/main/graph/badge.svg?token=27Z4W0COFH)](https://codecov.io/gh/withtwoemms/recruitment) [![publish](https://github.com/withtwoemms/recruitment/workflows/publish/badge.svg)](https://github.com/withtwoemms/recruitment/actions?query=workflow%3Apublish) [![PyPI version](https://badge.fury.io/py/recruitment.svg)](https://badge.fury.io/py/recruitment)

![Message Queue Resilience (Mark 1 1)](https://user-images.githubusercontent.com/7152453/157880655-fcbf0717-45c3-4783-a155-ff0c8a01891d.png)

# Overview

This code provides abstractions (mostly housed [here](https://github.com/withtwoemms/recruitment/blob/main/recruitment/agency/__init__.py) at time of writing this) that support unified and robust interaction with cloud services.
The `Broker` concept allows for the recasting of methods provided by cloud integration SDKs (e.g. [boto](http://boto.cloudhackers.com/en/latest/)) into an interface of your choosing. The `Communicator` SDK houses method bindings defined by the `Broker.interface` while the `Consumer`, `Publisher`, and `Agent` entities implement the bound interface with [actionpack](https://github.com/withtwoemms/actionpack)ed resilience 💥

The picture, above, demonstrates a fail-safe apparatus where a `Publisher` publishes messages to some cloud backend and record failures to local disk when encountered. The `Agent` lives in a separate execution context and can re-publish failed messages.