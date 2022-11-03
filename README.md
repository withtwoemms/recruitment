# recruitment

> a lib for sourcing actionpacked entities capable of getting the job done

[![tests](https://github.com/withtwoemms/recruitment/workflows/tests/badge.svg)](https://github.com/withtwoemms/recruitment/actions?query=workflow%3Atests) [![codecov](https://codecov.io/gh/withtwoemms/recruitment/branch/main/graph/badge.svg?token=27Z4W0COFH)](https://codecov.io/gh/withtwoemms/recruitment) [![publish](https://github.com/withtwoemms/recruitment/workflows/publish/badge.svg)](https://github.com/withtwoemms/recruitment/actions?query=workflow%3Apublish) [![PyPI version](https://badge.fury.io/py/recruitment.svg)](https://badge.fury.io/py/recruitment)

# Overview

This code provides abstractions (mostly housed [here](https://github.com/withtwoemms/recruitment/blob/main/recruitment/agency/__init__.py) at time of writing this) that support unified and robust interaction with cloud services.
The `Broker` concept allows for the recasting of methods provided by cloud integration SDKs (e.g. [boto](http://boto.cloudhackers.com/en/latest/)) into an interface of your choosing. The `Communicator` SDK houses method bindings defined by the `Broker.interface` while the `Consumer`, `Publisher`, and `Agent` entities implement the bound interface with [actionpack](https://github.com/withtwoemms/actionpack)ed resilience 💥

### Some Terms

When dealing with AWS data storage services, data is either published or consumed.
This library presents a flexible API for doing just that.
The primary entities are a type of `Job` as follows:

* `Consumer`
* `Publisher`

A `Job` leverages a `Coordinator` to do work.
A `Coordinator` is constructed using a `Commlink` for making external calls and an optional `Contingency` for responding to failures when making external calls.
Each `Commlink` hosts the communication interface provided by a `Config`.
Instatiating a `Config` with a given service name binds a different interface.
The following diagram the relationship between the types:

![recruitment-diagram-1](https://user-images.githubusercontent.com/7152453/199724835-9bf8a86b-0f55-48ce-9b7e-48e4bdb37224.png)

This one zooms-in on the `Broker`:

![recruitment-diagram-2](https://user-images.githubusercontent.com/7152453/199724871-78f8b7f6-9251-4adb-9d6e-a9509f3575d2.png)

There also exists an `Agent` type (not pictured) capable of both consuming _and_ publishing by requiring injection of the aforementioned `Job` types upon construction.

# Usage

Say you'd like to pull files from s3; just follow these steps:

* Define a `Config`
```python
config = Config(
    service_name='s3',  # can also pass Broker.s3
    region_name=,
    access_key_id=,
    secret_access_key=,
    endpoint_url=,
)
```
* Build the `Job`
```python
consumer = Consumer(
    Coordinator(
        Commlink(config),
        Contingency
    )
)
```

Simple as that.
Give it a try.
Being that a `Consumer` was built, above, the `.consume` method is available.
Similar can by done with a `Publisher`.
A `Result` type is returned for convenience (see [here](https://github.com/withtwoemms/actionpack#what-are-actions-for) for more info).

# Development

### Setup

Build scripting is managed via [`noxfile`](https://nox.thea.codes/en/stable/config.html).
Execute `nox -l` to see the available commands (set the `USEVENV` environment variable to view virtualenv-oriented commands).
To get started, simply run `nox`.
Doing so will install `recruitment` on your PYTHONPATH.
Using the `USEVENV` environment variable, a virtualenv can be created in the local ".nox/" directory with something like: `USEVENV=virtualenv nox -s recruitment-venv-install-3.10`.

All tests can be run with `nox -s test` and a single test can be run with something like the following:

```
TESTNAME=<tests-subdir>.<test-module>.<class-name>.<method-name> nox -s test
```

Coverage reports are optional and can be disabled using the `COVERAGE` environment variable set to a falsy value like "no".

---

## Coming Soon...

Sometimes you'd like to resume work or automate remediation.
In such a case, you could serialize, then persist progress locally for some other process to work from later.
This sort of design would facilitate the closed loop for ensuring whatever work tasked eventually gets done without error.

![Message Queue Resilience (Mark 1 1)](https://user-images.githubusercontent.com/7152453/157880655-fcbf0717-45c3-4783-a155-ff0c8a01891d.png)

The picture, above, demonstrates a fail-safe apparatus where a `Publisher` publishes messages to some cloud backend and record failures to local disk when encountered. The `Agent` lives in a separate execution context and can re-publish failed messages.