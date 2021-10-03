<!--
    =====================================
    generator=datazen
    version=1.7.11
    hash=4b18188cdfb9c35b5a586e330cc2c0c8
    =====================================
-->

# Serializable Data Structures

([back](README.md#documentation))

* [UserEnum](#userenum)

It's frequent that a telemetry protocol needs to support a negotiation or
configuration handshake for individual entities to transfer data as densely as
possible.

A simple example: one "channel" of information may exist as a time series of
discrete values. For practical use, such a "channel" should have things like:
* A human-readable name.
* Be expressed in a typical SI unit, or an otherwise context-specific unit.
* Be scaled from a "raw reading" to the actual physical phenomenon (i.e.
pressure read as a voltage, convert volts to a unit of pressure and apply
a sensor-specific scaling).
* A transparent "primitive type" to understand storage and precision
constraints.
* A transparent mapping from "human-readable value" to "primitive-type value"
for channels that may encode a logical enumeration rather than a true
measurement.

This list could grow longer depending on what other features may be desired. In
any case, the burden of duplicating any of the above information in a single
data-point delivery is significant. For a single data-point delivery, we
ideally want zero overhead: nothing more than the actual value (in its
"primitive type" binary representation) and optionally a timestamp (optional
because a receiver can apply a timestamp and accept some loss in precision).

If we only have one "channel", this could be simple: only send single points of
data (or an array of points) in some kind of datagram or packet. Even in this
contrived example there are problems, how can sender and receiver be
guaranteed-synchronized on some of the attributes, even the primitive type?

This problem has no simple solution (note how many bespoke "application layer"
protocols we have to support today!). In the case of this project, the protocol
as a whole works to support good ergonomics and simplicity for expressing
attributes of raw data and information.

**Below are explicit schemas of JSON-representable messages and data structures
that may be used throughout the protocol's implementation (and linked to from
other parts of documentation).**

## Schemas

In the Python implementation of the protocol,
[Cerberus](https://docs.python-cerberus.org/en/stable/) is used for schema
enforcement at runtime. Python also has built-in support for JSON encoding and
decoding.

### UserEnum

The `name` value should be
[snake case](https://en.wikipedia.org/wiki/Snake_case). Note that although
keys for `mappings` are integers, they need to be converted back to integers
from their JSON representation (since JSON only has String keys, see
[RFC 7159](https://datatracker.ietf.org/doc/html/rfc7159#section-4)).


*This can be sent as an
[`enum`](message_type.md#enum) message.*

#### [Cerberus](https://docs.python-cerberus.org/en/stable/) Data

```
{
    "default": {
        "type": "string"
    },
    "mappings": {
        "keysrules": {
            "type": "integer"
        },
        "type": "dict",
        "valuesrules": {
            "regex": "[a-z]+",
            "type": "string"
        }
    },
    "name": {
        "regex": "[a-z_]+",
        "type": "string"
    }
}
```

#### Example

```
{
    "default": "a",
    "mappings": {
        "1": "a",
        "2": "b",
        "3": "c"
    },
    "name": "sample_enum"
}
```
