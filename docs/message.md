<!--
    =====================================
    generator=datazen
    version=2.0.0
    hash=5986e333e4611fde732fb78e7af829b4
    =====================================
-->

# Frame Types

([back](README.md#documentation))

*See [Primitive Types](primitive.md#defaults) for `default` type
mappings.*

This document describes frames: the discrete unit of information transfer for
this project. General frame structure as well as frame-specific schemas are
covered.

**All fields are packed in
[network byte-order](https://en.wikipedia.org/wiki/Endianness#Networking)
(big-endian).**

## Frame Header

These header fields appear in every frame, regardless of the type.
Given this header schema and the frame-specific interpretation of `size` it
becomes possible to determine a frame's boundary.

Depending on the transport mechanism, the start of the next frame may come
at the start of the next byte or the entire protocol may be wrapped in yet
another framing mechanism (such as some form of
[consistent overhead byte stuffing](https://ieeexplore.ieee.org/document/769765)).

Semantics of frame transfer based on the transport mechanism is not covered in
this document.

Field | Type | Description
------|------|------------
`length` | `defaults.count` | The length of this frame (less this field) in bytes. This is an essential first field as it allows stream-based reading interfaces to stay synchronized with the flow of data.
`app_id` | `defaults.id` | An application identifier used to allow unique identification of the sender (not a security feature). It is assumed that users control both client and server, so an application identifier can be used to perform arbitration on multiple data sources. If this feature isn't needed, this field can be ignored.
`type` | `defaults.enum` | The type of frame that should be parsed after this header. Information on parsing each frame is below.
`timestamp` | `defaults.timestamp` | An integer timestamp for the frame. Neither an exact epoch or unit is strictly defined.
`size` | `defaults.count` | A size parameter to be interpreted based on the frame type.

## Frame Footer

The footer is **not required** and its presence should be checked once the
rest of a frame's contents have been parsed.

Field | Type | Description
------|------|------------
`crc` | `defaults.crc` | An optional checksum for the frame. In [Python](https://www.python.org/) this is done with [`zlib.crc32`](https://docs.python.org/3/library/zlib.html#zlib.crc32) on the entire frame's contents minus the checksum field itself.

## Frame Structure

Frames contain a number of possible payloads based on the `type` field.
A `header` and optional `footer` encapsulate this payload.

[`header`](#frame-header) | frame contents | [`[footer]`](#frame-footer)
--------------------------|----------------|----------------------------

## Frame Types

Note that frame types are considered a type of `enum` so it's packed as
`uint8` when transported. As this protocol is updated, it's
possible that new frame types will be added.

Name | Value | Description
-----|-------|------------
[`data`](#data) | 1 | A simple frame containing an array of channel indices followed by channel data appearing in the same order as indicated by the array of indices.
[`event`](#event) | 2 | A simple frame containing an array of channel indices followed by an "event" structure containing a "previous" and "current" pair of values and timestamps. This frame is useful for data that warrants asynchronous updates more than synchronous ones.
[`invalid`](#invalid) | 0 | A frame type of zero is not considered any kind of frame, though it is sometimes useful to use when testing protocol or client/server machinery without any real data to transfer.
[`message`](#message) | 3 | A frame containing bytes for one portion of a variable-length message.
[`stream`](#stream) | 4 | A frame containing bytes from a stream channel starting at a provided index.

### Data

A data frame stores `size` channel-data elements where the frame body
consists of two `size` length arrays:
1. The first array contains `defaults.id` elements that hold the
[channel identifiers](channel_identifier.md).
1. The second array contains channel data in the order that the indices
appeared where each element's size in bytes must be understood in advance
by mapping the channel index to a specific [primitive](primitive.md) type.

#### Frame Contents Structure

`channel_id[0]` | . . . | `channel_id[size - 1]` | `channel_data[0]` | . . . | `channel_data[size - 1]`
----------------|-------|------------------------|-------------------|-------|-------------------------


### Event

An event frame stores `size` channel-event elements where the frame body
also (like the [data](#data) frame) consists of two `size` length arrays:
1. The first array contains `defaults.id` elements that hold the
[channel identifiers](channel_identifier.md).
1. The second array contains event data in the order that the indices
appeared where an event structure is as follows:

    Field | Type
    ------|-----
    Previous Channel Value | Channel's Primitive Type
    Previous Timestamp | `defaults.timestamp`
    Current Channel Value | Channel's Primitive Type
    Current Channel Timestamp | `defaults.timestamp`

    Timestamps should be considered the times that the channel value was
    last assigned a value, even if it was the same value. *This is true
    for all channels whether they emit events or not.*

#### Frame Contents Structure

`channel_id[0]` | . . . | `channel_id[size - 1]` | `channel_event[0]` | . . . | `channel_event[size - 1]`
----------------|-------|------------------------|--------------------|-------|--------------------------


### Invalid

No further interpretation of an `invalid` frame can be made. If a client
is expecting to process real data and encounters this frame, discard and
move on to the next delivery of the frame-encapsulating transmission.

If the transport mechanism is stream-oriented and can't distinguish
discrete transmissions, the client should close the stream and indicate
error.


### Message

A message frame is used to transfer runtime information that can help
telemetry emitters and clients correctly interpret any frame. In order for
frames to contain minimal data but remain coherent, some configuration
messages must be transferred asynchronously such as ones that describe
channels based on [channel identifiers](channel_identifier.md), enumeration
and types mapping, et cetera.

In order for a generic message transportation mechanism to be useful in
practice, the protocol defines a [message type](message_type.md) mapping
that supports both protocol-agnostic and protocol-specific messages. Fields
found within the message frame are described below:

Field | Type | Description
------|------|------------
`message_type` | `defaults.enum` | An enumeration associated with this message so it can be interpreted based on protocol-defined [message types](message_type.md).
`message_number` | `defaults.id` | The instance of this message type being sent. This should increment only if the full message payload differs from that of the current message payload, otherwise a message can be sent again with the same number. **This instance number is specific to the message type and is not global for all message types.**
`message_crc` | `defaults.crc` | A checksum of this message's contents (all fragment bytes). It can be assumed that a new message of a given type with an equivalent checksum to a previously-seen message of the same type has identical contents. Messages can be stored in a cache with checksums as keys, but receivers should compare new message contents and caches evict stale entries on an interval regular enough to ensure correctness.
`fragment_index` | `defaults.id` | The current fragment of the message contained in this frame.
`total_fragments` | `defaults.id` | The total number of fragments required to assemble the full message payload.
`fragment_byte[n]` | `uint8` | A byte belonging to the message fragment. In total there are `size` bytes in the fragment.

#### Frame Contents Structure

`message_type` | `message_number` | `message_crc` | `fragment_index` | `total_fragments` | `fragment_byte[0]` | . . . | `fragment_byte[size - 1]`
---------------|------------------|---------------|------------------|-------------------|--------------------|-------|--------------------------


### Stream

A stream frame contains data for a stream-oriented channel. Regardless of
the current state of the channel as understood by the emitter or any
current clients, the frame should contain `size` elements of its primitive
type and also carry the element index that the stream frame should start
at. Fields found within the frame are described below:

Field | Type | Description
------|------|------------
`channel_id` | `defaults.id` | The [channel identifier](channel_identifier.md) used to determine channel attributes (like its primitive type).
`stream_index` | `defaults.count` | Location in the stream where these `size` elements start.
`channel_data[n]` | Channel's Primitive Type | An element in the stream at position `n`.

#### Frame Contents Structure

`channel_id` | `stream_index` | `channel_data[stream_index]` | . . . | `channel_data[stream_index - size - 1]`
-------------|----------------|------------------------------|-------|----------------------------------------
