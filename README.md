# PHPME

Make your PHP coding session more fun than ever.

This plugin developed based on [PHP Companion][4] plugin.

## Installation

### Package control

You can install this plugin easily with [Sublime Package Control][5].

Then there is two option:
- Search for PHPMe in package control, select install then you're ready.
- Add this plugin repository [https://github.com/eghojansu/phpme.git][2].
  (`Package Control: Add Repository` to insert repository url).

### Download Manually

Download tar/zip from [this plugin repository][1], extract them then put the extracted folder into your sublime package folder.

## Commands

All command prefixed by `phpme_`

### insert_namespace

Insert namespace on the current file. This feature use composer.json file (if exists) to guest namespace.
If there is no composer.json you can configure in your project/global setting. See settings below.

### use_class

Use/import class.

To use this feature you need to put cursor on valid class symbol then trigger this command.

(Support multiple selection).

### expand_fqcn

Expand class to Fully Qualified Name Space.

To use this feature you need to put cursor on valid class symbol then trigger this command.

(Support multiple selection).

### implements

Implements interface method.

To use this feature you need to implements your class with one or more interface. Trigger this command then pick one or more methods you wants to implement.

(Support parent tree).

### override_method

To use this feature you need to extends your class with parent class. Trigger this command then pick one or more methods you wants to override.

(Support parent tree).

### getter_setter

Generate getter and setter method based on properties on your class.
This command accept `mode` as argument and its value can be 1, 2 or 3.

    (1) generate getter;
    (2) generate setter and;
    (3) generate getter and setter.

To use this feature you do not need to put cursor on valid symbol, just trigger this command.

### generate_constructor

Generate class constructor. You can pick declared properties as its parameter.

To use this feature you do not need to put cursor on valid symbol, just trigger this command.

### goto_definition_scope

Search for a method definition based on the current scope. It will fallback to the "goto_definition" command if a match was not found.

To use this feature you need to put cursor on a method name, then trigger this command.

(Not support multiple cursor).

## Settings

Settings can be stored either in your system wide "PHPMe.sublime-settings" file or in the project
settings file. This allows you to set preferences per-project if you need to.

If you're storing settings in a project file, put them in a phpme node like this:

```
"phpme": {
    "exclude_dir": [
        "vendor",
        "build"
    ]
}
```

### namespaces
Namespace and relative path to current folder pairs, trailing slash/backslash are optional.
Relative path can be array. This configuration mimic composer.json autoload psr-4/psr-0 schema.

Type: json, examples:
```
"namespaces": {
     "App\\": "src/",
     "App\\Test\\": "tests/src/"
     "AnotherNamespace\\": ["other/", "other2/"]
}
```

### exclude_dir

List of directories to exclude when searching for the class declaration file.
Path is relative to the project directory.

Please note that the filtering is done after the search in the index. So this option has no impact on performance,
it's just a convenient way to avoid duplicate namespace declaration in some case.

Type: array of exclude dir pattern

### use_sort_length

When importing use statements with the `phpme_use_class` command, sort statements by the length of the line.

Type: boolean, defaults to false.

### allow_use_from_global_namespace

Set to true to allow plugin search class in globals namespace.
Need the php binary to work.

Type: boolean, defaults to true.

### docblock_inherit

Copy comment doc from parent or interface to implemented class.

Type: string, valid options are "none", "copy" or "inheritdoc" defaults to "none"

### prefix_fqcn

Set true, to add leading backslash when performing `phpme_expand_fqcn`.

Type: boolean, defaults to true.

### generate_docblock

Generate docblocks for getter, setter and constructor.

Type: boolean, defaults to false.

### setter_chainable

Make generated setter chainable (return $this).

Type: boolean, defaults to true.

### static_property

Keyword to use for static property.

Type: string, valid options are "static" or "self" defaults to "static"

## Keybinding

This plugin do not provide keybindings. You will have to install your own shortcuts. This examples will give you the shortcuts I personally use.

```json
[
    { "keys": ["f3"], "command": "phpme_implements" },
    { "keys": ["shift+f3"], "command": "phpme_override_method" },
    { "keys": ["f4"], "command": "phpme_insert_namespace" },
    { "keys": ["f5"], "command": "phpme_use_class" },
    { "keys": ["f6"], "command": "phpme_expand_fqcn" },
    { "keys": ["f7"], "command": "phpme_generate_constructor" },
    { "keys": ["f8"], "command": "phpme_getter_setter", "args": {"mode": 3} },
    { "keys": ["shift+f12"], "command": "phpme_goto_definition_scope" }
]
```

## Known Issues

- This plugin works based on Regex. If you feel this plugin sucks detecting your code, please let me know.

  [Submit issues][3].
- We assume you're working with php7. Any text on docblock for variable will be included as variable type when generate method.
- We do not support multiple class declaration in one file. As we use regex to detect curly brace (`}`) as the end of class.


```sh
Happy coding,

ekokurniawan
(Web Developer)
```

[1]: https://github.com/eghojansu/phpme
[2]: https://github.com/eghojansu/phpme.git
[3]: https://github.com/eghojansu/phpme/issues
[4]: https://packagecontrol.io/packages/PHP%20Companion
[5]: https://packagecontrol.io/installation
