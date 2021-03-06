## 2017-12-12

- Initial release

## 2017-12-12

Add generate project meta command

- [Improve] Detecting parent class tree
- [Add] Option 'Pick None' when generate class constructor
- [Fix] Find namespace only detect at BOL

## 2017-12-13

Add option to enable php7 coding session

## 2017-12-13 - v1.1.2

- Fix use same class in same namespace
- Fix generate getter setter command

## 2017-12-16

- Command API not change but its logic has many changes
- Fix bug: use same class in same namespace (again)
- Fix generate getter and setter in pair
- Register command, Override Abstract Command

## 2017-11-16

- Update getter_setter message
- Fix properties getter/setter order

## 2017-12-16

- Fix generate getter/setter method name

## 2017-12-19

- Fix insert namespace relative to project root
- Fix expand fqcn and use class selection list sorting

## 2017-12-20

- Fix parser to accept function pass by reference declaration

## 2017-12-25

- Allow native hintable in method generation

## 2017-12-26

- Fix hint in method generation
- Add phpme_copy_method_command
- Add phpme_generate_test_command
- Add setting: test_case_pattern, test_public_only, test_generate_content
- Fix class method and properties parsing

## 2017-12-27

- Add total method/properties info
- Reduce identic logic command

## 2017-12-28

- Fix generate getter/setter (not propose exists method)

## 2017-12-29

- Add log_message setting
- Fix generate test method, remove ampersand in method name
- Fix generate test method, add ampersand suffix

## 2018-01-27

- Generate method now on first active cursor

## 2018-01-30

- Add default visibility method

## 2018-05-02

- Add declare_strict option
- Remove prefix_fqcn option
- Rename Expand Fully Qualified Namespace Class to Expand FQCN
- Add Expand FQCN (w/ Leading Backslash)
- Edit insert namespace now can be done without opening php tag

## 2018-05-07

- Remove return type on test method generation

## 2018-05-08

- Modify default method test stub

## 2018-02-19

- Fix bug on project_meta_command
- Change behaviour of project_meta_command
- Simplify generate test method stub
- Remove docblock on test method generation
- Fix bug on generate setter