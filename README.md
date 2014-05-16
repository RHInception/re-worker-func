re-worker-func
==============
Func Worker for Release Engine for our new [release engine hotness](https://github.com/RHInception/?query=re-)

[![Build Status](https://api.travis-ci.org/RHInception/re-worker-func.png)](https://travis-ci.org/RHInception/re-worker-func/)

## Unittests
Run ``make tests`` from the main directory to execute unittests
(including [pep8](https://pypi.python.org/pypi/pep8) and
[pyflakes](https://pypi.python.org/pypi/pyflakes))

## Configuration
The configuration file uses the following pattern in JSON format.

```json
{
    "FUNC_MODULE.METHOD": ["NAMES_OF", "REQUIRED", "PARAMETERS"],
}
```

### Method with One Parameter

This demonstrates a **funcworker** configured to run a func module
method which requires one parameter:

```json
# conf/example.json
{
    "command.run": ["command"]
}
```

The ``example.json`` configuration (above) defines the behavior of a
**funcworker** which runs the **command** module's ``run`` task. The
task requires one argument, ``command`` (as noted in the square
brackets, above).

When used as a step in a playbook, the parameter name described above
is used to supply arguments to the actual func method call. Example of
the above snippet, used in a playbook:

```json
    // ...
    "steps": [
        {
            "name": "Example step",
            "plugin": "funcworker",
            "parameters": {
                "method": "command.run",
                "command": "touch /tmp/foo"
            }
        }
    ],
    // ...
```




Example:
```
{
    "yumcmd": {
        "install": ["package"],
        "remove": ["package"],
        "update": []
    }
}
```

**Note:** See
[Func - Module List](https://fedorahosted.org/func/wiki/ModulesList)
for more information.


**TODO**: Cut over to RTD when ready.
# For documentation see the [Read The Docs](http://release-engine.readthedocs.org/en/latest/workers/reworkerfunc.html) documentation.

# Use as an Engine Step

After ``steps`` below you can see examples of how to incorporate a
**funcworker** configured to with the ``service`` command, and one
configured with the ``yumcmd`` command.

```json
{
    "project": "example project",
    "ownership": {
        "id": "Some team",
        "contact": "someteam@example.com"
    },
    "steps": [
        {
            "name": "stop foo service",
            "plugin": "funcworker",
            "parameters": {
                "command": "service",
                "subcommand": "stop",
                "service": "megafrobber"
            }
        },
        {
            "name": "foo",
            "plugin": "funcworker",
            "parameters": {
                "command": "yumcmd",
                "subcommand": "install",
                "package": "xemacs",
            }
        }
    ]
}
```
