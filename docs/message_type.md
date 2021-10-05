<!--
    =====================================
    generator=datazen
    version=1.7.11
    hash=943116cbc50f3ad89bb285b9de51a831
    =====================================
-->

# Message Types

([back](README.md#documentation))

*See [Frame Types](message.md#message) for the message frame's
definition.*

This document describes protocol-defined message types so that certain
messages can be used to bootstrap practical decoding of other frames.

## Message Types

Extending this list of protocol-defined message types may become warranted as
canon use of the protocol identifies a gap where introduction of a new message
type could simplify implementations.

Appication-specific messaging proxied through this protocol can use the
[`agnostic`](#agnostic) message type.

Name | Value | Description
-----|-------|------------
[`agnostic`](#agnostic) | 0 | A message that has no protocol-defined interpretation.
[`text`](#text) | 1 | A message that should be interpreted as [UTF-8](https://en.wikipedia.org/wiki/UTF-8)-encoded, plain text.
[`json`](#json) | 2 | A message that should be interpreted as [UTF-8](https://en.wikipedia.org/wiki/UTF-8)-encoded, arbitrary [JSON](https://www.json.org/json-en.html).
[`enum`](#enum) | 3 | A message that should be interpreted as [JSON](https://www.json.org/json-en.html)-encoded [UserEnum](serializable.md#userenum) data.
[`enum_registry`](#enum-registry) | 4 | A message that should be interpreted as [JSON](https://www.json.org/json-en.html)-encoded [EnumRegistry](serializable.md#enumregistry) data.
[`primitive`](#primitive) | 5 | A message that should be interpreted as [JSON](https://www.json.org/json-en.html)-encoded [SerializablePrimitive](serializable.md#serializableprimitive) data.

### Agnostic

This message type can be used to send an arbitrary payload, it is useful
for testing of the message-transport correctness itself or as an
application-defined encapsulation.

### Text

This message type contains text. It is discouraged to encode an additional
layer of decoding assistance (such as a String identifier) within this
generic message. It is also discouraged to perform "logging" with this
message as [`stream`](message.md#stream) frames are intended for such
use-cases. If and when text-based messages serve practical purposes for
the protocol itself, they should exist as message types distinct from this
one despite also containing text.

### Json

This message contains [JSON](https://www.json.org/json-en.html)-encoded
data. Like the [`text`](message_type.md#text) message, if and when delivery
of protocol or application metadata commonly bootstraps functionality, a
new message type shall be defined and shall offer a supplementing schema.

Application's may use this message to send application data, but they must
implement logic for determining the data's purpose.

### Enum

This message contains runtime enumeration data. Whether by using the `name`
attribute (to identify a protocol-significant enumeration) or defining
further protocol-specific messages, a runtime enumeration may have
significance at the protocol level. Other enumerations may only be
significant to the application or runtime context.

### Enum Registry

This message contains a registry of runtime enumerations. Enumerations are
mapped to integer identifiers so they can be referenced as integers when a
type reference should be packed into a frame or message.

### Primitive

This message describes a fundamental type. It can be used by bespoke
implementations to corroborate how numerical, boolean or other values
should be interpreted.

A primitive type can be assigned an integer value so that an entity
transferred via this protocol can express the type of that entity by that
value (also requiring the "primitive type mapping" to be exchanged in
advance).
