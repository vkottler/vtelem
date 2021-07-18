<!--
    =====================================
    generator=datazen
    version=1.7.8
    hash=7941b7bc49b40569438202344ffc3086
    =====================================
-->

# Primitive Types

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
`id` | `uint16`
