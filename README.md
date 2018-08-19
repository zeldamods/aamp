# Nintendo parameter archive (AAMP) library

Everything should work correctly for BotW parameter archives, though this hasn't been tested a lot.

Some more esoteric parameter types are left unsupported currently.

## Setup

Install with `pip install aamp` or on Windows `py -m pip install aamp`.

### Converter usage

`aamp_to_yml` will convert an AAMP to a human readable representation.
`yml_to_aamp` will do the opposite.

### Library usage

To read a parameter archive, create a Reader and give it the binary archive data,
then call `parse()` to get a ParameterIO. This API is purposefully very similar to Nintendo's
official parameter utils to help with reverse engineering and re-implementing parts of the game code.

Parameter is a simple value, for example a boolean or an integer.

ParameterObject is a key-value mapping where keys are strings and values are always Parameters.

ParameterList is also a key-value mapping, but it contains objects and other lists rather than Parameters.

ParameterIO is a special ParameterList with some extra attributes, like a version number and a type string (usually `xml`).

```py
>>> import aamp
>>> reader = aamp.Reader(open('test_data/DamageReactionTable.bxml', 'rb').read())
>>> pio = reader.parse()
>>> pio.list('param_root').list('Basic').object('Edge')
ParameterObject(params={375673178: True, 2982974660: True, 4022901097: True, 2861907126: True, 3947755327: True, 1529444359: False})
>>> pio.list('param_root').list('Basic').object('Edge').param('Damage')
True
```

ParameterObject:
* `.param(param_name)` returns a parameter. KeyError is raised if the parameter doesn't exist.
* `.set_param(param_name, value)`

ParameterList:
* `.list(list_name)` returns a parameter list. KeyError is raised if the list doesn't exist.
* `.object(object_name)` returns a parameter object. KeyError is raised if the object doesn't exist.
* `.set_list(list_name, param_list)`
* `.set_object(object_name, param_object)`

ParameterIO:
* Same as ParameterList, but with extra attributes `version` (usually 0) and `type` (usually `xml`).

For writing a binary parameter archive, create a Writer and pass it a ParameterIO,
then call `write(stream)` with a seekable stream.

## License

This software is licensed under the terms of the GNU General Public License, version 2 or later.
