<!--
    =====================================
    generator=datazen
    version=1.13.5
    hash=615acc661decc9cafed36a841c7cfa3b
    =====================================
-->

# Serializable Data Structures

([back](README.md#documentation))

* [UserEnum](#userenum)
* [EnumRegistry](#enumregistry)
* [SerializablePrimitive](#serializableprimitive)

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
[`enum`](message_type.md#enum)
message.*

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
    },
    "type": {
        "regex": "^user_enum$",
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
    "name": "sample_enum",
    "type": "user_enum"
}
```
### EnumRegistry

A registry for storing runtime enumerations (see also [UserEnum](#userenum)).
A mapping of integers to enumeration names is provided so that a specific
enumeration can map to an integer via a registry. An integer reference to an
enumeration may be required to allow channel values to map to the correct
Strings (and thus, the channel keeps track of this integer identifier for the
enumeration that it uses).

All data under `enums` can be transparently interpreted as individual
[UserEnum](#userenum)'s.


*This can be sent as an
[`enum_registry`](message_type.md#enum-registry)
message.*

#### [Cerberus](https://docs.python-cerberus.org/en/stable/) Data

```
{
    "enums": {
        "keysrules": {
            "type": "string"
        },
        "type": "dict",
        "valuesrules": {
            "type": "dict"
        }
    },
    "mappings": {
        "keysrules": {
            "type": "integer"
        },
        "type": "dict",
        "valuesrules": {
            "type": "string"
        }
    },
    "type": {
        "regex": "^enum_registry$",
        "type": "string"
    }
}
```

#### Example

```
{
    "enums": {
        "enum_a": {
            "default": "a",
            "mappings": {
                "1": "a",
                "2": "b",
                "3": "c"
            },
            "name": "enum_a",
            "type": "user_enum"
        },
        "enum_b": {
            "default": "d",
            "mappings": {
                "1": "d",
                "2": "e",
                "3": "f"
            },
            "name": "enum_b",
            "type": "user_enum"
        }
    },
    "mappings": {
        "0": "enum_a",
        "1": "enum_b"
    },
    "type": "enum_registry"
}
```
### SerializablePrimitive

An expression of a primitive type constituting a base unit that channels,
types and other entities may claim as an attribute. It contains information
allowing an implementation to store it and perform arithmetic operations on
it.


*This can be sent as an
[`primitive`](message_type.md#primitive)
message.*

#### [Cerberus](https://docs.python-cerberus.org/en/stable/) Data

```
{
    "integer": {
        "type": "boolean"
    },
    "max": {
        "required": false,
        "type": "integer"
    },
    "min": {
        "required": false,
        "type": "integer"
    },
    "name": {
        "type": "string"
    },
    "signed": {
        "type": "boolean"
    },
    "size": {
        "type": "integer"
    },
    "type": {
        "regex": "^serializable_primitive$",
        "type": "string"
    }
}
```

#### Example

```
{
    "integer": true,
    "max": 127,
    "min": -128,
    "name": "int8",
    "signed": true,
    "size": 1
}
```
