<!--
    =====================================
    generator=datazen
    version=1.13.5
    hash=c2cd426a94cf08ea1ba803b0a3e66209
    =====================================
-->

# Primitive Types

([back](README.md#documentation))

All transmission of information over a physical medium that uses binary bits
must be formatted so that receivers can understand it.

This document describes fundamental types used to transfer data.

## Standard Types

All transmission of information uses these standard types, the telemetry
runtime can only otherwise be extended with custom enumerations. Channels can
only store the following primitive types:

Name | Bytes | Signed | Integer
-----|-------|--------|--------
`boolean` | 1 | `False` | `False`
`int8` | 1 | `True` | `True`
`uint8` | 1 | `False` | `True`
`int16` | 2 | `True` | `True`
`uint16` | 2 | `False` | `True`
`int32` | 4 | `True` | `True`
`uint32` | 4 | `False` | `True`
`int64` | 8 | `True` | `True`
`uint64` | 8 | `False` | `True`
`float` | 4 | `True` | `False`
`double` | 8 | `True` | `False`

## Defaults

Some protocol constants must be understood ahead of trying to parse messages.
Based on the purpose of a "header" or metadata field in a message, the default
types used are as follows:

Purpose | Type
--------|-----
`version` | `uint8`
`enum` | `uint8`
`timestamp` | `uint64`
`metric` | `uint32`
`count` | `uint32`
`crc` | `uint32`
`id` | `uint16`

**It is expected that clients and servers implementing protocols defined by
this project understand these defaults ahead of encoding or decoding
information.**

These defaults can change based on `version`, so implementations should keep
track of one or more "`version` to defaults" mappings in order to correctly
encode and decode messages. It is assumed that the mapping of `version` to
`uint8` will **never** change.
