re-worker-func
==============
Func Worker for Release Engine for our new [release engine hotness](https://github.com/RHInception/?query=re-)

[![Build Status](https://api.travis-ci.org/RHInception/re-worker-func.png)](https://travis-ci.org/RHInception/re-worker-func/)

## Unittests
Use *nosetests -v --with-cover --cover-min-percentage=80 --cover-package=replugin test/* from the main directory to execute unittests.

## Configuration
The configuration file uses the following pattern in JSON format:

```
{
    "FUNC_COMMAND": {
        "SUB_COMMAND_1": ["REQUIRED", "PARAMETERS"],
        "SUB_COMMAND_2": ["ONE_ITEM"],
        "SUB_COMMAND_N": []
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
