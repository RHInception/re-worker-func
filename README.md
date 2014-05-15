re-worker-func
==============
Func Worker for Release Engine for our new [release engine hotness](https://github.com/RHInception/?query=re-)

[![Build Status](https://api.travis-ci.org/RHInception/re-worker-func.png)](https://travis-ci.org/RHInception/re-worker-func/)

## Unittests
Run ``make tests`` from the main directory to execute unittests
(including [pep8](https://pypi.python.org/pypi/pep8) and
[pyflakes](https://pypi.python.org/pypi/pyflakes))

## Configuration
The configuration file uses the following pattern in JSON format:

```
{
    "FUNC_MODULE": {
        "COMMAND_1": ["REQUIRED", "PARAMETERS"],
        "COMMAND_2": ["ONE_ITEM"],
        "COMMAND_N": []
    }
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
