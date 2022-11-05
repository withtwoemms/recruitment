# recruitment

> a lib for sourcing actionpacked entities capable of getting the job done

[![tests](https://github.com/withtwoemms/recruitment/workflows/tests/badge.svg)](https://github.com/withtwoemms/recruitment/actions?query=workflow%3Atests) [![codecov](https://codecov.io/gh/withtwoemms/recruitment/branch/main/graph/badge.svg?token=27Z4W0COFH)](https://codecov.io/gh/withtwoemms/recruitment) [![publish](https://github.com/withtwoemms/recruitment/workflows/publish/badge.svg)](https://github.com/withtwoemms/recruitment/actions?query=workflow%3Apublish) [![PyPI version](https://badge.fury.io/py/recruitment.svg)](https://badge.fury.io/py/recruitment)

# Overview

This code provides abstractions (mostly housed [here](https://github.com/withtwoemms/recruitment/blob/main/recruitment/agency/__init__.py) at time of writing this) that support unified and robust interaction with cloud services.
The `Broker` concept allows for the recasting of methods provided by cloud integration SDKs (e.g. [boto](http://boto.cloudhackers.com/en/latest/)) into an interface of your choosing. The `Commlink` concept houses method bindings defined by the `Broker.interface` while the `Consumer`, `Publisher`, and `Agent` entities implement the bound interface with [actionpack](https://github.com/withtwoemms/actionpack)ed resilience 💥

### Some Terms

When dealing with AWS data storage services, data is either _published_ or _consumed_.
This library presents a flexible API for doing just that.
The primary entities are a type of `Job` as follows:

* `Consumer`
* `Publisher`

This list outlines the main types used:

| Type | Description |
| --- | ----------- |
| `Config` | selects an interface to bind; holds credentials |
| `Commlink` | hosts the bound interface |
| `Contingency` | description of how to handle failure |
| `Coordinator` | namespace for describing how to do work |
| `Job` | top-level scope for executing work |

The following diagrams the relationship between the types:

![recruitment-diagram-1](https://user-images.githubusercontent.com/7152453/199785691-0880622f-9f92-4e90-8da1-3d204aaf11dc.png)

This one zooms-in on the `Broker`:

![recruitment-diagram-2](https://user-images.githubusercontent.com/7152453/199785718-5b74626b-b47f-45e6-bc1c-d9f6f365ffda.png)

There also exists an `Agent` type (not pictured) capable of both consuming _and_ publishing by requiring injection of both aforementioned `Job` types upon construction.
Work done (say by invoking `.consume` or `.publish`), is encapsulated as an `Effort` type.
The culmination of that work can be found under the eponymous attribute of an `Effort` instance.

| `Effort` | Description |
| --- | ----------- |
| `.culmination` | outcome from retrying |
| `.initial_attempt` | first attmept |
| `.final_attempt` | last attempt |
| `.attempts` | all attempts |
| `.retries` | attempts - initial_attempt |

Attempts are returned as `Result` types for convenience (see [here](https://github.com/withtwoemms/actionpack#what-are-actions-for) for more about that type).

# Usage

Say you'd like to pull files from s3; just follow these steps:

* Define a `Config`
```python
config = Config(
    service_name='s3',  # can also pass Broker.s3
    region_name='somewhere-in-the-world',
    access_key_id='s3curityBadge!',
    secret_access_key='p@ssw0rd!',
    endpoint_url='some-computer.com',
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

### Contingencies

Things can go wrong and when they do, it may be helpful to try again.
Passing a `Contingency` to a `Coordinator` is how you do that.
The class, alone, can be passed for some default behavior or it can be instantiated with the params.
The `max_retries` param is self-expanatory as it governs the maximum number of retries that will be attempted.
```python
from actionpack.actions import Call
from actionpack.utils import Closure

callback = Call(Closure(print, 'did a thing!')
Contingency(max_retries=3, reaction=callback)
```
The `reaction` param is a bit more nuanced.
If an `Action` is passed, it's guaranteed to be performed after the original job is completed.
This feature is great for logging or notifying other processes of the what has occurred.

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

Sometimes you'd like to resume work or even automate remediation.
In such cases, you could serialize, then persist progress locally for some other process to work from later.
This sort of design would facilitate the closed loop for ensuring whatever work tasked eventually gets done without error.

![Message Queue Resilience (Mark 1 1)](https://user-images.githubusercontent.com/7152453/157880655-fcbf0717-45c3-4783-a155-ff0c8a01891d.png)

The picture, above, demonstrates a fail-safe apparatus where a `Publisher` publishes messages to some cloud backend and record failures to local disk when encountered. The `Agent` lives in a separate execution context and can re-publish failed messages.