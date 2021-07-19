<!--
    =====================================
    generator=datazen
    version=1.7.8
    hash=598f255c994f0029f68c4f0062410973
    =====================================
-->

# Message Types

([back](../README.md#documentation))

*See [Primitive Types](primitive.md) for default-type mappings.*

This document describes frames: the discrete unit of information transfer for
this project. General frame structure as well as frame-specific schemas are
covered.

**All fields are packed in
[network byte-order](https://en.wikipedia.org/wiki/Endianness#Networking)
(big-endian).**

## Frame Header

These header fields appear in every message, regardless of the frame type.
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
`app_id` | [`defaults`](primitive.md#defaults)`.id` | An application identifier used to allow unique identification of the sender (not a security feature). It is assumed that users control both client and server, so an application identifier can be used to perform arbitration on multiple data sources. If this feature isn't needed, this field can be ignored.
`type` | [`defaults`](primitive.md#defaults)`.enum` | The type of frame that should be parsed after this header. Information on parsing each frame is below.
`timestamp` | [`defaults`](primitive.md#defaults)`.timestamp` | An integer timestamp for the frame. Neither an exact epoch or unit is strictly defined.
`size` | [`defaults`](primitive.md#defaults)`.count` | A size parameter to be interpreted based on the frame type.

## Frame Types

Note that frame types are considered a type of `enum` so it's packed as
`uint8` when transported. As this protocol is updated, it's
possible that new frame types will be added.

Name | Value | Description
-----|-------|------------
[`invalid`](#invalid) | 0 | A frame type of zero is not considered any kind of frame, though it is sometimes useful to use when testing protocol or client/server machinery without any real data to transfer.
[`data`](#data) | 1 | A simple frame containing an array of channel indices followed by channel data appearing in the same order as indicated by the array of indices.
[`event`](#event) | 2 | A simple frame containing an array of channel indices followed by an "event" structure containing a "previous" and "current" pair of values and timestamps. This frame is useful for data that warrants asynchronous updates more than synchronous ones.

### Invalid

No further interpretation of an `invalid` frame can be made. If a client
is expecting to process real data and encounters this frame, discard and
move on to the next delivery of the frame-encapsulating transmission.

If the transport mechanism is stream-oriented and can't distinguish
discrete transmissions, the client should close the stream and indicate
error.


### Data

TODO.

### Event

TODO.
